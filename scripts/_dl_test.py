#!/usr/bin/env python3
import os, sys, time
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HUB_DISABLE_XET"] = "1"
from huggingface_hub import hf_hub_download, snapshot_download

ROOT = os.path.join(os.path.dirname(__file__), "..", "_vendor", "im_assets")
os.makedirs(ROOT, exist_ok=True)

# 1) 测试小文件能否访问 zero123plus 仓库
try:
    p = hf_hub_download("sudo-ai/zero123plus-v1.2", "model_index.json",
                        local_dir=os.path.join(ROOT, "zero123plus-v1.2"),
                        local_dir_use_symlinks=False)
    print("OK zero123plus model_index.json", flush=True)
except Exception as e:
    print("ERR zero123plus index:", repr(e), flush=True)

# 2) 必需的普通文件
for repo, fn, sub in [
    ("TencentARC/InstantMesh", "diffusion_pytorch_model.bin", "ckpts"),
    ("TencentARC/InstantMesh", "instant_mesh_base.ckpt", "ckpts"),
]:
    try:
        p = hf_hub_download(repo, fn, local_dir=os.path.join(ROOT, sub),
                            local_dir_use_symlinks=False)
        print(f"OK {fn} -> {p}", flush=True)
    except Exception as e:
        print(f"ERR {fn}:", repr(e), flush=True)

# 3) dino
try:
    p = snapshot_download("facebook/dino-vitb16", local_dir=os.path.join(ROOT, "dino-vitb16"),
                          local_dir_use_symlinks=False)
    print("OK dino snapshot", flush=True)
except Exception as e:
    print("ERR dino:", repr(e), flush=True)

# 4) 试 zero123plus 全量（XET 禁用）
try:
    t0=time.time()
    p = snapshot_download("sudo-ai/zero123plus-v1.2", local_dir=os.path.join(ROOT, "zero123plus-v1.2"),
                          local_dir_use_symlinks=False)
    print(f"OK zero123plus full ({time.time()-t0:.0f}s)", flush=True)
except Exception as e:
    print("ERR zero123plus full:", repr(e), flush=True)
print("TEST_DONE", flush=True)
