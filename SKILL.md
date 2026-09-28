---
name: tavern-card-refinement
tier: T2  # T分级: T2=直接做 / T1=先请示 / T0=一律拒
description: SillyTavern 角色卡全流程与台账——7 字段精修、素材层、可用性验收（演卡+样本实测+双卡同场）、PNG 嵌卡与发布命名。触发：精修/批量改卡、验收卡、发卡到群、双卡同场。
---

# 酒馆角色卡 · 精修（单卡/批量）

> 2026-09-04 合并 tavern-card-batch-refine（内容 90% 重叠的执行层版本）——本技能=精修唯一入口，含单卡与批量流程。
> **互补 skill：** 格式规格/工具链/写卡方法论在 `sillytavern-cards`（已对外：<https://github.com/feverZHONG/liya-sillytavern-cards>）；素材层（角色资料与台词库）在素材仓。
> **本仓只装方法、工具与通用口径**——具体角色的台账、台词出处索引、精修进度都是私档（`workspace/records/tavern-card-refinement/`），随卡库走、不进本仓。

## 触发

精修角色卡 / 批量化改卡 / 「按范例完成精修」 / 查哪张卡还没精修 / 把基础版卡升到 v0.2

## 前置：确认范例与素材

1. **先定一张范例卡**——本机取卡库台账里标着 v0.2 成品的那张（`workspace/tavern-cards/INDEX.md`）。要照它对齐的是三处：
   - 顶层要带 system_prompt / post_history_instructions 双份（老格式卡顶层只有 9 键，v0.2 是 11 键）
   - **PList 类别顺序 body → Setting → Personality**（Trappu 口径「最重要的放最后」）——**别无脑照范例卡抄顺序**：全库归一那次就是拿一张自己写反的卡当范例，一下带偏 9 张
   - description 格式：**老形状**＝场景块 + `\n\n<START>…`（块间单 `\n`）；**新形状（归位后）**＝`[Personality]` ＋ `[body]` ＋ `[Genre/Tags]` 锚，示例搬进 `mes_example`、场景句搬进 `scenario`、`Setting` 搬进 `personality`——见「槽位归位」节
2. **素材路径**（本机约定）：`<素材仓>/personas/{角色名}/`（IDENTITY / persona-soul / AGENTS.md）+ `sources/{NN-角色名}/03-角色对话.txt`（台词库）+ `curated/01-characters/*.md`（外观/原句）

## 素材层（从零建四件套）

见 `references/material-prep.md` —— 四件套格式契约、料源分层（一手原话 → 正文引语 → 声线锚点 → 官方设定）、声线锚点档怎么提、没有台词库时怎么派子代理、卡图/立绘取法。

## 7 字段修改清单（data + 顶层同名双份同步）

1. **description** — 老形状：保留现有场景块原样，`\n\n` 后追加 3 组手写 `<START>`（覆盖三种性格面；{{user}} 短问 + {{char}} 带 `*动作*` 长回复；user/char 台词必须不同，复读=示例污染）。**改完走「槽位归位」，把示例／场景／性格搬去各自的槽**
2. **first_mes** — 场景化开场 `*动作* + 登场 + 台词库原句 + 互动钩子`；全程单换行（禁 `\n\n`）；不替用户行动（禁 `*你...*`）
3. **extensions.depth_prompt.prompt** — Personality 解读词 → 行为锚点/具体设定（「口头禅「…」」「自称…」「囤货癖」这类短标签 ≤16 字，标签风格照范例卡）；body 原样保留；Setting 去掉台词/对白，只留设定+关系
4. **system_prompt** — 删 ✅❌ 对照表 → `{{original}}\n你是{角色名}——` + 1-3 句硬规则（自称/口癖/句式/禁止事项并入）
5. **post_history_instructions** — `{{original}}\n` + 对话节奏（被夸/被反驳/被问往事/称呼/边界）
6. **character_version** → 首发精修 `0.2`；**对外发过之后再有改动就顺延**（`0.3` → `0.4`…），别把改动堆在同一版号上。（2026-09-26 阁下定：「0.2 有过改动的话就顺延到 0.3，不要堆」——发出去的版本得能区分，否则群里两个同名 0.2 谁也不知道谁。）白名单已相应放开到 `0.2-0.9`（`check_refined_card.py`）；每次顺延把改动写进 `creator_notes`，那才是审计线索。
7. **creator_notes** — 模板（`{角色名}` 用短名=文件名去 `.json`，**不是** `data.name` 全名——写「<短名>精修版 v0.2」而不是「<全名>精修版 v0.2」）：`{角色名}精修版 v{与 character_version 一致}——first_mes 场景化（台词库原句）；PList 解读词换行为锚点；Setting 去台词；system_prompt 去对照表改直接规则；补手写 <START> 轮次。08-26 清复读示例/施工注释。`

基础版卡顶层只有 data 层有 system_prompt/post_history_instructions——精修时补顶层双份（范例卡是顶层+data 双份）。

## 台词库空占位兜底

`sources/*/03-角色对话.txt` 里有的角色是空占位（只有标题「1、」或 0 字节）——**不是素材缺失，别卡住等台词库**。原句兜底链：**角色设定档的示例表 ✅ 列 → 设定文档引文 → persona-soul 原句 → curated 原句 → 生日故事等其余 sources**。台词主体用原句，动作描写/衔接词可轻量编（范例卡同）。

精修前先确认台词库非空；空库时照兜底链凑够 first_mes ＋ 3 组 `<START>` 且互不重复，`creator_notes` 仍按模板写、例外在汇报里说明。本机各角色的空库情况与实战分配法 → 私档 `workspace/records/tavern-card-refinement/空库分配法.md`。

## 槽位归位

见 `references/slot-mechanics.md` —— 各格按酒馆官方字段定义各就各位（**机制 ＋ 操作**一档全包：注入顺序/预算门 + 逐格怎么搬）。

## 批量改动

见 `references/batch-cli.md` —— 先用 `tavern` CLI，别手改 JSON。

## 交付前的可用性验收（不装酒馆也能量出来）

见 `references/usability-acceptance.md` —— 自己演卡 ＋ 隔离样本实测 ＋ 双卡同场。

## 脚本模式（自定义内容改动才写脚本）

1. 精修脚本：`json.load` 读卡 → 改 data 字段 + 顶层同名字段同步（description/first_mes/system_prompt/post_history_instructions）→ `json.dump(ensure_ascii=False, indent=2)` 写回。**同步不是可选项**：只改 `data` 那份、顶层留着旧的，`tavern verify` 直接判 `FAIL 顶层/数据不同步: <字段>`——实测栽过；改完两个 prompt 立刻回写顶层再 verify。
2. 断言 6 类（`scripts/check_refined_card.py <卡1>.json [卡2.json ...]`，接受多文件）：① first_mes 以 `*` 开头/无空行/无 `*你…*`/非模板；② 恰 3 组 `<START>`、场景块未改、user/char 不同句（**`description` 与 `mes_example` 两处都扫**——归位后示例在 mes_example）；③ PList 类别**相对次序** body→Setting→Personality（**允许缺类**——备注收敛后只剩 `Personality` 是合法形状，顺序对但缺类不该判 FAIL）、无施工注释；④ Setting 无台词；⑤ Personality 标签 ≤16 字；⑥ 两个 prompt 以 `{{original}}\n` 开头、无 ✅❌——另含版本（白名单 `0.2-0.9`）+ creator_notes「精修版 v0.x」标记检查
3. 跑 `sillytavern-cards/scripts/validate_tavern_card.py <卡>.json --deep` → ✅ V2 + 无 ⚠️ warning，exit=0
4. git diff 确认改动真实落地（脚本打印 ✅ 不等于文件真改了）

## 批次台账

**本机卡库的进度**（哪些精修过、版本、token 实测数）在私档：`workspace/records/tavern-card-refinement/台账.md`，实时状态看卡库 `workspace/tavern-cards/INDEX.md`。

## 踩坑

见 `references/pitfalls.md`（精修操作坑）；机制层的坑见 `references/refinement-notes.md`。

## 引用

| 要查什么 | 打开 |
|:---------|:-----|
| CLI 收口（台账/批量/归一化/对齐 v0.2） | `bin/tavern`（`tavern --help`）|
| 卡库台账（本机卡库状态） | `workspace/tavern-cards/INDEX.md` |
| 精修质量复核脚本（6 类断言+版本/creator_notes 检查） | `scripts/check_refined_card.py` |
| **槽位归位工具**（示例→mes_example／场景→scenario／性格→personality，默认预览、`--fix` 写回） | `scripts/slot_realign.py` |
| **备注收敛工具**（归位第二步：描述去 `[Genre:]` 行、备注只留指定类别；幂等可重放） | `scripts/trim_depth_dup.py` |
| **槽位机制**（注入顺序／mes_example 解析成对话轮次／预算门／恒定 vs 非永久——改槽位前必读） | `references/slot-mechanics.md` |
| 两卡逐字段比对（V2/V3 双版、改卡前后；CRLF 与类型漂移分列） | `scripts/diff_cards.py` |
| 嵌卡 PNG 复验（结构 · CRC · chara chunk 恰一个 · 与同名卡逐字节比对） | `scripts/verify_embedded_card.py` |
| 台词原句出处速查（**私档，不在本仓**） | `workspace/records/tavern-card-refinement/台词原句出处速查.md` |
| 机制吃透笔记（精修踩坑：mes_example 复读/双换行/括号/顺序，附实测案例） | `references/refinement-notes.md` |
| **世界书机制主档**（调用链五层/判定链/匹配/扫描源/位置/预算/字段——写调共用书、动卡内书条目前必读） | `sillytavern-worldbook/references/12-worldbook-mechanics.md` |
| **机制附档**（递归/包含组·outlet·向量化/角色过滤器/扫描状态机·时间效果/版本复核） | `sillytavern-worldbook/references/12b-mechanics-advanced.md` |
| **条目设计规范**（靠什么进·放哪·要不要恒在场／拆分与减法／关系层 A 卡内书·B 独立关系书架构） | `sillytavern-worldbook/references/13-entry-design.md` |
| V2 格式规格/工具链/完整写卡方法论/validate 脚本 | `sillytavern-cards` skill（公开仓库） |
| 素材挖掘（一个角色的料源清单 → 进卡位置） | 素材仓的 `tavern-card-material-mining` 档 |

## 生成初稿 / 发布

```bash
# 默认值已写在 ~/.config/tavern-cards.json（personas / curated / out_dir / genre / tags / creator）
python3 skills/sillytavern-cards/scripts/make_tavern_card.py <角色名> --out <卡库>/<角色名>.json
# 显式指定也一样（--src 指角色目录，或父目录）
python3 skills/sillytavern-cards/scripts/make_tavern_card.py <角色名> --src <素材仓>/personas
```

初稿出来走上面 7 字段清单精修 → `check_refined_card.py` → `validate_tavern_card.py --deep`。
发布：PNG/JSON 发群文件（本机走 `qq-group-intel`），登记卡库台账 `workspace/tavern-cards/INDEX.md`。

**发布命名**：文件名要能一眼分辨**角色名 + 版本 + 日期**（例：`<角色名>_v0.2_26.09.26.png`）。
- **形式不求统一**（2026-09-26 阁下：「正常发就行，用不着跟我当初做的一样」）——分隔符用下划线还是空格都行，**别为此重发、撤回或纠结**；能分辨就是达标。
- **本地卡库保持简洁名**（`<角色名>.json` / `<角色名>.png`），**发群时才改名**（`qqfile <群> <文件> --name '…'`）——排名、批量工具、INDEX 都按简洁名对齐，别为此重命名本地文件。

## 拆分记录

- **2026-09-28 拆薄**：SKILL.md 296 行 →（11.3KB）。素材层 → `references/material-prep.md`；槽位归位 → 并入既有 `references/slot-mechanics.md`（机制与操作合档）；批量改动 → `references/batch-cli.md`；可用性验收 → `references/usability-acceptance.md`；踩坑 → `references/pitfalls.md`。**搬运逐字、一条未删**。「槽位归位」「交付前的可用性验收」两个节名被 `sillytavern-cards` 按名引用，档内节名原样保留并已同步外部指向。
