#!/usr/bin/env python3
import os, sys
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HUB_DISABLE_XET"] = "1"
from huggingface_hub import hf_hub_download, snapshot_download
ROOT = os.path.join(os.path.dirname(__file__), "..", "_vendor", "im_assets")
os.makedirs(ROOT, exist_ok=True)

# 仅小文件测试可达性
for repo, fn, sub in [
    ("sudo-ai/zero123plus-v1.2", "model_index.json", "zero123plus-v1.2"),
    ("TencentARC/InstantMesh", "instant_mesh_base.ckpt", "ckpts"),
]:
    try:
        p = hf_hub_download(repo, fn, local_dir=os.path.join(ROOT, sub), local_dir_use_symlinks=False)
        print("OK", fn, os.path.getsize(p), flush=True)
    except Exception as e:
        print("ERR", fn, repr(e)[:200], flush=True)
print("SMALL_DONE", flush=True)
