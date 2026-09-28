#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""精修版角色卡质量复核——补 validate_tavern_card.py --deep 的盲区。

用法:
    python3 check_refined_card.py <卡.json> [卡.json ...]
退出码: 0=全过, 1=有问题。逐项打印 PASS/FAIL。

覆盖 --deep 查不到的维度（对应 SKILL.md 自检断言的可执行版）:
1. 顶层/数据双份同步（含 system_prompt / post_history_instructions——精修版必须补顶层两份）
2. <START> 块格式: user 行「「」」双括号残留、user/char 同句复读
3. PList 类别顺序 body → Setting → Personality + 施工注释残留
4. system_prompt / post_history_instructions 以 {{original}}\n 开头、无 ✅❌ 对照表残留
5. first_mes 单换行（无空行）、无 *你...* 替用户行动
"""
import json
import re
import sys


def check_card(path: str) -> list:
    problems = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            card = json.load(f)
    except Exception as e:
        return [f"读取失败: {e}"]

    if card.get("spec") not in ("chara_card_v2", "chara_card_v3"):
        return [f"不是 V2/V3 卡: spec={card.get('spec')!r}"]
    data = card.get("data", {})
    if not isinstance(data, dict):
        return ["data 缺失"]

    # 1. 顶层/数据双份同步（V1 字段 + system_prompt/post_history_instructions）
    for f in ["name", "description", "personality", "scenario", "first_mes", "mes_example",
              "system_prompt", "post_history_instructions"]:
        if card.get(f) != data.get(f):
            problems.append(f"顶层/数据不同步: {f}")
    for f in ["system_prompt", "post_history_instructions"]:
        if f not in card:
            problems.append(f"顶层缺 {f}——精修版需 data+顶层双份")

    # 2. <START> 块（2026-09-26 起示例可归位到 mes_example——两处都扫）
    for src in ("description", "mes_example"):
        text = data.get(src, "")
        if not (isinstance(text, str) and "<START>" in text):
            continue
        for i, b in enumerate(text.split("<START>")[1:], 1):
            m = re.search(r"\{\{user\}\}:\s*(.+?)\n\{\{char\}\}:\s*(.+)", b.strip(), re.S)
            if not m:
                problems.append(f"{src} 第 {i} 个 <START> 块格式异常")
                continue
            u, ch = m.group(1).strip(), m.group(2).strip()
            if "「「" in u or "」」" in u:
                problems.append(f"{src} 第 {i} 个 <START> user 行双括号残留: {u[:30]!r}")
            if u == ch:
                problems.append(f"{src} 第 {i} 个 <START> user/char 同句复读")

    # 3. PList 类别相对次序 body → Setting → Personality（可缺类：备注收敛后只剩 Personality 是合法形状）
    dp = data.get("extensions", {}).get("depth_prompt", {})
    plist = dp.get("prompt", "") if isinstance(dp, dict) else ""
    if isinstance(plist, str) and plist:
        order = []
        for line in plist.splitlines():
            mm = re.match(r"\[.+?'s (\w+)= ", line)
            if mm:
                order.append(mm.group(1))
        expect = [c for c in ("body", "Setting", "Personality") if c in order]
        if order != expect:
            problems.append(f"PList 类别应保持 body→Setting→Personality 的相对次序（允许缺类），实际: {order}")
        for bad in ("基础版", "需按角色精修"):
            if bad in plist:
                problems.append(f"PList 施工注释残留: {bad}")

    # 4. system_prompt / post_history_instructions 质量
    for f in ["system_prompt", "post_history_instructions"]:
        v = data.get(f, "")
        if not v.startswith("{{original}}\n"):
            problems.append(f"{f} 应以 {{{{original}}}}\\n 开头")
        if "✅" in v or "❌" in v:
            problems.append(f"{f} 还有 ✅❌ 对照表残留——应改直接规则")

    # 5. first_mes 质量
    fm = data.get("first_mes", "")
    if "\n\n" in fm:
        problems.append("first_mes 含双换行（\\n\\n）——改单 \\n")
    if re.search(r"\*你[^*]{0,20}\*", fm):
        problems.append("first_mes 出现 *你...* 动作描写——替用户行动")

    # 6. character_version + creator_notes 模板（2026-09-04 并入 batch-refine 版检查；09-16 放开 v0.3/v0.4）
    ver = data.get("character_version")
    if not (isinstance(ver, str) and re.fullmatch(r"0\.[2-9]", ver)):
        problems.append(f"character_version={ver!r}（应为 0.2-0.9——每有一次对外改动就顺延，别堆在同一版号）")
    notes = data.get("creator_notes", "")
    if not re.search(r"精修版 v0\.[2-9]", notes):
        problems.append("creator_notes 缺 '精修版 v0.x' 标记")

    return problems


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: check_refined_card.py <卡.json> [卡.json ...]")
        return 2
    if sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0
    rc = 0
    for path in sys.argv[1:]:
        problems = check_card(path)
        print(f"===== {path} =====")
        if problems:
            rc = 1
            for p in problems:
                print(f"  FAIL {p}")
        else:
            print("  PASS 全部通过")
    return rc


if __name__ == "__main__":
    sys.exit(main())
