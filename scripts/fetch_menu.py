#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""拉取真实麦当劳在售菜单 -> assets/materials_raw.json（开发期素材快照）。"""
import json, os, sys, urllib.request, urllib.error

URL = "https://mcp.mcd.cn"
TOKEN = os.environ.get("MCD_MCP_TOKEN", "")
if not TOKEN:
    print("ERROR: 设置 MCD_MCP_TOKEN"); sys.exit(1)

BASE = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"}
sid = None

def parse(raw):
    raw = raw.strip()
    if raw.startswith("{"): return json.loads(raw)
    out=None
    for line in raw.splitlines():
        line=line.strip()
        if line.startswith("data:"):
            d=line[5:].strip()
            if d and d!="[DONE]":
                try: out=json.loads(d)
                except: pass
    return out

def rpc(method, params=None, notif=False):
    global sid
    body={"jsonrpc":"2.0","method":method}
    if not notif: body["id"]=1
    if params is not None: body["params"]=params
    data=json.dumps(body).encode()
    h=dict(BASE)
    if sid: h["Mcp-Session-Id"]=sid
    req=urllib.request.Request(URL,data=data,headers=h,method="POST")
    try:
        resp=urllib.request.urlopen(req,timeout=40)
    except urllib.error.HTTPError as e:
        print("HTTP",e.code,e.read().decode('utf-8','ignore')[:300]); raise
    s=resp.headers.get("Mcp-Session-Id") or resp.headers.get("mcp-session-id")
    if s and not sid: sid=s
    raw=resp.read().decode("utf-8","ignore")
    return None if notif else parse(raw)

def init():
    rpc("initialize",{"protocolVersion":"2024-11-05","capabilities":{},
        "clientInfo":{"name":"mcd-burger-studio-dev","version":"1.0.0"}})
    rpc("notifications/initialized",notif=True)

def call(name,args=None):
    return rpc("tools/call",{"name":name,"arguments":args or {}})

def extract_text(r):
    for c in (r or {}).get("result",{}).get("content",[]):
        if c.get("type")=="text": return c.get("text","")
    return ""

def main():
    init()
    # 1) 获取门店
    print(">> query-nearby-stores (city=上海)")
    stores = call("query-nearby-stores", {"beType":1,"searchType":2,"city":"上海","keyword":"人民广场"})
    stext = extract_text(stores)
    # 尝试解析 storeCode
    store_code=None
    try:
        # 响应可能包含 Original Response JSON
        idx=stext.find("Original Response")
        seg=stext[idx:] if idx>=0 else stext
        # 找第一个 success json
        jstart=seg.find("{")
        # 简单提取 storeCode
        import re
        m=re.search(r'"storeCode"\s*:\s*"(\d+)"', seg)
        if m: store_code=m.group(1)
    except Exception as e:
        print("parse store err",e)
    print("store_code=",store_code)
    print("stores text (前800):", stext[:800])
    with open("assets/stores_raw.json","w",encoding="utf-8") as f:
        json.dump(stores,f,ensure_ascii=False,indent=2)

    if not store_code:
        print("无法获取 storeCode，退出")
        return

    # 2) 拉菜单
    print("\n>> query-meals")
    meals = call("query-meals", {"storeCode":store_code,"orderType":1,"beType":1})
    mtext = extract_text(meals)
    with open("assets/materials_raw.json","w",encoding="utf-8") as f:
        json.dump(meals,f,ensure_ascii=False,indent=2)
    idx=mtext.find("Original Response")
    print("meals data (前2500):", (mtext[idx:] if idx>=0 else mtext)[:2500])

if __name__=="__main__":
    main()
