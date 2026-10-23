#!/usr/bin/env python3
import os, sys, time
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HUB_DISABLE_XET"] = "1"
from huggingface_hub import hf_hub_download
ROOT = os.path.join(os.path.dirname(__file__), "..", "_vendor", "im_assets")
os.makedirs(ROOT, exist_ok=True)
# 试 zero123plus 的 unet（CAS 大文件）
t0=time.time()
try:
    p = hf_hub_download("sudo-ai/zero123plus-v1.2", "unet/diffusion_pytorch_model.bin",
                        local_dir=os.path.join(ROOT, "zero123plus-v1.2"), local_dir_use_symlinks=False)
    print("OK unet", os.path.getsize(p), f"{time.time()-t0:.0f}s", flush=True)
except Exception as e:
    print("ERR unet:", repr(e)[:300], flush=True)
print("DONE", flush=True)
