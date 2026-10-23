#!/usr/bin/env python3
# 本地经 hf-mirror 下载 InstantMesh 全部权重（XET 禁用，规避 CAS），输出 _vendor/im_assets
import os, sys, time, traceback
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HUB_DISABLE_XET"] = "1"
from huggingface_hub import snapshot_download, hf_hub_download

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "_vendor", "im_assets"))
os.makedirs(ROOT, exist_ok=True)
log = open(os.path.join(ROOT, "dl_progress.log"), "a", buffering=1)

def ok(msg):
    print("OK ", msg, flush=True); log.write("OK "+msg+"\n")
def err(msg, e):
    print("ERR", msg, repr(e)[:300], flush=True); log.write("ERR "+msg+" "+repr(e)[:300]+"\n")

# 1) zero123plus-v1.2 全量
try:
    t=time.time()
    p = snapshot_download(repo_id="sudo-ai/zero123plus-v1.2", local_dir=os.path.join(ROOT,"zero123plus-v1.2"), local_dir_use_symlinks=False)
    ok(f"zero123plus-v1.2 ({time.time()-t:.0f}s) -> {p}")
except Exception as e:
    err("zero123plus-v1.2", e)

# 2) Tencent 自定义 unet
try:
    t=time.time()
    p = hf_hub_download(repo_id="TencentARC/InstantMesh", filename="diffusion_pytorch_model.bin",
                        local_dir=os.path.join(ROOT,"ckpts"), local_dir_use_symlinks=False)
    ok(f"diffusion_pytorch_model.bin ({time.time()-t:.0f}s) -> {p}")
except Exception as e:
    err("diffusion_pytorch_model.bin", e)

# 3) dino-vitb16
try:
    t=time.time()
    p = snapshot_download(repo_id="facebook/dino-vitb16", local_dir=os.path.join(ROOT,"dino-vitb16"), local_dir_use_symlinks=False)
    ok(f"dino-vitb16 ({time.time()-t:.0f}s) -> {p}")
except Exception as e:
    err("dino-vitb16", e)

print("ALL_ATTEMPTED", flush=True); log.write("ALL_ATTEMPTED\n")
