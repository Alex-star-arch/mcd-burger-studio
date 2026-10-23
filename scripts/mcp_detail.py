#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""调用麦当劳 MCP query-meal-detail，获取代表性餐品的官方组成/外观信息。"""
import json
import os
import sys
import urllib.request
import urllib.error

URL = "https://mcp.mcd.cn"
TOKEN = os.environ.get("MCD_MCP_TOKEN", "")
if not TOKEN:
    print("ERROR: 请设置环境变量 MCD_MCP_TOKEN")
    sys.exit(1)

BASE_HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}
session_id = None
_notif_id = 0


def _parse_body(raw):
    raw = raw.strip()
    if raw.startswith("{"):
        return json.loads(raw)
    out = None
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            data = line[len("data:"):].strip()
            if data and data != "[DONE]":
                try:
                    out = json.loads(data)
                except Exception:
                    pass
    return out


def rpc(method, params=None, is_notification=False):
    global session_id, _notif_id
    body = {"jsonrpc": "2.0", "method": method}
    if not is_notification:
        body["id"] = 1
    if params is not None:
        body["params"] = params
    data = json.dumps(body).encode("utf-8")
    headers = dict(BASE_HEADERS)
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    req = urllib.request.Request(URL, data=data, headers=headers, method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=40)
    except urllib.error.HTTPError as e:
        print(f"HTTPError {e.code}: {e.read().decode('utf-8','ignore')[:500]}")
        raise
    sid = resp.headers.get("Mcp-Session-Id") or resp.headers.get("mcp-session-id")
    if sid and not session_id:
        session_id = sid
    raw = resp.read().decode("utf-8", "ignore")
    if is_notification:
        return None
    return _parse_body(raw)


def init():
    rpc("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "mcd-dev", "version": "1.0.0"}})
    rpc("notifications/initialized", is_notification=True)


def call(name, args):
    return rpc("tools/call", {"name": name, "arguments": args})


def extract_text(result):
    if not result:
        return ""
    content = result.get("result", {}).get("content", [])
    for c in content:
        if c.get("type") == "text":
            return c.get("text", "")
    return ""


def main():
    mat = json.load(open(os.path.join(os.path.dirname(__file__), "..", "assets", "materials.json"), encoding="utf-8"))
    by_code = {m["code"]: m for m in mat["materials"]}
    # 选出代表性 code
    picks = []
    for m in mat["materials"]:
        n = m["name"]
        if any(k in n for k in ["巨无霸", "安格斯", "麦辣鸡腿", "三文鱼", "薯条", "可乐", "新地", "麦旋风"]):
            picks.append(m["code"])
    picks = picks[:10]
    print("代表性 code:", picks)

    init()
    out = {}
    for code in picks:
        try:
            r = call("query-meal-detail", {"storeCode": "1450713", "orderType": 1, "beType": 1, "code": code})
            text = extract_text(r)
            out[code] = {"name": by_code.get(code, {}).get("name"), "raw": text}
            # 截取组成相关片段
            print("\n=====", code, by_code.get(code, {}).get("name"), "=====")
            # 找 Original Response 后的 JSON
            idx = text.find("Original Response")
            seg = text[idx+len("Original Response"):] if idx >= 0 else text
            print(seg[:1800])
        except Exception as e:
            print("FAIL", code, e)
    with open(os.path.join(os.path.dirname(__file__), "..", "assets", "meal_detail_raw.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("\n已保存 assets/meal_detail_raw.json")


if __name__ == "__main__":
    main()
