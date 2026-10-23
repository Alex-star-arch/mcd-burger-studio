#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
麦当劳 MCP 探测脚本（仅用于开发期验证集成 & 生成素材库快照）。
通过 Streamable HTTP 协议连接 mcp.mcd.cn，列出工具并拉取在售菜单与营养数据。
token 从环境变量 MCD_MCP_TOKEN 读取，避免硬编码。
"""
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


def _parse_body(raw: str):
    """解析 Streamable HTTP 返回：可能是 JSON 也可能是 SSE (data: ...)。"""
    raw = raw.strip()
    if raw.startswith("{"):
        return json.loads(raw)
    # SSE
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
    if is_notification:
        _notif_id -= 1
        body = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            body["params"] = params
        req_id = None
    else:
        body = {"jsonrpc": "2.0", "id": 1, "method": method}
        if params is not None:
            body["params"] = params
        req_id = 1

    data = json.dumps(body).encode("utf-8")
    headers = dict(BASE_HEADERS)
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    req = urllib.request.Request(URL, data=data, headers=headers, method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=40)
    except urllib.error.HTTPError as e:
        print(f"HTTPError {e.code}: {e.read().decode('utf-8', 'ignore')[:500]}")
        raise
    # 捕获 Session-Id
    sid = resp.headers.get("Mcp-Session-Id") or resp.headers.get("mcp-session-id")
    if sid and not session_id:
        session_id = sid
    raw = resp.read().decode("utf-8", "ignore")
    if is_notification:
        return None
    return _parse_body(raw)


def initialize():
    r = rpc("initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "mcd-burger-studio-dev", "version": "1.0.0"},
    })
    # 发送 initialized 通知
    try:
        rpc("notifications/initialized", is_notification=True)
    except Exception:
        pass
    return r


def tools_list():
    return rpc("tools/list", {})


def tools_call(name, arguments=None):
    return rpc("tools/call", {"name": name, "arguments": arguments or {}})


def main():
    print("== initialize ==")
    init = initialize()
    print(json.dumps(init, ensure_ascii=False)[:400])
    print("\n== tools/list ==")
    tl = tools_list()
    tools = tl.get("result", {}).get("tools", []) if tl else []
    print(f"工具数量: {len(tools)}")
    for t in tools:
        print(" -", t.get("name"), "::", (t.get("description") or "")[:60])
    # 保存工具清单
    with open(os.path.join(os.path.dirname(__file__), "..", "assets", "mcp_tools_snapshot.json"), "w", encoding="utf-8") as f:
        json.dump(tl, f, ensure_ascii=False, indent=2)
    print("\n工具清单已保存到 assets/mcp_tools_snapshot.json")

    # 尝试调用 query-meals 获取在售菜单
    print("\n== tools/call query-meals ==")
    try:
        meals = tools_call("query-meals", {})
        with open(os.path.join(os.path.dirname(__file__), "..", "assets", "meals_raw.json"), "w", encoding="utf-8") as f:
            json.dump(meals, f, ensure_ascii=False, indent=2)
        # 简要打印
        content = (meals or {}).get("result", {}).get("content", [])
        text = ""
        for c in content:
            if c.get("type") == "text":
                text = c.get("text", "")
                break
        print("返回文本长度:", len(text))
        print(text[:1500])
    except Exception as e:
        print("query-meals 调用失败:", e)

    # 尝试调用 list-nutrition-foods
    print("\n== tools/call list-nutrition-foods ==")
    try:
        nutri = tools_call("list-nutrition-foods", {})
        with open(os.path.join(os.path.dirname(__file__), "..", "assets", "nutrition_raw.json"), "w", encoding="utf-8") as f:
            json.dump(nutri, f, ensure_ascii=False, indent=2)
        content = (nutri or {}).get("result", {}).get("content", [])
        text = ""
        for c in content:
            if c.get("type") == "text":
                text = c.get("text", "")
                break
        print("返回文本长度:", len(text))
        print(text[:1500])
    except Exception as e:
        print("list-nutrition-foods 调用失败:", e)


if __name__ == "__main__":
    main()
