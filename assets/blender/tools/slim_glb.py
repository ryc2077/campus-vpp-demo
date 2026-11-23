#!/usr/bin/env python3
"""瘦身总览 GLB：只动贴图，不动几何 / 材质 / 节点。

口径（BLENDER_MODELS.md §10，池塘返工版）：
  - color（baseColorTexture）贴图 -> 最长边 512px + JPEG q80；
  - normal / metallicRoughness 贴图 -> 最长边 256px PNG；
  - 草叶 alpha 贴图（带透明通道，如 grass-side-colour）永不转 JPEG，
    一律 PNG、最长边 512px；
  - 同时挂在 color 与 normal/mr 两个槽位的贴图按 normal 处理（256px PNG），
    避免 JPEG 破坏法线 / 粗糙度数据；
  - 只缩小不放大；已小于等于目标尺寸且格式已是目标格式的贴图原字节保留；
  - 几何（accessor / mesh / primitive / 材质槽）与节点树一字不改。

做法：重建 BIN chunk——原样拷贝全部非贴图 bufferView（逐个 4 字节对齐），
再追加重编码后的贴图字节；accessor 的 bufferView 索引按旧->新映射重写，
image 的 bufferView / mimeType 指向新数据。旧贴图字节不保留（否则瘦不下来）。
GLB JSON 除 images / bufferViews / buffers 三处外逐字节等价，脚本末尾自检。

用法：
  python3 slim_glb.py <输入.glb> <输出.glb> [--color-dim 512] [--jpeg-q 80] [--norm-dim 256]
依赖：Pillow（本机 python3 已装，10.2.0）。
"""

import argparse
import copy
import io
import json
import struct
import sys

from PIL import Image

GLB_MAGIC = 0x46546C67  # 'glTF'
GLB_VERSION = 2
CHUNK_JSON = 0x4E4F534A  # 'JSON'
CHUNK_BIN = 0x004E4942  # 'BIN\0'


def _pad4(n):
    return (4 - n % 4) % 4


def read_glb(path):
    with open(path, "rb") as f:
        data = f.read()
    magic, version, _length = struct.unpack("<III", data[:12])
    if magic != GLB_MAGIC or version != GLB_VERSION:
        raise ValueError("%s 不是 glTF 2.0 GLB" % path)
    jlen, jtype = struct.unpack("<II", data[12:20])
    if jtype != CHUNK_JSON:
        raise ValueError("%s 首 chunk 不是 JSON" % path)
    gltf = json.loads(data[20:20 + jlen])
    off = 20 + jlen
    bin_data = b""
    if off < len(data):
        blen, btype = struct.unpack("<II", data[off:off + 8])
        if btype != CHUNK_BIN:
            raise ValueError("%s 第二 chunk 不是 BIN" % path)
        bin_data = data[off + 8:off + 8 + blen]
    return gltf, bin_data


def write_glb(path, gltf, bin_data):
    j = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    j += b" " * _pad4(len(j))
    b = bin_data + b"\x00" * _pad4(len(bin_data))
    total = 12 + 8 + len(j) + (8 + len(b) if b else 0)
    with open(path, "wb") as f:
        f.write(struct.pack("<III", GLB_MAGIC, GLB_VERSION, total))
        f.write(struct.pack("<II", len(j), CHUNK_JSON))
        f.write(j)
        if b:
            f.write(struct.pack("<II", len(b), CHUNK_BIN))
            f.write(b)


def image_roles(gltf):
    """image 索引 -> 它被哪些材质槽引用。"""
    roles = {}
    for mat in gltf.get("materials", []):
        pbr = mat.get("pbrMetallicRoughness", {})
        slots = []
        for key in ("baseColorTexture", "metallicRoughnessTexture"):
            t = pbr.get(key)
            if t is not None:
                slots.append((key, t["index"]))
        for key in ("normalTexture", "emissiveTexture", "occlusionTexture"):
            t = mat.get(key)
            if t is not None:
                slots.append((key, t["index"]))
        for key, tidx in slots:
            tex = gltf["textures"][tidx]
            roles.setdefault(tex["source"], set()).add(key)
    return roles


def _has_alpha(img):
    if img.mode in ("RGBA", "LA", "PA"):
        return True
    if img.mode == "P":
        return "transparency" in img.info
    return False


def reencode(img, role_set, color_dim, norm_dim, jpeg_q):
    """返回 (新字节, 新 mime, 处理说明)。"""
    alpha = _has_alpha(img)
    if alpha:
        target, fmt, mime = 512, "PNG", "image/png"
        why = "alpha->PNG512"
    elif "normalTexture" in role_set or "metallicRoughnessTexture" in role_set:
        target, fmt, mime = norm_dim, "PNG", "image/png"
        why = "normal/mr->PNG%d" % norm_dim
    elif "baseColorTexture" in role_set:
        target, fmt, mime = color_dim, "JPEG", "image/jpeg"
        why = "color->JPEG%d q%d" % (color_dim, jpeg_q)
    else:
        # 无材质引用的贴图：保守按 normal 口径走 PNG，不转 JPEG。
        target, fmt, mime = norm_dim, "PNG", "image/png"
        why = "norole->PNG%d" % norm_dim
    w, h = img.size
    scale = min(1.0, target / max(w, h))
    if scale < 1.0:
        img = img.resize((max(1, int(round(w * scale))),
                          max(1, int(round(h * scale)))),
                         Image.LANCZOS)
    buf = io.BytesIO()
    if fmt == "JPEG":
        if img.mode in ("RGBA", "LA", "PA"):
            img = img.convert("RGB")
        elif img.mode == "P":
            img = img.convert("RGB")
        img.save(buf, "JPEG", quality=jpeg_q, optimize=True)
    else:
        img.save(buf, "PNG", optimize=True)
    return buf.getvalue(), mime, "%s %dx%d" % (why, img.size[0], img.size[1])


def main():
    ap = argparse.ArgumentParser(description="瘦身 GLB：只动贴图。")
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--color-dim", type=int, default=512)
    ap.add_argument("--jpeg-q", type=int, default=80)
    ap.add_argument("--norm-dim", type=int, default=256)
    args = ap.parse_args()

    gltf, bin_data = read_glb(args.src)
    orig = copy.deepcopy(gltf)  # 自检对照：瘦身前 JSON 原样快照
    images = gltf.get("images", [])
    bvs = gltf.get("bufferViews", [])
    roles = image_roles(gltf)

    # 贴图按 bufferView 分组（同一 bufferView 被多图共用时合并角色处理）。
    bv_to_images = {}
    for idx, im in enumerate(images):
        if "uri" in im:
            raise ValueError("image %d 有外部 uri（%s），本脚本只处理内嵌贴图"
                             % (idx, im["uri"]))
        bv_to_images.setdefault(im["bufferView"], []).append(idx)
    img_bv_set = set(bv_to_images)

    # 逐组重编码贴图。
    new_img_bytes = {}   # image 索引 -> (字节, mime)
    stats = {}
    for bv_idx, idxs in sorted(bv_to_images.items()):
        bv = bvs[bv_idx]
        off = bv.get("byteOffset", 0)
        raw = bin_data[off:off + bv["byteLength"]]
        img = Image.open(io.BytesIO(raw))
        img.load()
        role_set = set()
        for i in idxs:
            role_set |= roles.get(i, set())
        orig_mime = images[idxs[0]].get("mimeType", "image/png")
        target = 512 if _has_alpha(img) else (
            args.norm_dim if ("normalTexture" in role_set
                             or "metallicRoughnessTexture" in role_set)
            else args.color_dim)
        # 已达标且格式已是目标格式：原字节保留，零风险。
        want_jpeg = (not _has_alpha(img)
                     and "normalTexture" not in role_set
                     and "metallicRoughnessTexture" not in role_set
                     and "baseColorTexture" in role_set)
        if (max(img.size) <= target
                and ((want_jpeg and orig_mime == "image/jpeg")
                     or (not want_jpeg and orig_mime == "image/png"))):
            for i in idxs:
                new_img_bytes[i] = (raw, orig_mime)
            stats.setdefault("kept-original", []).append(
                "%s %dx%d" % (images[idxs[0]].get("name", "?"),
                              img.size[0], img.size[1]))
            continue
        data, mime, note = reencode(img, role_set, args.color_dim,
                                    args.norm_dim, args.jpeg_q)
        for i in idxs:
            new_img_bytes[i] = (data, mime)
        stats.setdefault(note.split(" ")[0], []).append(
            "%s: %d -> %d B" % (images[idxs[0]].get("name", "?"),
                                len(raw), len(data)))

    # 重建 BIN：先原样拷贝非贴图 bufferView，再追加新贴图字节。
    new_bin = bytearray()
    bv_remap = {}   # 旧 bufferView 索引 -> 新索引
    new_bvs = []
    for old_idx, bv in enumerate(bvs):
        if old_idx in img_bv_set:
            continue
        off = len(new_bin)
        data = bin_data[bv.get("byteOffset", 0):
                        bv.get("byteOffset", 0) + bv["byteLength"]]
        new_bin += data
        new_bin += b"\x00" * _pad4(len(data))
        nbv = dict(bv)
        nbv["byteOffset"] = off
        bv_remap[old_idx] = len(new_bvs)
        new_bvs.append(nbv)
    for idx, im in enumerate(images):
        data, mime = new_img_bytes[idx]
        off = len(new_bin)
        new_bin += data
        new_bin += b"\x00" * _pad4(len(data))
        nbv = {"buffer": 0, "byteOffset": off, "byteLength": len(data)}
        new_bvs.append(nbv)
        im["bufferView"] = len(new_bvs) - 1
        im["mimeType"] = mime

    # accessor 引用的 bufferView 按映射重写；其余字段一字不改。
    for acc in gltf.get("accessors", []):
        if "bufferView" in acc:
            acc["bufferView"] = bv_remap[acc["bufferView"]]
    gltf["bufferViews"] = new_bvs
    gltf["buffers"] = [{"byteLength": len(new_bin)}]

    write_glb(args.dst, gltf, bytes(new_bin))

    # 自检：除 images / bufferViews / buffers 外，JSON 必须与输入一致；
    # accessors 只允许 bufferView 索引变（重建 BIN 所致），其余字段不动。
    gltf2, _ = read_glb(args.dst)
    for key in orig:
        if key in ("images", "bufferViews", "buffers", "accessors"):
            continue
        assert gltf2.get(key) == orig[key], "JSON 字段 %s 被改动！" % key
    assert len(gltf2["images"]) == len(images)
    assert len(gltf2["nodes"]) == len(orig.get("nodes", []))
    assert len(gltf2["materials"]) == len(orig.get("materials", []))
    assert len(gltf2["accessors"]) == len(orig.get("accessors", []))
    for a_old, a_new in zip(orig.get("accessors", []),
                            gltf2.get("accessors", [])):
        ao = {k: v for k, v in a_old.items() if k != "bufferView"}
        an = {k: v for k, v in a_new.items() if k != "bufferView"}
        assert ao == an, "accessor 被改动：%s" % (ao,)
    # 材质槽：每个 primitive 的 material 索引与输入逐项相同。
    for m_old, m_new in zip(orig.get("meshes", []),
                            gltf2.get("meshes", [])):
        assert [p.get("material") for p in m_old["primitives"]] == \
               [p.get("material") for p in m_new["primitives"]], \
               "mesh %s 的材质槽被改动" % m_old.get("name")

    import os
    src_size = os.path.getsize(args.src)
    dst_size = os.path.getsize(args.dst)
    print("SLIM %s -> %s" % (args.src, args.dst))
    print("SLIM size %d -> %d B (%.1f%%)" % (src_size, dst_size,
                                            100.0 * dst_size / src_size))
    print("SLIM images %d, nodes %d, materials %d, accessors %d"
          % (len(images), len(gltf.get("nodes", [])),
             len(gltf.get("materials", [])),
             len(gltf.get("accessors", []))))
    for k in sorted(stats):
        print("SLIM %-22s %d" % (k, len(stats[k])))
    print("DONE slim_glb")


if __name__ == "__main__":
    main()
