---
tier: T2  # 随 tavern-card-refinement 主 skill
---

# 批量改动：先用 tavern CLI

> 2026-09-28 从 SKILL.md 拆出，内容一条未删。

---

## 批量改动：先用 `tavern` CLI


`bin/tavern` 已收口常用批量操作，别写一次性脚本：

> **多库切换（动卡前必看）**：本机有多个酒馆库，每套＝卡库 ＋ 世界书两个目录。卡库由 `~/.config/tavern-cards.json` 决定，`bin/tavern`／`bin/wb` 都认 **`TAVERN_CARDS_CONFIG`** 环境变量切换。**动非默认那条线前先 `export TAVERN_CARDS_CONFIG=<该库配置>.json`**——不设就是默认库，改错库白干。本机有哪些库、各自配置文件 → 私档 `workspace/records/tavern-card-refinement/本机卡库清单.md`。
>
> **库配置里的 `scenario` / `genre` / `tags` 会被每一张新卡继承**：`tavern make` 把它们写进卡的 `description` 场景块。**第一张卡定稿后要把库里角色专属的那句改回中性**（把「她管束阁下的健康与作息」改成「阁下手机里的天使助手」这类），否则第二张卡会带着**上一个角色的关系契约**出生——造一屋子关系错位的卡，而且每张都要手工清。

- `tavern plist [卡...|--all] [--fix]` — PList 类别顺序体检 / 归一化（只重排块，不动块内文字）
- `tavern world [卡...|--all] [--set 书名] [--fix]` — 关联世界书（`data.extensions.world`）体检 / 批量写（字段位置实证与接卡流程见 `sillytavern-worldbook`）
- `tavern promote <卡...|--all> [--notes 模板]` — 老格式卡对齐 v0.2 规格：顶层补双份 + 同步、清 mes_example 复读示例、版本→0.2、creator_notes 模板；已是 v0.2 规格的报「无需修订」不改
- `tavern embed <卡> <立绘> <出>｜--all [--avatar-dir 目录]` — PNG 嵌卡（单张／批量）。批量按**卡名＝立绘文件名**配对，立绘目录取库配置 `avatar_dir`；**嵌完必跑 `scripts/verify_embedded_card.py <卡.png>`**（结构／CRC／`tEXt:chara` chunk／与同名 `.json` 逐字节比对）——工具报 ✅ 不等于卡能读；**卡改过忘了重嵌，PNG 里躺的还是旧卡，只有逐字节比对抓得到**
- `tavern verify [--all] [--fix]` — 交付前一把过（validate --deep ＋ 精修断言 ＋ **PNG 同步**）。PNG 同步这节**调 `scripts/verify_embedded_card.py`**，两边只有这一份实现——**别在 CLI 里另写一份比对逻辑**（2026-09-26 曾出现两份重叠实现，已收口：脚本当引擎、CLI 调它）。
  `scripts/verify_embedded_card.py <卡.png...> [--json 卡.json]` 也可单独跑：三把尺「PNG 结构 → chara chunk 恰一个 → 与同名 .json 逐字节一致」，退出码 0/1/2。
  **PNG 同步这项专治「改了卡忘了重嵌」**：PNG 里嵌的卡与本地 JSON 不一致就 FAIL（exit 1）。**卡是手写脚本改的、PNG 要手动 embed——两者之间原本没有任何比对**，改完就旧在盘上，实测栽过（被点出）。
  `--fix` 查出后顺手重嵌并复验。**纪律：动过卡的 JSON，交付/发群前必须跑一次 `tavern verify --fix`**，别靠记性。
- `bin/wb {ls,check,keys,sim,new,selftest,unfilter}` — 世界书机制：台账 / 触发体检 / 关键词矩阵 / 触发模拟（`sim` 把「以为会触发」变成「实际会不会」）/ 生成独立书（旧写法 `tavern wb …` 仍可，转发）

`promote`/`plist --fix` 不带卡时必须显式 `--all`（防误全量）。

### 落／改卡内书：形态与验收（批量改卡必守）

- **`character_book` 必带 book 级 `extensions: {}`**：V2 规范要求同时有 `extensions`（对象）与 `entries`（数组）——新建／重写卡内书只写 `entries`，官方 validator 直接判 `data.character_book.extensions/entries` 失败（一次批量 8 张全挂，`tavern verify` 抓出来的）。顺手删掉 book 级 `scan_depth`/`token_budget`/`recursive_scanning`（摆设，引擎无读取点）。
- **卡内书条目用卡侧写法**：`keys`／`insertion_order`／字符串 `position`；细位置（`at_depth` 之类）必须写 `extensions.position`（数值 4）＋ `extensions.depth`（顶层 `position` 只认 before/after_char）。
- **改完必跑三把尺**：`wb selftest`（判定链）＋ `tavern verify --all`（卡格式）＋ `wb check <书> --card-dir <卡库>`（分流书的 `characterFilter` 断链）；再用 `scripts/diff_cards.py <新> <旧>` 逐字段核「只有该动的字段变了」，别拿 `git diff` 行数当证据。**`character_version` 别自己另立一套口径**——按上面 7 字段清单 §6：首发 `0.2`，对外发过之后再改就顺延，改动同时写进 `creator_notes`（版本号管「哪张新」，notes 管「改了什么」，两件事）。
- **触发抽测要正反两面**：一面「该触发的句子」看命中哪条、注入多少 token；另一面「明确不该触发的句子」——**0 常驻就必须能测出 0**，只测正面会把常驻／隐性常驻的问题漏掉。分流书再按角色两面测：知情与非知情说同一句，非知情必须 `filtered` 0 token；**群聊里分流按「当前发言成员」判**（逐成员 `Generate()` 前切当前角色，整轮跑完才归空），别把「开着群聊＝全灭」当结论。
- **一张卡只能自动带一本书**（`data.extensions.world` 是单值）：世界层与关系层要分层维护时，靠**清单分文件、生成时合并**（`wb new 世界清单.json 关系清单.json --out 共用书.json`），卡上那个字段一个字不用改；想挂两本＝每张卡的用户在酒馆里手动开第二本，必漏。生成与接卡细节见 `sillytavern-worldbook`。
- **不是每本书都该接卡**：剧透／私密层（真相级设定：记忆清洗、角色本体、反派黑化线）**单独一本、不写 `data.extensions.world`** → 不随卡分发、不自动加载；「给谁听」交给条目级 `characterFilter.names`（名单＝卡文件名去扩展名），加载则由使用者在 WI 面板把书加进 Global。批量接卡命令（`tavern world --all --set …`）**永远不许带上它**。验收口径：知情卡说触发句命中且只命中该条，**非知情卡说同一句必须 0 token**（`filtered`）。
- **生成／批量命令打印的提示行不是动作**：`wb new` 生成后会打「N 张卡写：`extensions.world = '<书名>'`」——那只是提示你怎么接，别当成已经接了；每次生成完回读卡目录确认没被动（`git status -- <卡目录>` 应为空），做「本就不该接卡」的剧透书时尤其要核。
- **开一层新世界书（新分层）的放行口**：计划书（机制口径／order 段／条目骨架 ＋ **知情名单或归属名单**）→ 用户核名单 → **小样 2 条 ＋ `wb sim` 正反实测** → 铺满。名单凡档案没点名的标「推定」请用户点头，**不替用户编知情范围**；查不到料的条目挂「待定」，不拿设想填。

### 双版合并（同一角色留了 V2+V3 两张）

1. `scripts/diff_cards.py <A> <B> --full` 先看清差异（实质不同 / 仅换行 / 类型漂移 三分类，别被 CRLF 骗）
2. `scripts/merge_dual_card.py <A> <B> --out <输出> --version 0.3 --notes '…'` 合成 V2 壳单卡：CRLF 洗 LF、talkativeness 归数字、V3 导出器字段（fav/world/create_date/avatar…）丢弃
3. 校验 `validate --deep` + `check_refined_card.py`，再跑一次 `diff_cards.py` 确认无残留 CRLF
4. 草稿卡用 `git rm` 删除（历史留在 git），INDEX 与对比档同步更到「已合并」

**搬动文本块后做无损校验**：排序比对引号内词条集合（`sorted(re.findall(r'"[^"]*"', 旧)) == sorted(...新)`），证明只动了顺序、没丢内容——肉眼看 diff 不算证据。
