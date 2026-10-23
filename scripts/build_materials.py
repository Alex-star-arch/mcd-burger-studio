#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
根据麦当劳 MCP 真实返回（materials_raw.json + nutrition_raw.json）构建分类素材库 assets/materials.json。
分类角色(role): burger/wrap/chicken/beef/fish/breakfast/side/dessert/drink/sauce/veg/cheese/other
每个素材带 color/emoji/price/image/tags，并尽量关联营养数据。
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")

# 角色 -> (配色, emoji, 中文名)
ROLE_META = {
    "burger":   ("#C8772E", "🍔", "汉堡"),
    "wrap":     ("#E0A458", "🌯", "卷类"),
    "chicken":  ("#E8893B", "🍗", "炸鸡"),
    "beef":     ("#8B3A2B", "🥩", "牛肉"),
    "fish":     ("#3E8E8A", "🐟", "鱼/虾"),
    "breakfast":("#F2C14E", "🥯", "早餐"),
    "side":     ("#E8B84B", "🍟", "小食"),
    "dessert":  ("#E98AAE", "🍦", "甜品"),
    "drink":    ("#5AA9E6", "🥤", "饮料"),
    "sauce":    ("#C0392B", "🥫", "酱料"),
    "veg":      ("#6FB35A", "🥬", "蔬果"),
    "cheese":   ("#F4B400", "🧀", "芝士"),
    "other":    ("#B9A7C9", "🍽️", "其他"),
}

# 关键词优先级（从高到低），第一个命中决定角色
ROLE_RULES = [
    ("cheese",    ["芝士", "吉士", "cheese"]),
    ("sauce",     ["酱", "蘸酱"]),
    ("dessert",   ["新地", "麦旋风", "派", "冰淇淋", "圆筒", "圣代", "雪糕"]),
    ("drink",     ["可乐", "雪碧", "茶", "咖啡", "奶昔", "奶茶", "果汁", "水", "柠檬", "豆浆", "美式", "拿铁", "饮"]),
    ("veg",       ["沙拉", "玉米杯", "果蔬", "生菜", "蔬菜"]),
    ("breakfast", ["麦满分", "早餐", "可颂", "贝果", "多拿", "吐司", "煎蛋", "猪柳", "烟肉", "火腿"]),
    ("fish",      ["鱼", "虾", "三文鱼", "鳕鱼", "海鲜"]),
    ("beef",      ["牛", "安格斯", "板烧", "吉士堡", "双层吉士"]),
    ("chicken",   ["鸡", "炸鸡", "鸡翅", "鸡块", "麦乐鸡"]),
    ("wrap",      ["卷"]),
    ("burger",    ["堡"]),
    ("side",      ["薯条", "薯饼", "洋葱圈", "薯格", "鸡块", "鸡翅", "小食", "拼盘"]),
]

CATEGORY_ROLE_HINT = {
    "饮品": "drink", "麦咖啡™": "drink", "小食甜品/其他": "side",
    "开心乐园": "other", "炸鸡": "chicken", "蘸酱炸鸡": "chicken",
    "小食拼盘/多人餐": "side", "鸡肉汉堡/卷": "chicken", "巨无霸牛鱼肉堡": "burger",
    "安格斯MAX厚牛堡": "beef", "大堡口福单人餐": "burger",
}


def classify(name, category):
    for role, kws in ROLE_RULES:
        for kw in kws:
            if kw in name:
                return role
    hint = CATEGORY_ROLE_HINT.get(category.strip())
    if hint:
        return hint
    return "other"


def parse_nutrition(data_str):
    """解析 list-nutrition-foods 的 data 字段（已 unescape 的字符串），返回 {productName: {...}}。"""
    nutri = {}
    m = re.search(r"\[(\d+)\]\{([^}]*)\}", data_str)
    if not m:
        return nutri
    cols = [c.strip() for c in m.group(2).split(",")]
    body = data_str[m.end():]
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith("["):
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < len(cols):
            continue
        rec = dict(zip(cols, parts))
        name = rec.get("productName", "")
        if name:
            nutri[name] = {
                "energyKcal": rec.get("energyKcal"),
                "protein": rec.get("protein"),
                "fat": rec.get("fat"),
                "carbohydrate": rec.get("carbohydrate"),
                "sodium": rec.get("sodium"),
                "calcium": rec.get("calcium"),
            }
    return nutri


SUFFIX_CLEAN = re.compile(r"(三件套|二件套|五件套|套餐|单品|随心配|分享餐|多人餐|单人餐|双人餐|\（.*?\）|\（.*|组合|超大|超值|精选|经典|全新|上新|限定|回归|同款|周边|麦金卡|爆款).*$")

def clean_name(name):
    n = name
    for s in ["三件套", "二件套", "五件套", "套餐", "单品", "随心配", "分享餐", "多人餐",
              "单人餐", "双人餐", "组合", "（", "）", "【", "】"]:
        n = n.replace(s, "")
    return n.strip()

def match_nutri(name, nutri):
    if name in nutri:
        return nutri[name]
    cname = clean_name(name)
    if cname in nutri:
        return nutri[cname]
    # 双向包含匹配（用清洗后名称）
    for n, v in nutri.items():
        if n and (n in name or name in n or (cname and (n in cname or cname in n))):
            return v
    return None


def main():
    # 读菜单
    raw = json.load(open(os.path.join(ASSETS, "materials_raw.json"), encoding="utf-8"))
    text = ""
    for c in raw.get("result", {}).get("content", []):
        if c.get("type") == "text":
            text = c.get("text", "")
    idx = text.find("Original Response")
    seg = text[idx + len("Original Response"):]
    jstart = seg.find("{")
    data = json.loads(seg[jstart:])
    meals_map = data["data"]["meals"]
    categories = data["data"]["categories"]
    cat_of_code = {}
    for cat in categories:
        cname = cat["name"].replace("\n", "/")
        for m in cat["meals"]:
            code = m["code"]
            cat_of_code.setdefault(code, cname)

    # 读营养
    nutri = {}
    nraw = json.load(open(os.path.join(ASSETS, "nutrition_raw.json"), encoding="utf-8"))
    for c in nraw.get("result", {}).get("content", []):
        if c.get("type") == "text":
            ntext = c.get("text", "")
            i = ntext.find("Original Response")
            seg = ntext[i + len("Original Response"):].strip()
            jstart = seg.find("{"); jend = seg.rfind("}")
            if jstart >= 0 and jend > jstart:
                try:
                    obj = json.loads(seg[jstart:jend + 1])
                    nutri = parse_nutrition(obj.get("data", ""))
                except Exception as e:
                    print("营养解析失败:", e)

    materials = []
    for code, info in meals_map.items():
        name = info.get("name", "")
        if not name:
            continue
        cat = cat_of_code.get(code, "")
        role = classify(name, cat)
        color, emoji, role_cn = ROLE_META[role]
        try:
            price = float(info.get("currentPrice") or 0)
        except Exception:
            price = 0.0
        nut = match_nutri(name, nutri)
        materials.append({
            "code": code,
            "name": name,
            "role": role,
            "role_cn": role_cn,
            "category": cat,
            "color": color,
            "emoji": emoji,
            "price": price,
            "originalPrice": info.get("originalPrice"),
            "image": info.get("image", ""),
            "tags": [],
            "nutrition": nut,
        })

    # 角色统计
    from collections import Counter
    cnt = Counter(m["role"] for m in materials)
    out = {
        "updated_at": "2026-10-20",
        "source": "麦当劳 MCP query-meals（门店 1450713 上海黄浦华旭国际大厦餐厅）+ list-nutrition-foods",
        "store": {"storeCode": "1450713", "storeName": "麦当劳上海黄浦华旭国际大厦餐厅"},
        "total": len(materials),
        "role_counts": dict(cnt),
        "materials": materials,
    }
    with open(os.path.join(ASSETS, "materials.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"已生成 materials.json: 共 {len(materials)} 个素材")
    print("角色分布:", dict(cnt))
    # 打印样例
    for m in materials[:8]:
        print(f"  [{m['role_cn']}] {m['name']} ¥{m['price']} {m['emoji']} nutri={'Y' if m['nutrition'] else 'N'}")


if __name__ == "__main__":
    main()
