#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成"可发布"的精简目录（白名单复制）。

为什么需要它：
  仓库根目录含 `_vendor/`（InstantMesh 权重，约 22 GB）、`_backup/`、`_shots/` 等
  仅开发期使用的重量级目录。云平台发布是**整目录上传**，直接发布根目录会超时/失败。
  本脚本只复制运行必需的运行时文件到 `_publish/site/`，并做体积与完整性校验。

用法：
  python scripts/prepare_deploy.py            # 生成/更新 _publish/site
  python scripts/prepare_deploy.py --clean    # 先清空再生成
  python scripts/prepare_deploy.py --check    # 只校验现有 _publish/site 是否完整

发布：
  workbuddy_sites_deploy(directory="_publish/site")
  服务读取 PORT 环境变量并绑定 0.0.0.0（studio_server.py 已支持）。
"""
import argparse
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "_publish", "site")

# 运行时必需：服务端脚本 + 前端 + 数据 + 官方图 + three.js
FILES = [
    "scripts/studio_server.py",
    "assets/burger_components_3d.html",
    "assets/components3d.js",
    "assets/materials.json",
    "gallery/gallery.json",
]
DIRS = [
    "assets/mcd_photos",
    "assets/vendor",
]

# 明确不上传的重量级 / 无关目录（仅用于提示）
SKIP_NOTE = ["_vendor", "_backup", "_shots", "_legacy_pages", ".git",
             "assets/mcd_models", "assets/mcd_models_clean",
             "assets/mcd_models_hq", "assets/mcd_component_models",
             "assets/mcd_photos_clean"]

# 发布站自检：这些相对路径必须能访问
REQUIRED_REL = FILES + ["assets/mcd_photos/1100.png",
                        "assets/vendor/three.min.js",
                        "assets/vendor/OrbitControls.js",
                        "assets/vendor/GLTFLoader.js"]


def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return "%.1f %s" % (n, unit) if unit != "B" else "%d B" % n
        n /= 1024.0


def dir_size(path):
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total


def build(clean=False):
    if clean and os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT, exist_ok=True)

    missing = []
    for rel in FILES:
        src = os.path.join(ROOT, rel)
        if not os.path.isfile(src):
            missing.append(rel)
            continue
        dst = os.path.join(OUT, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)

    for rel in DIRS:
        src = os.path.join(ROOT, rel)
        if not os.path.isdir(src):
            missing.append(rel + "/")
            continue
        dst = os.path.join(OUT, rel)
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)

    # 作品预览图跟着 gallery.json 一起走
    gsrc = os.path.join(ROOT, "gallery")
    gdst = os.path.join(OUT, "gallery")
    os.makedirs(gdst, exist_ok=True)
    for name in os.listdir(gsrc):
        if name.startswith("img_") and name.lower().endswith((".jpg", ".jpeg", ".png")):
            shutil.copy2(os.path.join(gsrc, name), os.path.join(gdst, name))

    if missing:
        print("缺少必需文件，无法发布：")
        for m in missing:
            print("  [x] " + m)
        return 1
    return 0


def report():
    size = dir_size(OUT)
    n = sum(len(f) for _, _, f in os.walk(OUT))
    print("发布目录: %s" % OUT)
    print("文件数  : %d" % n)
    print("总体积  : %s" % human(size))
    print("-" * 54)
    absent = [r for r in REQUIRED_REL if not os.path.exists(os.path.join(OUT, r))]
    if absent:
        print("关键文件缺失 %d 项：" % len(absent))
        for a in absent:
            print("  [x] " + a)
    else:
        print("关键文件 %d 项齐全" % len(REQUIRED_REL))
    print("-" * 54)
    print("已排除（不进发布包）: " + ", ".join(SKIP_NOTE[:6]) + " …")
    return 0 if not absent else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clean", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if args.check:
        if not os.path.isdir(OUT):
            print("发布目录不存在，请先运行 python scripts/prepare_deploy.py")
            return 1
        return report()

    rc = build(clean=args.clean)
    if rc:
        return rc
    return report()


if __name__ == "__main__":
    sys.exit(main())
