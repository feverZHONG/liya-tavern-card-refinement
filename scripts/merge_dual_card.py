#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V2 / V3 双版角色卡合并 → 单张 V2 卡。

场景：同一角色存了两个 spec 版本（如 <角色>.json=V2 与 <角色>_需补充.json=V3），
     内容高度重合但各有缺项。本工具按字段取并集合成一张，输出卡库标准的 V2 结构。

用法:
    merge_dual_card.py <卡A.json> <卡B.json> --out <输出.json> --version 0.3 [--notes 文案] [--prefer a|b]

规则:
    - 双方逐字段取并集：一方空（""/[]/{}/None）取另一方；都非空且不同 → 记冲突，按 --prefer（默认 b）取
    - 全篇 CRLF/CR → LF（v0.2+ 规范要求单换行）
    - talkativeness 字符串数字 → 数字（酒馆里类型要一致）
    - 输出按 V2 白名单重建 data / 顶层 / extensions，丢弃 V3 导出器塞的字段（fav/world/create_date/avatar…）

退出码: 0=合并完成（有冲突也返回 0，冲突在报告里列出）；1=失败。
"""
import argparse
import json
import os
import sys

V2_DATA_KEYS = ["name", "description", "personality", "scenario", "first_mes", "mes_example",
                "creator_notes", "system_prompt", "post_history_instructions",
                "alternate_greetings", "tags", "creator", "character_version",
                "extensions", "character_book"]
V2_TOP_KEYS = ["name", "description", "personality", "scenario", "first_mes", "mes_example",
               "system_prompt", "post_history_instructions"]
V2_EXT_KEYS = ["talkativeness", "depth_prompt", "twinvision"]
EMPTY = (None, "", [], {})


def clean(v):
    """CRLF/CR → LF，递归。"""
    if isinstance(v, str):
        return v.replace("\r\n", "\n").replace("\r", "\n")
    if isinstance(v, list):
        return [clean(x) for x in v]
    if isinstance(v, dict):
        return {k: clean(x) for k, x in v.items()}
    return v


def load(path):
    with open(path, encoding="utf-8") as f:
        return clean(json.load(f))


def merge_field(va, vb, key, prefer_b, conflicts):
    if va == vb:
        return va, "同"
    if va in EMPTY:
        return vb, "取B"
    if vb in EMPTY:
        return va, "取A"
    conflicts.append(key)
    return (vb if prefer_b else va), ("取B*" if prefer_b else "取A*")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("card_a")
    ap.add_argument("card_b")
    ap.add_argument("--out", required=True)
    ap.add_argument("--version", required=True)
    ap.add_argument("--notes")
    ap.add_argument("--prefer", choices=["a", "b"], default="b")
    args = ap.parse_args()

    A, B = load(args.card_a), load(args.card_b)
    da, db = A.get("data", {}), B.get("data", {})
    prefer_b = args.prefer == "b"
    conflicts, report = [], []

    data = {}
    for k in V2_DATA_KEYS:
        if k == "character_version":
            data[k] = args.version
            report.append((k, "→ " + args.version))
            continue
        if k not in da and k not in db:
            continue
        val, src = merge_field(da.get(k), db.get(k), k, prefer_b, conflicts)
        if k == "extensions":
            ext = {}
            if not isinstance(val, dict):
                val = {}
            for ek in V2_EXT_KEYS:
                if ek not in val:
                    continue
                ev, esrc = merge_field(da.get(k, {}).get(ek), db.get(k, {}).get(ek), ek, prefer_b, conflicts)
                if ek == "talkativeness" and isinstance(ev, str):
                    try:
                        ev = float(ev)
                        esrc += "(类型归位)"
                    except ValueError:
                        pass
                ext[ek] = ev
                report.append((f"extensions.{ek}", esrc))
            data[k] = ext
            continue
        data[k] = val
        report.append((k, src))

    if args.notes:
        data["creator_notes"] = args.notes
        report.append(("creator_notes", "→ 指定文案"))

    card = {"spec": "chara_card_v2", "spec_version": "2.0"}
    for k in V2_TOP_KEYS:
        if k in data:
            card[k] = data[k]
    card["data"] = data

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(card, f, ensure_ascii=False, indent=2)

    print(f"A = {os.path.basename(args.card_a)}  (spec={A.get('spec')})")
    print(f"B = {os.path.basename(args.card_b)}  (spec={B.get('spec')})")
    print(f"输出 → {args.out}  (V2 / v{args.version})\n")
    for k, src in report:
        print(f"  {k:<28} {src}")
    if conflicts:
        print(f"\n⚠️  {len(conflicts)} 处双方都有值且不同，按 --prefer={args.prefer} 取值：")
        for k in conflicts:
            print(f"    - {k}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
