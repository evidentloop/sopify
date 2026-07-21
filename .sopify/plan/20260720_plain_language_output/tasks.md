# 任务清单: Sopify 清晰表达、高频 Skill 与推广页优化

目录: `.sopify/plan/20260720_plain_language_output/`

## Wave 0 | GitHub Pages Demo 与风格定稿

- [x] Checkpoint P0（用户动作）：用户已批准只执行 Wave 0 本地推广页 Demo，并要求不过度设计、完成后停在 U0。
- [x] 0.1 冻结 Demo 内容和参考边界。
  - 动作：从当前中英文 README、正式协议和现有公开素材提炼页面 brief，固定 Hero、核心问题、三个价值点、工作流、跨宿主恢复、安装、可选 EvidentLoop、FAQ 与 GitHub / 文档入口；以安装命令为主动作。
  - 验收：所有产品、宿主、安装和流程声明都能指向当前仓库事实；英文与中文各自自然表达，不逐句翻译；EvidentLoop 只作可选说明，不进入 Hero；不出现星数、性能、客户、定价、赞助或无法证明的领先声明。
  - 验收：页面结构只参考 `fireworks-tech-graph`，暖白编辑式原则只参考 `codebase-to-course`，开发者交互只参考 `fireworks-design` 的 OSS CLI 示例；不复制外部源码，不安装或运行外部设计工作流。
- [x] 0.2 创建本地中英文静态 Demo。
  - 动作：创建英文 `index.html`、中文 `zh-CN.html` 和最小共享页面样式 / 交互；采用暖白技术手账视觉，复用现有 logo、封面和架构图；按当前正式协议和最新 Fireworks 几何契约原路径重画中英文 workflow 图。
  - 验收：两页共用结构、CSS、交互和素材，语言入口互相可达；正文使用清晰字体，命令使用等宽字体，手绘封面只作 Hero；workflow 图承担主要流程解释，架构图作为唯一产品结构图和技术入口；复制按钮之外不增加必要性不足的交互。
  - 验收：中文展示标题不使用末尾句号，字体、字号和短语断行在桌面与手机宽度均自然；所有图片保持原始比例，白色技术卡片与暖白网格背景形成有意层级，不靠裁切或固定高度伪装同色背景。
  - 验收：不使用 React、Vue、Vite、Tailwind、外部设计运行时、CMS、多语言运行时、主题切换或新构建链；不新生成 logo、插画、架构图或动效，不新增第二张 Hero；页面只在本地可预览，不启用 Pages、不 commit、不 push。
- [x] 0.3 验证 Demo 并在 U0 停车。
  - 动作：在桌面与手机视口检查完整页面，验证键盘操作、复制命令、`prefers-reduced-motion`、中英文链接、本地素材、安装 / GitHub / 文档链接、无控制台错误和 `git diff --check`。
  - 验收：提供可直接打开的中英文 Demo 和临时桌面 / 手机截图供用户审计；不把截图、探索稿或外部项目副本纳入仓库；不建设视觉回归平台，不用 Lighthouse 分数代替内容与视觉判断。
  - Checkpoint U0（用户动作，已通过）：用户已接受当前中英文 Demo、字体、内容、工作流图和素材分工；后续只同步经验证的公开事实，不重新开启视觉方案选择。
- [x] 0.4 收口产品形态表达。
  - 动作：把现有中英文接续区局部重写为产品形态与接续说明；在原路径校正两张 Product Form SVG，并同步 README、长期蓝图和既有结构测试。
  - 验收：首页不新增区块或 Product Form 图，现有架构图继续作为唯一产品结构图；两张 SVG 路径不变，只在 README 使用，保留 Host、Skill、Assets、Handoff、Archive 五个组成；中英文事实一致且无过强承诺，不新增前端平台、动效或第二张架构图。

Checkpoint P1（用户动作，已通过）：用户已批准本地执行 Wave 1–4.3，并要求不过度设计、整体收口及独立角色复核；旧 `plan_version` 的 P1 批准不自动继承。

## Wave 1 | 行为证据与工作流契约

- [x] 1.1 建立当前行为基线和场景集。
  - 动作：检查现行中英文方案、Analyze、Design、Develop、KB 和咨询输出；建立 4–6 个版本化行为场景，覆盖用户材料输入、目标交接、方案取舍、Bug 共同根因、实施收口、知识写回、直接入口和双语表达，并记录 Copilot 单文件字符、字节和行数。
  - 验收：场景包含 `scenario_id`、语言、消费面、输入与证据、期望行为、允许写集和源 revision；同一场景可观察工作流交接或直接入口结果；直接入口至少包含中英文语义等价的“只分析、不修改、等待确认”样例，沿用既有 `consult_readonly`，不新增意图类型、关键词 / 正则、route 或 state；该样例允许写集为空，执行前后代码、方案、state、KB、audit、receipt 和 Git index 不变；输出结论和必要证据，仅在存在时给出阻塞项或待决策项，随后停车；不保存标准文案，不新增评测平台；Analyze 123 / Develop 114 / Design 49 仅作为用户提供的优先级证据。
- [x] 1.2 只读审计五个 Skill 及工作流 owner。
  - 动作：在修改 prompt 前，按 Analyze、Develop、Design、KB、Templates 的真实使用优先级检查中英文入口、references、assets、scripts、共享规则和 header，逐项判断“保留 / 修改 / 无需修改”，并检查重复 owner、交接断点、规则归属和无效披露。
  - 验收：五个 Skill 全覆盖；每个拟修改项能指向 1.1 的可复现缺口或权威契约冲突；审计结果只服务本方案实施，不另建长期审计文档；没有证据的理念不进入修改清单。
- [x] 1.3 最小重写共享写作规则。
  - 动作：基于 1.1–1.2 的证据最小重写中英文 `shared-writing-dna.md`，只保留跨入口必要的表达原则，并分别处理中文和英文的自然表达。
  - 验收：结论顺序、事实与推断、具体主语和动作、术语、引用与套话都有可执行边界；中英文不是逐句翻译；不引入人格模仿、AI 味指标或机械句式规则。
- [x] 1.4 更新输出、交接与 readiness 契约。
  - 动作：基于 1.1–1.2 的证据更新中英文 `output-contract.md`、Design rules 和输出资产，区分内部证据处理与用户输出顺序，明确阶段输入、输出和唯一 owner，将 Design summary 改为 `Ready / Needs decision + 证据`，并同步本方案自身表达。
  - 验收：Ready / Needs decision 有明确判据；Analyze 可计算评分与 `require_score` 路由不变；下游消费上游结论且不复制判断；直接入口不模拟被跳过阶段；不新增 schema、state 或路由。

## Wave 2 | 工作流分工与高频 Skill

- [x] 2.1 强化 Analyze 的目标、证据与交接。
  - 动作：更新 Analyze rules 和必要输出资产，使其先整合与任务有关、由用户提供或当前可访问的证据，例如文档、接口资料、设计稿、代码与历史方案；再区分用户目标、本次交付物和候选实现路径，并把足以供 Design 决策的边界与未知项交接下去。
  - 验收：仅当答案会改变目标、交付物、范围边界、成功标准或安全可行性时追问；影响交付的冲突给出依据、影响和推荐；Analyze 不替 Design 选择实现，也不新增宿主意图路由或触发词匹配。
- [x] 2.2 强化 Design 与 Develop 的唯一判断职责。
  - 动作：Design 在目标明确后检查项目现有实现、正式契约、适用的原生能力和已安装依赖，再说明取舍、非目标与最小充分路径；Develop 对 Bug 或共享边界核对真实调用方，在最窄共同根因处实施并验证同类路径。
  - 验收：Design 不套用绝对技术梯子，以 readiness 证据证明收敛；Develop 不静默扩范围，批准边界内保留实现裁量，只有事实改变范围、方案路径或验收标准时才重新规划；Quick Fix 只做必要局部选择；正确性、安全、授权和验证不因追求更短而降级。
- [x] 2.3 收口 KB、Templates、入口密度和所有权。
  - 动作：保持 Analyze、Design、Develop 的 `SKILL.md` 只含阶段职责、核心判断、骨架、导航和边界；根据证据精简或拆分 KB；保留 KB 的初始化、渐进物化、读取、长期保留和 `knowledge_sync` 政策；将方案模板唯一保留在 Design `assets/`，Templates 只保留知识库文档结构和导航。
  - 验收：KB 不替阶段决策、不直接管理 plan 生命周期、不写一次性细节或重复正文；Protocol / writer 继续唯一管理 active plan、receipt 和 finalize；Templates 不持有业务政策；入口不重复 header 协议；KB 不为目录对称拆分；Light、Standard、Architecture 文件契约保持不变；总内容不因优化机械增长。

## Wave 3 | 宿主输出与单文件渲染

- [x] 3.1 同步 header 与宿主回复契约。
  - 动作：同步中英文 Design readiness、阶段摘要、工作流交接、直接入口和表达规则；将“builtin Skill 不支持独立调用”的过窄表述收口为“由宿主消费，也可按请求直接路由单个 Skill”；删除不承担入口职责的重复内容。
  - 验收：品牌、配置、既有意图入口、4 步协议、footer、风险停车和修改授权保持完整；consult / Quick Fix 不接续无关 active plan；单 Skill 入口不模拟整条工作流；本方案不新增 route、state 或触发词匹配。
- [x] 3.2 精简 Copilot 单文件渲染。
  - 动作：在现有 `render_single_file()` 中停止内联 Python 源码，检查其 payload、bootstrap 等全部真实调用方，并调整单文件语义，使脚本未分发时仍可按已内联规则完成等价判断。
  - 验收：中英文产物不含 Python 源码、仓库相对脚本路径和无条件悬空脚本引用；核心判断仍可执行；所有真实调用方通过；渲染顺序确定；无 manifest、注册表或通用裁剪器。
- [x] 3.3 验证四个宿主的真实消费路径。
  - 动作：复核 Codex、Claude、Qoder、Copilot 的实际安装产物、home-scope / single-file 边界和 HostAdapter 行为。
  - 验收：Codex、Claude、Qoder 验证 header + Skill tree，Copilot 验证 managed single-file；Qoder 至少有真实安装 smoke；直接 Skill 入口仍复用共同契约；不使用合成单文件结果替代 home-scope 验证，不新增宿主特判。
- [x] 3.4 同步经验证的最终推广页事实。
  - 动作：在 Wave 1–3 的产品与表达变化稳定后，对照最终中英文 README、安装命令、宿主支持与正式契约，只同步 Demo 中受影响的事实、链接和自然语言表达；为最终发布增加 `.nojekyll`，并从现有封面派生两张 `1200×630` 的本地化 Open Graph 分享图。
  - 验收：保留 U0 已接受的结构、暖白技术手账风格和素材分工，不借事实同步重做页面；中英文语义一致但不逐句翻译；canonical、hreflang、Open Graph 与 `main / root` 入口完整；没有不再成立的能力、版本、安装或发布声明。

## Wave 4 | 行为验证与 EvidentLoop 自用审计

- [x] 4.1 运行修改前后行为对比。
  - 动作：用 1.1 的同一场景和 rubric 复跑中英文代表性行为，按整条 managed plan 交接和直接入口记录实际结果与人工判断，并增加最小稳定语义测试。
  - 验收：比较目标理解、交接质量、取舍收敛、根因位置、范围纪律、知识去重、语言清晰度和允许写集；判断/写作类规则未产生可观察改善或出现关键回退时不保留；不比较逐字输出，不以更短替代正确，不用已知答案污染独立验证。
- [x] 4.2 完成仓库验证和 required knowledge sync。
  - 动作：运行相关定向测试、全量测试、`git diff --check`、链接 / 版本一致性、中英文安装产物测量和推广页桌面 / 手机验证；完成 `knowledge_sync.required` 项并复核 `review` 项。
  - 验收：区分本方案失败与无关基线；3.3 已承担四宿主真实消费验证，4.2 不重复建设第二套宿主测试；推广页验证复用 Wave 0 的静态检查和浏览器流程，不新增前端测试平台；前后体积数据只作为回退信号，不替代语义验收；交付候选前不存在未完成 required sync。
- [x] 4.3 冻结 scoped diff，生成首次 EvidentLoop 报告并停车。
  - 动作：先记录并保护既有 index 状态，只将本方案允许写集加入审计主体；若与既有 staged / unstaged 状态无法安全隔离则停车。随后使用已发布兼容 EvidentLoop 执行 `prepare → host review → finalize`，不 commit。
  - 验收：审计主体包含实现、测试、Skill、模板、宿主资产、推广页、共享页面资产和当前方案语义；暂存前记录显式允许路径和既有 index，原有已暂存路径与内容保持不变，新增暂存只来自允许路径；任一目标文件的 staged / unstaged 内容无法安全隔离时立即停车，不自动改写既有 index；排除 `audits/**`、`receipts/**`、临时截图、临时报告和纯 finalize 差异；首次报告生成后不写 `verify_NNN` receipt。
  - Checkpoint U1（用户动作，已通过）：用户接受两个 Analyze finding 的最小修复，确认推广页保持同包、Copilot 体积改为上界回归，并批准方案内正式审计和本地 Git 收口。
- [x] 4.4 按用户裁定闭环报告。
  - 动作：复用已完成的正式审计轮次并附着到 `audits/plan/`；模型报告原样保留两个 finding，不手改结论、不重复发起语义审查。修复公开页面的 handoff 持久化表述，并在现有结构测试中解码验证两张 Open Graph JPEG 的真实尺寸。
  - 验收：方案内只保留一组有效 `audit.json` / `audit.html`；两项修复通过定向测试、全量回归和尺寸校验；根目录两组临时报告删除后，通过 writer 写 `verify_NNN` receipt，明确区分报告原结论与修复后验证。

## Wave 5 | 统一 Sopify Release 与归档

- [x] 5.1 形成经审计的交付候选。
  - 动作：Wave 4 闭环且 required knowledge sync 完成后，核对本方案改动、验证、EvidentLoop 证据和工作区状态；记录用户已授权的本地 commit 与当前分支 push 范围。
  - 验收：交付时只暂存本方案允许路径并保护其他工作；commit 与远端分支指向同一 SHA。PR、merge、Pages、release 和 finalize 仍停车，不包含新的 EvidentLoop 发布动作。
- [ ] 5.2 动态确定版本并执行发布授权停车。
  - 动作：运行 release preflight，根据发布时状态确定 Sopify 版本；在 tag、push、GitHub Release 和首次启用 `main / root` GitHub Pages 前分别请求明确授权，获授权后核对元数据、资产、Pages 地址和公开页面。
  - 验收：未获对应授权不执行该发布动作；统一 release 包含上一个方案的四个提交 `7dcd768`、`00db38b`、`d41f4b6`、`ea92482` 和本方案变化；Pages 目标为 `https://evidentloop.github.io/sopify/`，英文与中文入口均可达；不修改或发布 EvidentLoop。
- [ ] 5.3 显式 finalize，并单独交付归档变更。
  - 动作：Sopify release 证据可用后，将方案置为 `ready_to_archive`，由用户显式 `~go finalize`；通过 writer 将最终 `plan_version`、EvidentLoop 证据引用和 Sopify release 结果写入结构化 `receipts/final.json`，`receipt.md` 只保留人类可读 outcome、summary 与 key decisions；随后报告归档 diff 并等待其 commit / push 授权。
  - 验收：finalize 前 required knowledge sync 已完成；归档失败时保留 plan 与 state；history index 可追溯两个方案；未获归档 Git 授权不 commit / push，也不重做已完成 release。

## 总体验收

- [x] 所有 prompt 修改都发生在行为基线与 owner 审计之后，并有可复现缺口或权威契约证据。
- [x] Analyze 能结合用户材料澄清目标、交付物和候选路径，并把足够的边界与证据交给 Design。
- [x] Design、Develop、KB、Templates 各有准确 owner；直接入口可单独完成职责但不复制整条工作流。
- [x] Ponytail 只留下经本地行为证据支持的最小决策原则，无新增人格、模式、技术梯子、critic、runtime 或通用框架。
- [x] 中英文方案和宿主回复直接、具体、自然、可核验，不依赖 AI 味评分、人格模仿或固定文案。
- [x] 四个宿主继续通过真实 instruction surface 消费；Copilot 单文件不含 Python 源码或悬空脚本指令。
- [x] 中英文推广页使用原创暖白技术手账视觉、真实产品事实和现有 Sopify 素材；U0 后只同步受影响事实，不建设前端平台或重做已接受风格。
- [x] P0 只执行本地 Demo 并在 U0 停车；U0 已通过，旧 P1 未继承到新 `plan_version`，用户已重新审计并批准当前 P1。
- [x] P1 已在首次 EvidentLoop 报告后停车并完成 U1 裁定；方案内报告、两项修复验证与 `verify_NNN` 已按用户要求关联，不重复模型审查。
- [ ] 最终只发布一个包含两个方案变化的 Sopify release；GitHub Pages、finalize 证据和归档 Git 交付可追溯且分别授权。
