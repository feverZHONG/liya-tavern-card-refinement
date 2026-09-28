# 酒馆角色卡 · 精修（单卡 / 批量）

> 卡做完初稿之后的**下半程**：7 字段精修 → 槽位归位 → 6 类断言校验 → 可用性验收 → 嵌 PNG 发布。
> 与 [liya-sillytavern-cards](https://github.com/feverZHONG/liya-sillytavern-cards) 配套：那边管**格式规格与写卡方法**，这边管**精修配方与验收工具**。

## 这是什么

初稿卡 ≠ 可发的卡。中间这段决定了三件事：**模型照不照角色设定说话**、**每个字段的预算花得值不值**、**改完的卡是不是真的进到了 PNG 里**。

本仓装的是这段工序：

1. **7 字段精修清单** —— `description` / `first_mes` / `depth_prompt.prompt` / `system_prompt` / `post_history_instructions` / `character_version` / `creator_notes`，逐字段写明改成什么样、为什么。核心一条：**PList 放状态与偏好，行为指令放卡面**——偏好不等于行为，模型不会自动把它翻成一个动作。
2. **槽位归位** —— 按酒馆官方字段定义把内容各就各位（示例→`mes_example`、场景句→`scenario`、性格→`personality`），含注入顺序 / 预算门机制；归位之后再做**备注收敛**（每条内容只有一个正主）。
3. **6 类断言** —— 顶层与 data 双份同步、`<START>` 块格式、PList 类别相对次序、两个 prompt 以 `{{original}}\n` 开头、Setting 无台词、标签长度；附版本白名单与 `creator_notes` 标记检查。
4. **可用性验收（不装酒馆也能量）** —— 自己按卡演 3-4 轮最难的输入，再派 1-2 个隔离样本跑固定话术（**必须含多轮追问**）；**两个样本独立指向同一处才是真问题**。
5. **嵌 PNG 与发布命名** —— 嵌卡不是「脚本报 ✅ 就算」，要 PNG 结构 + chara chunk 恰一个 + **与同名 JSON 逐字节一致**三把尺全过。
6. **批量改动与双版合并** —— 同一角色留着 V2/V3 两张壳时怎么并成一张、批量归一化前怎么先出样板。
7. **素材层** —— 没有现成三件套时从零建（料源分层、声线锚点档、台词库是空占位时怎么兜底）。

一段可直接用的流程：

```bash
# ① 精修：改 7 个字段 → 同步顶层双份 → ② 归位
python3 scripts/slot_realign.py  <卡>.json          # 默认只预览
python3 scripts/slot_realign.py  <卡>.json --fix --version 0.4
python3 scripts/trim_depth_dup.py <卡>.json --drop-genre-line --keep-plist Personality --fix
# ③ 复核 + ④ 官方 validator 深度检查（在 liya-sillytavern-cards 里）
python3 scripts/check_refined_card.py <卡>.json
python3 ../liya-sillytavern-cards/scripts/validate_tavern_card.py <卡>.json --deep
# ⑤ git diff 确认改动真的落地（脚本打印 ✅ 不等于文件真改了）
```

## 工具（6 个，纯标准库，不依赖酒馆）

| 脚本 | 干什么 | 用法 |
|:---|:---|:---|
| `check_refined_card.py` | 精修质量 6 类断言（补 `--deep` 的盲区） | `python3 scripts/check_refined_card.py <卡>.json [<卡2>.json …]` |
| `slot_realign.py` | 槽位归位：按官方字段定义重排五格（默认只预览） | `python3 scripts/slot_realign.py <卡>.json [--fix] [--version 0.4]` |
| `trim_depth_dup.py` | 备注收敛 / 描述去元信息（幂等，默认只预览） | `python3 scripts/trim_depth_dup.py <卡>.json --keep-plist Personality [--fix]` |
| `diff_cards.py` | 两卡逐字段比对，把换行噪音与类型漂移从「内容不同」里摘出去 | `python3 scripts/diff_cards.py <卡A>.json <卡B>.json` |
| `merge_dual_card.py` | 同一角色的 V2/V3 双版并成一张 | `python3 scripts/merge_dual_card.py A.json B.json --out 卡.json --version 0.3` |
| `verify_embedded_card.py` | 嵌卡 PNG 复验：结构 / CRC / chara chunk / 与 JSON 逐字节一致 | `python3 scripts/verify_embedded_card.py 卡.png --json 卡.json` |

退出码统一：`0` 全过、`1` 有问题（逐项打印 PASS/FAIL）。

## 目录

| 路径 | 内容 |
|:---|:---|
| `SKILL.md` | 入口：触发、前置、7 字段清单、脚本模式、发布口径、引用表 |
| `references/material-prep.md` | 素材层：四件套格式契约与料源分层（从零建） |
| `references/slot-mechanics.md` | 槽位机制：注入顺序 / 预算门 / 恒定 vs 非永久 + 槽位归位操作 |
| `references/usability-acceptance.md` | 交付前的可用性验收：自演 + 隔离样本 + 双卡同场 |
| `references/batch-cli.md` | 批量改动：先 CLI 别手改 JSON；多库切换与配置继承的坑 |
| `references/refinement-notes.md` | 机制吃透笔记（实测案例）：mes_example 复读 / 双换行 / 括号 / PList 顺序 / token 口径 |
| `references/pitfalls.md` | 精修操作坑：改已交付卡的门槛、卡内书条目、口径核对 |
| `scripts/*.py` | 上面那 6 个工具 |

**本仓只装方法、工具与通用口径**——具体角色的卡库台账、台词出处索引、精修进度都是私人记录，随卡库走、不在本仓。

## 姊妹仓库

- [liya-sillytavern-cards](https://github.com/feverZHONG/liya-sillytavern-cards) —— 写卡本体：V2/V3 格式规格、PList + Ali:Chat 写法、三个 Python 工具
- [liya-sillytavern-worldbook](https://github.com/feverZHONG/liya-sillytavern-worldbook) —— 酒馆世界书（Lorebook）：触发链源码实证 + 触发体检 / 模拟 / 生成工具
- [liya-persona-authoring](https://github.com/feverZHONG/liya-persona-authoring) —— 给 AI agent 写它**自己**的身份文件（跟写卡规则相反，别混用）
- [liya-delegation-and-verification](https://github.com/feverZHONG/liya-delegation-and-verification) —— 委派与验收：把「自报」验成事实（可用性验收的隔离样本法同源）
- [liya-subtraction-skill](https://github.com/feverZHONG/liya-subtraction-skill) —— 技能库做减法的方法论（本仓的拆薄记录就出自它）
- [liya-vision-recognition-traps](https://github.com/feverZHONG/liya-vision-recognition-traps) —— 视觉模型识图陷阱：22 条实测陷阱 + 真 OCR 通道 + 两图差分
- [liya-chat-game-referee](https://github.com/feverZHONG/liya-chat-game-referee) · [liya-spy-game](https://github.com/feverZHONG/liya-spy-game) · [liya-sea-turtle-soup](https://github.com/feverZHONG/liya-sea-turtle-soup) —— 聊天里能玩的三件（回合制裁判引擎 / 谁是卧底 / 海龟汤）
- [liya-prose-quality-metrics](https://github.com/feverZHONG/liya-prose-quality-metrics) —— 稿子读起来「平」怎么办：先量再改（对话占比·句长σ·台词宽度·标点谱·段均句）＋ 7 个工具

## 提思路 / 提修正

- 你那边踩到的精修坑、验收没抓到的病、别的字段口径 → 开 [Issue](https://github.com/feverZHONG/liya-tavern-card-refinement/issues)，写清场景（什么卡、什么模型、改前改后什么现象）
- 想直接改 → Fork + PR

## 许可

**双许可**——文档与代码分开：

- **代码**（`scripts/` 下的文件）：**MIT** —— 拿去用、改、再发，保留版权声明即可。
- **文档**（`SKILL.md`、`references/`、本 README 的正文）：**[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)** —— 可以自由使用、改编、连商用都行，**但要署名**（莉娅 / [@feverZHONG](https://github.com/feverZHONG)）并注明来源。

两份许可的全文：`LICENSE`（MIT）／`LICENSE-DOCS`（CC BY 4.0）。

---

*莉娅（[@feverZHONG](https://github.com/feverZHONG)）· 宇宙美好记录官*
