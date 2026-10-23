#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
麦当劳「真」随心配 —— 交付前自检（8 项断言）。

设计原则：
  * 不联网（不需要 MCP），纯净目录也能跑
  * 不占固定端口（用 0 号端口自动分配，不会撞掉你正在跑的服务）
  * 任何一项 FAIL 都以非零码退出，方便挂到 CI / pre-push 钩子

用法：
  python scripts/selfcheck.py
  python scripts/selfcheck.py -v      # 打印通过项细节
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

EXPECT_TOTAL = 119
EXPECT_BUYABLE = 63

# SKILL.md 中不应再出现的旧表述（重写前的架构残留）
FORBIDDEN = [
    "burger_studio.html",
    "burger_studio_3d.html",
    "img2mesh",
    "按官方规范排序",
    "布告板",
    "模式 1 ·",
    "模式 2 ·",
    "模式 3 ·",
]

results = []  # [(no, name, status, detail)]


def record(no, name, ok, detail="", skip=False):
    status = "SKIP" if skip else ("PASS" if ok else "FAIL")
    results.append((no, name, status, detail))
    return ok


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def parse_frontmatter(text):
    """极简 YAML frontmatter 解析：只取 key: value 顶层标量。"""
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end < 0:
        return None
    block = text[3:end]
    meta = {}
    for line in block.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        meta[k.strip()] = v.strip()
    return meta


# ---------------------------------------------------------------- 1
def check_frontmatter():
    try:
        meta = parse_frontmatter(read("SKILL.md"))
    except Exception as e:
        return record(1, "SKILL.md frontmatter", False, "读取失败: %s" % e)
    if meta is None:
        return record(1, "SKILL.md frontmatter", False, "缺少 --- 包裹的 frontmatter")
    missing = [k for k in ("name", "description", "version", "license") if not meta.get(k)]
    if missing:
        return record(1, "SKILL.md frontmatter", False, "缺字段: " + ", ".join(missing))
    if meta["name"] != os.path.basename(ROOT):
        return record(1, "SKILL.md frontmatter", False,
                      "name=%s 与目录名 %s 不一致" % (meta["name"], os.path.basename(ROOT)))
    desc = meta["description"]
    if len(desc) < 60:
        return record(1, "SKILL.md frontmatter", False, "description 仅 %d 字，应 ≥60" % len(desc))
    return record(1, "SKILL.md frontmatter", True, "name=%s version=%s desc=%d 字" % (meta["name"], meta["version"], len(desc)))


# ---------------------------------------------------------------- 2
PATH_RE = re.compile(r"(?:^|[\s`(\[])((?:assets|scripts|references|gallery|examples)/[A-Za-z0-9_./*-]+)")


def check_no_deadlink():
    try:
        text = read("SKILL.md")
    except Exception as e:
        return record(2, "SKILL.md 路径无死链", False, "读取失败: %s" % e)
    cand = set()
    for m in PATH_RE.findall(text):
        p = m.rstrip(".,;:)】」`'\"")
        cand.add(p)
    bad = []
    checked = 0
    for rel in sorted(cand):
        target = os.path.join(ROOT, rel.replace("*", "").rstrip("/"))
        if "*" in rel:
            # 通配：只要求父目录非空
            parent = os.path.dirname(target)
            checked += 1
            if not (os.path.isdir(parent) and os.listdir(parent)):
                bad.append(rel)
            continue
        checked += 1
        if not os.path.exists(target):
            bad.append(rel)
    if bad:
        return record(2, "SKILL.md 路径无死链", False, "%d/%d 失效: %s" % (len(bad), checked, ", ".join(bad[:6])))
    return record(2, "SKILL.md 路径无死链", True, "校验 %d 条路径" % checked)


# ---------------------------------------------------------------- 3
def load_materials():
    with open(os.path.join(ROOT, "assets", "materials.json"), encoding="utf-8") as f:
        return json.load(f)


def check_materials():
    try:
        d = load_materials()
    except Exception as e:
        return record(3, "materials.json 完整性", False, "解析失败: %s" % e)
    ms = d.get("materials") or []
    buyable = sum(1 for m in ms if m.get("buyable"))
    if len(ms) != EXPECT_TOTAL:
        return record(3, "materials.json 完整性", False, "total=%d，期望 %d" % (len(ms), EXPECT_TOTAL))
    if buyable != EXPECT_BUYABLE:
        return record(3, "materials.json 完整性", False, "buyable=%d，期望 %d" % (buyable, EXPECT_BUYABLE))
    priced = sum(1 for m in ms if m.get("buyable") and m.get("price") is not None)
    if priced < buyable:
        return record(3, "materials.json 完整性", False, "可单点项中 %d 项缺价格" % (buyable - priced))
    return record(3, "materials.json 完整性", True, "119 项 / 63 可购 / 价格齐全")


# ---------------------------------------------------------------- 4
def check_photos():
    try:
        ms = load_materials().get("materials") or []
    except Exception as e:
        return record(4, "官方图覆盖", False, "materials.json 不可读: %s" % e)
    miss = []
    for m in ms:
        photo = m.get("photo") or ""
        if not photo:
            miss.append(m.get("code", "?"))
            continue
        rel = photo.lstrip("/")
        if not os.path.isfile(os.path.join(ROOT, rel)):
            miss.append(m.get("code", "?"))
    n_files = len([x for x in os.listdir(os.path.join(ROOT, "assets", "mcd_photos"))
                   if x.lower().endswith((".png", ".gif", ".jpg"))])
    if miss:
        return record(4, "官方图覆盖", False, "%d 项无图: %s" % (len(miss), ", ".join(miss[:8])))
    return record(4, "官方图覆盖", True, "%d/%d 项有图，目录内 %d 张" % (len(ms), len(ms), n_files))


# ---------------------------------------------------------------- 5
def check_vendor():
    vendor = os.path.join(ROOT, "assets", "vendor")
    need = ["three.min.js", "OrbitControls.js", "GLTFLoader.js"]
    miss = [f for f in need if not os.path.isfile(os.path.join(vendor, f))]
    if miss:
        return record(5, "前端依赖就绪", False, "vendor 缺: " + ", ".join(miss))
    node = shutil.which("node")
    js = os.path.join(ROOT, "assets", "components3d.js")
    if not node:
        try:
            src = open(js, encoding="utf-8").read()
        except Exception as e:
            return record(5, "前端依赖就绪", False, "components3d.js 不可读: %s" % e)
        if "Components3D" not in src:
            return record(5, "前端依赖就绪", False, "components3d.js 未定义 Components3D")
        return record(5, "前端依赖就绪", True, "vendor 3 个 JS 齐全（无 node，跳过语法校验）")
    r = subprocess.run([node, "--check", js], capture_output=True, text=True)
    if r.returncode != 0:
        return record(5, "前端依赖就绪", False, "components3d.js 语法错误: " + r.stderr.strip()[:200])
    return record(5, "前端依赖就绪", True, "vendor 3 个 JS + components3d.js 语法通过")


# ---------------------------------------------------------------- 6
def check_gallery():
    p = os.path.join(ROOT, "gallery", "gallery.json")
    if not os.path.isfile(p):
        return record(6, "gallery.json 结构", False, "文件不存在")
    try:
        with open(p, encoding="utf-8") as f:
            g = json.load(f)
    except Exception as e:
        return record(6, "gallery.json 结构", False, "解析失败: %s" % e)
    if not isinstance(g.get("designs"), list):
        return record(6, "gallery.json 结构", False, "designs 不是数组")
    for d in g["designs"]:
        if not isinstance(d.get("id"), str) or "votes" not in d:
            return record(6, "gallery.json 结构", False, "作品字段缺失: %r" % (d.get("id"),))
    return record(6, "gallery.json 结构", True, "%d 件作品" % len(g["designs"]))


# ---------------------------------------------------------------- 7
def check_api():
    try:
        import studio_server
        from http.server import ThreadingHTTPServer
    except Exception as e:
        return record(7, "HTTP 接口连通", False, "导入 studio_server 失败: %s" % e)
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", 0), studio_server.Handler)
    except Exception as e:
        return record(7, "HTTP 接口连通", False, "无法绑定本地端口: %s" % e)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    ok_all, detail = True, []
    try:
        for path, key in (("/api/ping", "ok"), ("/api/materials", "materials"), ("/api/gallery", "designs")):
            try:
                with opener.open("http://127.0.0.1:%d%s" % (port, path), timeout=5) as r:
                    body = json.loads(r.read().decode("utf-8"))
                if r.status != 200 or key not in body:
                    ok_all = False
                    detail.append("%s 缺字段 %s" % (path, key))
            except Exception as e:
                ok_all = False
                detail.append("%s 异常 %s" % (path, e))
        # 静态资源与首页
        for path in ("/", "/assets/materials.json"):
            try:
                with opener.open("http://127.0.0.1:%d%s" % (port, path), timeout=5) as r:
                    if r.status != 200:
                        ok_all = False
                        detail.append("%s -> %d" % (path, r.status))
            except Exception as e:
                ok_all = False
                detail.append("%s 异常 %s" % (path, e))
    finally:
        srv.shutdown()
    if not ok_all:
        return record(7, "HTTP 接口连通", False, "; ".join(detail[:5]))
    return record(7, "HTTP 接口连通", True, "ping/materials/gallery/首页/静态资源 均 200")


# ---------------------------------------------------------------- 8
def check_no_legacy():
    try:
        text = read("SKILL.md")
    except Exception as e:
        return record(8, "无过期架构表述", False, "读取失败: %s" % e)
    hit = [k for k in FORBIDDEN if k in text]
    if hit:
        return record(8, "无过期架构表述", False, "仍出现: " + ", ".join(hit))
    return record(8, "无过期架构表述", True, "8 类旧表述均未出现")


CHECKS = [check_frontmatter, check_no_deadlink, check_materials, check_photos,
          check_vendor, check_gallery, check_api, check_no_legacy]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    print("麦当劳「真」随心配 · 交付前自检")
    print("=" * 64)
    for fn in CHECKS:
        try:
            fn()
        except Exception as e:  # 单项炸掉不拖垮全局
            record(0, fn.__name__, False, "未捕获异常: %s" % e)
    for no, name, status, detail in results:
        mark = {"PASS": "[PASS]", "FAIL": "[FAIL]", "SKIP": "[SKIP]"}[status]
        print("%s %d. %-22s %s" % (mark, no, name, detail if (args.verbose or status != "PASS") else ""))

    passed = sum(1 for r in results if r[2] == "PASS")
    failed = [r for r in results if r[2] == "FAIL"]
    print("=" * 64)
    print("结果: %d/%d 通过%s" % (passed, len(results), "" if not failed else "，%d 项失败" % len(failed)))
    if failed:
        print("失败项: " + "; ".join("%d.%s" % (r[0], r[1]) for r in failed))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
