# 精修经验：机制吃透笔记（实测案例 · 2026-08-13）

> 吃透 Trappu 指南 + 官方 Seraphina 示范卡后，对一张卡做第一轮精修的发现。
> 写卡/精修前先读这份，避免重复踩同一个坑。

## 核心认识：三个字段各自教什么

| 字段 | 教的 | 机制 |
|------|------|------|
| PList（depth_prompt） | 角色**是什么**（标签/特征） | 永久 token，第一记忆篮，长对话保人设 |
| Ali:Chat（description） | 角色**怎么说话**（口癖/句式/动作） | 永久 token，但对话久了进第三记忆篮变弱 |
| first_mes | **开局**定风格（场景/语气/关系） | 临时 token，但开局影响最强 |

**PList 和 Ali:Chat 是天作之合**：对话长了 description 被挤到第三记忆篮失去效力时，depth_prompt 里的 PList 能「拉动」description 里包含的信息保持相关——这就是为什么 PList 必须放 depth_prompt 而不是 description 里。

## 踩到的坑（每条都是实际发生的）

### 1. mes_example 复读 bug —— 最脏的一个

旧版那张卡 mes_example 里 `{{user}}` 和 `{{char}}` 说**一模一样的话**：
```
{{user}}: 「店长是个笨蛋！……不过你没事就好。」
{{char}}: 「店长是个笨蛋！……不过你没事就好。」
```
根因：make 脚本把 AGENTS 示例表（正确✅|错误❌ 对照表）的两列抄成了 user/char 对话——对照表根本不是对话轮次，抄出来必然复读。
**教训：**
- 官方 Seraphina 示范 mes_example 是**空的**，示例全进 description 的 `<START>`
- Ali:Chat 示例必须**手写完整对话轮次**（user 简短 + char 带动作的长回复），不能从对照表自动抄
- 脚本自动生成 description 时也只写场景块，`<START>` 示例留给精修手写

### 1b. 存量卡复读块残留 —— 脚本修了，旧卡没清（2026-08-26 抓包）

make 脚本 08-13 就修了（build_description 只写场景块），但 **13 张基础版卡是旧脚本生成的，description 里 3 个 `<START>` 块全是 user/char 同句复读**——08-13 全量复验只跑了 V2+deep 格式，deep 检查没拦复读，存量污染一直躺到 08-26 被点出「写法有点微妙」才发现。
**教训：**
- 脚本修 bug ≠ 存量清完——修完源头要**全量重扫存量产物**，别假设旧卡自动好了
- `validate_tavern_card.py --deep` 已新增两道拦截：① `<START>` 块 user/char 同句复读检测 ② PList「# PList 基础版/需按角色精修」施工注释残留检测（施工注释会直接暴露进 prompt）
- PList 里不写施工注释——给人类看的「待精修」标记进 creator_notes，不进 prompt

### 2. first_mes 双换行铁律

Trappu 明确警告：**「写对话示例和第一条消息时，切勿使用两个换行符」**——很多模型把 `\n` 当分隔符，双换行会扰乱上下文理解。
旧版那张卡 first_mes 是 `\n\n` 分段 → 改成单 `\n` 或直接连写。

### 3. 括号心理描写 → `*...*`

旧版 first_mes 写 `*（蜂蜜牛奶的甜香飘过来……）*`——括号里的心理/旁白注释会被模型当 OOC 指令学走。
**教训：动作/神态描写统一用 `*...*`，不用括号。**

### 4. PList 类别顺序：最重要的放最后

Trappu：类别按重要性从低到高排（先 body/衣服，最后 Personality）。
旧版顺序是 Personality → body → Setting（反了）→ 改成 body → Setting → Personality。
位置影响在对话开始时很小，但积少成多。

### 5. user 话要简短（分享卡模式）

分享给别人的卡，`{{user}}` 消息要**简短笨拙**——建立「简短 user 换冗长角色回复」的模式，文笔最差的用户也能舒服玩。旧版 user 话写得像礼貌的正式关心（抄了 AGENTS ❌ 列），改成了「今天也来咖啡馆坐坐，蛋糕卷还有吗？」这种日常短句。

### 6. PList 可以加喜欢/讨厌

Trappu 说 PList 没有固定写法，类别可扩展。给那张卡加了：
`"喜欢蜂蜜牛奶/瑞士蛋糕卷/甜食/茶会", "讨厌牙医/芥末"` —— 这比单独写「甜食依赖」标签更具体，模型直接知道她爱吃什么。

## 精修后长啥样（对照模板）

- **description**：`[Genre/Tags/Scenario]` 场景块 + 3 组 `<START>` 完整轮次（日常寒暄 / 关心傲娇回应 / 甜食破防——覆盖三种性格面）
- **first_mes**：场景化开场（咖啡馆 + 蜂蜜牛奶 + 蛋糕卷 + 傲娇推椅子），单换行，全程 `*...*`
- **PList**：body（9 标签）→ Setting（7 标签）→ Personality（9 标签 + 喜欢/讨厌）
- **mes_example**：空（官方示范）
- **system_prompt**：傲娇规则精简（口癖/句式/边界）
- **post_history_instructions**：对话节奏（被关心／被对手捉弄／谈到甜食→各怎么反应）

## 验证

`validate_tavern_card.py <卡>.json --deep` → V2 通过 + 深度检查无 warning。

## 减法教训（v0.9，2026-08-13）

**挖料是给素材库的，写卡是减法。** 从 v0.3 到 v0.8 一路「挖到就塞」的错误：
- description 台词本塞了 4 组混两类（典型场景 + 深感情）→ 砍深感情组，台词本只教「典型场景怎么说话」
- PList 塞到 18 标签（4 条隐藏习惯）→ 精简到 13，隐藏习惯合并
- system_prompt 3-4 行 → 官方短写法 1-2 句（`{{original}}` + 一句话人设）

**原则：** 挖出来的料先进 skill references/素材库（05-material-mining），卡里只放「这个角色现在就得用到的」。深感情台词没浪费——在 world book 店长条目里当点缀。

## description 忠于角色设定（v0.10，2026-08-13）

**Scenario/description 只写设定事实，不写解读、不写重复、不写标注。** 从 v0.9 挖出的问题：
- `（用户）` 标注——多余，{{user}} 本身就是用户
- 「这是她心里最重的结」「最亲近的人」——本文的解读，角色设定文档里没有这词
- 「处理日常事务」——展开说明，多余
- 「工作场合称店长，私下叫哥哥」——称呼规则，system_prompt/PList 已有，重复

**对照：** 角色设定文档有「过度保护倾向」→ 卡里写「店长是她的哥哥，前作里为救她而死」就够，不补「所以她很担心」这类推理。模型会自己从设定推出行为，解读是噪音。

## 重复检查（v0.12，2026-08-13）

**精修完必须扫一遍跨字段重复——同一信息两处 = 浪费 token = 稀释注意力。**
发现的实例：
- 某卡 PList「梦想成为军火女王」↔ wb5「梦想：成为军火女王……」→ 删 wb5 梦想行（PList 标签已有）
- 另一卡 PList「对店长嘴上嫌弃实际依赖」↔ post_hist「对店长：嘴上嫌弃，实际依赖」↔ wb0「她嘴上总是嫌弃店长」→ 删 PList（post_hist 行为规则 + wb0 关系设定已覆盖）

**检查方式：** 跨字段 8+ 字连续文本撞车（n-gram 对比），world book 条目两两对比，台词本与 wb「角色会这么说」对比。
**判定原则：** 同一信息保留「最近的职责位」——PList 标签、post_hist 行为规则、wb 关系设定各司其职；重复的删掉。

## 改卡先 git diff 确认再 commit（2026-08-13）

**流程教训：改卡脚本打印「✅ 已改」≠ 文件真的改进了 commit。** 上一轮重复检查后脚本显示成功，但 commit 时卡文件 diff 为空——工作区被覆盖/写入丢失，差点白干。
**铁律：**
1. 改卡脚本跑完 → `git diff workspace/tavern-cards/` 确认改动真实存在
2. diff 确认后再 `git add` + commit
3. 只看脚本打印不 commit——脚本可能成功也可能被覆盖，diff 是唯一事实

## 精修必须对照 AGENTS 三件套（v0.12，2026-08-13）

**精修时只盯着 sources 设定文档，把 personas 三件套的 AGENTS.md 互动硬规则漏了**——精修完才发现（通病，不是个案）：
- 一张卡 system_prompt 丢「句子长度上限 15 字，超过 3 句必须拆短」「结论先行→补充细节→结束，不铺垫」
- 同一张卡台词本第一句是编的，还违反自己 15 字上限（20+ 字）
- 另一张卡 system_prompt 丢「必须」——设定档原话「口癖必须每句结尾出现，这是最核心的语言特征，不能丢」
- 某卡减法时砍掉口头禅和禁止事项（情感别直白／年龄设定别写成另一档）

**流程修正：精修三处之后必须「对照 AGENTS 逐条落实硬规则」**——system_prompt 收口癖/句式限制，post_hist 收对话节奏/禁止事项。AGENTS 的示例表（✅|❌）是台词本素材的第一来源，优先于自编。

## token 统计口径（v0.13，2026-08-14）

**酒馆 UI 的「累计/恒定」怎么算**（源码 RossAscends-mods.js `RA_CountCharTokens` + index.html 的 `data-token-counter` 元素）：
- **累计** = name + description + personality + scenario + first_mes + mes_example + system_prompt + post_history_instructions + depth_prompt.prompt 的 token 和
- **恒定** = 其中带 `data-token-permanent` 的字段：name / description / personality / scenario / depth_prompt.prompt
- **不算进卡片统计**：alternate_greetings、character_book（世界书单独算）——别把这两个加进对比

**tokenizer 差异**：酒馆界面实测值取决于主 API 的 tokenizer（deepseek 系比 cl100k 对中文更省 token）。所以登记一律两值并存：
- `extensions.twinvision.token_stats.guild_measured` = 酒馆界面实测（为准）
- `extensions.twinvision.token_stats.script_est` = validate 脚本 tiktoken cl100k 估算（参考）

**实测**：1949 累计 / 1146 恒定（酒馆界面，填三个【需补充】字段后）。脚本 cl100k 估算 2478/1400——量级一致、绝对值偏大，用于趋势对比没问题。

**教训：填完【需补充】字段再测 token**——占位符状态测的数字（1899/1115）不是最终值，容易误判预算。

## 同角色双版（V2/V3）怎么比

同一角色可能同时留着 V2 卡和 V3 卡（如 `<角色>.json` V2 2.0 与 `<角色>_需补充.json` V3 3.0）——它们**不是两张卡**，是同一份内容的两种壳，按字段分布看差异：

| 内容 | V2 放哪 | V3 放哪 |
|:-----|:--------|:--------|
| 角色标签 | `extensions.depth_prompt.prompt`（PList） | 同 V2 ＋ `personality` 段落 |
| 场景/世界观 | `description` 场景块 | 同 V2 ＋ `scenario` 段落 |
| 对话示例 | `description` 的 `<START>` 组 | 同 V2 ＋ `mes_example` 组 |
| 世界书 | `character_book` | `character_book`（常为同一份） |
| 两个 prompt | 只在 `data` 层 | `data` + 顶层双份 |

- V3 顶层字段更全（多 fav / talkativeness / tags / create_date / creatorcomment / avatar），V2 顶层通常只有 9 键
- **先跑 `scripts/diff_cards.py`**（加 `--full` 看实质差异原文），CRLF 与类型漂移会单列，不会和内容差异混在一起
- 结论口径：V3 真正独有的通常只有 personality / scenario / mes_example 三块；其余字段常常逐字相同——别被换行符差异骗成「两张不同的卡」
- 定稿前把 CRLF 转成 LF，否则两个 prompt 的 `{{original}}\n` 前缀断言和 first_mes 单换行规则都不成立
