#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
麦当劳「真」随心配 —— 本地工作室服务（零依赖，仅用 Python 标准库）。

提供：
  GET  /                      主应用（2D 套餐搭配 + 3D 组件汉堡 + 作品画廊）
  GET  /api/materials         官方素材库（源自麦当劳 MCP query-meals）
  GET  /api/gallery           作品列表（按票数降序）
  POST /api/designs           发布作品（套餐 / 组件汉堡，含预览图 dataURL）
  POST /api/vote              投票（按昵称去重）
  GET  /gallery/<file>        作品预览图

运行：python scripts/studio_server.py [--port 8765] [--host 0.0.0.0]
"""
import base64
import json
import os
import socket
import sys
import time
import threading
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
GALLERY_DIR = os.path.join(ROOT, "gallery")
GALLERY_PATH = os.path.join(GALLERY_DIR, "gallery.json")
MAT_PATH = os.path.join(ASSETS, "materials.json")
APP_HTML = os.path.join(ASSETS, "burger_components_3d.html")

_lock = threading.Lock()
_mat_cache = {"mtime": 0, "data": None}

CTYPE = {
    ".js": "application/javascript; charset=utf-8",
    ".mjs": "application/javascript; charset=utf-8",
    ".png": "image/png",
    ".gif": "image/gif",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml; charset=utf-8",
    ".glb": "model/gltf-binary",
    ".gltf": "model/gltf+json",
    ".woff2": "font/woff2",
}


def load_materials():
    """带 mtime 缓存的素材库读取。"""
    try:
        mt = os.path.getmtime(MAT_PATH)
    except OSError:
        return {"materials": [], "groups": []}
    if _mat_cache["data"] is not None and _mat_cache["mtime"] == mt:
        return _mat_cache["data"]
    with open(MAT_PATH, encoding="utf-8") as f:
        data = json.load(f)
    _mat_cache["data"] = data
    _mat_cache["mtime"] = mt
    return data


def materials_by_code():
    return {m["code"]: m for m in load_materials().get("materials", [])}


def load_gallery():
    if not os.path.exists(GALLERY_PATH):
        return {"designs": []}
    try:
        with open(GALLERY_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {"designs": []}
    data.setdefault("designs", [])
    return data


def save_gallery(data):
    os.makedirs(GALLERY_DIR, exist_ok=True)
    tmp = GALLERY_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, GALLERY_PATH)


def read_body(handler):
    n = int(handler.headers.get("Content-Length", 0) or 0)
    if n <= 0:
        return {}
    raw = handler.rfile.read(n)
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return {}


def save_preview(data_url, did):
    """把前端 canvas 生成的 dataURL 存成 gallery/<id>.jpg，返回可访问路径。"""
    if not isinstance(data_url, str) or not data_url.startswith("data:image/"):
        return ""
    try:
        head, b64 = data_url.split(",", 1)
    except ValueError:
        return ""
    if "base64" not in head:
        return ""
    blob = base64.b64decode(b64)
    if not blob or len(blob) > 6 * 1024 * 1024:      # 上限 6MB
        return ""
    os.makedirs(GALLERY_DIR, exist_ok=True)
    name = "img_%s.jpg" % did
    with open(os.path.join(GALLERY_DIR, name), "wb") as f:
        f.write(blob)
    return "/gallery/" + name


class Handler(BaseHTTPRequestHandler):
    server_version = "McdSuixinpei/3.0"

    def log_message(self, *args):
        pass

    # ---------- 基础输出 ----------
    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False)
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path, ctype):
        if not os.path.isfile(path):
            self._send(404, {"error": "not found"})
            return
        with open(path, "rb") as f:
            data = f.read()
        self._send(200, data, ctype)

    def _static(self, rel):
        """安全的静态文件读取（限制在项目根目录内）。"""
        fpath = os.path.normpath(os.path.join(ROOT, rel.lstrip("/")))
        if not fpath.startswith(ROOT):
            self._send(403, {"error": "forbidden"})
            return
        ext = os.path.splitext(fpath)[1].lower()
        self._send_file(fpath, CTYPE.get(ext, "application/octet-stream"))

    # ---------- GET ----------
    def do_GET(self):
        p = urlparse(self.path)
        path = p.path
        if path in ("/", "/index.html"):
            self._send_file(APP_HTML, CTYPE[".html"])
        elif path.startswith("/assets/"):
            self._static(path)
        elif path.startswith("/gallery/"):
            self._static(path)
        elif path == "/api/materials":
            self._send_file(MAT_PATH, CTYPE[".json"])
        elif path == "/api/gallery":
            self._send(200, load_gallery())
        elif path == "/api/ping":
            self._send(200, {"ok": True, "time": time.strftime("%Y-%m-%d %H:%M:%S")})
        elif path in ("/components", "/components.html"):
            self._send_file(APP_HTML, CTYPE[".html"])
        else:
            self._send(404, {"error": "not found"})

    # ---------- POST ----------
    def do_POST(self):
        path = urlparse(self.path).path
        body = read_body(self)
        if path == "/api/designs":
            self._create_design(body)
        elif path == "/api/vote":
            self._vote(body)
        else:
            self._send(404, {"error": "not found"})

    def _create_design(self, body):
        name = str(body.get("name", "")).strip()[:24] or "未命名作品"
        author = str(body.get("author", "")).strip()[:12] or "匿名麦粉"
        mode = "component" if str(body.get("mode", "")) == "component" else "combo"
        by_code = materials_by_code()
        summary = body.get("summary") if isinstance(body.get("summary"), dict) else {}

        items, layers, names = [], [], []
        if mode == "combo":
            raw_items = body.get("items")
            if not isinstance(raw_items, list):
                # 兼容仅传 layers（重复 code 列表）
                raw_items = [{"code": c, "qty": 1} for c in (body.get("layers") or [])]
            total = 0
            for it in raw_items[:20]:
                if not isinstance(it, dict):
                    continue
                code = str(it.get("code", ""))
                if code not in by_code:
                    continue
                try:
                    qty = int(it.get("qty", 1))
                except Exception:
                    qty = 1
                qty = max(1, min(9, qty))
                if total + qty > 30:
                    qty = max(0, 30 - total)
                if qty <= 0:
                    break
                total += qty
                items.append({"code": code, "qty": qty})
                layers.extend([code] * qty)
                names.append(by_code[code].get("name", code))
            if not items:
                self._send(400, {"error": "请至少选择一件官方单品"})
                return
        else:
            labels = body.get("labels")
            raw = body.get("layers")
            if not isinstance(raw, list) or not raw:
                self._send(400, {"error": "组件列表为空"})
                return
            layers = [str(c) for c in raw if isinstance(c, str)][:30]
            if not layers:
                self._send(400, {"error": "组件列表为空"})
                return
            if isinstance(labels, list) and len(labels) == len(layers):
                names = [str(x)[:16] for x in labels]
            else:
                names = layers

        with _lock:
            data = load_gallery()
            did = "d%d" % int(time.time() * 1000)
            preview = save_preview(body.get("preview"), did)
            design = {
                "id": did,
                "name": name,
                "author": author,
                "created_at": time.strftime("%Y-%m-%d %H:%M"),
                "mode": mode,
                "items": items,
                "layers": layers,
                "item_names": names,
                "summary": {
                    "price": summary.get("price"),
                    "kcal": summary.get("kcal"),
                    "protein": summary.get("protein"),
                    "fat": summary.get("fat"),
                    "carb": summary.get("carb"),
                    "sodium": summary.get("sodium"),
                    "count": summary.get("count", len(layers)),
                },
                "preview": preview,
                "votes": 0,
                "voters": [],
            }
            data["designs"].append(design)
            save_gallery(data)
        self._send(200, design)

    def _vote(self, body):
        did = str(body.get("id", ""))
        voter = str(body.get("voter", "")).strip()[:12]
        if not did or not voter:
            self._send(400, {"error": "请先填写昵称再投票"})
            return
        with _lock:
            data = load_gallery()
            design = next((d for d in data["designs"] if d.get("id") == did), None)
            if not design:
                self._send(404, {"error": "作品不存在"})
                return
            voters = design.setdefault("voters", [])
            if voter in voters:
                self._send(409, {"error": "你已经为该作品投过票啦", "votes": design.get("votes", 0)})
                return
            voters.append(voter)
            design["votes"] = len(voters)
            save_gallery(data)
        self._send(200, {"votes": design["votes"], "voter": voter})


def lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def main():
    ap = argparse.ArgumentParser()
    # 云平台（WorkBuddy 发布 / 容器）通过 PORT 环境变量注入端口，必须优先读取；
    # 命令行参数仍可覆盖，便于本地指定。
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8765")))
    ap.add_argument("--host", default=os.environ.get("HOST", "0.0.0.0"))
    args = ap.parse_args()
    os.makedirs(GALLERY_DIR, exist_ok=True)
    if not os.path.exists(GALLERY_PATH):
        save_gallery({"designs": []})
    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    print("🍔 麦当劳「真」随心配 已启动")
    print("   监听地址: %s:%d" % (args.host, args.port))
    print("   本机访问: http://127.0.0.1:%d" % args.port)
    if args.host == "0.0.0.0":
        print("   局域网访问: http://%s:%d   (其他用户可访问并投票)" % (lan_ip(), args.port))
    print("   素材库: %s" % MAT_PATH)
    print("   画廊数据: %s" % GALLERY_PATH)
    try:
        sys.stdout.flush()
    except Exception:
        pass
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")
        srv.shutdown()


if __name__ == "__main__":
    main()
