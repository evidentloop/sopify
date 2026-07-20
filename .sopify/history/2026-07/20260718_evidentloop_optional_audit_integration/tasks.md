# 任务清单: EvidentLoop 可选方案审计接入与 CrossReview 收口

目录: `.sopify/plan/20260718_evidentloop_optional_audit_integration/`

## Wave 1 | 方案入口与版本契约

- [x] 1.1 对齐 `skills/{zh,en}/header.md.template`、design Skill、templates Skill 和分级脚本：方案级别统一为 `light / standard / architecture`，所有级别都有 `plan.md`；standard 增加 `tasks.md`，architecture 再增加 `design.md`。
  - 验收：不再生成缺少 `plan.md` 的 managed plan；不再把 plan 级 `background.md`、空 receipts/assets/ADR/diagram 当作必备文件。
- [x] 1.2 在现有 Sopify 代码中实现一个确定性的 `plan_version` 计算并复用到 writer、`workspace_status_lite`、protocol check 和入口预检语义。
  - 验收：先按 level 精确校验语义文件集合，再按固定顺序包含 `plan.md`、该级别的 `tasks.md`、`design.md`；路径与原始字节共同参与计算，输出值携带算法前缀。
  - 验收：writer 写 plan receipt 时把版本固定写到 `provenance.plan_version`，可选 `expected_plan_version` 冲突或结构无效时拒绝；lite status 以 `valid/error/version` 客观事实表达无效结构，不输出工作流结论或整体报错。
  - 验收：`tasks.md` 或 `design.md` 的真实变化会改变 `plan_version`；audits、receipts、assets 和 state 变化不会改变它。
  - 验收：现有 `finalize_plan` 在最终版本校验后写 final/history receipt 并迁移方案目录，只在归档成功后清 active plan/handoff；冲突或失败时保留源方案与 state，不新增 finalize 入口。
- [x] 1.3 增加最小防漂移测试，覆盖中英文 header、design/templates 资产、分级脚本、安装产物、plan 结构和版本计算；历史归档不参与迁移或重算。

## Wave 2 | CrossReview 退场与当前真相

- [x] 2.1 删除 `.agents/skills/cross-review/` 和中英文 develop rules 中默认 `post_develop` CrossReview advisory 钩子；不创建仓库内 EvidentLoop Skill 副本，也不增加新的默认钩子。
- [x] 2.2 删除 `.sopify/plan/20260418_cross_review_engine/` 全部文件；不移动到 history，不移植 bridge、checkpoint mapping、`review.md`、handoff 字段或通用 rubric 设想。
- [x] 2.3 更新 `.sopify/blueprint/{background,design,tasks,protocol}.md`、相关当前 ADR/registry、中英文公开说明与宿主资产：当前能力收口为通用 Verifier + EvidentLoop 可选实例。
  - 验收：entry-preflight 保持“先判意图再接续”；`plan.md` 仍是统一入口，方案并行推进和正式审计统一比较 `plan_version`。
  - 验收：Verifier 只读并返回证据；宿主通过 writer 写 receipt。`audits/` 不进入 active plan/handoff 或 4 步默认读取链。
  - 验收：仅 Sopify、其他验证器、独立安装 EvidentLoop、`--with-evidentloop` 四种形态均有明确说明；安装来源不进入 runtime 判断或 receipt。
  - 验收：CrossReview 只允许保留在 history、历史 ADR 说明和 Git 历史中，不把旧编号改写成 EvidentLoop 新契约。
- [x] 2.4 收口 Wave 1–2 审计问题：统一校验公共 writer 的 `plan_id` 与归档月份，finalize checker 拒绝残留 state 并复核新格式归档的 `plan_version`；同时澄清语义 reviewer 只读与宿主执行官方受限审计命令的边界。
  - 验收：只覆盖路径逃逸、残留 state、归档后语义文件变化三个主负路径；旧历史不迁移、不复算，不增加通用路径框架或新的权限系统。

## Wave 3 | EvidentLoop 通用版本能力

- [x] 3.1 在 EvidentLoop 独立仓库重新核对 main、用户改动和公开版本状态，按其独立生命周期建立最小方案；范围仅为通用 `diff_version / report_version`，不包含任何 Sopify 名称或 plan 语义。
- [x] 3.2 复用 EvidentLoop 已有确定性哈希，在正式 `audit.json` 的 namespaced extension 和 `finalize / revise` 结构化结果中提供通用版本值；同步 API、CLI、Skill、数据模型和定向测试。
  - 验收：`diff_version` 唯一对应本次实际 Git diff；`report_version` 唯一对应正式 `audit.json` 字节；正式 HTML 继续校验与 JSON 的 graph/run identity 一致，不单设版本字段。
  - 验收：新报告 finalize 返回非空两版本；带版本报告 revise 原样继承 `diff_version`；legacy schema `0.4` 报告缺失时仍可 revise，并明确返回 `diff_version: null`，不得猜测。
  - 验收：覆盖 legacy `0.4`、连续两轮 revise、copy、in-place、recovery 和 Skill 校验路径。
  - 验收：不升级 code-diff schema 版本，不迁移已发布字段，不增加 plan profile、宿主 adapter、模型 SDK、provider 配置或集成注册表。
- [x] 3.3 完成 EvidentLoop 定向与全量验证后，在 tag/PyPI/GitHub Release 前停车请求用户发布授权；获授权后发布 `v0.1.0a2`，并核对 package、schema、prompt、Release metadata 和 evidence asset 状态。
  - 证据：[Publish run](https://github.com/evidentloop/evidentloop/actions/runs/29678876261) 成功；[PyPI](https://pypi.org/project/evidentloop/0.1.0a2/) 包含未撤回的 wheel 与 sdist；[GitHub prerelease](https://github.com/evidentloop/evidentloop/releases/tag/v0.1.0a2) 为非草稿，schema `0.4`、prompt `v0.5` 未变，Release 无额外 assets 不阻断。

## Wave 4 | 多宿主可选配套安装

- [x] 4.0 收口当前分发契约的三处既有漂移，不重开 Wave 1–2，也不引入新状态或宿主框架。
  - 验收：中英文 header 与 develop Skill/rules 统一为“develop 完成后更新 `plan.md` 的 `ready_to_archive` 生命周期元数据并保留在 `plan/`；只有显式 `~go finalize` 才通过 writer 归档”。
  - 验收：中英文 `$kb/$templates` 使用 `state/active_plan.json → plan/<plan_id>/plan.md`，删除退役的 `current_plan.path + current_plan.files` 口径。
  - 验收：五个内置 Skill 都声明 `codex / claude / qoder / copilot`，同步生成 catalog 和最小防漂移测试；`host_support` 只表示官方适配器可交付并消费 Skill 语义，不替代 `HostCapability` 的能力等级与 E2E 证据。
- [x] 4.1 在现有 Python installer、shell/PowerShell wrapper 和用户文档中增加默认关闭的 `--with-evidentloop`，并在 HostAdapter 明确四个宿主的 Skill 目标：Codex `$HOME/.agents/skills/`、Claude `$HOME/.claude/skills/`、Qoder `$HOME/.qoder/skills/`、Copilot `<workspace>/.github/skills/`。
  - 验收：不带参数时不查找命令、不联网、不安装、不提示；现有核心安装、payload 和 `stdlib_only` 依赖声明不变。带参数时也先完成 Sopify；新宿主缺少映射或 EvidentLoop 未完成时只停止可选分支，不回滚或否定 Sopify。
  - 验收：公开包装器在下载前选择 Python 3.11+；没有兼容解释器时说明检测结果和未发生下载/安装，不静默跳过、不自动安装 Python、不修改用户环境。
- [x] 4.2 用一个 EvidentLoop 专用 helper 安装或复用 CLI 与 Skill，不建立通用组件框架。
  - 验收：新装 CLI 执行官方当前命令 `uv tool install evidentloop`；新装 Skill 执行 `npx skills@latest add evidentloop/evidentloop --skill evidentloop`，不提供版本选择或维护兼容矩阵。
  - 验收：只为缺失组件检查前置命令；CLI 缺失才要求 `uv`，Skill 缺失才要求 Git 和 `npx`。新装 CLI 必须能从 `PATH` 解析到同一文件；不可见时不改 shell，保留已安装 CLI 并给出 `uv tool update-shell`、重启和重跑提示。已有 CLI 通过 doctor 健康检查、已有 Skill 通过顶部 front matter 的 `name: evidentloop` 身份检查后直接复用，均不自动升级；兼容性归 EvidentLoop 自身负责。
  - 验收：四宿主都先在临时 HOME 或临时项目完成 Skill 安装与校验，再原子复制到最终目录；失败不留下未验证目标目录，可直接重跑或独立安装。Copilot 不写项目 `.agents/skills/` 或 `skills-lock.json`，也不自动提交或更新用户项目内容。仅子进程关闭匿名遥测。
  - 验收：不写 `evidentloop_enabled`、安装来源、component registry 或 state；不自动升级、降级、覆盖或卸载。
- [x] 4.3 用精简测试和隔离安装证据验证四宿主路径、官方当前命令、Skill 临时安装与原子复制、Copilot 定向复制、默认关闭、缺映射、按组件前置检查、健康复用、异常停车、失败可重试和单一用户错误提示。
  - 验收：安装/结构证据与 Skill discovery/E2E 结论分开；没有真实宿主证据时不宣称 discovery 已验证。Copilot 文档明确项目 Skill 与本机 CLI 的云端边界。
  - 证据：266 tests、71 subtests，Python 3.11 硬门禁 97 tests、4 subtests，5 个协议 smoke、payload smoke 与增量 Ruff 通过；来源、Copilot 项目归属和“Sopify 先完成、EvidentLoop 失败可重试或独立安装”的承诺已最小收窄，无外部错误诊断框架。

## Wave 5 | 验证冻结与公开版本真实 Dogfood

- [x] 5.1 在隔离 HOME 中用冻结的 Sopify release candidate 安装入口和 `--with-evidentloop` 完成 Codex 配套安装；在不读取或输出凭据的前提下核对 `evidentloop doctor --json` 返回的实际版本、package resources 和 Skill 文件，再用不继承当前讨论的新宿主会话证明真实 Skill discovery。
  - 证据：全新隔离 HOME 下同一入口返回成功，CLI 与 Skill 均为 `installed`；doctor 返回 `status=ok`、实际版本 `0.1.0a2`、4 个 package resources 可读；Codex `debug prompt-input` 在不调用模型的 fresh 上下文中列出隔离路径 `.agents/skills/evidentloop/SKILL.md`。
- [x] 5.2 完成 plan 契约、版本计算、installer/skill 分发、writer/lite status、protocol check、EvidentLoop 消费路径的定向测试，以及全量 `python3 -m pytest tests -v`、`git diff --check`、版本/链接一致性、CrossReview 当前层残留和 history 未改写检查；修复本方案问题，并完成 `project.md`、blueprint/protocol 和方案语义同步。
  - 验收：所有可能改变实现或契约的动作在审计前结束；区分本方案失败与无关基线问题。
  - 证据：初次审计 finding 最小修复后，172 tests、46 subtests 定向验证与 266 tests、71 subtests 全量回归通过；Python 3.11 release preflight 的 97 tests、4 subtests、5 个协议 smoke、payload smoke、golden snapshot、catalog drift、链接和版本一致性检查全部通过；隔离 HOME 中的当前官方 Skill 通过新身份检查并真实复用，当前层无 CrossReview/退役兼容面残留，history 与 tracked state 无差异。
- [x] 5.3 冻结只属于本方案的“实现与契约 staged diff”和当前 `plan_version`，在 Git 忽略的 `reports/` 下完成 `prepare → host review → finalize`，随后停车并把初次报告交给用户裁定。
  - 审计主体包含实现、测试、Skill/模板、当前 blueprint/protocol 和方案语义；排除 `audits/**`、`receipts/**`、报告临时目录及 finalize 的纯状态/归档差异。
  - Checkpoint U1（用户动作，不由宿主勾选）：用户查看初次报告并提交裁定/反馈；宿主不得自动代替。
  - 证据：替代报告覆盖冻结 staged diff 的 16/16 文件；用户正式裁定唯一 finding 为误报，确定性修订后结论为 `complete / pass_candidate`、风险 0、开放问题 0。
- [x] 5.4 收到用户裁定后继续：若要求修改审计主体，回到 5.2 并生成新报告；若提交会改变报告裁定的有效反馈块，只执行确定性 `revise`；若明确接受初始报告且没有有效反馈变化，不调用 `revise`。随后将对应的最终报告附着到 `audits/plan/`、验证可搬移性，并通过 writer 写未占用的 `verify_NNN` receipt。
  - receipt 顶层 `verdict` 保存结论，`provenance.plan_version` 绑定冻结方案；evidence 保存 `source`、package/schema/prompt 版本、run ID、review status、`diff_version`、`report_version` 和 `audit_path`。
  - 验收：报告附着和 receipt 写入不改变 `plan_version`；active pointer 与 handoff 保持符合预期；`pass_candidate` 不解释为用户授权。
  - 证据：最终报告已原字节附着到 `audits/plan/`，无工作区绝对路径；writer 已写入 `receipts/verify_001.json`，附着前后 `plan_version` 一致。

## Wave 6 | 残留复核与归档

- [x] 6.1 只读比较冻结快照与当前工作区：确认新增差异仅为最终报告、receipt 和 finalize 所需的机械状态/归档变化；若实现、测试、Skill、blueprint/protocol 或方案目标、范围、方法、任务要求变化，废弃旧审计并回到 5.2。
- [x] 6.2 再次确认没有 CrossReview 当前入口、旧方案、默认触发、兼容别名、bridge、新 state/tool/schema、验证器注册表、安装 component framework、自动升级或报告索引，且 `.sopify/history/**` 旧正文未被改写；该步骤只读，不再引入修复。
- [x] 6.3 完成所有任务和方案生命周期的 `ready_to_archive` 状态更新，确认语义文件不再变化并计算最终 `plan_version`。
  - Finalize action（writer 机械动作，不是第二个任务）：以最终版本作为 `expected_plan_version` 写 `final.json` 和 `receipt.md`，将完整方案迁入未占用的 `history/2026-07/`，成功后才清 active plan/handoff；宿主随后更新可重建的 history index。
  - 验收：归档包复算版本等于 `final.json.provenance.plan_version`；final/history receipt 写入、目标冲突或迁移失败均保留源方案和 state。history index 失败需告警和单独重试，但不回滚已完成归档。

## 验收标准

- [x] light、standard、architecture 三种方案都能从 `plan.md` 进入，生成器与 entry-preflight 不再互相矛盾。
- [x] `plan_version` 是唯一方案版本名称，并覆盖当前级别的全部语义文件；用户面不再混用 digest、fingerprint、package hash 等术语。
- [x] EvidentLoop 对所有消费者提供通用 `diff_version / report_version`，公共契约不包含 Sopify 专用字段。
- [x] Sopify 当前执行面不再包含 CrossReview，也不提供兼容层或默认 EvidentLoop 钩子。
- [x] 未选择配套安装时 Sopify 核心安装与工作流完全不依赖 EvidentLoop；选择后可一次补齐目标宿主所需公开 CLI 与 Skill。
- [x] Codex 完成真实安装、Skill discovery 和审计 E2E dogfood；其他宿主只声明实际取得的安装/结构证据，不被错误标记为 Codex-only 或 E2E 已验证。
- [x] 已独立安装的健康 EvidentLoop 可直接使用；兼容性由其产品自身负责；其他验证器可写通用 evidence/receipt，不被 ELoop 字段或目录约束。
- [x] 配套安装不保存运行开关、不管理已有安装升级；官方当前安装、健康复用、异常停车和失败可重试边界可验证。
- [x] 独立审计、`audits/plan/` 主审计和 `audits/<scope>/` 附加审计边界清楚，只有正式方案证据写 receipt。
- [x] 本方案产出一份由公开 EvidentLoop 版本生成、经过显式用户裁定、可搬移且由 receipt 关联三个版本值的主审计报告；审计主体不包含报告自身、receipt 或机械归档差异。
- [x] 未新增命令、MCP tool、state、schema、handoff 字段、报告索引、聚合或自动门禁。
- [x] 历史事实保持不变；旧 CrossReview deferred 方案的删除和替代由本方案及最终 receipt 可追溯。
