---
title: Sopify 清晰表达、高频 Skill 与推广页优化
plan_id: 20260720_plain_language_output
status: in_progress
lifecycle_state: in_progress
level: standard
created: 2026-07-20
updated: 2026-07-20
archive_ready: false
knowledge_sync:
  project: review
  background: review
  design: required
  tasks: review
---

# Sopify 清晰表达、高频 Skill 与推广页优化

## Plan Snapshot

- **Goal**: 让 Sopify 的中英文方案包、宿主回复和公开推广页更清楚、自然、符合用户心智，同时用更少重复内容提升高频工作流的判断质量。
- **Status**: Wave 0–4.4 和交付候选已完成。方案内正式报告保留模型的两个 finding，相关问题已修复并通过全量验证；用户已授权本地 commit 和当前分支 push，PR、merge、Pages、release 与 finalize 仍未授权。
- **Next**: 完成当前分支 commit / push 后停车，等待后续 Git 或发布授权。
- **Task**: 20/22。

就绪状态: Ready
依据: 目标、范围、实现路径和验收标准均已确认；剩余停车点只负责审计裁定、Git 交付与发布授权，不改变本地实施方案。

## Context / Why

用户提供的真实运行快照为 Analyze 123 次、Develop 114 次、Design 49 次，KB 也属于核心使用面。高频 Skill 的价值不在规则更多，而在同一工作流中用更少上下文完成稳定交接。

Analyze 目前偏重补齐字段，对用户提供或当前可访问的证据利用不足。五个 Skill 也存在 owner 重复：Design 与 Templates 同时持有方案模板，Develop 重述 KB 政策，header 复制阶段流程；Copilot 单文件还会内联 Python。中英文共享规则则缺少结论顺序、具体主语和自然表达边界。

Ponytail 只作为批判证据：其可复现实验支持“充分理解后再最小化”和“检查调用方、在共同根因处修一次”；也证明仅仅增加正确理念的 prompt 文字可能无效甚至退化。Sopify 只吸收这些决策原则，不移植人格、强度模式、绝对技术梯子、输出格式或独立审计 Skill。其他外部 Skill 同样只提供渐进披露和代表性验证的参照，不成为运行时依赖。

上一个 `20260718_evidentloop_optional_audit_integration` 方案已归档，并由提交 `ea92482cec1e93f41cbe63b68e1b067805f5dfd0` 收口。本方案从该提交建立叠加分支；两个方案依次进入 main 后，只发布一个同时包含两组变化的 Sopify release。

Sopify 目前没有公开 GitHub Pages 推广页。本方案用仓库现有事实和素材建立中英文静态页面；外部项目只提供信息结构与视觉取舍参考，不复制源码或引入运行时依赖。

## Scope

- 优化中英文方案包正文和 Sopify 管理的宿主回复。
- 把 Analyze、Design、Develop、KB、Templates 作为同一工作流审计；按真实使用优先处理前三个，审计不等于全部修改。
- 明确各阶段的输入、输出、唯一决策 owner 和交接边界，不新增 handoff schema 或第二套工作流。
- 让 Analyze 结合用户提供的文档、接口、设计和代码完成目标与需求澄清。
- 保留 Analyze 的需求完整性评分；将 Design 主观双评分改为 `Ready / Needs decision + 证据`。
- 保留 KB 的初始化、渐进物化、读取、保留和同步职责，并与 Protocol / writer 生命周期职责分开。
- 由 Design `assets/` 唯一持有方案正文模板；Templates 只保留知识库模板和导航。
- 优化 `SKILL.md`、references、assets、scripts 的职责和渐进披露，重点降低高频入口成本。
- 复用现有 `instruction_surface` 和 HostAdapter，验证 Codex、Claude、Qoder、Copilot 的真实消费路径。
- 精简单文件渲染，排除 Python 源码，同时避免留下不可执行的悬空脚本指令。
- 建立英文 `index.html` 与中文 `zh-CN.html` 的静态推广页，复用同一套页面样式、交互和现有 Sopify 素材。
- 采用“暖白技术手账 + 克制的开发者工具界面”，以安装命令为主动作，GitHub 与文档为次级入口。
- 先完成本地 Demo 与用户视觉/内容审计；GitHub Pages 使用 `evidentloop.github.io/sopify` 和 `main / root` 作为目标发布形态，但实际启用必须单独授权。
- 用版本化行为场景、结构测试、全量回归和 EvidentLoop 完成验收。
- 在两个方案都进入 main 后，完成一次统一 Sopify release，并单独收口 finalize 产生的归档变更。

## Approach

- 执行顺序固定为“先建立基线并审计 owner，再改规则”：没有可复现行为缺口或权威契约冲突，不进入修改清单。
- Managed plan 按正式 Protocol 进入；Analyze 形成目标与证据，Design 选择最小充分方案，Develop 实施并验证，KB 按 `knowledge_sync` 管理长期知识，Templates 只提供知识库文档结构。
- Analyze 先读取与任务有关、用户提供或当前可访问的证据，再区分目标、交付物和候选路径；候选路径不自动成为成功标准。输出先给结论，再给必要证据。
- 只有答案会改变目标、交付物、范围边界、成功标准，或导致当前路径无法安全落地时才追问。影响当前交付的冲突才进入推荐；小口径差异不阻塞，也不新建 defer 状态。
- Design 消费 Analyze 的目标和边界，先核对项目现有实现、正式契约、适用的原生能力与已安装依赖，再决定是否新增；以正确性、兼容性和用户价值为前提选择最小充分路径，不把固定技术梯子当答案。
- Develop 先核对批准方案与代码事实。Bug 或共享边界变更要检查受影响调用方，在最窄共同根因处修复并验证同类路径；批准范围内的实现裁量就地完成，只有新事实会改变范围、方案路径或验收标准时才重新规划。Quick Fix 没有 Design 产物时，Develop 只做完成当前请求所需的局部选择，不补建方案或复制 Design 全套规则。
- 新增或强化判断、写作类 prompt 规则，必须对应本地可复现行为缺口，并在同一场景中产生可观察改善且无关键回退；否则不保留。协议、安全、授权等硬约束可由权威契约冲突驱动，但仍需结构或回归验证。
- 中文重点处理翻译腔、口号化短句、名词和括号堆叠；英文重点处理名词堆叠、企业套话和伪口语。两种语言共享事实与边界，但不逐句翻译，也不故意模仿人格或不完整表达。
- 高频 `SKILL.md` 只保留阶段职责、执行骨架、资源导航和边界；长规则进入 references，模板进入 assets，确定性 helper 留在 scripts。是否拆分由真实入口负担决定。
- 固定 4–6 个版本化行为场景，覆盖 managed plan 交接和直接入口，保存输入、证据、语言、消费面、期望行为和允许写集，不保存标准文案。修改前后使用同一场景和判断标准，不建设评测平台。
- 中英文页面共享结构、样式和素材，文案各自自然表达。U0 通过后只同步受影响的事实与发布元数据，不重做已接受的视觉方向。
- 单文件优化只调整现有渲染选择，并检查 `render_single_file()` 的全部真实调用方。脚本存在时可执行确定性逻辑；脚本未随单文件分发时，保留可执行的等价规则，不引入 manifest、注册表或第二套宿主模型。
- Required `knowledge_sync` 在交付候选形成前完成；release 后由显式 `~go finalize` 收口，归档变更再等待独立 Git 交付授权。
- README 只在公开承诺、命令或示例因本方案失真时做最小更新。

## Waves / Steps

0. 先建立本地中英文推广页 Demo，验证风格与内容，并在 U0 等待用户裁定。
1. 建立行为基线，先审计工作流 owner，再收口中英文表达、交接和 Design readiness 契约。
2. 按真实使用优先级优化五个 Skill，收口阶段判断和渐进披露。
3. 同步宿主输出与真实安装面，精简 Copilot 单文件渲染。
4. 完成行为对比、仓库回归和首次 EvidentLoop 审计，在 U1 等待用户裁定。
5. 裁定闭环后形成交付候选，统一发布 Sopify；经单独授权启用 GitHub Pages，并显式 finalize 和单独交付归档变更。

## Key Decisions

- 方案级别为 standard，只包含 `plan.md + tasks.md`；不创建 `design.md`、ADR 或 diagrams。
- Skill 虽可被宿主单独消费，仍是 Sopify 工作流能力；保留阶段特有判断和唯一 owner，不设计五套自治流程。
- Consult、Quick Fix 和单 Skill 入口继续由宿主路由；直接入口只完成本入口职责，不补演被跳过阶段。
- Ponytail 只贡献四个原则：充分理解后再最小化、先查现有与权威实现、Bug/共享边界检查调用方并修共同根因、无可复现改善则不新增 prompt 规则。
- 运行次数只用于确定审计优先级，不进入运行时路由、评分或永久 KPI。
- 本方案不修改宿主的意图识别，不新增 `read_only_review`、触发词正则或状态模型；Analyze 做目标澄清，宿主负责授权判断。
- Design `Ready` 表示没有会改变实现范围、方案路径或验收标准的未决用户选择；否则为 `Needs decision`，并给出选项、影响和推荐。动态版本与不可逆操作授权属于执行期 checkpoint，不自动降低 readiness。
- 仅当用户或方案明确接受真实、非阻塞的工程限制时，才在现有决策位置记录上限和有意义的重访条件；影响当前正确性、安全、授权或验收的限制必须阻塞，不能靠注释放行。
- 必要注释只解释代码现场必须知道的非显然意图、约束或风险，不复述代码，不新增 `ponytail:` 标记或债务台账。
- 行为验证使用版本化 scenario set 和 rubric，不使用固定文案 golden、逐句 snapshot、AI 味评分器或词语黑名单。
- Design `assets/` 是方案正文模板唯一来源；Templates 只管理知识库模板和导航；KB 管理知识政策，Protocol / writer 管理方案生命周期。
- 现有四个宿主验证真实安装和消费路径；后续官方适配器只需继续从 canonical instruction surface 渲染，不预设专用规则。
- U0 已接受中英文页面的结构、字体、工作流图和素材分工；后续产品审计只把现有接续区局部重写为产品形态说明，不新增首页区块或图片。
- P1 已按 `sha256:d17ccd6c1a4537967b6a745612da9ee2950146bd5ef60efad81e2ffd98471f6a` 获批；首次报告已在 U1 停车并完成用户裁定。用户随后批准最终实质 diff 审计、本地收口、commit，并在验证通过后推送当前分支。
- Scoped staging 必须保全既有 index，只加入本方案允许写集；任一文件无法安全隔离时立即停车，不 commit。
- Blocking finding 必须修改、重验并重新审计；non-blocking concern 只有经用户明确接受才可保留。最终 `verify_NNN` receipt 在 4.4 完成，不包含在首次 U1 停车前。
- 推广页采用原创的 Sopify 暖白技术手账视觉；外部项目只作批判参考。`codebase-to-course` 未见明确许可证，因此不得复制其 CSS / HTML；`fireworks-design` 和 `fireworks-tech-graph` 也不作为运行时或构建依赖。
- Wave 0 保留手绘封面作为 Hero；workflow 图承担主要流程解释，现有架构图同时承担产品形态说明和技术细节入口。Product Form 中英文 SVG 保持原路径、只在 README 使用，保留 Host、Skill、Assets、Handoff、Archive 五个组成，仅校正事实并统一双语。页面图使用白色技术卡片承载，与暖白网格背景形成有意层级，不通过裁切或固定高度伪造同色背景。
- 页面展示型 H1 / H2 不使用末尾句号；中文字体、字号和断行按短语调整，避免把“可追溯”“阶段”“未知项”等语义单元拆开。该规则只服务页面排版，不进入通用写作协议。
- Sopify 首页的 EvidentLoop “了解详情”指向 `https://evidentloop.github.io/evidentloop/` 产品页；GitHub 仓库继续作为源码入口，不混成同一个动作。
- 本方案本地 commit 与当前分支 push 已单独授权。PR、merge、tag、GitHub Release、Pages 启用和 finalize 后归档交付仍需对应阶段的单独授权；Pages 目标为 `main / root` 和 `https://evidentloop.github.io/sopify/`。
- 最终只发布一个 Sopify release；版本在发布检查点动态确定，本方案不修改或发布 EvidentLoop。

## Constraints / Not-in-scope

- 不安装、复制或依赖 Humanizer、Ponytail、Superpowers 或其他外部 Skill。
- 不新增 AI 味检测器、写作评分器、critic Skill、通用 checklist 引擎、评测平台或新的工作流层。
- 不新增前端框架、CSS 框架、构建链、CMS、多语言运行时、主题切换、设计生成流水线或视觉回归平台。
- 不复制外部页面源码，不把参考项目的品牌、深色终端风、课程导航、复杂动画、赞助、定价、虚构指标或客户证言带入 Sopify。
- 不为 Demo 新生成 logo、插画、架构图或动效；workflow 图只按当前协议原路径重画，不扩成第二张架构图；Product Form 只在原路径校正现有五段表达，不进入首页；除两张本地化 Open Graph 派生图外，其他素材复用仓库现有内容。
- 不移植 Ponytail 的人格、常驻开关、强度模式、绝对 `stdlib/platform/dependency` 梯子、one-liner、最少文件、净删行指标、固定输出格式或独立 review/audit 模式。
- 不用 LOC、文件数、内容更短或删除量代替正确性、用户价值、协议、安全和验证证据。
- 不使用触发词正则、固定句子或精确文案 snapshot 判断用户意图和语言质量。
- 不强制所有请求经过完整主线；也不让单 Skill 入口复制整条工作流或其他阶段规则。
- 不为了更短而删除安全边界、协议入口、验证证据、必要注释或技术术语。
- 不把所有材料差异写成 deferred debt，也不新增冲突、上限或技术债台账。
- 不要求五个 Skill 全部改动，不以文件数、规则数或内容增量衡量优化。
- 不全量重写 README、docs、历史方案或 dormant blueprint。
- 不重开上一个方案已完成的 finalize、active plan 入口或 `host_support` 收口。
- 不在本方案发布 EvidentLoop；除已授权的本地 commit 与当前分支 push 外，不执行其他 Git 交付或外部发布动作。

## Status / Progress

- [x] 用户确认中英文表达、五个 Skill 的工作流分工和 Analyze 的证据驱动目标澄清方向。
- [x] 用户确认只吸收有本地证据的最小原则，不新增意图路由、评测平台或外部 Skill 依赖。
- [x] 用户确认推广页的暖白技术手账方向、中英文入口、Pages 目标和独立发布授权边界。
- [x] 用户确认 P1 到首次 EvidentLoop 报告为止，真实 finding 修改重审，Git 交付、release 与 finalize 分别授权。
- [x] Checkpoint P0（用户动作）：用户已批准只执行 Wave 0 本地 Demo，并要求不过度设计、完成后停在 U0。
- [x] Checkpoint U0（用户动作）：用户已接受当前 Demo、字体与内容方向，并确认可以先按现状收口。
- [x] Checkpoint P1（用户动作）：用户已批准本地执行 Wave 1–4.3，并要求不过度设计、整体收口及独立角色复核；旧版本的 P1 批准不自动继承。
- [x] Checkpoint U1（用户动作）：用户已接受两个 Analyze finding 的最小修复，确认推广页保持同包、Copilot 体积只做上界回归，并批准方案内正式审计和本地 Git 收口。
- [x] Wave 0 本地中英文 Demo 与产品形态表达跟进已实施并完成定向验证；未 commit、push 或启用 Pages。
- [x] Wave 1–4.3 本地实施、独立复验和用户裁定已完成。
- [x] Wave 4.4 正式报告和修复验证已关联；模型原结论保留，未重复发起语义审查。
- [x] Wave 5.1 经审计的本地交付候选已形成，Git 交付只按已授权的 commit / 当前分支 push 执行。
- [ ] Wave 5 Git 交付、统一发布、Pages 和归档完成。

## Next

完成当前分支 commit / push 后停车。未经后续授权，不创建 PR、不合并、不发布、不启用 GitHub Pages，也不 finalize。
