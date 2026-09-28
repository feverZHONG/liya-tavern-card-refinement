#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""嵌卡 PNG 复验器 —— 交付前必跑（不要拿 embed 脚本的 ✅ 当证据）。

用法:
    python3 verify_embedded_card.py <卡.png> [<另一张.png> ...]
    python3 verify_embedded_card.py <卡.png> --json <对应卡.json>

三把尺，全过才算数:
  1. PNG 结构：签名 / chunk 字节对齐 / 每块 CRC / IHDR 首 IEND 末
  2. 卡在不在：tEXt chunk keyword=chara 恰一个，base64 解码得合法 JSON
  3. 卡对不对：解出的 JSON 与同名 .json **逐字节一致**（不给 --json 时自动找同目录同名 .json）

第 3 条最要紧：卡改过之后忘了重新 embed，PNG 里躺的还是旧卡，只有逐字节比对抓得到。
退出码 0=全过 / 1=有问题 / 2=用法错。
"""
import base64
import binascii
import json
import os
import struct
import sys

SIG = b"\x89PNG\r\n\x1a\n"


def parse_chunks(path):
    """返回 (chunks, err)。chunks = [(ctype, payload, crc_ok), ...]"""
    b = open(path, "rb").read()
    if b[:8] != SIG:
        return None, "不是 PNG（签名不符）"
    pos, chunks = 8, []
    while pos < len(b):
        if pos + 8 > len(b):
            return None, f"chunk 头越界 @{pos}"
        (ln,) = struct.unpack(">I", b[pos:pos + 4])
        ctype = b[pos + 4:pos + 8]
        if pos + 12 + ln > len(b):
            return None, f"chunk 数据越界 @{pos} ({ctype!r})"
        payload = b[pos + 8:pos + 8 + ln]
        (declared,) = struct.unpack(">I", b[pos + 8 + ln:pos + 12 + ln])
        chunks.append((ctype, payload,
                       binascii.crc32(ctype + payload) & 0xFFFFFFFF == declared))
        pos += 12 + ln
    if pos != len(b):
        return None, "chunk 长度没对齐到文件尾"
    return chunks, None


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if args else 2
    explicit = None
    if "--json" in args:
        i = args.index("--json")
        explicit = args[i + 1]
        del args[i:i + 2]
    bad = 0
    for png in args:
        print(f"── {png} ──")
        chunks, err = parse_chunks(png)
        if err:
            print(f"  ❌ {err}")
            bad += 1
            continue
        types = [c.decode("latin-1") for c, _, _ in chunks]
        crc_bad = [t for t, _, ok in chunks if not ok]
        print(f"  {'✅' if not crc_bad else '❌'} 结构：{len(chunks)} 块、字节对齐；CRC 错 {len(crc_bad)}"
              f"｜IHDR 首 {types[0] == 'IHDR'}｜IEND 末 {types[-1] == 'IEND'}")
        if crc_bad:
            bad += 1
        chara = [pl for c, pl, _ in chunks if c == b"tEXt" and pl.startswith(b"chara\x00")]
        if len(chara) != 1:
            print(f"  ❌ tEXt:chara 应恰 1 个，实为 {len(chara)} 个")
            bad += 1
            continue
        try:
            dec = base64.b64decode(chara[0][6:]).decode("utf-8")
            card = json.loads(dec)
        except Exception as e:
            print(f"  ❌ 解不出卡：{e}")
            bad += 1
            continue
        d = card.get("data", {}) if isinstance(card.get("data"), dict) else {}
        print(f"  ✅ 卡：spec={card.get('spec')} name={d.get('name')} "
              f"版本={d.get('character_version')} world={d.get('extensions', {}).get('world')}")
        jp = explicit or os.path.splitext(png)[0] + ".json"
        if not os.path.isfile(jp):
            print(f"  ⚠ 没有可比对的 .json（{jp}）——只验到「卡在且合法」")
            continue
        orig = open(jp, encoding="utf-8").read()
        same = dec == orig
        print(f"  {'✅' if same else '❌'} 与 {os.path.basename(jp)} 逐字节一致: {same}")
        if not same:
            print(f"     （嵌出 {len(dec)}B vs 卡 {len(orig)}B——卡改过就重新 embed 一次）")
            bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
