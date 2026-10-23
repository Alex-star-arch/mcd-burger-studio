#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
麦当劳「真」随心配 —— 一键启动器。

做的事（按顺序）：
  1. 体检关键文件是否齐全（缺文件直接报错，不装作能跑）
  2. 从 --port 开始找第一个能绑定的端口（最多试 20 个，被占用自动 +1）
  3. 先 bind 再起 serve 线程，然后轮询 /api/ping，通了才打印访问地址
  4. 可选自动打开系统浏览器

用法：
  python scripts/run.py                     # 默认 127.0.0.1:8765
  python scripts/run.py --port 9000
  python scripts/run.py --lan               # 监听 0.0.0.0，同一 WiFi 可访问并投票
  python scripts/run.py --no-open           # 无头环境 / CI，不弹浏览器
  python scripts/run.py --check             # 只体检，不启动服务

零第三方依赖，Python 3.8+。
"""
import argparse
import json
import os
import socket
import sys
import threading
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

PORT_TRIES = 20
REQUIRED = [
    "assets/burger_components_3d.html",
    "assets/components3d.js",
    "assets/materials.json",
    "assets/vendor/three.min.js",
    "assets/vendor/OrbitControls.js",
    "scripts/studio_server.py",
]


def _utf8_stdout():
    """Windows 控制台默认 GBK，emoji 会炸；能改就改成 utf-8 并开行缓冲。

    行缓冲很关键：后台任务/管道捕获输出时，块缓冲会让"已启动 + 地址"迟迟不出现。
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
        except Exception:
            pass


def preflight():
    """返回 (ok, 问题列表)。"""
    problems = []
    if sys.version_info < (3, 8):
        problems.append("Python 版本 %s 低于 3.8" % sys.version.split()[0])
    for rel in REQUIRED:
        if not os.path.isfile(os.path.join(ROOT, rel)):
            problems.append("缺少文件: " + rel)
    mat = os.path.join(ROOT, "assets", "materials.json")
    if os.path.isfile(mat):
        try:
            with open(mat, encoding="utf-8") as f:
                data = json.load(f)
            if not data.get("materials"):
                problems.append("materials.json 里 materials 为空")
        except Exception as e:
            problems.append("materials.json 解析失败: %s" % e)
    gal = os.path.join(ROOT, "gallery", "gallery.json")
    if os.path.isfile(gal):
        try:
            with open(gal, encoding="utf-8") as f:
                if not isinstance(json.load(f).get("designs"), list):
                    problems.append("gallery.json 缺 designs 数组")
        except Exception as e:
            problems.append("gallery.json 解析失败: %s" % e)
    return (not problems), problems


def bind_server(host, want_port):
    """从 want_port 开始尝试绑定，返回 (server, port)。"""
    from http.server import ThreadingHTTPServer
    import studio_server

    os.makedirs(studio_server.GALLERY_DIR, exist_ok=True)
    if not os.path.exists(studio_server.GALLERY_PATH):
        studio_server.save_gallery({"designs": []})

    last = None
    for off in range(PORT_TRIES):
        port = want_port + off
        if port > 65535:
            break
        try:
            srv = ThreadingHTTPServer((host, port), studio_server.Handler)
            return srv, port
        except OSError as e:
            last = e
            continue
    raise SystemExit("端口 %d~%d 全部不可用：%s" % (want_port, want_port + PORT_TRIES - 1, last))


def wait_ping(port, timeout=8.0):
    """轮询 /api/ping，通了返回 True。"""
    url = "http://127.0.0.1:%d/api/ping" % port
    deadline = time.time() + timeout
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # 绕开系统代理
    while time.time() < deadline:
        try:
            with opener.open(url, timeout=1.0) as r:
                if r.status == 200 and json.loads(r.read().decode()).get("ok"):
                    return True
        except Exception:
            time.sleep(0.15)
    return False


def lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None


def open_browser(url):
    try:
        import webbrowser
        webbrowser.open(url)
    except Exception:
        pass


def do_check():
    _utf8_stdout()
    ok, problems = preflight()
    print("麦当劳「真」随心配 · 启动前体检")
    print("-" * 52)
    print("项目根目录 : %s" % ROOT)
    print("Python     : %s" % sys.version.split()[0])
    print("依赖文件   : %d/%d 就位" % (len(REQUIRED) - sum(1 for p in problems if p.startswith("缺少文件")), len(REQUIRED)))
    for p in problems:
        print("  [x] " + p)
    print("-" * 52)
    print("结论: " + ("可以启动" if ok else "存在阻塞项，请先修复"))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="麦当劳「真」随心配 · 一键启动")
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8765)))
    ap.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    ap.add_argument("--lan", action="store_true", help="监听 0.0.0.0，局域网内其他设备可访问并投票")
    ap.add_argument("--no-open", action="store_true", help="不自动打开浏览器")
    ap.add_argument("--check", action="store_true", help="只体检，不启动服务")
    args = ap.parse_args()

    if args.check:
        return do_check()

    _utf8_stdout()
    ok, problems = preflight()
    if not ok:
        print("无法启动，先解决这些问题：")
        for p in problems:
            print("  [x] " + p)
        return 1

    host = "0.0.0.0" if args.lan else args.host
    srv, port = bind_server(host, args.port)
    if port != args.port:
        print("提示: %d 已被占用，改用 %d" % (args.port, port))

    threading.Thread(target=srv.serve_forever, daemon=True).start()
    if not wait_ping(port):
        srv.shutdown()
        print("服务已绑定但 /api/ping 无响应，请检查端口 %d 是否被防火墙拦截" % port)
        return 2

    local = "http://127.0.0.1:%d" % port
    print("")
    print("🍔 麦当劳「真」随心配 已启动")
    print("   本机访问  : %s" % local)
    if host == "0.0.0.0":
        ip = lan_ip()
        if ip:
            print("   局域网访问: http://%s:%d   (同一 WiFi 下其他设备可打开并投票)" % (ip, port))
    print("   自检入口  : %s/?selftest=1   (自动合成预览并试发布一条作品)" % local)
    print("   素材库    : assets/materials.json")
    print("   作品数据  : gallery/gallery.json")
    print("   停止服务  : Ctrl+C")
    print("")
    try:
        sys.stdout.flush()   # 被管道/后台任务捕获时必须立刻刷出，否则 Agent 读不到地址
    except Exception:
        pass

    if not args.no_open:
        open_browser(local)

    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print("\n已停止")
        srv.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
