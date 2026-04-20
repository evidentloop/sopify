# 变更提案: Cross-Review 独立内核方案

## 需求背景

Sopify 当前的核心价值已经比较清晰：它把 AI 编程从一次性对话，收敛成带有 `runtime gate / checkpoint / handoff / plan / blueprint / history` 的可恢复工作流。这个方向解决的是“如何让 agent 少走偏、走偏后能恢复、关键节点可见且可控”。

但在稳定性结构上，Sopify 目前主要覆盖了两层能力：

1. **预防层**：通过 runtime gate、execution gate、clarification / decision checkpoint、防止 AI 自行拍板。
2. **恢复层**：通过 `current_handoff.json`、阶段状态、plan/history/blueprint，支持中断恢复与阶段回退。

在“发现错误”这一层，当前只有局部基础设施，还没有一个正式的一等能力：

- 已有 `~compare` 多模型对比运行时，可并发多个候选模型并统一结果。
- 已有 `compare_decision`，可把多结果包装成统一 decision facade。
- 已有 `develop_quality` 契约，可表达 `spec_compliance / code_quality` 两段质量结果。
- 但这些能力还没有收口成一个明确的、面向“独立验证 / 交叉审查”的产品。

用户的实际经验表明：**生产会话和审查会话分离**，无论是否更换模型，往往都会显著提高发现问题的能力。典型模式是：

1. 一个 session 负责产出方案或代码。
2. 产出完成后，新开一个 session，用另一个模型或同模型新上下文来 review 之前的改动。
3. 新 session 往往比原 session 的“自审”更容易发现回归、遗漏和逻辑不一致。

这个现象说明，真正有效的不是“多模型”本身，而是**独立验证**：

- 生产者和审查者职责不同；
- 审查上下文应与生产上下文隔离；
- review 输入应是任务、证据、diff、测试结果，而不是整段历史自我解释；
- 审查结论需要结构化，才能进入后续 gate / checkpoint / replay / policy。

因此，本次要设计的不是 `~compare` 的又一个变体，而是一个以 **`CrossReview`** 为产品品牌名、以 **cross-review** 为能力名、以 **verification loop** 为内核语义的独立验证产品，并允许：

1. 作为独立产品或独立 skill 使用；
2. 被 Sopify 在 analyze / design / develop 阶段按 policy 集成；
3. 未来被 blueprint graphify 之类的增强链路旁路复用，而不绑死在某个宿主里。

## 现状梳理

### Sopify 已有能力

1. **可插拔 runtime skill 发现**
   `runtime/skill_registry.py` 已支持 builtin + external skill 发现，并允许 workspace / user 级技能目录参与注册。

2. **runtime skill 执行**
   `runtime/skill_runner.py` 已支持通过稳定 Python entry convention 执行 runtime skill。

3. **多模型 fan-out 底座**
   `scripts/model_compare_runtime.py` 已具备抽取、脱敏、截断、共享 payload、并发调用、归一化结果的稳定链路。

4. **decision facade**
   `runtime/compare_decision.py` 已可把 compare 结果转为宿主可消费的统一选择 contract。

5. **develop 质量契约**
   `runtime/develop_quality.py` 已定义 `spec_compliance / code_quality` 两阶段 review 结果及回退条件。

6. **plan / blueprint / history / state 分层**
   这使得 Cross-Review 不需要从零解决上下文真相、阶段恢复与结构化沉淀问题。

### 当前缺口

1. **配置层没有正式的 `cross_review` 顶层能力**
   当前只有 `multi_model`，语义偏“对比候选答案”，而不是“验证当前产物是否可靠”。

2. **路由层没有正式的 review artifact 抽象**
   目前 compare 主要围绕“问题文本”，不是围绕 `diff / plan / answer / command result / migration` 等工件类型。

3. **缺少 producer / reviewer / adjudicator 的清晰分工**
   现在已有 compare runtime，但没有独立定义 review pipeline 中不同角色的职责和边界。

4. **缺少 review verdict 的统一 contract**
   当前 develop_quality 只能表达 develop 阶段质量结果，还不是通用的 cross-review verdict schema。

5. **缺少 policy 入口**
   还没有机制去声明：
   - 哪些阶段默认做 advisory review
   - 哪些风险标签必须 block
   - 哪些情况下从建议级 review 升级为 checkpoint / execution gate

6. **缺少“独立内核 + Sopify adapter”的产品边界**
   如果直接把这件事做成一个内部 compare 小技巧，会和 Sopify 现有 runtime 耦合过深，不利于未来单独使用。

7. **plan 包缺少一等的评审资产**
   当前 plan 主要围绕 `background / design / tasks` 三类文档展开，runtime 虽然已经有 review state、plan review、develop quality 等运行时概念，但“设计评审报告 / 任务复核报告 / 最终审计报告”还没有作为 tracked plan asset 被正式建模。

### 新识别出的结构问题：review 没有进入 plan 生命周期

从产品完整性看，review 不应只是一次聊天动作，也不应只存在于运行态 state 中。  
如果要支持真正可审计的稳定性结构，review 结果需要进入 plan 生命周期：

1. plan 创建后，存在**设计评审**，用于审视 `background/design/tasks` 的完整性、风险和可执行性；
2. task 执行过程中，存在**任务级复核**，用于记录某个 task 完成后的代码/结果是否通过 review；
3. plan 进入收口前，存在**最终审计**，用于判断所有 task 与 review 是否闭环；
4. plan 归档到 history 时，review 报告一并归档，形成后续可追溯证据。

这意味着：

- review 应成为 plan 的正式组成，而不只是宿主会话的附带行为；
- review 文档需要与 plan 同步演进，并随 history 归档；
- Sopify 现有的 `review_or_execute_plan`、`develop_quality`、session review state 等能力，应被视为运行时控制面，而不是最终资产面。

## 核心问题定义

本轮要解决的问题不是“如何再多调用几个模型”，而是：

1. 如何把“独立验证”定义成一个明确产品，而不是一个个人习惯。
2. 如何让它既能独立运行，又能作为 Sopify 的可插拔能力集成。
3. 如何把 review 的输入、执行、裁决、输出做成稳定 contract，而不是自然语言散落。
4. 如何在正确率与成本之间建立可配置 policy，而不是默认全量开启。
5. 如何把评审结果沉淀为 plan / history 中可审计的正式资产，而不是只留在 state 或会话里。

## 命名决策（已拍板）

> **状态：已拍板，不再是候选。**

本方案采用三层命名体系，各层职责已明确：

| 层 | 名字 | 说明 |
|---|---|---|
| 品牌名 / repo | `CrossReview` / `cross-review` | 宿主中立，不带 sopify- 前缀 |
| 用户面能力名 | `cross-review` | 命令名、README 主标题、文档标题 |
| 架构内核概念 | `verification loop` | 设计文档用语，类比 Claude 的 query loop，不作为用户面命令名 |
| config key | `cross_review` | snake_case，与 `multi_model` 并列 |

**拍板理由**：

- 产品的核心差异化是方法本身（交叉 / 独立验证），用方法命名品牌语义准确
- `CrossReview` 宿主中立，不带 `sopify-` 前缀，避免宿主绑定感
- `verification loop` 作为架构概念名保留，描述"如何运作"，不暴露给用户
- repo 命名 `cross-review`（kebab-case），品牌显示名 `CrossReview`（PascalCase），是同一产品的不同格式表达
- 仓库先放个人 GitHub 孵化，core schema 稳定后再评估迁移 org

**不再使用**：`sopify-cross-review` 作为产品名或 repo 名。


## `cross-review`、`code-review` 与 Sopify 的关系判断

当前更合理的分层不是：

- `cross-review` 是 `code-review` 的一部分

而是：

- `cross-review` 是更上层的**通用 review/verification 内核**
- `code-review` 是其中一个**面向代码工件的垂直能力**
- 与之并列的还应该有：
  - `design-review`
  - `plan-review`
  - `final-audit`

原因：

1. 如果把 `cross-review` 定义为 `code-review` 的一部分，那么设计评审、方案评审、最终审计都会变成“代码评审的附属物”，语义过窄。
2. 你当前新增的想法本质上已经超出了代码 diff review，进入了 plan 生命周期 review，这说明 `code-review` 不是总集，最多只是一个 vertical。
3. Sopify 需要集成的是**通用 review substrate**，然后在不同阶段实例化为不同 review 形态。

因此，本方案当前建议：

- `CrossReview`：独立产品 / 总能力承载体
- `cross-review`：产品中的通用 review 能力名
- `sopify-code-review`：基于 `cross-review` 的代码工件 review 垂直产品
- Sopify：集成 `cross-review`，并在 design / develop / finalize 阶段分别触发对应 review 模式

## plan 资产面建议

如果要把 review 正式纳入 plan 生命周期，建议不要只追加零散报告，而是显式定义 review 资产层。

MVP 已拍板资产结构（Q5）：

```text
.sopify-skills/plan/YYYYMMDD_feature/
├── background.md
├── design.md
├── tasks.md
└── review.md   # 懒加载；首次 review 运行时创建，随 plan 一起进入 history
```

设计理由：

1. `review.md` 单文件，与 `background/design/tasks` 平级，兼顾人类可读与审计可追溯。
2. 不引入 `reviews/` 子目录（Phase 1 不做，避免过度设计）。
3. `review.md` 在 finalize 时包含 **finding snapshot**，确保 history 有可审计证据（详见 design.md）。
4. 运行态 state 只承载机器事实，finalize 后清理；持久证据全部在 `review.md`。

## 本轮目标

1. 形成一个**独立的 Cross-Review 内核方案包**，不直接进入实现。
2. 明确它和 `~compare`、`develop_quality`、runtime skill、policy gate 的关系。
3. 明确它是“独立产品内核 + Sopify adapter”而不是 compare 的 prompt 增强。
4. 明确 `cross-review` 与 `code-review` 的层级关系，以及它们如何进入 Sopify。
5. 明确 `CrossReview / sopify-code-review / Sopify` 三者的产品层关系。
6. 给出一个便于持续迭代的方案包结构，后续可围绕命名、artifact、schema、集成方式逐步优化。

## 产品尺度定位

当前方案还需要一个明确约束：  
`CrossReview` 不应该长成另一个 `Sopify`。

更准确地说：

- `Sopify` 是工作流宿主，负责完整开发链路的组织与恢复
- `CrossReview` 是验证内核，负责独立审查、finding、verdict、policy 与审计表达

这意味着 `CrossReview` 的产品尺度应当：

1. **比 Sopify 小**
   - 不承担完整 workflow orchestration
   - 不接管需求分析、计划生成、checkpoint 生命周期本身

2. **比 Sopify 更集中**
   - 只围绕“如何验证一个已有工件是否可靠”展开
   - 聚焦 artifact、review pack、reviewer、adjudication、verdict

3. **比单点 code-review 更宽**
   - 不只面向代码 diff
   - 还覆盖 design review、plan review、final audit 等验证场景

也就是它在产品层应处于中间位置：

```text
Sopify > CrossReview > sopify-code-review
```

这个尺度关系很重要，因为它直接决定：

- 什么能力属于 `CrossReview core`
- 什么能力应留在 `Sopify adapter`
- 什么能力只应该作为 vertical profile 存在

如果这个产品不保持“小而集中”，它就容易重新演化成一个轻量版 Sopify，失去独立产品边界。

## 仓库形态建议

当前建议把“独立产品边界”和“当前开发位置”拆开描述：

1. **目标形态**
   - `CrossReview` 从产品边界上看，最终拥有独立仓库是合理方向

2. **当前阶段**
   - 先在现有方案中把命名、contract、资产层、adapter 边界讲清楚
   - 不把“现在立刻拆新仓库”视为当前阶段必须动作

3. **原因**
   - 如果在 artifact / verdict / review asset / config key 尚未稳定时就先拆仓，后续容易因边界调整反复搬运代码和文档
   - 反过来，如果先把独立产品边界说清楚，再决定分仓时点，工程节奏更稳

因此，本方案当前采用的表述是：

- **按独立产品设计**
- **以独立仓库为合理目标**
- **但不在本阶段钉死分仓时点**

## 非目标

- 本轮不直接修改 runtime/router/config/skill registry。
- 本轮不直接创建 `cross_review` 配置键。
- 本轮不直接把能力接进 analyze / design / develop。
- 本轮不实现模型调用、审查裁决、artifact 抽取代码。
- 本轮不强制决定最终命名，只先给出偏向性判断与可比较结构。
