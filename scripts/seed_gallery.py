#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成画廊初始作品（3 份套餐 + 1 份组件汉堡），用于演示与回归。
- 套餐预览图：PIL 按前端 canvas 的同一版式合成（官方产品图直接贴图）
- 组件汉堡预览图：由无头 Chrome 截取 3D 场景后裁切

运行：python scripts/seed_gallery.py [--reset]
"""
import argparse
import base64
import io
import json
import os
import subprocess
import sys
import tempfile
import urllib.request

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
GAL_DIR = os.path.join(ROOT, "gallery")
GAL_PATH = os.path.join(GAL_DIR, "gallery.json")
SHOTS = os.path.join(ROOT, "_shots")
FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\simhei.ttf", r"C:\Windows\Fonts\arial.ttf",
]

CW, CH, PAD, TOP = 200, 210, 26, 92


def font(size, bold=False):
    cands = list(FONT_CANDIDATES)
    if bold:
        cands = [r"C:\Windows\Fonts\msyhbd.ttc"] + cands
    for p in cands:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def load_materials():
    with open(os.path.join(ASSETS, "materials.json"), encoding="utf-8") as f:
        d = json.load(f)
    return {m["code"]: m for m in d["materials"]}


def nutri(m):
    n = m.get("nutrition")
    if not n:
        return None
    g = lambda k: float(n.get(k) or 0) if str(n.get(k) or "").replace(".", "", 1).isdigit() else 0.0
    return {"kcal": g("energyKcal"), "protein": g("protein"), "fat": g("fat"),
            "carb": g("carbohydrate"), "sodium": g("sodium")}


def compose(items, name, by_code):
    """items: [(code, qty)] -> (JPEG bytes, summary)"""
    flat = []
    price = kcal = pro = fat = carb = sod = 0.0
    for code, qty in items:
        m = by_code.get(code)
        if not m:
            continue
        for _ in range(qty):
            flat.append(m)
        price += float(m.get("price") or 0) * qty
        nu = nutri(m)
        if nu:
            kcal += nu["kcal"] * qty
            pro += nu["protein"] * qty
            fat += nu["fat"] * qty
            carb += nu["carb"] * qty
            sod += nu["sodium"] * qty
    cols = min(4, max(1, len(flat)))
    rows = (len(flat) + cols - 1) // cols
    W = cols * CW + PAD * 2
    H = TOP + rows * CH + PAD
    im = Image.new("RGB", (W, H), (255, 253, 248))
    d = ImageDraw.Draw(im)
    # 竖向渐变背景 + 顶部品牌条
    top_c, bot_c = (255, 253, 248), (255, 236, 203)
    for y in range(H):
        t = y / max(1, H - 1)
        d.line([(0, y), (W, y)], fill=tuple(int(top_c[i] + (bot_c[i] - top_c[i]) * t) for i in range(3)))
    d.rectangle([0, 0, W, 6], fill=(232, 148, 59))
    d.text((PAD, 18), name, font=font(26, True), fill=(58, 44, 26))
    d.text((PAD, 54), "共 %d 件 · ¥%.2f · ≈%d kcal" % (len(flat), price, round(kcal)),
           font=font(18), fill=(138, 122, 102))
    for i, m in enumerate(flat):
        col, row = i % cols, i // cols
        bx, by = PAD + col * CW + 6, TOP + row * CH + 4
        bw, bh = CW - 12, CH - 12
        d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=16, fill=(255, 255, 255),
                            outline=(240, 226, 204), width=2)
        p = os.path.join(ASSETS, "mcd_photos", m["code"] + ".png")
        if os.path.exists(p):
            pic = Image.open(p).convert("RGBA")
            pic.thumbnail((bw - 24, bh - 58), Image.LANCZOS)
            px = bx + (bw - pic.width) // 2
            py = by + 8 + (bh - 58 - pic.height) // 2
            im.paste(pic, (px, py), pic)
        nm = m["name"]
        if len(nm) > 9:
            nm = nm[:9] + "…"
        f2 = font(15, True)
        tw = d.textlength(nm, font=f2)
        d.text((bx + (bw - tw) / 2, by + bh - 36), nm, font=f2, fill=(58, 44, 26))
        pr = "¥%.1f" % float(m.get("price") or 0)
        f3 = font(16, True)
        tw = d.textlength(pr, font=f3)
        d.text((bx + (bw - tw) / 2, by + bh - 17), pr, font=f3, fill=(192, 57, 43))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=88)
    summary = {"price": round(price, 2), "kcal": round(kcal), "protein": round(pro, 1),
               "fat": round(fat, 1), "carb": round(carb, 1), "sodium": round(sod),
               "count": len(flat)}
    return buf.getvalue(), summary


def post(body):
    req = urllib.request.Request("http://127.0.0.1:8765/api/designs",
                                 data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=20).read())


def vote(did, voter):
    req = urllib.request.Request("http://127.0.0.1:8765/api/vote",
                                 data=json.dumps({"id": did, "voter": voter}).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=10).read())
    except Exception:
        return None


def chrome_shot(url, out, w=1200, h=900):
    chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if not os.path.exists(chrome):
        chrome = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    if not os.path.exists(chrome):
        return False
    os.makedirs(SHOTS, exist_ok=True)
    cmd = [chrome, "--headless=new", "--no-sandbox", "--disable-gpu",
           "--use-gl=angle", "--use-angle=swiftshader", "--hide-scrollbars",
           "--window-size=%d,%d" % (w, h), "--virtual-time-budget=14000",
           "--screenshot=" + out, url]
    subprocess.run(cmd, capture_output=True, timeout=90)
    return os.path.exists(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true")
    args = ap.parse_args()
    by_code = load_materials()
    if args.reset:
        os.makedirs(GAL_DIR, exist_ok=True)
        for f in os.listdir(GAL_DIR):
            if f.startswith("img_"):
                os.remove(os.path.join(GAL_DIR, f))
        with open(GAL_PATH, "w", encoding="utf-8") as f:
            json.dump({"designs": []}, f, ensure_ascii=False, indent=2)
        print("画廊已清空")

    seeds = [
        ("巨无霸经典套餐", "正浩", [("1100", 1), ("4810", 1), ("9900008751", 1)]),
        ("双牛芝士狂欢", "小鹿", [("1120", 1), ("521316", 1), ("4810", 1), ("4437", 1), ("9900008751", 1)]),
        ("板烧轻食组合", "阿橙", [("1406", 1), ("6102", 1), ("515520", 1), ("515837", 1)]),
    ]
    made = []
    for name, author, items in seeds:
        jpg, summary = compose(items, name, by_code)
        res = post({
            "name": name, "author": author, "mode": "combo",
            "items": [{"code": c, "qty": q} for c, q in items],
            "preview": "data:image/jpeg;base64," + base64.b64encode(jpg).decode(),
            "summary": summary,
        })
        made.append(res["id"])
        print("套餐已发布:", name, res["id"], "¥%.2f" % summary["price"])

    # 组件汉堡：截 3D 场景
    shot = os.path.join(SHOTS, "seed3d.png")
    url = "http://127.0.0.1:8765/?burger=511781"
    if chrome_shot(url, shot):
        im = Image.open(shot).convert("RGB")
        w, h = im.size
        box = (270, 54, w - 302, h)          # 只留中间 3D 画布
        crop = im.crop(box)
        crop.thumbnail((1000, 700), Image.LANCZOS)
        buf = io.BytesIO(); crop.save(buf, "JPEG", quality=88)
        layers = ["bunBottom", "beef", "sauce", "cheese", "tomato", "bacon", "lettuce", "bunTop"]
        labels = ["面包胚(下)", "牛肉饼", "酱料", "芝士片", "番茄片", "培根", "生菜", "面包胚(上·带芝麻)"]
        res = post({"name": "培根安格斯厚牛堡(重组)", "author": "大壮", "mode": "component",
                    "layers": layers, "labels": labels,
                    "preview": "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode(),
                    "summary": {"price": 24.6, "kcal": 606, "protein": 44.3, "fat": 27,
                                "carb": 48, "count": len(layers)}})
        made.append(res["id"])
        print("组件汉堡已发布:", res["id"])
    else:
        print("跳过组件汉堡（未找到浏览器）")

    # 预置一些票，让排名有区分
    for i, did in enumerate(made):
        for v in ["小明", "小红", "阿杰", "Lily", "Tom", "老王", "测试用户"][: (len(made) - i) * 2 + 1]:
            vote(did, v)
    g = json.loads(urllib.request.urlopen("http://127.0.0.1:8765/api/gallery").read())
    print("画廊共 %d 件：" % len(g["designs"]))
    for d in g["designs"]:
        print("   %-24s %-4s %2d 票  ¥%s" % (d["name"], "套餐" if d["mode"] == "combo" else "汉堡",
                                            d["votes"], (d.get("summary") or {}).get("price")))


if __name__ == "__main__":
    main()
