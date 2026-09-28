# 槽位机制（源码实证）：四个槽怎么进上下文、代价差在哪

> 来源：`public/scripts/openai.js` ＋ `public/script.js` 精读（官方仓库 SillyTavern/SillyTavern）。
> 一句话：`description` / `personality` / `scenario` 是三个**并列的独立注入点**，`mes_example` 是第四个——性质不同（真对话轮次 ＋ 预算门）。

## 注入顺序（Chat Completion）

`worldInfoBefore → main → worldInfoAfter → charDescription（description）→ charPersonality（personality）→ scenario → personaDescription → … → dialogueExamples（mes_example）`

（`populateChatCompletion`：`addToChatCompletion('charDescription')` / `('charPersonality')` / `('scenario')` 依次入列。）

| 事实 | 机制 |
|------|------|
| 四个槽是并列的独立 system 消息 | 各有 identifier（`charDescription` / `charPersonality` / `scenario`），可排序、可单独禁用；`scenario` 位置在另两个**之后** → recency 最强 |
| `personality` / `scenario` 有格式模板 | `personality_format` / `scenario_format`（默认 `{{personality}}` / `{{scenario}}`），用户可自定义包装 |
| `mes_example` 不是文本，是**对话轮次** | `parseMesExamples`：字符串**必须以 `<START>` 开头**（否则自动补），按 `/<START>/gi` 切数组；`parseExampleIntoIndividual` 逐块解析——`{{user}}:` → `example_user`、`{{char}}:` → `example_assistant`，**每块跳过第一行**（约定为标题行），按 `name1` / `name2` 切分 |
| `mes_example` 有预算门 | `populateDialogueExamples` 每块先 `canAffordAll` 检查，挤不下就 `break`（后续块全丢）→ **非永久**，不占恒定开销 |
| `description` 里的 `<START>` 无特殊处理 | 就是普通文本，每轮全量重发；`<START>` 字样本身不触发任何解析 |
| 群聊里 `mes_example` 会带角色名前缀 | `appendNamesForGroup` → `${name}: ${msg}` |

## 结论

- 示例写 `description` ＝ 每轮吃恒定预算 ＋ 模型只当文本读
- 示例写 `mes_example` ＝ 拿到「对话轮次」＋「预算门」两样
- 场景句写 `scenario` ＝ 位置更靠后（recency）＋ 可被用户模板包装
- 性格标签写 `personality` ＝ 位置紧接 `description`，与 depth_prompt 的 PList 形成前后两道锚
- 三份内容挤进 `description` 的卡，恒定 token 有一大块是白烧的——归位前后各跑一次 `validate_tavern_card.py` 比对「累计/恒定」即能量出来

---

## 追加 · 槽位归位（2026-09-28 从 SKILL.md 并入，节名保持）

## 槽位归位（各格按酒馆官方字段定义各就各位）


> 触发：阁下说卡「错位／身兼多职」；阁下**只甩文件不说话**（《酒馆问题汇总vN》这类＝字段实况 dump，本身就是问题清单，读它推诊断）；或卡是 `make` 出来的新初稿。
> 机制依据（源码实证）→ `references/slot-mechanics.md`。
> **字段定义依据**＝酒馆编辑界面每一格的官方说明（阁下提供的两份《酒馆笔记》）——**定义优先于社区惯用形状**：官方说「角色描述＝角色的身体和精神特征」，那特征就该在这格，而不是躺在备注里。
> ⚠️ `sillytavern-cards` 的 **SKILL.md 字段表**仍是**老形状**（示例进 `description`、`personality`/`scenario` 建议留空）——那是兼容形状、不是最优；它自己的 `sillytavern-cards/references/writing-method.md` 已改到归位口径。那张表要改＝改对外仓内容，**先请阁下点头再走 `skillrepo sync`**，别顺手扩面。**归位口径以本节为准。**

**病**：`description` 一格干三份活（分类元信息 ＋ 场景契约 ＋ 对话教学），`personality` / `scenario` / `mes_example` 三格空着。示例躺在 `description` 里＝纯文本、每轮全量重发；`mes_example` 才是「真对话轮次 ＋ 预算门」。

**官方定义 → 归位去向**

| 字段 | 官方定义（酒馆界面原文） | 归位后放什么 |
|:--|:--|:--|
| 角色描述 | 角色的**身体和精神特征** | `[Personality= …]` ＋ `[body= …]`（从备注搬上来，＝官方示范同序）；`[Genre/Tags]` 锚归「嵌入的标签」格，**不进描述** |
| 角色设定摘要 | 角色设定的**简要描述** | PList 的 `Setting` 行（去 PList 壳，仅换分隔符） |
| 情景 | 交互的**情况和背景** | description 顶部 `[Scenario: …]` 的值 |
| 对话示例 | 设置角色的**写作风格**（很重要），每例 `<START>` 起行 | description 里的 `<START>` 示例块 |
| 角色备注 | 文本作为指定身份插入到**指定深度**（官方：通常用来**反复强化某些角色特质**） | **只留 `Personality` 深度锚**——整块原样保留会与描述／摘要三处重复（见下面「第二步：备注收敛」） |
| 创作者的注释 | 描述角色／使用技巧／测试过的模型，**显示在角色列表里** | 一句话角色描述 ＋ 使用技巧（**不是**变更日志；审计线索放 INDEX） |

**工具**：`scripts/slot_realign.py <卡.json> [...]`（默认只预览，`--fix` 写回，可加 `--version 0.4`；**幂等**——已归位的卡报「无改动」）。只搬运、不新写内容。

**「角色描述」收什么**（2026-09-27 阁下问「这是不是角色简介」后查实）：官方示范卡 Seraphina 的描述就是**标签块 ＋ `<START>` 示例 ＋ Genre/Tags 尾行**（拆 PNG chunk 读的原文），官方文档又写明描述「格式任意、所有重要事实都放这儿」——所以**描述用 PList 标签块合法且有官方出处**，判据在**内容覆盖**而不是文体。另：酒馆**没有**叫「简介」的字段（zh-cn 语言包零命中），社区口语的「角色简介」是卡本体统称——别照这个词去找格子。
**被质疑字段语义时回三处源头查，别拿推断答**（阁下问「描述是这么写的？」时就是这么查的）：

1. 官方文档 `docs.sillytavern.app/usage/core-concepts/characterdesign/`——每格的官方定义（描述／摘要＝Personality summary／备注＝按深度强化特质）
2. **酒馆自带示范卡原文**：`<酒馆安装目录>/default/content/default_Seraphina.png`，解 `tEXt:chara` chunk（base64 JSON 就是那张卡）——判「这种写法有没有先例」的直接证据
3. **界面文案**：`public/locales/zh-cn.json`——判某个说法到底是不是酒馆的格子名（社区流传的叫法很多是口语，不在界面里）

**第二步：备注收敛（归位之后必做）**——归位那一步做的是**复制**（把 PList 内容搬进各专槽），备注又原样留着，同一份信息就三处并存（2026-09-27 另一条线的同款实测：描述第三行 `[Genre/Tags]` 与 `data.tags` 一字不差，备注整格 364 token 全是复述）。
收法（阁下拍）：**备注只留 `Personality` 那一行**——行为锚最值得每轮重申（Trappu「最重要的放最后」），外貌／身份交给描述与设定摘要的正主；描述里的 `[Genre/Tags]` 行一并删（＝「嵌入的标签」第三遍）。效果：恒定 918→598 / 820→525，累计同步降。
判定口径：**每条内容只有一个正主**；只有「离对话最近的强化」才允许刻意并存，且要在档里记账。槽位归位的文案若与本节冲突，以本节为准（§7 字段清单 #3 那句「body 原样保留」是归位前的旧形状）。
工具：`scripts/trim_depth_dup.py <卡.json...> [--keep-plist Personality] [--drop-genre-line] [--version 0.x] [--notes-append '…'] [--fix]`——默认预览、幂等、自带 token 前后对比；从改动前的备份重放能逐字节复现成品（拿它当验收证据）。

**纪律**

- **先出一张小样交阁下实操**（导入酒馆看每格都填上了、跑几轮），口径点头后再铺开其余卡。
- **量化收益**：跑 `validate_tavern_card.py` 取「累计/恒定」改前改后对比（恒定＝name＋description＋personality＋scenario＋depth_prompt），别只说「顺眼了」。**恒定会降、累计会升**（标签在描述／设定摘要／备注三处刻意并存），两个数都要如实报。
- `system_prompt` / `post_history_instructions` 归位时**一字不动**——那是多轮实测磨出来的硬规则层，要动是另一案。
- 改完照「改完卡的收尾三步」走：`tavern verify <卡> --fix` → 版本顺延 → 重出发布物 ＋ 登记。
- **别替阁下定取舍**：待定项点名交他（例：两个 prompt 的长度口径各写一遍，是否合并）。
- **官方定义与社区方法冲突时，先摆给阁下看**：PList 放 depth 是社区口径（Trappu「最重要的放最后」），官方定义却把特征划给描述框——两者都留就是重复，这个取舍必须他拍。
- 断言脚本已改扫 `description` ＋ `mes_example` **两处**（`check_refined_card.py` / `validate_tavern_card.py`）：只扫一处会把归位后的卡判成「无示例」，也会漏掉 mes_example 里的复读污染。
- **原始反馈原样留档**：阁下甩来的《酒馆问题汇总vN》《酒馆笔记》这类文件收进 `<卡库>/反馈原文/`，另写一份 README 表登记「哪份是官方说明／哪份触发了哪次改动」——只留自己的二手总结，下次翻账对不上原文。
