#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用「麦当劳 MCP query-meals」官方快照重建单品素材库 + 下载官方产品图。

输入：
  assets/menu_snapshot_20261023.json   MCP query-meals 原始快照（code -> [name, imgPath, price, origPrice]）
  assets/nutrition_raw.json            MCP list-nutrition-foods 快照
  assets/materials.json                旧素材库（仅作营养/条目兜底）
输出：
  assets/mcd_photos/<code>.png         官方产品图（GIF 取首帧转 PNG，保留透明通道）
  assets/materials.json                重建后的素材库（附 group 分组、photo 本地路径）

用法：python scripts/refresh_menu_from_mcp.py [--no-download]
"""
import io
import json
import os
import re
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
PHOTO_DIR = os.path.join(ASSETS, "mcd_photos")
SNAP = os.path.join(ASSETS, "menu_snapshot_20261023.json")
MAT = os.path.join(ASSETS, "materials.json")
NUTRI_RAW = os.path.join(ASSETS, "nutrition_raw.json")

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
      "Referer": "https://www.mcdonalds.com.cn/"}

# 分组：(key, 中文名, emoji, 主色) —— 供 2D 单品货架分组展示
GROUPS = [
    ("burger",  "汉堡",       "🍔", "#C8772E"),
    ("chicken", "炸鸡",       "🍗", "#E8893B"),
    ("side",    "小食",       "🍟", "#E8B84B"),
    ("dessert", "甜品冰品",   "🍦", "#E98AAE"),
    ("drink",   "饮品",       "🥤", "#5AA9E6"),
    ("coffee",  "麦咖啡",     "☕", "#8B5E3C"),
    ("sauce",   "蘸酱",       "🥫", "#C0392B"),
    ("combo",   "整份套餐",   "🍱", "#9B8AB8"),
    ("merch",   "周边",       "🧣", "#B9A7C9"),
    ("other",   "其他",       "🍽️", "#B9A7C9"),
]
GROUP_CN = {g[0]: g[1] for g in GROUPS}
GROUP_EMOJI = {g[0]: g[2] for g in GROUPS}
GROUP_COLOR = {g[0]: g[3] for g in GROUPS}


# 名称不足以判断的个别商品，显式指定分组
OVERRIDE = {
    "1401": "side",     # 麦乐鸡（鸡块类小食，不属炸鸡）
    "1100": "burger",   # 巨无霸（名称无"堡"字）
    "1450": "burger",   # 麦香鸡（实为鸡腿汉堡）
}


def classify(name, code=""):
    """把官方商品名归入单一分组。顺序即优先级。"""
    if code in OVERRIDE:
        return OVERRIDE[code]
    n = name
    # 1) 周边
    if any(k in n for k in ["丝巾", "棒球帽", "水手帽", "星愿贴", "捶", "痒痒挠",
                            "周边", "徽章", "贴纸", "玩具"]):
        return "merch"
    # 2) 整份套餐（含多件套 / 随心选 / 拼盘 / 双拼 / 开心乐园餐）
    if re.search(r"(件套|套餐|随心选|随心配|分享餐|双人餐|单人餐|拼盘|任选|四宫格|双拼|"
                 r"全盒|超值|乐园餐|单品精选)", n):
        return "combo"
    # 3) 汉堡（先于鱼/牛/鸡，避免"鳕鱼堡/鸡腿堡"落到其他类）
    if "堡" in n or "巨无霸" in n:
        return "burger"
    # 4) 炸鸡（"蘸酱炸鸡""蘸酱…鸡块"属炸鸡产品线，先于酱料判断）
    if any(k in n for k in ["炸鸡", "脆汁鸡", "鸡块", "鸡翅", "翅", "鸡排", "肉骨鸡", "骨鸡"]):
        return "chicken"
    # 5) 蘸酱
    if "酱" in n:
        return "sauce"
    # 6) 麦咖啡线
    if any(k in n for k in ["咖啡", "拿铁", "美式", "卡布奇诺", "浓缩", "奶铁", "黑巧"]):
        return "coffee"
    # 7) 甜品冰品（奶昔计入甜品）
    if any(k in n for k in ["冰淇淋", "圆筒", "新地", "麦旋风", "派", "圣代", "雪糕", "奶昔", "阿芙佳朵"]):
        return "dessert"
    # 8) 饮品
    if any(k in n for k in ["可乐", "雪碧", "茶", "果汁", "纯悦", "牛奶", "燕麦奶", "柠檬", "橙",
                            "柠柠", "饮", "怡泉", "麦炫酷", "水"]):
        return "drink"
    # 9) 小食（薯类/芝士条/玉米/苹果）
    if any(k in n for k in ["薯", "芝士条", "玉米", "苹果", "沙拉"]):
        return "side"
    # 10) 鱼虾单品
    if any(k in n for k in ["鱼", "虾"]):
        return "chicken"
    # 11) 其余含"鸡"
    if "鸡" in n:
        return "chicken"
    return "other"


def parse_nutrition(path):
    """解析 list-nutrition-foods 的 data 字段 → {productName: {...}}"""
    out = {}
    if not os.path.exists(path):
        return out
    try:
        raw = json.load(open(path, encoding="utf-8"))
    except Exception:
        return out
    text = ""
    for c in raw.get("result", {}).get("content", []):
        if c.get("type") == "text":
            text = c.get("text", "")
    i = text.find("Original Response")
    seg = text[i + len("Original Response"):] if i >= 0 else text
    j0, j1 = seg.find("{"), seg.rfind("}")
    if j0 < 0 or j1 <= j0:
        return out
    try:
        obj = json.loads(seg[j0:j1 + 1])
    except Exception:
        return out
    data_str = obj.get("data", "")
    m = re.search(r"\[(\d+)\]\{([^}]*)\}", data_str)
    if not m:
        return out
    cols = [c.strip() for c in m.group(2).split(",")]
    for line in data_str[m.end():].splitlines():
        parts = [p.strip() for p in line.strip().split(",")]
        if len(parts) < len(cols):
            continue
        rec = dict(zip(cols, parts))
        nm = rec.get("productName", "")
        if nm:
            out[nm] = {k: rec.get(k) for k in
                       ("energyKcal", "protein", "fat", "carbohydrate", "sodium", "calcium")}
    return out


SUFFIX = re.compile(r"(三件套|四件套|八件套|套餐|单品|随心配|随心选|分享餐|双人餐|单人餐|拼盘|"
                    r"（.*|\(.*|【.*?】|组合|超值|精选|经典|全新|上新|限定|回归|同款|周边|麦金卡|爆款).*$")


def clean_name(name):
    n = name
    for s in ["三件套", "四件套", "八件套", "套餐", "单品", "随心配", "随心选", "分享餐",
              "双人餐", "单人餐", "拼盘", "组合", "（", "）", "(", ")", "【", "】"]:
        n = n.replace(s, "")
    return n.strip()


def match_nutri(name, table):
    if name in table:
        return table[name]
    cn = clean_name(name)
    if cn and cn in table:
        return table[cn]
    # 双向包含（取名称最长、最贴近的一条，避免"可乐"命中"零度可乐"之类）
    best, best_len = None, 0
    for k, v in table.items():
        if not k:
            continue
        if k in name or (cn and (k in cn or cn in k)):
            if len(k) > best_len:
                best, best_len = v, len(k)
    return best


def download_image(url, code):
    """下载官方图；GIF 取首帧存 PNG。返回 (ok, bytes_len)"""
    dest = os.path.join(PHOTO_DIR, code + ".png")
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=25) as r:
            blob = r.read()
    except Exception as e:
        return False, "ERR " + str(e)[:80]
    if len(blob) < 500:
        return False, "too small"
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(blob))
        if im.mode not in ("RGBA", "LA"):
            im = im.convert("RGBA")
        else:
            im = im.convert("RGBA")
        im.save(dest, "PNG", optimize=True)
    except Exception as e:
        return False, "PIL " + str(e)[:60]
    return True, len(blob)


def main():
    no_dl = "--no-download" in sys.argv
    snap = json.load(open(SNAP, encoding="utf-8"))
    base = snap.get("img_base", "")
    meals = snap["meals"]

    # 旧素材库（兜底：营养 + 快照缺失的季节性单品）
    old = {}
    if os.path.exists(MAT):
        try:
            for m in json.load(open(MAT, encoding="utf-8")).get("materials", []):
                old[m["code"]] = m
        except Exception:
            pass
    nutri = parse_nutrition(NUTRI_RAW)

    os.makedirs(PHOTO_DIR, exist_ok=True)
    rows, dl_ok, dl_fail = [], 0, []
    for code, rec in meals.items():
        name, img_path, price, orig = (list(rec) + [None] * 4)[:4]
        url = base + img_path
        if not no_dl:
            ok, info = download_image(url, code)
            if ok:
                dl_ok += 1
            else:
                dl_fail.append((code, name, info))
        # 营养：MCP 营养表 → 旧素材库
        nut = match_nutri(name, nutri) or (old.get(code) or {}).get("nutrition")
        grp = classify(name, code)
        rows.append({
            "code": code,
            "name": name,
            "group": grp,
            "group_cn": GROUP_CN[grp],
            "emoji": GROUP_EMOJI[grp],
            "color": GROUP_COLOR[grp],
            "price": float(price or 0),
            "originalPrice": orig,
            "image": url,
            "photo": "/assets/mcd_photos/%s.png" % code,
            "nutrition": nut,
            "buyable": grp not in ("combo", "merch"),
        })

    # 说明：MCP 快照即为「当前官方在售」权威清单。
    # 旧库里已下架的季节限定单品（不在快照中）不再进入单品货架，避免展示不可购买的商品。
    dropped = [m["name"] for c, m in old.items() if c not in meals]
    if dropped:
        print("已下架、不计入货架的历史单品 %d 项：%s" % (len(dropped), "、".join(dropped[:8])))

    # 分组排序：按 GROUPS 顺序，组内按价格降序（主餐在前）
    order = {g[0]: i for i, g in enumerate(GROUPS)}
    rows.sort(key=lambda r: (order.get(r["group"], 99), -r["price"]))

    from collections import Counter
    cnt = Counter(r["group"] for r in rows)
    out = {
        "updated_at": time.strftime("%Y-%m-%d %H:%M"),
        "source": "麦当劳 MCP query-meals + list-nutrition-foods（门店 %s %s）"
                  % (snap.get("storeCode"), snap.get("storeName")),
        "store": {"storeCode": snap.get("storeCode"), "storeName": snap.get("storeName")},
        "total": len(rows),
        "group_counts": dict(cnt),
        "groups": [{"key": g[0], "cn": g[1], "emoji": g[2], "color": g[3]} for g in GROUPS],
        "materials": rows,
    }
    with open(MAT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print("素材库已重建：%d 项（官方图下载成功 %d）" % (len(rows), dl_ok))
    print("分组：", dict(cnt))
    print("可单独购买（进入单品货架）：", sum(1 for r in rows if r["buyable"]))
    n_nutri = sum(1 for r in rows if r["nutrition"])
    print("含营养数据：%d / %d" % (n_nutri, len(rows)))
    if dl_fail:
        print("下载失败 %d 项：" % len(dl_fail))
        for c, n, i in dl_fail[:15]:
            print("   ", c, n, i)


if __name__ == "__main__":
    main()
