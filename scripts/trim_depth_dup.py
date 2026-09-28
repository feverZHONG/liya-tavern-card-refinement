#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""备注收敛 / 描述去元信息 —— 槽位归位之后的第二步（幂等，默认只预览）。

归位那一步是「复制」：PList 内容被复制进 description / personality 各专槽，备注原样留着，
同一份信息就三处并存。本工具做分家：**每条内容只有一个正主**。

做的事（两项都可单用）:
  --drop-genre-line        描述里去掉 `[Genre: …]` 行（＝「嵌入的标签」的第三遍，净重复）
  --keep-plist Personality 备注只留指定类别（PList 相对次序不变；可给多个，逗号分隔）

配套（顺延版号才用，手工也要做）:
  --version 0.5            写 character_version（顶层 + data 同步）
  --notes-append '…'       把本次改动追加进 creator_notes

用法:
    trim_depth_dup.py <卡.json> [卡.json ...]                    # 预览
    trim_depth_dup.py <卡.json> --keep-plist Personality --drop-genre-line --fix
退出码 0=成功 / 1=有卡失败 / 2=参数错误
"""
import json
import os
import re
import sys

ORDER = ("body", "Setting", "Personality")
try:
    import tiktoken
    ENC = tiktoken.get_encoding("cl100k_base")
except Exception:  # 缺库则退化为字符数（只看相对变化）
    ENC = None


def tok(s):
    return len(ENC.encode(s)) if ENC else len(s)


def parse_args(argv):
    opt = {"drop_genre": False, "keep": None, "version": None, "notes": None, "fix": False}
    files, i = [], 0
    while i < len(argv):
        a = argv[i]
        if a == "--fix":
            opt["fix"] = True
        elif a == "--drop-genre-line":
            opt["drop_genre"] = True
        elif a == "--keep-plist":
            i += 1
            opt["keep"] = [c.strip() for c in argv[i].split(",") if c.strip()]
        elif a == "--version":
            i += 1
            opt["version"] = argv[i]
        elif a == "--notes-append":
            i += 1
            opt["notes"] = argv[i]
        elif a in ("-h", "--help"):
            print(__doc__)
            sys.exit(0)
        elif a.startswith("-"):
            print(f"未知参数: {a}")
            sys.exit(2)
        else:
            files.append(a)
        i += 1
    if not files:
        print("用法: trim_depth_dup.py <卡.json> [--keep-plist Personality] [--drop-genre-line] [--version 0.5] [--fix]")
        sys.exit(2)
    return files, opt


def process(path, opt):
    with open(path, encoding="utf-8") as f:
        card = json.load(f)
    data = card["data"]
    changed = []

    desc = data["description"]
    new_desc = desc
    if opt["drop_genre"]:
        kept = [l for l in desc.split("\n") if not l.startswith("[Genre:")]
        if len(kept) != len(desc.split("\n")):
            new_desc = "\n".join(kept)
            changed.append(f"描述去掉 {len(desc.splitlines()) - len(kept)} 行 `[Genre: …]`")

    dp = data.get("extensions", {}).get("depth_prompt", {})
    old_plist = dp.get("prompt", "") if isinstance(dp, dict) else ""
    new_plist = old_plist
    if opt["keep"]:
        bad = [c for c in opt["keep"] if c not in ORDER]
        if bad:
            print(f"  ⚠️ 未知类别 {bad}（本工具只认 {ORDER}）")
            return False
        lines = old_plist.split("\n")
        kept = [l for l in lines if re.match(r"\[.+?'s (\w+)= ", l) and re.match(r"\[.+?'s (\w+)= ", l).group(1) in opt["keep"]]
        if not kept:
            print(f"  ⚠️ 备注里没有 {opt['keep']} 类别，没动")
        else:
            new_plist = "\n".join(kept)
            dropped = [re.match(r"\[.+?'s (\w+)= ", l).group(1) for l in lines if l not in kept]
            if new_plist != old_plist:
                changed.append(f"备注只留 {opt['keep']}（去掉 {dropped}）")

    new_ver = opt["version"] or data["character_version"]
    notes = data.get("creator_notes", "")
    if opt["version"]:
        # creator_notes 里的「精修版 vX.Y」要跟版号一起走，否则列表里显示的是旧版
        bumped = re.sub(r"精修版 v0\.\d", f"精修版 v{new_ver}", notes)
        if bumped != notes:
            notes = bumped
            changed.append(f"creator_notes 版号标记 → v{new_ver}")
    if opt["notes"] and f"本次（v{new_ver}）" not in notes:
        notes = notes.rstrip() + f"  本次（v{new_ver}）：{opt['notes']}"
        changed.append("creator_notes 追加本次改动")
    if opt["version"] and data["character_version"] != opt["version"]:
        changed.append(f"版号 {data['character_version']} → {opt['version']}")

    before = tok(data["name"]) + tok(desc) + tok(data["personality"]) + tok(data["scenario"]) + tok(old_plist)
    after = tok(data["name"]) + tok(new_desc) + tok(data["personality"]) + tok(data["scenario"]) + tok(new_plist)
    print(f"===== {os.path.basename(path)}  v{data['character_version']} → v{new_ver} =====")
    print(f"  描述 {tok(desc)} → {tok(new_desc)} ｜ 备注 {tok(old_plist)} → {tok(new_plist)} ｜ 恒定 {before} → {after}（Δ {after - before}）")
    if not changed:
        print("  无改动（幂等）")
        return False
    for c in changed:
        print(f"  · {c}")
    if not opt["fix"]:
        print("  （预览——加 --fix 才写回）")
        return True

    data["description"] = new_desc
    if isinstance(dp, dict):
        dp["prompt"] = new_plist
    data["character_version"] = new_ver
    data["creator_notes"] = notes
    card["description"] = new_desc          # 顶层同步（V2 兼容字段）
    card["character_version"] = new_ver
    with open(path, "w", encoding="utf-8") as f:
        json.dump(card, f, ensure_ascii=False, indent=2)
    print("  ✅ 已写回（顶层/数据已同步）")
    return True


def main():
    files, opt = parse_args(sys.argv[1:])
    touched = 0
    for p in files:
        touched += 1 if process(p, opt) else 0
    print(f"\n共 {len(files)} 张，{'将改' if not opt['fix'] else '已改'} {touched} 张。"
          if touched else f"\n共 {len(files)} 张，全部无改动。")
    if opt["fix"] and touched:
        print("下一步：tavern verify <卡> --fix（含 PNG 重嵌）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
