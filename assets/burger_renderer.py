#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
汉堡可视化渲染器：把一组麦当劳素材（按从下到上的堆叠顺序）渲染成 SVG。
同时提供营养/价格聚合工具。被 web 前端、agent 模式与 gallery 共用。
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAT_PATH = os.path.join(ROOT, "assets", "materials.json")


def load_materials():
    with open(MAT_PATH, encoding="utf-8") as f:
        return json.load(f)


def materials_by_code():
    m = load_materials()
    return {x["code"]: x for x in m["materials"]}


def _brightness(hex_color):
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return 255
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return 0.299 * r + 0.587 * g + 0.114 * b


def _text_color(hex_color):
    return "#1a1a1a" if _brightness(hex_color) > 150 else "#ffffff"


def aggregate(codes, by_code=None):
    if by_code is None:
        by_code = materials_by_code()
    total_price = 0.0
    kcal = protein = fat = carb = 0.0
    counted = 0
    for c in codes:
        item = by_code.get(c)
        if not item:
            continue
        total_price += item.get("price", 0) or 0
        n = item.get("nutrition")
        if n:
            for key, attr in (("energyKcal", "kcal"), ("protein", "protein"),
                              ("fat", "fat"), ("carbohydrate", "carb")):
                v = n.get(key)
                if v not in (None, "", "null"):
                    try:
                        if attr == "kcal":
                            kcal += float(v)
                        elif attr == "protein":
                            protein += float(v)
                        elif attr == "fat":
                            fat += float(v)
                        elif attr == "carb":
                            carb += float(v)
                    except Exception:
                        pass
            counted += 1
    return {
        "price": round(total_price, 2),
        "kcal": round(kcal),
        "protein": round(protein, 1),
        "fat": round(fat, 1),
        "carb": round(carb, 1),
        "nutri_items": counted,
    }


def render_burger_svg(codes, by_code=None, name="", width=360):
    """渲染汉堡 SVG。codes 为从下到上的素材编码列表。"""
    if by_code is None:
        by_code = materials_by_code()
    layers = []
    for c in codes:
        item = by_code.get(c)
        if item:
            layers.append(item)
    if not layers:
        layers = [{"name": "空盘子", "color": "#e8d9b5", "emoji": "🍽️",
                   "role": "other", "price": 0}]

    # 各层参数
    bun_h = 46
    fill_h = 30
    top_extra = 18  # 顶部圆顶额外高度
    gap = 3
    n = len(layers)
    inner_h = bun_h + n * (fill_h + gap) + bun_h
    height = inner_h + top_extra + 16
    x0 = 40
    w = width - 80

    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
                 f'width="{width}" height="{height}" font-family="-apple-system,Segoe UI,Microsoft YaHei,sans-serif">')
    # 背景
    parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" rx="18" fill="#fff7ec"/>')
    if name:
        parts.append(f'<text x="{width/2}" y="20" text-anchor="middle" font-size="15" '
                     f'font-weight="700" fill="#7a4a16">{name}</text>')

    y = (16 if name else 8) + top_extra
    base_y = y

    # 顶部圆顶（芝麻胚）
    top_y = base_y
    parts.append(f'<defs><linearGradient id="bun" x1="0" y1="0" x2="0" y2="1">'
                 f'<stop offset="0" stop-color="#f4c069"/><stop offset="1" stop-color="#d99a3c"/></linearGradient></defs>')
    parts.append(f'<path d="M {x0} {top_y+bun_h} Q {width/2} {top_y-18} {x0+w} {top_y+bun_h} '
                 f'L {x0+w} {top_y+bun_h} L {x0} {top_y+bun_h} Z" fill="url(#bun)" stroke="#c98a2e" stroke-width="1.5"/>')
    # 芝麻
    import random
    random.seed(7)
    for i in range(7):
        sx = x0 + 18 + random.random() * (w - 36)
        sy = top_y + 18 + random.random() * (bun_h - 26)
        parts.append(f'<ellipse cx="{sx:.0f}" cy="{sy:.0f}" rx="3.2" ry="1.8" fill="#fff3d6" transform="rotate({random.randint(-40,40)} {sx:.0f} {sy:.0f})"/>')

    y = top_y + bun_h + gap
    # 中间夹料
    for idx, item in enumerate(layers):
        color = item.get("color", "#cccccc")
        emoji = item.get("emoji", "🍽️")
        nm = item.get("name", "")
        # 轻微随机宽度，营造层次感
        inset = 4 + (idx % 3) * 3
        lx = x0 + inset
        lw = w - inset * 2
        # 水滴/波浪底边
        parts.append(f'<rect x="{lx:.0f}" y="{y:.0f}" width="{lw:.0f}" height="{fill_h}" rx="11" '
                     f'fill="{color}" stroke="rgba(0,0,0,0.12)" stroke-width="1"/>')
        # 高光
        parts.append(f'<rect x="{lx:.0f}" y="{y:.0f}" width="{lw:.0f}" height="6" rx="6" fill="rgba(255,255,255,0.22)"/>')
        # emoji + 名称
        tcol = _text_color(color)
        parts.append(f'<text x="{width/2}" y="{y+fill_h/2+1:.0f}" text-anchor="middle" '
                     f'font-size="14" fill="{tcol}" font-weight="600">{emoji} {nm}</text>')
        y += fill_h + gap

    # 底部胚
    parts.append(f'<path d="M {x0} {y} L {x0+w} {y} L {x0+w} {y+bun_h-12} '
                 f'Q {width/2} {y+bun_h+8} {x0} {y+bun_h-12} Z" fill="url(#bun)" '
                 f'stroke="#c98a2e" stroke-width="1.5"/>')

    parts.append('</svg>')
    return "\n".join(parts)


def render_design_card(design, by_code=None):
    """生成单个作品的 HTML 卡片（含 SVG、营养、投票）。design: {id,name,author,layers,votes}。"""
    if by_code is None:
        by_code = materials_by_code()
    svg = render_burger_svg(design.get("layers", []), by_code, name=design.get("name", ""))
    agg = aggregate(design.get("layers", []), by_code)
    votes = design.get("votes", 0)
    did = design.get("id", "")
    author = design.get("author", "匿名麦粉")
    created = design.get("created_at", "")
    nutri_html = (f'🔥 {agg["kcal"]} kcal　💰 ¥{agg["price"]:.2f}　'
                  f'🥩 蛋白 {agg["protein"]}g　🛢️ 脂肪 {agg["fat"]}g'
                  if agg["nutri_items"] else f'💰 估算 ¥{agg["price"]:.2f}')
    return f"""
    <div class="card" data-id="{did}">
      <div class="card-svg">{svg}</div>
      <div class="card-meta">
        <div class="card-name">{design.get('name','未命名')}</div>
        <div class="card-author">👤 {author} · 🕒 {created}</div>
        <div class="card-nutri">{nutri_html}</div>
        <button class="vote-btn" data-id="{did}">🗳️ 投票 <span class="vote-count">{votes}</span></button>
      </div>
    </div>"""


def render_gallery_html(designs, by_code=None):
    if by_code is None:
        by_code = materials_by_code()
    cards = "\n".join(render_design_card(d, by_code) for d in designs)
    return cards


if __name__ == "__main__":
    # 自测
    bc = materials_by_code()
    sample = ["1440", "521903", "9900016076"]  # 麦辣鸡腿堡, 三文鱼双虾, 心形薯饼
    print(render_burger_svg(sample, bc, "测试至尊堡")[:300])
    print("AGG:", aggregate(sample, bc))
