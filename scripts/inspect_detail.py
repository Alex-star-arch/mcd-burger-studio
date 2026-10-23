#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探测 query-meal-detail 返回结构，定位'官方组成'字段。"""
import json, os, sys, urllib.request, urllib.error

URL = "https://mcp.mcd.cn"
TOKEN = os.environ.get("MCD_MCP_TOKEN", "")
BASE_HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
session_id = None

def parse_body(raw):
    raw = raw.strip()
    if raw.startswith("{"):
        return json.loads(raw)
    out = None
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            d = line[len("data:"):].strip()
            if d and d != "[DONE]":
                try: out = json.loads(d)
                except Exception: pass
    return out

def rpc(method, params=None, is_notification=False):
    global session_id
    body = {"jsonrpc": "2.0", "method": method}
    if not is_notification: body["id"] = 1
    if params is not None: body["params"] = params
    data = json.dumps(body).encode("utf-8")
    h = dict(BASE_HEADERS)
    if session_id: h["Mcp-Session-Id"] = session_id
    req = urllib.request.Request(URL, data=data, headers=h, method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=40)
    except urllib.error.HTTPError as e:
        print("HTTPError", e.code, e.read().decode('utf-8','ignore')[:300]); raise
    sid = resp.headers.get("Mcp-Session-Id") or resp.headers.get("mcp-session-id")
    if sid and not session_id: session_id = sid
    return parse_body(resp.read().decode("utf-8","ignore"))

def call(name, args): return rpc("tools/call", {"name": name, "arguments": args})
def extract_text(r):
    if not r: return ""
    for c in r.get("result",{}).get("content",[]):
        if c.get("type")=="text": return c.get("text","")
    return ""

def find_components(obj, path=""):
    """递归找疑似'组成'的数组（元素是带 name 的字典）。"""
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, list) and v and isinstance(v[0], dict) and "name" in v[0]:
                # 排除明显不是组成的（如 categories/meals）
                hits.append((path+"/"+k, [x.get("name") for x in v][:12]))
            hits += find_components(v, path+"/"+k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj[:3]):
            hits += find_components(v, path+f"[{i}]")
    return hits

rpc("initialize", {"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"mcd-dev","version":"1.0.0"}})
rpc("notifications/initialized", is_notification=True)
r = call("query-meal-detail", {"storeCode":"1450713","orderType":1,"beType":1,"code":"521903"})
text = extract_text(r)
idx = text.find("Original Response")
seg = text[idx+len("Original Response"):] if idx>=0 else text
jstart = seg.find("{"); jend = seg.rfind("}")
data = json.loads(seg[jstart:jend+1])
print("TOP KEYS:", list(data.keys()))
print("TOP-LEVEL 'data' keys:", list(data.get("data",{}).keys()) if isinstance(data.get("data"),dict) else type(data.get("data")))
print("\n--- 疑似组成数组 ---")
for p, names in find_components(data)[:20]:
    print(p, "=>", names)
