# T10 执行报告：README（中英文）重写与 Pages 同步（Qoder）

**执行者**：Qoder（Orca worker，task_3413b76a39ae / ctx_54f64801f605）
**基线**：`feat/sopify-narrow-focus`，HEAD 派单时 `32687ae`；期间 Codex 落地 `1ae94c2`（首次 `~go` 绑定项目）与一批重画图，均已在当前工作区复跑校验。
**写集**：`README.md`、`README.zh-CN.md`、`index.html`、`zh-CN.html`、`docs/how-sopify-works.md`、`docs/how-sopify-works.en.md`、`scripts/check-readme-links.py`（后两者为授权扩展，见下）。
**未做**：不 commit、不 push；未生成任何新图片文件；未改 `tests/**`、`skills/**`、`installer/**`、`docs/getting-started.md`、`.sopify/**`。

## 一、结论

README 中英文按大纲重写完成：首屏 24 行内给出「它是什么」，第 5/7 行是用户选定的主/副标语，第 26–40 行是安装命令与「哪个工具 → 哪个 target」小表，第 44 行进入第一个 `~go plan` 示例；价值场景用 Before/After 三组短句并引用 T9 真实证据；宿主表改为用户语言状态（已验证 / 基线 / 预览）并补 Antigravity、Trae。Pages 只同步标语、副标语、宿主清单与状态、安装相关文案，布局、样式、图片原样保留。全量测试 420 passed、97 subtests passed；`git diff --check` 干净；`scripts/check-readme-links.py` 通过（正文 115/115 行，预算 250）。

## 二、删除与挪动的段落及去向

| 原 README 段落 | 处置 | 去向 |
|---|---|---|
| 旧导语三段（"AI coding tools are fast…" / "Sopify stores plans…" / "No new editor…"） | 重写 | 新导语一段（它是什么，2–3 句）；"No new editor, no new CLI" 并入 Quick Start 与 Pages hero-note |
| "Design principles" 三条列表 | 删除 | 三点分别由主标语、价值场景、命令速查承担，不再单列 |
| "What Sopify prevents" 三条列表 | 改写 | 价值场景的 Before/After（中断续做、换工具换人、多 agent 分工） |
| "Sopify in a Real Codex Workflow"（原第 1 节） | 挪动 | 新第 6 节「真实案例 / A Real Case」，GIF、三条要点与三个归档链接原样保留 |
| "Why Sopify?" 三个叙事场景 + 三张场景插画 | 改写 + 取舍 | 场景改写为 Before/After；插画保留 cross-host（Codex 已按 T9 重画）与 decision 两张，「先问再写」那张撤下（文件保留未删） |
| "Product Form"（SVG + 说明段 + 三条） | 挪动 | `docs/how-sopify-works*.md`「核心价值」节新增 `### 产品形态`（图 + 说明 + 三条）；README 在「深入阅读」保留指向该 SVG 的链接（`tests/test_plain_language_contracts.py` 要求 README 引用该资产，见第五节） |
| "Architecture Details"（SVG） | 挪动 | `docs/how-sopify-works*.md`「目录结构与层级」节顶部；README 不再引用，Pages 仍展示 |
| "Installation" 的 review-before-run 代码块、EvidentLoop 长段、`--workspace` 说明 | 删除 | 统一指向 `docs/getting-started.md`（该文档已有 Inspect-First Setup 与 Optional EvidentLoop Companion 两节） |
| "Installation" 宿主表（含 PROTOCOL_VERIFIED 档位名） | 改写 | 新第 5 节「支持的宿主 / Supported Hosts」：用户语言状态列 + 7 个宿主 + 各自文档链接；Antigravity/Trae 标注从源码克隆安装 |
| "Command Reference" 表 | 改写 | 「命令速查 / Command Cheat Sheet」：三个命令各一句话 |
| "Configuration"（cp 命令 + YAML 块） | 删除 | 「深入阅读」一行链接 `examples/sopify.config.yaml`，并注明不配置也能用默认值 |
| "Directory Structure"（仓库源码树） | 删除 | `.sopify/` 层级本就在 `docs/how-sopify-works*.md`；仓库源码布局属维护者信息，CONTRIBUTING 已覆盖 prompt 层与 bundle 位置，不新建文档 |
| 徽章：docs(CC BY)、PRs welcome | 删除 | 按大纲只保留 license、version、宿主徽章（7 个） |
| "Version History" | 保留 | 一行指向 CHANGELOG；测试夹具依赖 `#version-history` / `#版本历史` 锚点，见第五节 |

新增内容：Quick Start 的 Windows PowerShell 块（见第六节风险 1）、价值场景末尾两张插画、`docs/how-sopify-works*.md` 的产品形态与架构图。

## 三、行数

| 文件 | 行数 | check-readme-links 正文行数（预算 250） |
|---|---|---|
| README.md | 151 | 115 |
| README.zh-CN.md | 151 | 115 |
| docs/how-sopify-works.md | 134 | — |
| docs/how-sopify-works.en.md | 134 | — |
| index.html | 278 | — |
| zh-CN.html | 270 | — |

中英文 README 行数完全一致，二级标题 10 节逐一对应（快速开始/Quick Start、价值场景/Where It Pays Off、什么时候不用/When Not to Use It、命令速查/Command Cheat Sheet、支持的宿主/Supported Hosts、真实案例/A Real Case、深入阅读/Further Reading、版本历史/Version History、许可证/License、贡献/Contributing）。

首屏核对（README.md 前 40 行）：第 5 行主标语、第 7 行副标语、第 24 行「它是什么」、第 26 行 Quick Start、第 31 行安装命令、第 34–40 行 target 表。三问（是什么、有什么价值、怎么开始）均在 40 行内有答。

## 四、Pages 同步内容（只同步，不重做）

`index.html` / `zh-CN.html` 改动限于：`meta description`、`og:title`、`og:description`、`<title>`、hero eyebrow、`<h1>`、hero-lede、hero-note、宿主清单 `<ul class="host-list">`（补 Antigravity、Trae，Claude → Claude Code）、FAQ「换宿主能力是否相同」一答、`#resume` 两句（去掉 "workflow protocol layer" / "managed entry" 黑话，与 README 导语同口径）。安装命令未变（EN `codex:en-US`、ZH `codex:zh-CN`，与 README 一致）。布局、CSS、图片、canonical/hreflang/OG 尺寸全部未动。

Pages 链接人工核对：两页 HTML 解析无未闭合标签，全部本地 `href`/`src` 均指向存在文件；`test_static_pages_keep_release_metadata` 与 `test_static_pages_include_cursor_host` 通过。

## 五、测试与脚本改动（含授权记录）

1. **`scripts/check-readme-links.py` 的 `EXPECTED_LEVEL2_SECTIONS`**：派单前经 `orca orchestration ask` 取得授权，只更新 README 中英文两组常量以匹配新结构，其余逻辑不动。
2. **`scripts/check-readme-links.py` 的 `/private/var` 崩溃修复**（补充第 4 条授权）：`check_relative_file_links` 在「锚点缺失」分支对 `resolved`（已 `resolve()`，符号链接已折叠）调用 `relative_to(ROOT)`，当 ROOT 是 macOS 未解析的临时目录（`/var/...`）时抛 `ValueError`。新增 `relative_to_root()`，依次尝试 `ROOT` 与 `ROOT.resolve()` 两个基。已用未解析临时目录复现：修复前抛 `ValueError`，修复后输出 `docs/how-sopify-works.md: missing anchor #版本历史 in README.zh-CN.md`。
3. **`tests/**` 未做任何改动**。三处锁定旧内容的断言以文档侧满足，未改测试：
   - `test_product_form_is_clear_without_duplicating_the_homepage` 要求 README 文本含 `./assets/sopify-product-form-release{,-en}.svg` → 在「深入阅读」保留指向该 SVG 的链接（该链接本身也有用）；同时保持 Pages 不含 `sopify-product-form-release`。
   - `test_static_pages_include_cursor_host` 钉住 `Cursor · baseline`、`Cursor · 基线支持` 与 `Codex, Claude, Qoder, Copilot, and Cursor targets` → Pages 宿主清单保留这些字符串，install-note 未动（该句描述的是已发布安装器支持的 5 个 target，今天仍然准确）。
   - `test_check_readme_links.py` 夹具钉住 `#version-history` / `#版本历史` 锚点 → README 保留一行「版本历史」节。
4. **校验结果**：`python3 -m pytest tests -q` → 420 passed, 97 subtests passed（在含 Codex 新图与 `1ae94c2` 的当前工作区复跑）；`pytest tests/test_check_readme_links.py -q` → 4 passed；`git diff --check` 退出 0；`scripts/check-version-consistency.sh` 通过；CI 的 protocol smoke（new-plan / continuation / finalize）与 install/payload smoke 均退出 0。

## 六、统一验收标准中不通过或有风险的项

- **不冗余（风险）**：`docs/getting-started.md` 目前没有 Windows/PowerShell 小节，因此 Windows 安装块留在 README Quick Start（第 61–66 行）以免丢失事实；若 Codex 后续在 getting-started 补该节，应删掉 README 这份副本。
- **不冗余（风险）**：README「深入阅读」的产品形态 SVG 链接与 `docs/how-sopify-works*.md` 的 `### 产品形态` 指向同一张图，属测试要求下的有意保留。
- **与其他宿主整体一致（小差异）**：Pages 状态词受测试钉住为 `baseline` / `基线支持`，README 用大纲指定的 `Baseline` / `基线`；语义一致、措辞不同，未强行统一。
- **时效性（风险）**：Antigravity / Trae 今天只能从源码克隆安装，README 与 Pages 如实标注；T11 发布新安装器后该说明会过时，需要在 release 时回改。
- **图片（遗留）**：`assets/sopify-og-*.jpg` 仍带旧标语文字，本轮不重画（更正只豁免封面，OG 图未列入重画清单），分享卡片上会出现新旧文案并存。
- **Pages 风格（遗留）**：`#why` 区块仍是旧的 "What it prevents" 三卡表述，按「不重做页面」未改；与 README 的 Before/After 口径兼容但不完全同构，是否统一由验收官/用户定。
- **判断项**：decision 插画放在「价值场景」末尾是我的取舍（补充要求保留 cross-host 与 decision 两张、撤下 ask 那张，但未指定位置）；如验收官认为应放「真实案例」，移动成本很低。

## 七、作为使用者的体验

以一个新用户身份重读改后的 README，第一感受是「终于知道它是个什么东西了」。旧版第一屏给我的是 "development process protocol layer" 这种词，我得读到第三段才拼出它装在哪、产出什么；新版第 24 行一句话讲完：装进你现有工具的一套规则和 Skill，方案和证据是仓库里的普通文件。Quick Start 的 target 小表解决了我旧版最大的停顿——「我用 Claude 是不是不能用这条命令」——现在一眼能看到自己工具的 target，不用去翻安装器帮助。

价值场景里 Before/After 的写法比旧版的三条原则列表有效：它把「我会遇到什么麻烦」放在前面，把「Sopify 之后变成什么」放在后面，尤其是第二条直接说「这个版本就是这样做出来的」，比任何形容词都可信。Codex 重画的那张 cross-host 插画和 alt 文字对得上（Claude Code `~go plan …` → `.sopify/` → Qoder `~go`），图不再说 "Seamless" 这种大话，反而更可信。

仍然会卡住我的地方有两处：一是 Antigravity / Trae 需要「从源码克隆安装」，对只想一行命令装完的人是额外一步，但这是今天的真实状态，写清楚比假装支持更好；二是 Windows 块放在 Quick Start 第 3 步之后，Windows 用户要读到第 61 行才看到自己的路径，这是为了不挤占首屏做的取舍。整体上，这版 README 让我在 40 行内决定「要不要试」，在 3 步内知道「怎么试」，这正是旧版缺的两件事。

## 八、交接

- 未 commit、未 push；工作区除本任务写集与 Codex 的图片/代码改动外无其他变更，无未跟踪文件。
- 待验收官审查与全新 Qoder 会话新手测试后，由用户做最终验收。
- 建议 T11 时同步处理：OG 图旧文案、Antigravity/Trae 安装说明时效、getting-started 若补 Windows 小节则回收 README 副本。

## 本轮变化（2026-10-21，按验收官 `t10-accept-gemini.md` 第八节做最小修改）

写集仍限于 `README.md` 与 `README.zh-CN.md`；未 commit、未 push；未碰 `assets/**`（Codex 并行重画两张产品形态图）、docs、Pages、脚本与测试。

1. **快速开始 target 表补两行**：EN `| Antigravity | antigravity:en-US / antigravity:zh-CN |` 与 `| Trae (Preview) | trae:en-US / trae:zh-CN |`；ZH 同构（`| Antigravity | antigravity:zh-CN / antigravity:en-US |`、`| Trae（预览） | trae:zh-CN / trae:en-US |`，语言顺序与全表一致）。
2. **支持的宿主表改为标准安装写法**：安装列去掉 `from a clone:` / `从源码克隆安装：` 前缀；删除表后「Antigravity 和 Trae 需要克隆本仓库后用 `python3 scripts/install_sopify.py --target <target>` 安装」一句（EN/ZH 同）。状态列与状态解释段未动。
3. **事实口径变化与发布顺序依赖**：README 现在表示 `releases/latest` 的安装器可直接装 `antigravity:*` 与 `trae:*`。该陈述成立的前提是 README 与含这两个适配器的安装器同批发布；T11 用 `render-release-installers.py` 生成 release 安装资产时必须包含这两个 target，否则此处会重新成为过时陈述。第六节原「时效性（风险）」条目由「克隆说明会过时」更新为「发布顺序依赖」，核对点不变。
4. **校验**：`python3 scripts/check-readme-links.py` 通过（正文 117/117 行，预算 250）；`pytest tests/test_check_readme_links.py -q` → 4 passed；`git diff --check` 退出 0；中英文各 153 行，十节结构仍逐一对应。首屏前 40 行仍含主/副标语、「它是什么」、安装命令与前五个 target 行，Antigravity/Trae 两行落在第 41–42 行，不改变首屏三问的可答性。
5. **未改**：`docs/how-sopify-works*.md`、`index.html`、`zh-CN.html`、`scripts/check-readme-links.py`、`tests/**`、`assets/**`。验收官第八节未要求改这些文件。

## 本轮变化（新手测试，2026-10-21）

依据 `newbie/answers.md` 第三步 3.4 与第四步第 2/3/5/8 条，做 4 处最小修改；写集为 `README.md`、`README.zh-CN.md`，以及 Pages 的同一事实句。未 commit、未 push；未碰 `installer/**`、`scripts/**`、`assets/**`（Codex 并行）。

1. **快速开始第 2 步改写**（B1、第四步第 2 条）：改为「Sopify 先追问还没定的事实，等你在对话里回答后才写 `plan.md`；非交互会话（如 `-p` / `--print`）下提问会结束本轮，把答案写进请求再发一次」。中英文同构；未引入 `require_score` 等内部名词。
2. **新增三行小表「What lands in your repo / 仓库里会多出什么」**（B4/B5/B6/B7、第四步第 5/7 条）：`.sopify/sopify.json`（项目标记，提交）、`.sopify/plan/` 与 `.sopify/history/`（方案与验收证据，提交）、`.sopify/state/`（本机指针，不提交，默认经 `.git/info/exclude` 忽略）。放在快速开始第 3 步之后、Windows 说明之前；用 `###` 三级标题，不新增大节，也不触碰 `check-readme-links` 的二级标题锁。
3. **"no runtime" → "no background process"**（第四步第 3 条）：README 中英文第 44 行同步改；Pages 的 install-trust 同句同步（"Sopify runtime" / "Sopify 运行时" → "background process" / "后台进程"），消除与安装输出 `Runtime:` 目录的撞词。四个文件现已无 runtime/运行时 字样。
4. **Qoder 的 target 补语言变体**（第四步第 8 条）：快速开始 target 表与支持的宿主表安装列同时改为 `qoder:en-US` / `qoder:zh-CN`（ZH 顺序 `qoder:zh-CN` / `qoder:en-US`），两处同事实一起改以免表间不一致；中英文一致。

**校验**：`python3 scripts/check-readme-links.py` 通过（正文 125/125 行，预算 250）；`pytest tests/test_check_readme_links.py -q` → 4 passed；`pytest tests/test_plain_language_contracts.py -q` → 16 passed；`git diff --check` 退出 0；README 中英文各 161 行，结构仍逐节对应。

**遗留（不在本轮 4 处授权内，供大脑定）**：

- 命令速查的 `~go plan` 行仍写 "Writes `.sopify/plan/<id>/plan.md` and changes no code"，与第 2 步新表述存在粒度差（B3）；完全对齐需改速查表，属第 5 处修改。
- 新手报告其余条目未处理：Python 3.9 下安装器直接抛 ImportError 而无提示（需改安装器或 README 明说）、安装输出 `Next: 2. Type: ~go` 与 Quick Start 示例不一致（安装器输出）、`[demo-ai]` 项目代号来源、`6 errors loading agent configs` 的归属、以及 `.git/info/exclude` 不随仓库分发对「换人接手」卖点的影响说明（属设计取舍，需大脑决定是否在 README 表态）。
- **第 5 处修改（2026-10-21，大脑授权）**：命令速查表 `~go plan` 行改为与快速开始第 2 步同口径的一句话——EN "New work that needs a plan — asks first when anything is unclear, writes `.sopify/plan/<id>/plan.md` only after you answer, and changes no code"；ZH「需要方案的新工作——不清楚时先追问，等你回答后才写 `.sopify/plan/<id>/plan.md`，不改代码」。Pages 无同句，未改。`python3 scripts/check-readme-links.py` 与 `pytest tests/test_check_readme_links.py -q`（4 passed）通过，正文 125/125、中英文各 161 行，`git diff --check` 干净。上一节遗留的第一条（B3 粒度差）至此关闭。

## 本轮变化（润色，2026-10-21）

写集：`README.md`、`README.zh-CN.md`、`index.html`、`zh-CN.html`。主标语行（README 第 5 行、Pages 的 `<h1>`/`<title>`/og）未动。未 commit、未 push、未碰 `assets/**`（Codex 并行改三张图）。

**用户已定的三项**：

1. **徽章排成一行**：7 个宿主徽章改 shields message-only 写法（去掉重复的 `host-` 前缀，只留宿主名），由两行合并为一行，风格与 License/Version 徽章一致；中英文同。
2. **Trae 去预览**：target 表、宿主表、Pages 宿主清单与 FAQ 一律改为基线 / Baseline；「基线」定义改为「安装已验证；真实会话证据因宿主而异，见各宿主文档」/ "the installation is verified; real-session evidence varies by host — see each host's doc"；删除「预览 / Preview」定义句。
3. **删否定式说明**：README 导语末尾 "Not a new editor, not a new CLI." / 「不是新编辑器，也不是新 CLI。」、Quick Start 的 "— no daemon, no background process, no new editor" / 「——没有守护进程、没有后台进程、不是新编辑器」、Pages hero-note 的同类短语、Pages install-trust 的否定排比，全部删除或改肯定句。

**采纳措辞审计（`language-audit-gemini.md`，含大脑修正）**：

4. `dogfood` → 「已在真实会话中实测」/ "tested in real sessions"（README 宿主表 Antigravity 状态、Pages FAQ；不采用审计原文「深度验证」）。
5. FAQ 首条由否定设问重构为正面问法，答案只写事实：EN "How does Sopify work with existing AI coding tools?" / "Sopify is a set of rules and Skills that installs into the AI coding tools you already use."；ZH「Sopify 如何与我现有的 AI 编程工具协同？」/「Sopify 是一套规则和 Skill，安装到你已有的 AI 编程工具里。」
6. 页脚：EN "Sopify · AI coding workflows that can stop, resume, and be inspected."；ZH「Sopify · 能停车、能恢复、能追溯的 AI 编程工作流。」
7. README 中文：安装说明删否定尾句；`git`→`Git`；「粘」→「粘贴」；「什么时候不用」收尾句去重复的「方案/明确」；真实案例删「不是编排好的终端演示」；「动效解释」→「上方动图展示了」；深入阅读链接标题 `Getting Started`→「入门指引」、「外部仓库 Quickstart／分步 demo」→「外部仓库快速上手／分步实操演示」。
8. README 英文：安装说明删否定尾句；`git`→`Git`（并把「What lands in your repo」表头 "In git?" 一并改为 "In Git?"）；「When Not to Use It」收尾句与中文同构精简；真实案例删 "; it is not a scripted terminal demo"。
9. Pages：install-trust 改肯定句（EN "Installs host instructions and supporting assets directly into your tools."、ZH「仅把宿主指令与配套资产写入你的工具。」）；install-note 宿主清单补 Antigravity/Trae（做法见下节第 1 条）。

**校验**：`python3 scripts/check-readme-links.py` 通过（正文 125/125）；`pytest tests/test_check_readme_links.py tests/test_plain_language_contracts.py -q` → 20 passed；`git diff --check` 退出 0；README 中英文各 160 行、逐段对齐。四个文件已无用户可见的 preview/预览/dogfood/「新编辑器」字样（grep 残留命中仅为资产文件名 `codex-dogfood.gif` 与 CSS 类名 `architecture-preview`/`preview-link`）。

## 我没采纳的审计建议及理由

1. **审计三 L207 / 四 L215 的原文改法未照搬**。审计要求把 Pages install-note 的宿主清单行改写为含 7 宿主与 Claude Code 全称；但 `tests/test_plain_language_contracts.py::test_static_pages_include_cursor_host` 钉住了 "Codex, Claude, Qoder, Copilot, and Cursor targets" 与「支持 Codex、Claude、Qoder、Copilot 与 Cursor」两个子串，本轮写集不含 tests。折中做法：钉住行原文保留，其后新增一行 li 补齐事实（EN "Antigravity and Trae targets"、ZH「支持 Antigravity 与 Trae」）。代价是该行内 Claude→Claude Code 的重命名仍未做（Pages 宿主 pills 与 README 两处均已是 Claude Code）；如需彻底统一，需大脑授权改该测试。
2. **审计一 L122 / 三 L250 的「深度验证」措辞未采纳**：按大脑修正改为「已在真实会话中实测」/ "tested in real sessions"，「深度」属无度量的夸大词。
3. **审计三 L237-239 / 四 L245-247 答案中的「无需更换工具或改变习惯」/ "without changing your setup" 未采纳**：按大脑修正，FAQ 答案只保留事实句。
4. 其余审计条目全部采纳。审计未覆盖、我自行延伸的仅一处：EN 表头 "In git?" → "In Git?"，与审计 L61 的专有名词大小写保持一致。

## 本轮变化（标语，2026-10-21）

写集：`README.md`、`README.zh-CN.md`、`index.html`、`zh-CN.html`，以及 `tests/test_plain_language_contracts.py` 的一处期望子串（本任务授权）。未 commit、未 push、未碰 `assets/**`（Codex 并行改三张图）。

1. **主/副标语替换为用户选定的 A 版**：README 中英文第 5/7 行逐字替换；Pages 的 `<title>`、`og:title`、meta description、`og:description`、hero `<h1>`、hero-lede 的 strong 与 hero-note（副标语逐字）同步；ZH 的 `<h1>` 保留 `keep-together`/`<wbr />` 断行结构。
2. **正文口径统一为「纳入 Git / 接续」**（按句意改写，未逐字硬替换）：README EN 导语 "in your repo … continues from the record" → "versioned in Git … resumes from the record"；第 3 步说明 "pick the work back up" → "resume the work"；价值场景第二条改为 "a fresh Qoder session whose only input was `~go` resumed a plan written by Claude Code"；cross-host 插画 alt 同步。README ZH 导语「保存在仓库的 `.sopify/` 里…接着做」→「保存在 `.sopify/` 并纳入 Git…接续」；第 3 步说明、价值场景两条、alt、命令速查 `~go` 行同步。Pages：EN `#why` 卡片 "live with the repo / continue" → "versioned in Git / resume"，hero-lede 正文同步；ZH `#why` 卡片与 `#resume` 首段同步。
3. **Pages 安装说明宿主行恢复单行 7 宿主**：删除上一轮为绕开测试新增的重复 li；单行改为 EN "Codex, Claude Code, Qoder, Copilot, Cursor, Antigravity, and Trae targets"、ZH「支持 Codex、Claude Code、Qoder、Copilot、Cursor、Antigravity 与 Trae」，Claude 统一为 Claude Code。同步把 `tests/test_plain_language_contracts.py::test_static_pages_include_cursor_host` 的两个 `install_copy` 期望子串改为上述新串——只改这一处参数，断言逻辑未放宽、未删除。
4. **校验**：`python3 scripts/check-readme-links.py` 通过（正文 125/125）；`pytest tests/test_check_readme_links.py tests/test_plain_language_contracts.py -q` → 20 passed；`git diff --check` 退出 0；README 中英文各 160 行、逐段对齐。四个文本文件 grep 旧标语字样（存进仓库／接着做／keep building／proof in your repo／stay direct／不强制走流程）均无命中。

**跨资产遗留**：`assets/sopify-architecture.svg` 与两张产品形态 SVG 内嵌的仍是旧标语（"AI coding plans and proof in your repo — keep building across tools, teammates, and agents." / 「AI 编程的方案和验收证据存进仓库，换工具、换人、换 agent 都能接着做。」）。assets 本轮禁改，需 Codex 下一轮按新标语 A 覆盖这三张 SVG 的文字，否则图与文不一致。
