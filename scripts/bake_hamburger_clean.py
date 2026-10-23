# -*- coding: utf-8 -*-
"""
汉堡 GLB 碎片清理：仅保留主体 + 与主体紧贴(dmin < ratio*gmax)的分量，
裁掉重建产生的悬空碎块（"主体之外的多余部分"）。
顶点数据完全不动，只重写索引缓冲 → 顶点色/UV/法线全部保留。
"""
import json, struct, sys, os, shutil
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

COMP = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}

def load_glb(path):
    with open(path, "rb") as f: data = f.read()
    magic, ver, length = struct.unpack("<III", data[:12])
    off = 12; j = None; b = None
    while off < length:
        clen, ctype = struct.unpack("<II", data[off:off+8]); body = data[off+8:off+8+clen]
        if ctype == 0x4E4F534A: j = json.loads(body.decode("utf-8"))
        elif ctype == 0x004E4942: b = body
        off += 8 + clen
    return j, b

def write_glb(gltf, binc, path):
    j = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    j += b" " * ((4 - len(j) % 4) % 4)
    b = bytes(binc) + b"\x00" * ((4 - len(binc) % 4) % 4)
    total = 12 + 8 + len(j) + 8 + len(b)
    out = struct.pack("<III", 0x46546C67, 2, total)
    out += struct.pack("<II", len(j), 0x4E4F534A) + j
    out += struct.pack("<II", len(b), 0x004E4942) + b
    with open(path, "wb") as f: f.write(out)

def acc(g, bc, idx):
    a = g["accessors"][idx]; bv = g["bufferViews"][a["bufferView"]]
    n = a["count"]; boff = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    if a["type"] == "VEC3":
        return np.frombuffer(bc, dtype=np.float32, count=n*3, offset=boff).reshape(n, 3)
    dt = COMP[a["componentType"]]
    return np.frombuffer(bc, dtype=dt, count=n, offset=boff)

def clean(path, out_path, ratio=0.03, verbose=True):
    g, b = load_glb(path)
    b = bytearray(b)
    prim = g["meshes"][0]["primitives"][0]
    V = acc(g, b, prim["attributes"]["POSITION"])
    I = acc(g, b, prim["indices"]).astype(np.int64).reshape(-1, 3)
    n = len(V)
    # 连通分量（向量化）
    e = np.vstack([I[:, [0, 1]], I[:, [1, 2]]])
    graph = coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n))
    _, labels = connected_components(graph, directed=False)
    counts = np.bincount(labels)
    mk = int(np.argmax(counts))
    mv = V[labels == mk]
    gmax = float((mv.max(0) - mv.min(0)).max())
    tree = cKDTree(mv)
    keep = np.zeros(len(counts), dtype=bool); keep[mk] = True
    removed = []
    for k in range(len(counts)):
        if k == mk: continue
        pv = V[labels == k]
        dmin = float(tree.query(pv, k=1)[0].min()) / gmax
        if dmin < ratio: keep[k] = True
        else: removed.append((int(counts[k]), round(dmin, 3)))
    vkeep = keep[labels]
    tri_keep = vkeep[I[:, 0]] & vkeep[I[:, 1]] & vkeep[I[:, 2]]
    newI = I[tri_keep].reshape(-1)
    # 尽量用 uint16（体积小、且更易原位覆盖旧缓冲）
    use16 = bool(V.shape[0] <= 65535)
    ctype = 5123 if use16 else 5125
    raw = newI.astype(np.uint16 if use16 else np.uint32).tobytes()

    old_ac = g["accessors"][prim["indices"]]
    old_bv = g["bufferViews"][old_ac["bufferView"]]
    old_room = old_bv["byteLength"] - old_ac.get("byteOffset", 0)
    if old_bv.get("byteStride") is None and len(raw) <= old_room:
        # 原位覆盖：不新增数据，文件不膨胀
        base = old_bv["byteOffset"] + old_ac.get("byteOffset", 0)
        b[base:base+len(raw)] = raw
        old_bv["byteLength"] = old_ac.get("byteOffset", 0) + len(raw)
        old_ac["count"] = int(len(newI)); old_ac["componentType"] = ctype
        reuse = "in-place"
    else:
        off = len(b); off += (4 - off % 4) % 4
        b += b"\x00" * (off - len(b))
        b += raw
        bv_idx = len(g["bufferViews"])
        g["bufferViews"].append({"buffer": 0, "byteOffset": off, "byteLength": int(len(raw))})
        ac_idx = len(g["accessors"])
        g["accessors"].append({"bufferView": bv_idx, "componentType": ctype,
                               "count": int(len(newI)), "type": "SCALAR"})
        prim["indices"] = ac_idx
        reuse = "appended"
    g["buffers"][0]["byteLength"] = len(b)
    write_glb(g, b, out_path)
    if verbose:
        print(f"  {os.path.basename(path)}: verts={n} comps={len(counts)} "
              f"removed={len(removed)} comps / {sum(r[0] for r in removed)} verts "
              f"({sum(r[0] for r in removed)/n*100:.1f}%) tris {len(I)}->{len(newI)//3} "
              f"[{reuse}] size {os.path.getsize(path)/1e6:.2f}->{os.path.getsize(out_path)/1e6:.2f}MB")
        if removed: print(f"      removed dmin: {sorted([r[1] for r in removed], reverse=True)[:8]}")
    return len(removed), int(sum(r[0] for r in removed))

if __name__ == "__main__":
    root = os.path.join(os.path.dirname(__file__), "..")
    src_dir = os.path.join(root, "assets", "mcd_models")
    dst_dir = os.path.join(root, "assets", "mcd_models_clean")
    os.makedirs(dst_dir, exist_ok=True)
    burgers = ["1100", "1120", "1440", "511781", "9900003586", "1406", "4648", "521316", "521952", "521903"]
    print("=== 汉堡碎片清理 ===")
    for c in burgers:
        p = os.path.join(src_dir, c + ".glb")
        if not os.path.exists(p): print("  MISS", c); continue
        clean(p, os.path.join(dst_dir, c + ".glb"))
    print("done ->", dst_dir)
