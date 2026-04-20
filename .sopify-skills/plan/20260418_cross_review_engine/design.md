# 技术设计: Cross-Review 独立内核方案

## 技术方案

本方案采用两层结构：

1. **独立内核层**：`CrossReview` / `cross-review engine`
   - 负责 artifact 抽取、review orchestration、finding 归一化、verdict 裁决、policy 输出。
   - 不依赖 Sopify 特定路由语义才能成立。

2. **Sopify 集成层**：`cross-review adapter`
   - 负责把内核能力接入 Sopify 的 analyze / design / develop / compare / checkpoint。
   - 复用现有 handoff、decision facade、develop_quality、state/replay。

这保证了两个目标同时成立：

- 独立使用：可作为单独 skill / runtime capability / CLI 运行。
- 内部集成：可被 Sopify 各阶段按 policy 嵌入，而不改变其核心定位。

在这个两层结构之上，再补一层**产品垂直面**：

1. **通用产品 / 通用内核**：`CrossReview`
2. **垂直能力**：
   - `design-review`
   - `sopify-code-review`
   - `final-audit`
3. **工作流宿主**：`Sopify`

也就是：

- `CrossReview` 解决“如何独立验证”
- `sopify-code-review` 解决“如何验证代码工件”
- `Sopify` 解决“验证发生在工作流的哪个阶段，并如何进入 plan/history 生命周期”

## 设计状态说明

本文件中的架构描述分为两类：

1. **可继续深化的推荐设计**
   - 用于支撑后续讨论、拆分 contract、完善 plan 资产结构
   - 当前可以继续展开细节

2. **必须等待用户拍板的设计决策**
   - 一旦涉及产品名、正式配置键、资产层是否入 plan、MVP 边界与首批集成阶段
   - 在用户明确确认前，不应转成实现前提

也就是说，本文件当前的任务是“把设计空间说清楚”，不是“替用户把最终产品策略定死”。

## 仓库形态与演进建议

### 建议的长期形态

当前更合理的长期目标是：

- `CrossReview` 作为独立产品内核
- `Sopify` 作为工作流宿主 / adapter 消费方

从架构边界看，二者最终分属不同仓库是合理方向，因为它们解决的问题不同：

- `CrossReview` 负责通用 review/verification 协议、profile、adjudication、policy
- `Sopify` 负责 plan / checkpoint / handoff / history / blueprint 生命周期

### 但当前不建议立刻钉死分仓

本方案不把“现在立刻拆新仓库”设为硬前提，原因有三点：

1. review 资产层、artifact taxonomy、正式配置键仍待用户拍板
2. 如果过早分仓，后续 contract 收敛时会反复调整 repo 边界
3. 当前更需要的是把 core / adapter 的责任边界说清楚，而不是先完成物理迁移

### 推荐的演进路径

当前建议按三阶段理解：

1. **阶段 A：独立产品方案阶段**
   - 在当前方案中把 `CrossReview` 的能力边界、资产层、profile、adapter 讲清楚
   - 这一步不要求实际分仓

2. **阶段 B：独立内核实现阶段**
   - 当命名、配置键、review asset、MVP 范围稳定后
   - 再创建 `CrossReview` 新仓库或等价独立包
   - 先实现 standalone core / CLI / profile

3. **阶段 C：宿主渐进接入阶段**
   - `Sopify` 进一步朝可插拔运行时框架收敛
   - 再按 `design -> develop -> finalize` 或试点顺序逐步接入

### core / adapter 边界建议

如果未来分仓，当前建议按下面边界理解：

#### `CrossReview` core 更适合承载

- artifact model
- review pack
- reviewer transport abstraction
- finding / verdict schema
- adjudicator
- policy
- vertical profiles
  - `design-review`
  - `code-review`
  - `final-audit`
- standalone CLI / runtime entry

#### `Sopify adapter` 更适合承载

- `.sopify-skills/plan` 生命周期写入
- `review.md` 的 plan/history 挂载
- checkpoint / handoff / execution gate 联动
- `develop_quality` 映射
- `current_handoff.json` / state 读写
- blueprint / history 归档联动

### 状态说明

上述“独立仓库”表述目前是**推荐演进方向**，不是冻结决策。  
是否真的创建新仓库、何时分仓、是先包级独立还是 repo 级独立，仍需用户后续拍板。

## 为什么它必须比 Sopify 更小、更聚焦

`CrossReview` 如果想成为成立的独立产品，就不能只是“把 Sopify 的一部分复制出去”，也不能继续长成另一个 workflow host。

当前更合理的尺度定位是：

- `Sopify`：完整 AI 编程工作流宿主
- `CrossReview`：独立验证内核
- `sopify-code-review`：代码工件 vertical

### 为什么必须更小

如果 `CrossReview` 同时承担下面这些能力：

- runtime gate
- clarification / decision checkpoint
- plan package 生命周期
- handoff / history / blueprint 主流程

那它就不再是验证产品，而是在重复构建一个更小的 Sopify。  
这样会带来两个问题：

1. 与 `Sopify` 的边界重叠，宿主 / 内核职责重新混乱
2. 独立产品无法保持清晰心智，用户不知道它究竟是“review 产品”还是“workflow 框架”

### 为什么必须更集中

`CrossReview` 的产品焦点应该稳定落在四件事上：

1. `independent`
   - 生产与评审上下文分离

2. `structured`
   - review 输入和输出可结构化表达

3. `decidable`
   - review 结果可以形成 verdict 与后续动作

4. `auditable`
   - review 结果可进入长期资产与审计链

只要一直围绕这四点，它就是独立验证产品；  
一旦开始扩张到“完整开发流程管理”，焦点就会跑掉。

### 因此建议的边界

#### 应保留在 `CrossReview core` 的能力

- artifact model
- review pack
- reviewer orchestration
- finding / verdict schema
- adjudicator
- policy engine
- report payload / report content generation

#### 应保留在 `Sopify adapter` 的能力

- 何时触发 review
- 如何写入 `.sopify-skills/plan/...`
- 如何更新 `review.md`
- 如何映射到 `develop_quality`
- 如何进入 `handoff / checkpoint / history`

#### 应留在 vertical profile 的能力

- `code-review` 的代码 rubric
- `design-review` 的方案挑战 rubric
- `final-audit` 的收口审计 rubric

### 对后续设计的约束

这条“更小、更聚焦”的原则，后续会约束三类设计：

1. **仓库边界**
   - core 与 adapter 必须分离

2. **文档边界**
   - `CrossReview` 文档聚焦验证协议，不扩张成完整 workflow 文档

3. **实现边界**
   - 不把 plan lifecycle、history 归档、checkpoint 主逻辑写进 `CrossReview` core

这一点目前不要求用户立即拍板，但应作为后续演进中的持续校验标准。

## 为什么不直接复用 `~compare`

`~compare` 和 `cross-review` 在产品语义上不同：

| 能力 | 目标 | 输入重心 | 输出重心 |
|---|---|---|---|
| `~compare` | 选优 | 同一问题的多个候选答案 | 候选结果 + 人工选择 |
| `cross-review` | 验错 | 已产生的 artifact 与证据 | findings + verdict + 后续动作 |

结论：

1. `cross-review` 可以复用 compare runtime 的 fan-out、context pack、normalize 基座。
2. 但不能继续使用 compare 的产品语义，否则会把“验证”错误地表达成“候选结果选择”。

因此，本方案把 compare runtime 视为**执行子模块**，而不是产品壳。

## 为什么不把 `cross-review` 直接并入 `code-review`

如果只看 develop 阶段，确实容易产生一种错觉：review = code review。  
但一旦把“设计评审报告”正式纳入 plan 生命周期，这个边界就变了。

更稳定的分层应该是：

| 层级 | 作用 | 示例 |
|---|---|---|
| 通用协议层 | 定义 review pack / finding / verdict / adjudication / policy | `cross-review` |
| 工件垂直层 | 针对某一类 artifact 提供专门 rubric 和输出 | `code-review`, `design-review` |
| 工作流层 | 决定何时触发、如何沉淀到 plan/history | `Sopify` |

因此建议：

1. `sopify-code-review` 不作为总产品名；
2. `sopify-code-review` 作为 `CrossReview` 的一个垂直产品 / 模式；
3. Sopify 集成的是 `cross-review` 内核和若干 review 模式，而不是只集成 `sopify-code-review`。

这能同时解释：

- 你原先独立做的 `code-review` 产品仍然成立；
- 现在新增的设计评审报告需求也能自然纳入；
- 不会让 review 体系被“代码”这个单一工件绑死。

## 核心抽象

### 1. Artifact

Cross-Review 的输入必须先被收口为显式 artifact，而不是随意问题文本。

建议首批支持：

- `code_diff`
- `plan_package`
- `task_result`
- `design_summary`
- `consult_answer`
- `command_result`

首期 MVP 正式落地（Q6 已拍板）：

- `code_diff`（MVP 唯一 artifact）

后续扩展：

- `plan_package`（Phase 1.5，design 集成时接入）
- `task_result`（Phase 2，是 code_diff 的超集，包含测试证据）

原因：
- `code_diff` 最容易结构化，与 develop_quality 基础设施最近；
- 先做 develop 集成（Q7 已拍板），验证 review.md 写入/handoff/finalize 链路；
- MVP 不需要 plan_package 和 task_result，保持最小化。

### 2. Review Pack

所有 reviewer 都消费同一种 review pack，而不是各自拿不同上下文。

建议结构：

```json
{
  "artifact_kind": "code_diff",
  "task": {
    "request": "...",
    "acceptance_criteria": ["..."],
    "constraints": ["..."]
  },
  "artifact": {
    "diff": "...",
    "files": ["src/a.ts", "src/b.ts"]
  },
  "evidence": {
    "tests": [
      {"command": "npm test", "status": "passed"}
    ],
    "snippets": [
      {"path": "src/a.ts", "start_line": 10, "end_line": 42, "content": "..."}
    ]
  },
  "policy_context": {
    "risk_tags": ["auth"],
    "severity_threshold": "high"
  }
}
```

设计原则：

1. reviewer 不直接读取 producer 的长推理过程；
2. 先看任务、工件、证据；
3. 作者说明若需要，应作为二阶段补充，而不是默认主输入。

### 3. Reviewer

reviewer 不等于“另一个模型”，而是一个执行角色。

Phase 1 支持三种 reviewer 类型（第四种 `skill_guided_reviewer` 为 Phase 2 预留接口，见下方）：

1. **fresh_session_same_model**
   - 同模型，新上下文（CrossReview 内置，直接输出结构化 finding JSON）。
   - 成本最低，且能明显降低自我锚定偏差。

2. **cross_model_reviewer**
   - 不同模型进行独立审查。
   - 更适合高风险或高不确定性工件。

3. **deterministic_checker**
   - 非 LLM checker，如 lint/test/schema rule/contract validator。
   - 不属于“语言审查”，但应进入同一 verdict 汇总。

**ReviewerTransport Protocol（统一接口）**：

所有 reviewer 类型都实现同一接口：

```python
class ReviewerTransport(Protocol):
    def execute(self, review_pack: ReviewPack) -> RawReviewerOutput: ...

class RawReviewerOutput:
    content: str               # 原始输出
    output_format: str         # "structured_json" | "free_form" | "deterministic"
```

**FindingNormalizer** 根据 `output_format` 选择解析策略：

| 路径 | Phase | 说明 |
|------|-------|------|
| `structured_json` | Phase 1 | 直接解析（`fresh_session_same_model` 输出） |
| `deterministic` | Phase 1 | 按工具规则解析（lint/test 输出） |
| `free_form` | Phase 2 预留 | 轻量 LLM 提取（`skill_guided_reviewer` 自然语言输出） |

Phase 1 只实现前两路；`free_form` 路不进入 Phase 1 实现范围。

**Phase 2 预留：skill_guided_reviewer**
- 使用外部 Markdown skill（如 Hermes `requesting-code-review/SKILL.md`）作为 reviewer 操作过程。
- 输出为自然语言，由 `FindingNormalizer` 的 `free_form` 路径（轻量 LLM 提取）转为结构化 finding。
- 允许 Hermes 社区 / 用户自定义 skill 插入 CrossReview pipeline。
- Phase 1 只预留接口定义，不实现 SKILL.md 解析与 free_form LLM 提取链路。

这里的关键结论是：

Cross-Review 不应被设计成“只会调多个 LLM”。  
它应该是一个统一验证编排层，LLM reviewer 只是其中一类执行者。  
`skill_guided` 类型让 CrossReview 可以消费任意 Markdown review 过程文档，包括 Hermes 社区 skill。

### 4. Finding

review 输出不能停留在自然语言点评，必须归一化。

建议 finding schema：

```json
{
  "id": "finding_001",
  "severity": "high",
  "category": "logic_regression",
  "title": "Token refresh path may bypass expiry check",
  "summary": "expiry validation moved behind early return",
  "evidence": [
    {
      "kind": "file_ref",
      "path": "src/auth/token.ts",
      "line": 88
    }
  ],
  "confidence": 0.81,
  "source_reviewer_id": "session_default_fresh"
}
```

建议首批 category：

- `logic_regression`
- `spec_mismatch`
- `missing_validation`
- `insufficient_tests`
- `risk_unmitigated`
- `architecture_mismatch`

**Finding 来源追溯**：所有 finding 进入 adjudicator 前必须归一化为同一 schema。
Phase 1 来源两路（`structured_json` / `deterministic`）；Phase 2 起新增 `free_form` 路。
来源类型通过 `source_reviewer_id` 可追溯。

### 5. Verdict

单个 finding 不是最终动作，最终要收口成 verdict。

Verdict 枚举（已冻结）：

| verdict | 语义 | 对应 action |
|---------|------|------------|
| `pass` | 无高风险问题，evidence 充分 | `continue` |
| `warn` | 存在中低风险问题，建议修改但不阻断 | `review_required` |
| `block` | 高风险或多 reviewer 共识问题，需阻断 | `block` |
| `inconclusive` | 证据不足 / 上下文不全 / reviewer 冲突过大 | `human_review` |

Action 枚举（已冻结）：

- `continue`：继续执行
- `review_required`：需要处理 finding 后重检
- `block`：阻断，进入 checkpoint_required 或 review_or_execute_plan
- `human_review`：证据不足，需要人工判断下一步（不是"人工做 code review"）

## Review 资产面设计

如果要让 review 真正进入 Sopify 的 plan 生命周期，建议把"控制面"和"资产面"拆开。

### 控制面

继续使用现有运行时机制：

- session review state
- `review_or_execute_plan`
- `develop_quality`
- `handoff.artifacts`
- checkpoint / resume / finalize

控制面负责本轮机器事实、阻断与恢复。

### 资产面（MVP 已拍板：review.md 单文件）

```text
plan/YYYYMMDD_feature/
├── background.md
├── design.md
├── tasks.md
└── review.md   # 懒加载，首次 review 运行时创建
```

资产面负责：

1. 给人类看；
2. 在 history 中长期保存；
3. 作为事后审计与复盘证据；
4. 为未来 graphify / blueprint 等长期知识层提供引用入口。

### `review.md` 的职责与结构

`review.md` 单文件承载所有 review 相关资产，使用分区结构避免膨胀：

**必选区块（MVP）：**

```yaml
# review.md 结构（v1）
review_id: <uuid>                 # 唯一标识，便于跨 plan 引用
schema_version: "1.0"
plan_id: YYYYMMDD_feature
last_updated: ISO8601

## 总状态
overall_verdict: pass|warn|block|inconclusive  # 当前最高优先级 verdict
open_issues: N                    # 未解决的 high/critical finding 数

## Finding Snapshot（finalize 时必须存在）
findings:
  - id: f-001
    category: spec_mismatch|security|logic|contract_violation|style
    severity: critical|high|medium|low
    reason_code: <short_code>      # 机器可识别，如 SPEC_GAP_001
    description: |
      简要描述（不超过 2 句话）
    status: open|resolved|deferred

## Verdict 历史
reviews:
  - run_id: <uuid>
    phase: develop|design|finalize
    artifact: code_diff|plan_package
    verdict: pass|block|warn
    reviewer_id: fresh_session_same_model|cross_model|...
    timestamp: ISO8601
```

**Finding Snapshot 的作用**：finalize 后 state 被清理，但 `review.md` 进入 history；
findings 快照确保 history 有"做完之后审了什么、发现了什么、如何收口"的可追溯证据。

## 裁决层设计

Cross-Review 不能只把多个 reviewer 原样输出给用户，必须有 adjudication 层。

建议 adjudicator 负责：

1. finding 去重
2. severity 归一化
3. reviewer 冲突整理
4. 依据 policy 形成最终 verdict

### 推荐裁决规则

MVP 建议使用确定性规则，不引入额外 LLM adjudicator：

1. 任一 reviewer 发现 `high` 且 evidence 充分的 finding → 至少 `warn`
2. 两个 reviewer 对同一问题独立命中 → 升级到 `block`
3. 只有一个 reviewer 提出、且 confidence 低、evidence 弱 → 保留为 `warn`
4. reviewer 全部失败或证据包过空 → `inconclusive`

这一步非常重要，因为它决定这件事更像工程系统，而不是多人聊天。

## 配置设计

当前不建议把能力继续挂在 `multi_model` 下。  
建议引入新的稳定父键：

```yaml
cross_review:
  enabled: false
  mode: advisory
  default_strategy: fresh_session_same_model

  reviewers:
    - id: session_default_fresh
      type: fresh_session_same_model
      enabled: true
    - id: qwen_reviewer
      type: cross_model_reviewer
      provider: openai_compatible
      model: qwen-plus
      enabled: false

  policy:
    develop:
      advisory_when:
        - changed_files_gt_2
      required_when:
        - auth
        - schema
        - payment
        - no_tests
    design:
      advisory_when:
        - architecture_change
        - long_term_contract_change
```

设计原则：

1. `multi_model` 仍保留给 compare；
2. `cross_review` 独立描述验证能力；
3. 未来如果底层调用器统一，也只复用执行层，不混淆产品配置语义。

如果未来需要把 `sopify-code-review` 暴露成独立产品，也建议采用“共享内核，不共享顶层配置名”的策略：

```yaml
cross_review:
  ...

code_review:
  enabled: false
  profile: strict
```

其中：

- `cross_review` 负责通用协议与 reviewer 编排；
- `code_review` 作为面向代码工件的产品型 profile 或 wrapper；
- Sopify 内部优先依赖 `cross_review`，而不是反向依赖 `code_review`。

> 状态说明：
> `cross_review` 顶层配置键**已拍板确认**，可作为实现前提。

## 与 Sopify 的集成边界

### 集成优先级（Q7 已拍板）

已拍板顺序：

1. **develop**（Phase 1，MVP）
2. **design**（Phase 2，plan package review）
3. **finalize**（Phase 3，收口审计）
4. **analyze**（Phase 4，需求反审，advisory only）

develop 先行原因：
1. `code_diff` artifact 是最小闭环验证单元；
2. 不需要 design review 基线，可直接开工；
3. 先跑通 review.md 写入 / handoff / finalize 链路，再扩展其他 phase。

design 第二阶段原因：
1. design review 需要 plan package 已物化；
2. 依赖 develop phase 积累的 reviewer 接口稳定性；
3. 不应在 confirm_execute 前强制触发（Phase 1 不做）。

### develop 集成方式

建议方式：

1. task 完成后，生成 `code_diff` review pack；
2. 执行 cross-review（fresh_session_same_model，MVP reviewer）；
3. findings + verdict 写入 `review.md`（finding snapshot 区块）；
4. 同步 verdict 到 `handoff.artifacts.cross_review_verdict`；
5. 映射进 `develop_quality.review_result`；
6. 若 verdict 命中 block policy → `checkpoint_required` 或 `review_or_execute_plan`。

设计重点：
- 不破坏 `develop_quality` 主 schema，以 artifact 扩展方式承载；
- `review.md` 是唯一 plan-level tracked 资产，state/handoff 只存机器事实。

### design 集成方式（Phase 2，不是 MVP）

> 注意：Phase 1 不做 design review。以下为 Phase 2 设计方向，仅供参考。

建议在 plan package 物化后、confirm_execute 前可选触发：
1. 生成 plan_package review pack；
2. 执行 cross-review；
3. findings 写入 `review.md`（design 区块）；
4. 若 design review 发现高风险问题，可阻断进入 develop。

### finalize 集成方式（Phase 3）

> 注意：Phase 1 不做 final audit。以下为 Phase 3 设计方向。

在 finalize 前补一轮收口检查：
1. 检查 task review 是否闭环（review.md 中 open_issues 是否为 0）；
2. 确认 finding snapshot 已写入 review.md；
3. 随 plan 一起进入 history（review.md 作为审计证据）。

### analyze 集成方式（Phase 4，advisory only）

只作为增强：
1. challenge requirement completeness；
2. 只做 advisory，不默认 block；
3. 避免把 analyze 变成噪音追问器。


## 独立使用形态

Cross-Review 内核至少应支持三种入口：

1. **独立 skill**
   - 例：`交叉验证这次改动`
   - 适合人工触发。

2. **runtime skill**
   - 可被 Sopify 路由调用。
   - 适合阶段内自动化集成。

3. **CLI / script**
   - 例：`python3 scripts/cross_review_runtime.py --artifact code_diff`
   - 适合 CI、维护者、宿主外调试。

建议第一版优先实现 runtime skill + script，两者共享同一内核入口。

如果保留你之前的独立产品 `sopify-code-review`，当前更合理的定位是：

1. `sopify-code-review` 作为 standalone vertical product 存在；
2. 它内部复用 `cross-review` 内核；
3. Sopify 不直接依赖 `sopify-code-review` 产品壳，而是集成 `cross-review` 与 `code-review profile`。

## Ownership Matrix：CrossReview core vs Sopify adapter

以下落表确定"谁生产什么、谁消费什么"，避免实现时越权。

| 责任域 | CrossReview core | Sopify adapter |
|--------|-----------------|----------------|
| findings 生产 | ✅ 负责 | 只读 |
| verdict 计算 | ✅ 负责（adjudicator） | 只读 |
| recommended_action 输出 | ✅ 负责 | 参考 |
| review_id / schema_version | ✅ 生成 | 透传 |
| reason_code 定义 | ✅ 负责 | 可扩展映射 |
| review.md 写入 | ✅ 负责（通过 adapter 接口） | 触发时机控制 |
| develop_quality.review_result | — | ✅ 负责（读 verdict 映射） |
| handoff.artifacts.cross_review_verdict | — | ✅ 负责（写） |
| checkpoint_required 触发 | — | ✅ 负责（读 block policy） |
| execution gate 判断 | — | ✅ 负责 |
| plan / history 写入 | — | ✅ 负责 |
| review policy 配置解析 | ✅ 负责（advisory_when / required_when） | 提供 policy config |
| reviewer 调度 | ✅ 负责（ReviewerTransport） | 提供模型/endpoint 配置 |

**核心原则**：

- CrossReview core 只负责"验证发现了什么"（findings）和"结论是什么"（verdict）。
- Sopify adapter 只负责"发现了什么之后 Sopify 怎么反应"（checkpoint / gate / handoff / history）。
- review.md 是两者的共享边界：core 负责内容，adapter 负责文件挂载时机与路径。


## 命名决策（已拍板）

> 命名已正式确认，以下为冻结约束。

1. **对外产品品牌名使用 `CrossReview`**（不使用 `sopify-cross-review`，宿主中立）
2. **对外能力名、命令名使用 `cross-review`**
3. **内核架构概念使用 `verification loop`**（设计文档内部语言，不暴露给用户）
4. **Sopify config key 使用 `cross_review`**（snake_case，与 `multi_model` 并列）
5. **repo 名为 `cross-review`**，先放个人 GitHub，core schema 稳定后再评估迁移 org
3. 对内模块名可使用：
   - `cross_review`
   - `verification_loop`
   - `review_pack`
   - `review_policy`
   - `review_adjudicator`

已拍板命名体系：

- 品牌名：`CrossReview`（不使用 `sopify-cross-review`）
- 能力名：`cross-review`
- 内核架构概念：`verification loop`
- config key：`cross_review`

产品层关系（Q4 已拍板）：

- `CrossReview`：通用 review/verification 总产品（已确认）
- `sopify-code-review`：基于 `cross-review` 的代码工件垂直产品（已确认）

## 后续开放问题

以下为 Q1-Q9 之外尚未收敛的设计问题，不阻断 Phase 1 开工：

1. **`code_review` 配置子键**
   - 是否需要 `code_review` 作为 profile / wrapper 配置面（对比 `cross_review` 直接展开）
   - 待 Phase 1 config 实现时确认


## MVP 范围（Q6+Q7 已拍板）

> Q6 已拍板：首版 MVP artifact = `code_diff` only。
> Q7 已拍板：首批集成 = develop 先行。

第一版 MVP 范围（已冻结）：

1. `code_diff` artifact（MVP 唯一 artifact）
2. `fresh_session_same_model` reviewer
3. `cross_model_reviewer` reviewer（可选，视成本）
4. 确定性 adjudicator
5. advisory / block 两档 policy
6. plan 内 `review.md` 单文件资产（Q5 已拍板，懒加载）
7. Sopify 首批集成：develop 阶段（Q7 已拍板）

Phase 1.5 扩展（develop 路径稳定后）：

- `plan_package` artifact → 接入 design 集成阶段
- `task_result` artifact → develop 集成的增强版

Phase 2：

- design 集成（plan package 完成后 → `review.md.design_verdict`）

先不做：

- analyze 自动 cross-review
- 多轮 reviewer 辩论
- LLM adjudicator
- PR 平台集成
- graphify / blueprint 联动自动触发

## 方案评级

- 方案质量: 8/10
- 落地就绪: 7/10

评分理由:
- 优点: 与 Sopify 现有 runtime skill、compare、quality gate、handoff 结构高度兼容，且产品边界比“继续强化 compare”更清晰。
- 扣分: 命名、schema 边界、policy 升级路径仍需进一步收敛，否则容易出现“compare / review / quality gate”职责重叠。

## 附录：最小 Contract 定义（v1）

> 以下为 Phase 1 实现的稳定 schema 基础，不代表完整设计。
> 不在此列的字段（artifact_digest, dedupe_key）留 Phase 1.5+。

### review_pack_v1

```python
@dataclass
class ReviewPackV1:
    schema_version: str = "1.0"          # 合约版本
    review_id: str = field(default_factory=lambda: str(uuid4()))  # 全局唯一
    artifact_type: str = "code_diff"      # MVP: 只支持 code_diff
    artifact_content: str = ""            # diff 文本
    context: dict = field(default_factory=dict)  # plan_id, task_id, phase 等
    created_at: str = ""                  # ISO8601
```

### review_result_v1

```python
@dataclass
class ReviewResultV1:
    schema_version: str = "1.0"
    review_id: str = ""                   # 关联 review_pack.review_id
    verdict: str = "pass"                 # pass | warn | block | inconclusive
    findings: list[FindingV1] = field(default_factory=list)
    recommended_action: str = "continue"  # continue | review_required | block | human_review
    reviewer_id: str = ""                 # 执行的 reviewer 类型
    run_at: str = ""                      # ISO8601

@dataclass
class FindingV1:
    id: str = ""                          # f-001, f-002...
    category: str = ""                    # spec_mismatch | security | logic | contract_violation
    severity: str = "medium"             # critical | high | medium | low
    reason_code: str = ""                 # 机器可识别短码，如 SPEC_GAP_001
    description: str = ""               # 简要描述，不超过 2 句话
    status: str = "open"                  # open | resolved | deferred
```

### review.md v1 必选字段

```
review_id        # 唯一标识
schema_version   # "1.0"
plan_id          # 关联 plan
last_updated     # ISO8601
overall_verdict  # pass | block | warn
open_issues      # 未解决 high/critical finding 数
findings[]       # finding snapshot（finalize 前必须存在）
reviews[]        # 每次 review run 的 verdict 历史
```

