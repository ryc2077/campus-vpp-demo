#!/usr/bin/env python3
"""配电房雾色差分对照墙面采样（R3）。

只用标准库（zlib/struct），CI 无需装 Pillow；解码 8-bit 非交错 PNG
（color type 2 RGB / 6 RGBA，Chrome 截图即此格式）。

用法：sample_png.py <补偿后png> <补偿前png> <x> <y>
在 (x, y) 取 9x9 均值，断言三条同时成立：
  (1) 补偿后约 (156,162,160)，每通道容差 40；
  (2) 补偿前约 (177,180,139)，每通道容差 40；
  (3) 方向：R_comp < R_nocomp - 5 且 B_comp > B_nocomp + 5
      （冷色补偿压 R 提 B；绝对值受光照影响，方向才是硬证据）。
任一不成立 exit 1；解码失败 exit 2。
"""
import struct
import sys
import zlib

EXP_COMP = (156, 162, 160)
EXP_NOCOMP = (177, 180, 139)
TOL = 40
PATCH = 4  # 9x9 均值


def read_png(path):
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path}: not a PNG")
    pos = 8
    idat = b""
    w = h = bitdepth = colortype = interlace = None
    while pos < len(data):
        (ln,) = struct.unpack(">I", data[pos:pos + 4])
        typ = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            w, h, bitdepth, colortype, _comp, _filt, interlace = struct.unpack(
                ">IIBBBBB", chunk)
        elif typ == b"IDAT":
            idat += chunk
        elif typ == b"IEND":
            break
        pos += 12 + ln
    if bitdepth != 8 or colortype not in (2, 6) or interlace != 0:
        raise ValueError(
            f"{path}: unsupported PNG (bitdepth={bitdepth} "
            f"colortype={colortype} interlace={interlace})")
    ch = 3 if colortype == 2 else 4
    raw = zlib.decompress(idat)
    stride = w * ch
    px = bytearray(w * h * ch)
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        ft = raw[p]
        p += 1
        line = bytearray(raw[p:p + stride])
        p += stride
        if ft == 1:
            for i in range(ch, stride):
                line[i] = (line[i] + line[i - ch]) & 0xFF
        elif ft == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif ft == 3:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif ft == 4:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                b = prev[i]
                c = prev[i - ch] if i >= ch else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        elif ft != 0:
            raise ValueError(f"{path}: bad filter {ft} at row {y}")
        px[y * stride:(y + 1) * stride] = line
        prev = line
    return w, h, ch, px


def sample(path, x, y):
    w, h, ch, px = read_png(path)
    rs = gs = bs = n = 0
    for dy in range(-PATCH, PATCH + 1):
        for dx in range(-PATCH, PATCH + 1):
            xx, yy = x + dx, y + dy
            if not (0 <= xx < w and 0 <= yy < h):
                continue
            o = (yy * w + xx) * ch
            rs += px[o]
            gs += px[o + 1]
            bs += px[o + 2]
            n += 1
    return (round(rs / n), round(gs / n), round(bs / n))


def close(a, b):
    return all(abs(x - y) <= TOL for x, y in zip(a, b))


def main():
    if len(sys.argv) != 5:
        print("usage: sample_png.py <comp.png> <nocomp.png> <x> <y>",
              file=sys.stderr)
        return 2
    comp_p, nocomp_p, x, y = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    try:
        comp = sample(comp_p, x, y)
        nocomp = sample(nocomp_p, x, y)
    except (OSError, ValueError, zlib.error) as e:
        print(f"SAMPLE ERROR: {e}", file=sys.stderr)
        return 2
    print(f"SAMPLE ({x},{y}) 9x9 avg: comp={comp} (expect ~{EXP_COMP}) "
          f"nocomp={nocomp} (expect ~{EXP_NOCOMP})")
    ok = True
    if not close(comp, EXP_COMP):
        print(f"SAMPLE FAIL: comp {comp} not within {TOL} of {EXP_COMP}")
        ok = False
    if not close(nocomp, EXP_NOCOMP):
        print(f"SAMPLE FAIL: nocomp {nocomp} not within {TOL} of {EXP_NOCOMP}")
        ok = False
    if not (comp[0] < nocomp[0] - 5 and comp[2] > nocomp[2] + 5):
        print(f"SAMPLE FAIL: no cooling direction "
              f"(R {comp[0]} vs {nocomp[0]}, B {comp[2]} vs {nocomp[2]})")
        ok = False
    print("SAMPLE PASS" if ok else "SAMPLE FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
