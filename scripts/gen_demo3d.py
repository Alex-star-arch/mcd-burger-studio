#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成离线展示页 demo3d.html（2D 官方图，无 WebGL，无需服务器，双击即可打开）。
   所有视觉元素均使用麦当劳官方产品图 assets/mcd_photos/*.png（相对路径引用，file:// 下无 CORS 问题）。"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAT = json.load(open(os.path.join(ROOT, "assets", "materials.json"), encoding="utf-8"))["materials"]
BY = {m["code"]: m for m in MAT}
try:
    COMP = json.load(open(os.path.join(ROOT, "assets", "official_composition.json"), encoding="utf-8"))
except Exception:
    COMP = {"compositions": {}, "priority": {}}

# 示例作品（仅保留存在的 code）
SEEDS = [
    {"name": "麦门至尊塔", "layers": ["1440", "521903", "1120", "4810", "521946"]},
    {"name": "海鲜狂想曲", "layers": ["521903", "1600", "6102"]},
    {"name": "甜蜜暴击", "layers": ["521950", "515837", "521917"]},
    {"name": "元气醒神", "layers": ["3755", "507387", "6102"]},
    {"name": "招牌双牛堡", "layers": ["4648", "511781", "1120", "4810", "521946"]},
    {"name": "龙焰芝士棒", "layers": ["521953", "521881", "1120", "4810"]},
]
for s in SEEDS:
    s["layers"] = [c for c in s["layers"] if c in BY]

def num(v):
    try: return float(v) if v is not None else 0
    except: return 0

def agg(cs):
    price=kcal=pro=fat=carb=n=0
    for c in cs:
        m=BY.get(c)
        if not m: continue
        price+=num(m.get("price"))
        nu=m.get("nutrition")
        if nu:
            kcal+=num(nu.get("energyKcal")); pro+=num(nu.get("protein"))
            fat+=num(nu.get("fat")); carb+=num(nu.get("carbohydrate")); n+=1
    return dict(price=price,kcal=kcal,pro=pro,fat=fat,carb=carb,nutri=n)

# 素材库按 role_cn 分组
groups={}
for m in MAT:
    groups.setdefault(m.get("role_cn") or "其他", []).append(m)
CAT_ORDER=["牛肉","炸鸡","鱼/虾","芝士","酱料","蔬果","汉堡","小食","甜品","饮料","其他"]
cats=sorted(groups.keys(), key=lambda k:(CAT_ORDER.index(k) if k in CAT_ORDER else 99))

def img_block(code, w=110, h=84):
    m=BY.get(code)
    if not m: return ""
    return (f'<div class="ic"><img loading="lazy" src="mcd_photos/{code}.png" alt="{m["name"]}">'
            f'<div class="icn">{m["name"]}</div></div>')

# 作品卡片
seed_cards=""
for i,s in enumerate(SEEDS):
    a=agg(s["layers"])
    imgs="".join(img_block(c) for c in s["layers"])
    names=" + ".join(BY[c]["name"] for c in s["layers"] if c in BY)
    nutri=(f'💰¥{a["price"]:.2f} · 🔥{int(a["kcal"])}kcal · 🥩{int(a["pro"])}g蛋白'
           f' · 🧈{int(a["fat"])}g脂肪') if a["nutri"] else f'💰¥{a["price"]:.2f}'
    seed_cards+=f'''
    <div class="card">
      <div class="pv">{imgs}</div>
      <div class="nm">{s["name"]}</div>
      <div class="it">{names}</div>
      <div class="nu">{nutri}</div>
      <div class="tagline">✅ 全部为麦当劳官方产品图 · 顺序依官方规范</div>
    </div>'''

# 素材库分组
lib_html=""
for cat in cats:
    items="".join(img_block(m["code"]) for m in groups[cat])
    lib_html+=f'<section class="libcat"><h3>{cat} <span>{len(groups[cat])} 款</span></h3><div class="libgrid">{items}</div></section>'

# 巨无霸官方组成（权威参考）
bm=COMP.get("compositions",{}).get("巨无霸",{})
bm_order=" → ".join(bm.get("order",[])) if bm else ""

HTML = f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>麦当劳「真」随心配 · 官方素材展示</title>
<style>
  :root{{--red:#da291c;--gold:#ffc72c;--cream:#fff7ec;--ink:#3a2c18;--muted:#9a8259;--line:#f0e2c8}}
  *{{box-sizing:border-box}} body{{margin:0;font-family:-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;background:var(--cream);color:var(--ink)}}
  header{{background:linear-gradient(90deg,var(--red),#e0442f);color:#fff;padding:16px 22px;box-shadow:0 2px 10px rgba(0,0,0,.15)}}
  header h1{{margin:0;font-size:21px}} header p{{margin:5px 0 0;font-size:13px;opacity:.93}}
  .wrap{{max-width:1180px;margin:0 auto;padding:18px}}
  .sec-title{{color:var(--red);font-size:18px;margin:22px 0 12px;border-left:5px solid var(--gold);padding-left:10px}}
  .note{{background:#fff2d6;border:1px solid var(--line);border-radius:12px;padding:14px;font-size:13px;line-height:1.7;color:#6a4a1a}}
  .note b{{color:var(--red-d,#b51f15)}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:16px}}
  .card{{background:#fff;border:1px solid var(--line);border-radius:14px;overflow:hidden;box-shadow:0 4px 14px rgba(180,120,30,.1)}}
  .card .pv{{background:radial-gradient(circle at 50% 30%,#fff3df,#f6c98a);display:flex;align-items:center;justify-content:center;gap:4px;flex-wrap:wrap;padding:10px;min-height:150px}}
  .card .pv img{{width:auto;height:92px;max-width:44%;object-fit:contain}}
  .card .nm{{font-weight:800;font-size:16px;padding:10px 12px 2px}}
  .card .it{{font-size:11px;color:var(--muted);padding:0 12px;line-height:1.35}}
  .card .nu{{font-size:12px;color:#8a5a16;background:#fff6e6;padding:5px 8px;border-radius:8px;margin:8px 12px;display:inline-block}}
  .card .tagline{{font-size:11px;color:var(--muted);padding:0 12px 12px}}
  .libcat{{margin-bottom:18px}}
  .libcat h3{{font-size:14px;color:var(--red);border-bottom:2px solid var(--gold);padding-bottom:5px;display:flex;justify-content:space-between}}
  .libcat h3 span{{color:var(--muted);font-weight:400;font-size:11px}}
  .libgrid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(96px,1fr));gap:10px;margin-top:10px}}
  .ic{{background:var(--cream);border:1px solid var(--line);border-radius:10px;padding:5px;text-align:center}}
  .ic img{{width:100%;height:70px;object-fit:contain;display:block}}
  .ic .icn{{font-size:10px;line-height:1.2;height:24px;overflow:hidden;margin-top:2px;color:var(--ink)}}
  footer{{text-align:center;color:var(--muted);font-size:12px;padding:24px}}
  code{{background:#fff;border:1px solid var(--line);padding:1px 6px;border-radius:5px}}
</style></head>
<body>
<header><h1>🍔 麦当劳「真」随心配 · 官方素材展示</h1>
<p>汉堡本体与全部食材均使用麦当劳官方提供的产品图呈现（无自定义/占位），顺序依官方规范</p></header>
<div class="wrap">

  <div class="note">
    <b>合规说明：</b>本工坊所有视觉元素（汉堡本体、牛肉、芝士、蔬菜、水果、饮品、小食等）一律来自
    <b>麦当劳官方产品图</b>（<code>assets/mcd_photos/*.png</code>，由麦当劳 MCP 真实在售菜单提供），
    <b>不使用任何自定义或占位几何/贴图</b>。<br>
    官方组成与排序规范参考麦当劳官网「了解当家产品」：<b>巨无霸 = {bm_order}</b>（双层牛肉、三层面包、约260粒芝麻）。
    单个堡的官方整图已内含正确的内部食材排列；组合设计时各产品按官方规范分类顺序排列。
  </div>

  <div class="sec-title">🏆 创意作品示例（官方产品图组合）</div>
  <div class="grid">{seed_cards}</div>

  <div class="sec-title">🧺 官方素材库（麦当劳在售，均可作为设计素材）</div>
  {lib_html}

  <footer>离线展示页 · 完整「网页设计 + 多人参与 + 投票」请运行 <code>python scripts/studio_server.py</code> 后访问在线工作室</footer>
</div>
</body></html>'''

out = os.path.join(ROOT, "assets", "demo3d.html")
open(out, "w", encoding="utf-8").write(HTML)
print("wrote", out, len(HTML), "bytes; seeds:", len(SEEDS), "; materials:", len(MAT))
