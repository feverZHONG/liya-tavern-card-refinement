#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""槽位归位——把卡的内容按酒馆官方字段定义各就各位。

问题（2026-09-26 阁下实操指出）：内容全挤在 description（charDescription）一个槽，
charPersonality / scenario / mes_example 三个槽空着。

依据：酒馆编辑界面各格官方说明（阁下提供两份《酒馆笔记》）
    角色描述     = 角色的身体和精神特征
    角色设定摘要 = 角色设定的简要描述
    情景         = 交互的情况和背景
    对话示例     = 写作风格示例，每例 <START> 起行
    角色备注     = 文本将作为指定身份被插入到聊天中指定的深度

ST 注入顺序（Chat Completion，源码 public/scripts/openai.js 1201-1209）：
    worldInfoBefore → main → worldInfoAfter
    → charDescription → charPersonality → scenario → … → dialogueExamples

归位规则（只搬运，不新写内容）：
    角色描述     ← PList 的 Personality 行 ＋ body 行 ＋ [Genre/Tags] 锚
    角色设定摘要 ← PList 的 Setting 行（去 PList 语法壳，仅换分隔符）
    情景         ← 描述框顶部的 [Scenario: …] 值
    对话示例     ← 描述框里的 <START> 示例块（ST 解析成 user/assistant 真对话轮次）
    角色备注     ← **保持原样**（PList 留在深度注入位；2026-09-26 阁下定：备注不空）

用法:
    python3 slot_realign.py <卡.json> [...]                    # 预览（默认只读）
    python3 slot_realign.py <卡.json> --fix [--version 0.4]   # 写回
退出码: 0=无需改动／已归位, 1=有卡需要归位（预览模式）
"""
import argparse
import json
import re
import sys

META_RE = re.compile(r"^\[(?P<meta>[^\]]*)\]\s*", re.S)
KNOWN_KEYS = ("Genre", "Tags", "Scenario")
SYNC_FIELDS = ("description", "personality", "scenario", "mes_example")
PLIST_KEYS = ("body", "Setting", "Personality")


def split_meta(meta: str) -> dict:
    """把 'Genre: x; Tags: y; Scenario: z' 拆成 {key: value}（值里含冒号也不怕）。"""
    marks = []
    for k in KNOWN_KEYS:
        m = re.search(rf"(?:^|;\s*){k}\s*:\s*", meta)
        if m:
            marks.append((k, m.start(), m.end()))
    marks.sort(key=lambda x: x[1])
    out = {}
    for i, (k, _s, e) in enumerate(marks):
        end = marks[i + 1][1] if i + 1 < len(marks) else len(meta)
        out[k] = meta[e:end].strip().rstrip(";").strip()
    return out


def plist_value(plist: str, key: str) -> str:
    m = re.search(rf"\[[^\]]*?'s {key}=\s*(?P<v>[^\]]+)\]", plist)
    return m.group("v").strip() if m else ""


def is_realigned(data: dict) -> bool:
    """已归位：描述里没有 <START> ＋ 示例在 mes_example ＋ 设定摘要已填。"""
    desc = data.get("description") or ""
    return (("<START>" not in desc)
            and bool((data.get("mes_example") or "").strip())
            and bool((data.get("personality") or "").strip()))


def realign(card: dict, version: str | None = None, notes: str | None = None) -> tuple[list, dict]:
    """返回 (changes, card)；changes 为空表示无需归位。"""
    data = card.get("data", {})
    changes = []
    if is_realigned(data):
        return changes, card

    name = data.get("name") or ""
    desc = data.get("description") or ""
    m = META_RE.match(desc)
    if m:
        parts, rest = split_meta(m.group("meta")), desc[m.end():]
    else:
        parts, rest = {}, desc

    si = rest.find("<START>")
    head = (rest[:si] if si >= 0 else rest).strip()
    examples = rest[si:].strip() if si >= 0 else ""

    dp = data.get("extensions", {}).get("depth_prompt", {})
    plist = (dp.get("prompt", "") if isinstance(dp, dict) else "") or ""
    body_v = plist_value(plist, "body")
    setting_v = plist_value(plist, "Setting")
    pers_v = plist_value(plist, "Personality")

    # A) 角色描述 = [Personality] → [body] → [Genre/Tags]（官方示范同序）
    blocks = []
    if pers_v:
        blocks.append(f"[{name}'s Personality= {pers_v}]")
    if body_v:
        blocks.append(f"[{name}'s body= {body_v}]")
    anchor = "; ".join(f"{k}: {parts[k]}" for k in ("Genre", "Tags") if parts.get(k))
    if anchor:
        blocks.append(f"[{anchor}]")
    if head:
        blocks.append(head)
    new_desc = "\n".join(blocks)
    if new_desc != desc:
        data["description"] = new_desc
        changes.append(f"角色描述重排：{len(desc)} → {len(new_desc)} 字符"
                       f"（{'＋'.join(['Personality' if pers_v else '', 'body' if body_v else '', 'Genre/Tags 锚' if anchor else '']).strip('＋')}）")

    # B) 对话示例
    if examples:
        if (data.get("mes_example") or "").strip():
            changes.append("⚠️ mes_example 已有内容，示例块未搬运")
        else:
            data["mes_example"] = examples
            changes.append(f"<START> 示例块 → 对话示例（{len(examples)} 字符，"
                           f"{examples.count('<START>')} 组，ST 解析成真对话轮次）")

    # C) 情景
    sc = parts.get("Scenario", "")
    if sc:
        if (data.get("scenario") or "").strip():
            changes.append("⚠️ scenario 槽已有内容，未覆盖")
        else:
            data["scenario"] = sc
            changes.append(f"[Scenario: …] → 情景（{len(sc)} 字符）")

    # D) 角色设定摘要
    if setting_v:
        if (data.get("personality") or "").strip():
            changes.append("⚠️ personality 槽已有内容，未覆盖")
        else:
            items = [t.strip().strip('"').strip("“”") for t in setting_v.split(",") if t.strip()]
            data["personality"] = "／".join(items)
            changes.append(f"PList Setting 行 → 角色设定摘要（{len(items)} 条，仅换分隔符）")

    # E) 角色备注保持原样（PList 留在深度注入位）——2026-09-26 阁下定：备注不空

    # F) 顶层双份同步
    for f in SYNC_FIELDS:
        if card.get(f) != data.get(f):
            card[f] = data.get(f)
            changes.append(f"顶层 {f} 同步")

    if version:
        old = data.get("character_version")
        data["character_version"] = version
        changes.append(f"character_version {old} → {version}")
    if notes:
        cur = data.get("creator_notes", "") or ""
        data["creator_notes"] = (cur.rstrip() + " " + notes).strip() if cur else notes
        changes.append("creator_notes 追加说明")

    return changes, card


def main() -> int:
    ap = argparse.ArgumentParser(description="槽位归位：按酒馆官方字段定义重排五格")
    ap.add_argument("cards", nargs="+", help="卡 JSON 路径")
    ap.add_argument("--fix", action="store_true", help="写回文件（默认只预览）")
    ap.add_argument("--version", help="同时顺延 character_version，如 0.4")
    ap.add_argument("--notes", help="追加到 creator_notes 的说明")
    args = ap.parse_args()

    rc = 0
    for path in args.cards:
        with open(path, "r", encoding="utf-8") as f:
            card = json.load(f)
        changes, new_card = realign(card, args.version, args.notes)
        print(f"===== {path} =====")
        if not changes:
            print("  已是归位形态（无改动）")
            continue
        rc = 1
        for c in changes:
            print(f"  · {c}")
        if args.fix:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(new_card, f, ensure_ascii=False, indent=2)
                f.write("\n")
            print("  ✅ 已写回")
    return rc


if __name__ == "__main__":
    sys.exit(main())
