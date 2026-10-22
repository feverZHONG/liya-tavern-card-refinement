#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""两张角色卡逐字段比对——V2/V3 双版差异、改卡前后复核。

用法:
    python3 diff_cards.py <卡A.json> <卡B.json> [--full]

输出分类（关键：把换行符噪音和类型漂移从「内容不同」里摘出去）:
    【实质不同】 归一化 CRLF 后仍不同的字段
    【仅换行差异】 内容一字不差，只是 \r\n vs \n —— 长度差全是这个
    【类型漂移】 同名字段类型不同（数字 0.5 vs 字符串 "0.5"）
    【字段缺失】 只有一边有
    顶层键 / extensions 子键差集；末尾单独报含 CRLF 的一侧

--full 额外打印实质不同字段的原文（截断 400 字）。
退出码: 0=比完（有差异也返回 0，这是体检不是断言）。
"""
import json
import sys

MAXSHOW = 400


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def norm(v):
    """递归把 CRLF 归一成 LF——比对前必做，否则满屏假差异。"""
    if isinstance(v, str):
        return v.replace("\r\n", "\n")
    if isinstance(v, dict):
        return {k: norm(x) for k, x in v.items()}
    if isinstance(v, list):
        return [norm(x) for x in v]
    return v


def has_crlf(v):
    if isinstance(v, str):
        return "\r" in v
    if isinstance(v, dict):
        return any(has_crlf(x) for x in v.values())
    if isinstance(v, list):
        return any(has_crlf(x) for x in v)
    return False


def show(v, limit=MAXSHOW):
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    if s is None:
        s = ""
    return s[:limit] + ("…" if len(s) > limit else "")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    full = "--full" in sys.argv
    if len(args) != 2:
        print(__doc__)
        return 2
    a, b = load(args[0]), load(args[1])
    da = a.get("data", {}) if isinstance(a.get("data"), dict) else {}
    db = b.get("data", {}) if isinstance(b.get("data"), dict) else {}

    print(f"A: {args[0]}  spec={a.get('spec')}/{a.get('spec_version')}")
    print(f"B: {args[1]}  spec={b.get('spec')}/{b.get('spec_version')}")
    print()

    real, noise, typed, missing = [], [], [], []
    for k in sorted(set(da) | set(db)):
        if k not in da or k not in db:
            missing.append(k)
            continue
        va, vb = da.get(k), db.get(k)
        if type(va) is not type(vb):
            typed.append(k)
        elif norm(va) == norm(vb):
            if va != vb:
                noise.append(k)
        else:
            real.append(k)

    print(f"【实质不同 {len(real)}】{'、'.join(real) or '（无）'}")
    print(f"【仅换行差异 {len(noise)}】{'、'.join(noise) or '（无）'}")
    print(f"【类型漂移 {len(typed)}】{'、'.join(typed) or '（无）'}")
    print(f"【字段缺失 {len(missing)}】{'、'.join(missing) or '（无）'}")
    for k in typed:
        print(f"    {k}: A={type(da.get(k)).__name__} {show(da.get(k), 60)!r}"
              f"  vs  B={type(db.get(k)).__name__} {show(db.get(k), 60)!r}")
    for k in missing:
        side = "仅 A" if k in da else "仅 B"
        print(f"    {k}: {side}")

    if full:
        for k in real:
            print(f"\n--- {k} ---")
            print(f"[A] {show(da.get(k))}")
            print(f"[B] {show(db.get(k))}")

    print()
    ka, kb = set(a), set(b)
    print(f"【顶层键】A 独有 {sorted(ka - kb)} | B 独有 {sorted(kb - ka)}")
    ea = da.get("extensions") if isinstance(da.get("extensions"), dict) else {}
    eb = db.get("extensions") if isinstance(db.get("extensions"), dict) else {}
    print(f"【extensions 键】A 独有 {sorted(set(ea) - set(eb))} | B 独有 {sorted(set(eb) - set(ea))}")
    for tag, card in (("A", a), ("B", b)):
        if has_crlf(card):
            print(f"⚠️  {tag} 含 CRLF（\\r\\n）——断言/比对前先转 LF")
    return 0


if __name__ == "__main__":
    sys.exit(main())
