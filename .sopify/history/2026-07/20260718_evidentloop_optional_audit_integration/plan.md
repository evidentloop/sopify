---
title: EvidentLoop 可选方案审计接入与 CrossReview 收口
plan_id: 20260718_evidentloop_optional_audit_integration
status: completed
lifecycle_state: ready_to_archive
level: architecture
created: 2026-07-18
updated: 2026-07-20
archive_ready: true
knowledge_sync:
  project: review
  background: required
  design: required
  tasks: required
---

# EvidentLoop 可选方案审计接入与 CrossReview 收口

## Plan Snapshot

- **Goal**: 保留 Sopify 产品无关的验证证据能力，以 EvidentLoop 替代当前 CrossReview 集成，并提供不绑定运行时的一次性可选配套安装与公开版本 dogfood。
- **Status**: Wave 1–6 已完成；公开版本安装、Codex Skill discovery、最终审计、用户裁定、正式 receipt 与只读残留复核均已闭环。
- **Next**: 无；方案已进入 `ready_to_archive`，由 `sopify_writer` 执行标准归档。
- **Task**: 21/21。

评分:
- 方案质量: 9/10
- 落地就绪: 10/10

评分理由:
- 优点: 统一复用现有 plan 入口、writer、Verifier 和 EvidentLoop 通用产物，不增加第二套审计协议或兼容层。
- 扣分: EvidentLoop 对误报后历史严重度和评论的展示仍可在其后续版本最小优化，不阻断 Sopify 本方案。

## Context / Why

P8 已删除 runtime registry 和多层状态，以 `active_plan.json → plan.md → handoff → receipts` 作为 managed plan 接续链。上一期 entry-preflight 又把 `plan.md` 是否存在落实为活动方案有效性判据，并用方案版本变化识别审计主体和并行推进。Wave 1 实施前，中英文 header、design Skill、templates 和分级脚本仍可能生成不含 `plan.md` 的 standard/full 方案，形成生产者与消费者契约断裂。

CrossReview 已被独立产品 EvidentLoop 替代，但 Wave 2 实施前，Sopify 当前层仍保留 CrossReview Skill、develop 完成后的默认 advisory 钩子、废弃方案包，以及把 CrossReview 当作当前参考实现的蓝图和协议文案。EvidentLoop 当前公开 code-diff 能力可以被 Sopify 消费，但正式报告尚未用简明、通用的版本字段同时表达“审查了哪份 diff”和“生成了哪版报告”。

本方案不建设审计平台。目标是修复方案入口契约、删除 CrossReview 当前执行面、让 EvidentLoop 只补通用版本能力，再由 Sopify 完成可选安装便利、目录、方案关联、receipt 和 dogfood 适配。Sopify 没有安装任何验证器、使用其他验证器或使用独立安装的 EvidentLoop 时，核心工作流都应成立。

## Scope

- 统一 plan 级别为 `light / standard / architecture`，所有级别以 `plan.md` 为唯一语义入口。
- 用 `plan_version` 表达完整方案版本，并使入口预检、并行推进检查和 receipt 使用同一语义。
- 删除 Sopify 当前 CrossReview Skill、默认钩子、废弃方案和当前文档承诺；历史归档保持不变。
- 在 EvidentLoop 独立仓库补充通用 `diff_version / report_version` 输出，并通过下一公开 Alpha 提供给所有消费者。
- 在进入可选安装前收口当前分发契约：develop 完成态、active plan 读取入口和内置 Skill 的宿主支持声明保持一致。
- 保持 Sopify 默认只提供产品无关的 Verifier evidence 消费；不安装验证器也能完整使用 plan、develop、handoff 和 receipt。
- 为 Sopify 可安装宿主增加显式 `--with-evidentloop` 配套安装：只在用户选择时按 EvidentLoop 官方当前方式安装缺失组件，已有健康组件直接复用且不自动升级；兼容性归 EvidentLoop，自身参数不作为运行能力开关。
- 允许用户直接使用已独立安装的 EvidentLoop 或其他验证组件，不要求经 Sopify 安装，不增加验证器注册表。
- 在 Sopify 定义独立审计、方案主审计和附加审计三种消费方式，不新增默认触发或专用命令。
- 使用公开 EvidentLoop CLI 与官方 Skill 审计本方案冻结后的“实现与契约 diff”，完成人工裁定、报告附着和 receipt 记录。
- 完成定向验证、全量回归、知识同步和标准归档。

## Approach

- `plan.md` 只承担统一入口；`plan_version` 由方案级别对应的语义文件共同计算，派生证据不参与计算。
- 在现有 `sopify_writer`、`workspace_status_lite` 和 protocol check 上复用一个确定性版本计算，不新增 state、registry、manifest 或 MCP tool。
- Verifier 契约保持产品无关。EvidentLoop 只输出通用 diff/report 版本与审计产物，不认识 Sopify 的 plan、receipt 或目录约定。
- `--with-evidentloop` 只是现有安装器的一条显式分支：不带参数时不探测、不访问 EvidentLoop 来源、不安装、不提示 EvidentLoop；带参数时才预检并安装缺失项。
- 安装来源不决定运行资格。用户显式请求 EvidentLoop 时，以当下 CLI doctor 和 Skill discovery 为准；已独立安装的健康版本与配套安装版本走同一消费链，兼容性由 EvidentLoop 自身负责。
- Sopify 负责把 `plan_version / diff_version / report_version / audit_path` 写入正式方案 receipt；独立审计不强制进入 Sopify 证据链。
- CrossReview 当前执行面直接删除，不提供命令别名、配置兼容、bridge、迁移器或本地 EvidentLoop Skill 副本。
- EvidentLoop 通用增强按其独立仓库生命周期实施和发布；Sopify dogfood 只消费公开安装物，不使用源码 checkout 或 editable install。

## Waves / Steps

1. 对齐方案包结构、`plan_version`、入口预检和中英文分发资产。
2. 删除 CrossReview 当前执行面，并收口 Sopify blueprint、protocol 与 ADR 当前真相。
3. 在 EvidentLoop 独立仓库补齐通用 `diff_version / report_version`，经确认后发布下一 Alpha。
4. 先收口当前分发契约漂移，再在现有 Sopify 多宿主安装器中加入 `--with-evidentloop` 最小分支，复用目标宿主映射并验证未选择、官方当前安装、健康复用、异常停车和失败可重试。
5. 先完成全量验证、残留审计和知识同步，再以 Codex 作为首轮真实宿主，用该公开版本与配套安装路径审计最终“实现与契约 diff”；初次报告生成后显式停车等待用户裁定。
6. 用户裁定闭环后附着报告、写 receipt，完成只读残留复核和标准 finalize 归档。

## Key Decisions

- `20260418_cross_review_engine` 直接删除，不迁入 history；原文由 Git 历史保存，替代关系进入本方案和最终 receipt。
- `.sopify/history/**` 不做名称迁移、内容重写或样例重生成；旧字段和旧版本值保持历史事实。
- 方案级别统一为：light 只有 `plan.md`；standard 为 `plan.md + tasks.md`；architecture 为 `plan.md + tasks.md + design.md`。不预建空 receipts、assets、ADR 或 diagrams。
- `plan.md` 是统一入口，`plan_version` 是完整方案版本。底层使用 SHA-256，但字段名和用户文案不暴露算法术语。
- develop 完成后只把 `plan.md` 生命周期元数据更新为 `ready_to_archive` 并保留在 `plan/`；只有显式 `~go finalize` 才通过 writer 归档。该状态不是新的 state 文件或生命周期引擎。
- `plan_version` 先按 level 校验精确文件集合，再按固定顺序读取该级别的 `plan.md / tasks.md / design.md`；排除 `audits/`、`receipts/`、`assets/`、state 和其他派生产物。
- EvidentLoop 通用提供 `diff_version` 与 `report_version`；Sopify 自己计算 `plan_version` 并建立 receipt 关联。EvidentLoop 不增加 `plan_id`、Sopify adapter、receipt 或 plan/design profile。
- Sopify 默认能力是消费通用 `verdict / evidence / source`；EvidentLoop 是官方推荐、可选配套安装的首个验证器，不是默认安装、默认执行或唯一实现。
- `--with-evidentloop` 默认关闭且只提供安装便利，不写 `evidentloop_enabled`、component registry、state 或持久安装来源。未选择时保持现有安装路径和 `stdlib_only` 核心依赖模型。
- Sopify 公开安装入口要求 Python 3.11+；包装器在源码下载前选择第一个兼容解释器，没有时明确停止。它不静默跳过显式配套安装，不自动安装 Python，也不修改用户环境。
- 配套安装复用现有 host adapter，但每个宿主使用自己的接入范围：Codex 为 `$HOME/.agents/skills/evidentloop/`，Claude 为 `$HOME/.claude/skills/evidentloop/`，Qoder 为 `$HOME/.qoder/skills/evidentloop/`，Copilot 为当前项目的 `.github/skills/evidentloop/`。新增宿主没有明确映射时停止，不猜路径。
- CLI 统一作为当前用户的 `uv tool` 安装；新装 CLI 与 Skill 使用 EvidentLoop 当前官方命令。已有 CLI 通过 doctor 健康检查、已有 Skill 通过顶部 front matter 的 `name: evidentloop` 身份检查后直接复用，均不自动升级；Sopify 不维护版本矩阵。Codex、Claude、Qoder 和 Copilot 都先在临时 HOME 或临时项目生成并校验 Skill，再原子复制到最终目录；Copilot 不在项目写 `.agents/skills/` 或 `skills-lock.json`。
- Sopify 核心安装和校验先完成，再按缺失组件检查 EvidentLoop 前置依赖：CLI 已健康时不要求 `uv`，Skill 已存在且结构健康时不要求 Git 和 `npx`。EvidentLoop 安装未完成时不回滚或否定 Sopify，最终 Skill 目录不留未验证内容；用户可重跑或独立安装。已有异常组件保持原样，不自动升级、降级或覆盖。
- Copilot Skill 放在 GitHub 文档支持的项目目录，属于用户项目内容；用户按需审查和提交，Sopify 不自动提交或更新。本机 `uv tool` 不会自动进入云端环境。本方案只承诺本地组件放置、健康检查和 PATH 可见性；Skill discovery 与审计 E2E 仍需宿主证据，云端 CLI 需另行提供。
- Codex 是本方案首轮真实 E2E dogfood 宿主，不是配套安装的唯一宿主。其他宿主必须区分“安装链/结构已验证”和“Skill discovery/审计 E2E 已验证”，不把安装成功宣传为完整可用证据。
- 内置 Skill 的 `host_support` 只表示其语义可由官方适配器交付到对应宿主的支持界面并被消费；它不代表原生 Skill discovery 或 E2E 已验证，能力等级继续由 `HostCapability` 表达。
- 本方案不自动管理 EvidentLoop 后续升级。用户可按 EvidentLoop 官方方式独立升级；升级后的兼容性由 EvidentLoop doctor 与 Skill 自身负责，Sopify 只复用健康组件。
- 用户使用其他验证器时沿用通用 Verifier evidence 与 receipt，不要求 `diff_version / report_version`、EvidentLoop 报告目录或安装参数。
- 独立 EvidentLoop 审计沿用产品默认目录，不绑定 Sopify 方案；方案主审计使用 `audits/plan/` 并必须写 receipt；附加审计使用 `audits/<scope>/`，仅在作为正式方案证据时写 receipt。
- 不使用 `overall`，不新增自动编号器、报告索引、manifest、latest 指针或聚合层；`audits/` 不进入 4 步协议默认读取链。
- EvidentLoop 不进入默认 plan、develop 或 finalize 流程；没有用户显式请求时，Sopify 不提示、安装或执行审计。
- 用户泛指验证但未指定组件且存在多个可用验证器时，宿主只询问一次选择；不新增默认优先级、自动路由或验证器发现注册中心。
- 最终审计主体只包含冻结时的产品实现、测试、Skill/模板、当前 blueprint/protocol 和方案语义，不包含后生成的 `audits/**`、`receipts/**`、报告临时目录或 finalize 的纯状态/归档差异。
- 报告先在 Git 忽略的 `reports/` 中生成；初次报告完成后宿主必须停车，由用户查看并提交裁定。若裁定要求修改审计主体，先改动、重跑验证并重新审计，不能只 revise 旧报告。
- 冻结后只允许报告附着、receipt 写入和 finalize 的机械状态/归档动作；若实现、测试、Skill、blueprint/protocol 或方案的目标、范围、方法、任务要求发生变化，旧审计失效并回到冻结前。
- 下一 EvidentLoop Alpha 的 tag、PyPI 和 GitHub Release 属外部发布动作，执行到发布点时再次请求用户明确授权；未发布前不得把源码验证写成公开版本 dogfood。
- 当前架构关系可用文字完整说明，因此不新增架构图或 ADR；若执行中出现新的跨产品调用关系，再单独评估是否需要一张图。

## Constraints / Not-in-scope

- 不保留 `crossreview` 命令别名、兼容层、迁移器、`bridge.py`、`review.md`、checkpoint 映射或 handoff 专用字段。
- 不新增 `~audit` 命令、MCP tool、state 文件、运行注册表、报告平台、自动质量门禁或默认 post-develop 审计。
- 不建设通用 installer component framework、依赖解析器、版本范围求解、自动升级、自动降级、卸载或跨安装器迁移。
- 不因本轮只在 Codex 完成真实 dogfood 就把配套安装硬编码为 Codex-only；也不为其他宿主虚构 Skill discovery 或审计 E2E 结论。
- 不在本方案实现 EvidentLoop `--path`、`--focus`、plan/design artifact profile、多审查者或确定性 checker。
- 不把 Sopify 的方案结构、目录命名、receipt 或 blueprint 语义写入 EvidentLoop 公共契约。
- 不修改或删除 CrossReview 独立仓库。
- 不读取、覆盖或提交 EvidentLoop 仓库中与本方案无关的用户改动；跨仓实施前必须重新核对工作区并隔离范围。
- Claude 持久 MCP 注册验证保持独立，已验证内容不重复纳入本方案。
- 不用新 renderer 覆盖旧 EvidentLoop audit 样例，不为命名整洁迁移已发布 schema 的历史字段。

## Status / Progress

- [x] 用户确认直接删除旧 CrossReview deferred 方案，不做 superseded 归档。
- [x] 用户确认所有方案级别统一以 `plan.md` 为入口，并按复杂度增加 tasks/design。
- [x] 用户确认对外统一使用 `plan_version / diff_version / report_version`，底层算法不进入字段名。
- [x] 用户确认独立审计、`audits/plan/` 主审计和 `audits/<scope>/` 附加审计三种方式。
- [x] 用户确认 EvidentLoop 只补通用能力，Sopify 自己完成 blueprint、目录和 receipt 适配。
- [x] 用户确认先补 EvidentLoop 通用版本输出并发布下一 Alpha，再完成 Sopify 公开版本 dogfood。
- [x] 用户确认方案包重写和两路独立审批。
- [x] 用户确认 Sopify 默认只保留产品无关的验证证据能力；EvidentLoop 是官方推荐但非默认的验证器。
- [x] 用户确认 `--with-evidentloop` 只是一次性可选配套安装；未选择、已独立安装或使用其他验证器都属于合法状态。
- [x] 用户确认配套安装是 Sopify 多宿主能力，Codex 只作为首轮真实 dogfood 宿主。
- [x] 上一版产品设计与技术架构审批已因安装边界重开，不再作为最终批准。
- [x] 产品设计与技术架构对最终重写版本重新审批通过；两路均为 P0=0、P1=0，无新用户决策。
- [x] 用户确认连续实施 Wave 1–2。
- [x] Wave 1–2 实施、定向验证、全量回归和当前知识收口完成。
- [x] Wave 1–2 审计问题最小修复与回归完成；两路独立审批 P0=0、P1=0，用户已接受。
- [x] Wave 1–2 已提交为本地 checkpoint `7dcd768`，Sopify 分支未推送。
- [x] Wave 3 的 EvidentLoop 通用版本实现、定向验证与 370 项全量回归完成。
- [x] EvidentLoop `v0.1.0a2` 已发布：[Publish](https://github.com/evidentloop/evidentloop/actions/runs/29678876261) 成功，[PyPI](https://pypi.org/project/evidentloop/0.1.0a2/) 包含未撤回的 wheel 与 sdist，[GitHub prerelease](https://github.com/evidentloop/evidentloop/releases/tag/v0.1.0a2) 为非草稿；schema `0.4`、prompt `v0.5` 保持不变，Release 无额外 assets 不阻断。
- [x] Task 4.0 已完成：develop/finalize 生命周期、active-plan 读取入口和四宿主 `host_support` 已双语收口；96 tests、36 subtests 与 Ruff 通过。
- [x] Wave 4 已按宿主原生路径收口：缺失组件使用 EvidentLoop 当前官方命令；四宿主 Skill 都先在隔离目录完成安装和校验，再原子复制到最终目录，失败不留下未验证目标目录。
- [x] Wave 4 回归已收口：266 tests、71 subtests，Python 3.11 硬门禁 97 tests、4 subtests，5 个协议 smoke、payload smoke、增量 Ruff、README 校验、shell 语法和 diff check 均通过；用户面只说明 Sopify 已可用、EvidentLoop 安装未完成，并给出重跑或独立安装入口。
- [x] Wave 5.1 已完成：隔离 HOME 的同一安装入口一次完成 Sopify、EvidentLoop CLI 与 Codex Skill；doctor 返回 `status=ok`、实际版本 `0.1.0a2` 和 4 个可读 package resources，Codex 本地 model-visible prompt 明确发现隔离路径中的 `evidentloop` Skill。
- [x] Wave 5.2 已完成：172 tests、46 subtests 定向验证与 266 tests、71 subtests 全量回归通过；Python 3.11 release preflight 全部通过，当前方案结构/version 有效，CrossReview 当前执行面与退役兼容面无残留，history 和 tracked state 无差异。
- [x] Wave 5 初次报告为 `complete / concerns`，唯一 medium finding 指出 Skill 身份校验不足；用户接受 finding 后，只增加顶部 front matter 的 `name: evidentloop` 检查并去除重复测试。定向、全量与 release preflight 仍全部通过，隔离 HOME 中的官方 Skill 已真实复用成功；旧报告因 diff 改变失效。
- [x] 替代报告覆盖冻结 staged diff 的 16/16 文件；用户正式裁定唯一 finding 为误报，确定性修订后结论为 `complete / pass_candidate`、风险 0、开放问题 0。
- [x] Wave 5.4 已附着最终 `audit.json + audit.html` 并由 writer 写入 `verify_001`；报告、diff 与方案三个版本值已绑定，附着未改变 `plan_version`。
- [x] Wave 6 只读残留复核通过；新增差异仅为最终报告、receipt 和收口状态，方案已进入 `ready_to_archive`。

## Next

无。方案通过 `sopify_writer` 标准归档后，以 history 包内的 final receipt 为最终机器证据。
