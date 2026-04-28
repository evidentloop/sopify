# CrossReview 方案综合分析：跨项目思想借鉴

> **Status**: Archived reference — 外部项目洞察资产
> **当前事实源**: CrossReview 产品/发布事实以 `cross-review/.sopify-skills/plan/20260425_crossreview_product_master_plan/` 和 `cross-review/docs/v0-scope.md` 为准。
> **使用方式**: 本文只作为历史分析与 v1+ 设计素材，不参与当前 v0 / PyPI / Sopify Phase 4a 执行判断。
>
> 基于 Sopify 代码 + superpowers + spec-kit + hermes-agent + helloagents 的深度分析
> 生成时间：2026-04-20

---

## 一、总体判断

CrossReview 的方案已经覆盖了核心架构（artifact → review pack → reviewer → finding → verdict → policy），但五个项目中有 **12 个高价值思想** 尚未被方案充分吸收。这些思想不是"功能点补充"，而是 **设计范式层面的增强**。

---

## 二、最高价值洞察（应优先考虑纳入设计）

### 🔴 1. 两层聚合模式（Hermes MoA → CrossReview Reviewer-Aggregator）

**来源**：hermes-agent `mixture_of_agents_tool.py`

**现状差距**：CrossReview 当前 adjudicator 是确定性规则（severity 计数 + reviewer 共识），本质上是 **扁平合并**。

**Hermes 做法**：
- **Layer 1**：N 个 reference model 并行生成多样化结果（temp=0.6）
- **Layer 2**：Aggregator 以 Layer 1 输出为输入，合成最终结论（temp=0.4）
- 关键：Layer 2 不是简单投票，而是 **看到所有 reviewer 的推理过程后综合判断**

**对 CrossReview 的启发**：
```
当前设计:  reviewer₁ ─┐
           reviewer₂ ─┤─→ 确定性 adjudicator → verdict
           reviewer₃ ─┘   （数 severity、看共识）

建议增强:  reviewer₁ ─┐
           reviewer₂ ─┤─→ synthesizer（Phase 2 LLM adjudicator）→ verdict
           reviewer₃ ─┘   （看推理过程、解决矛盾、合成结论）
```

**建议**：Phase 1 保持确定性 adjudicator 不变；Phase 2 增加 `synthesizer` 模式作为 adjudicator 的可选升级路径，尤其在 reviewer 冲突严重时自动切换。

---

### 🔴 2. Spec-as-Acceptance-Criteria 管道（Spec-Kit → CrossReview Review Pack）

**来源**：spec-kit 的 spec-template.md + analyze.md

**现状差距**：CrossReview 的 `review_pack.task.acceptance_criteria` 目前是自由文本列表，没有结构化来源。

**Spec-Kit 做法**：
- 每个 user story 自带 `Independent Test: [如何独立验证]`
- acceptance scenario 用 Given/When/Then 格式
- requirements 有唯一 ID（FR-001, SC-001）
- analyze 命令做 **跨文档一致性检查**（spec ↔ plan ↔ tasks）

**对 CrossReview 的启发**：
- review pack 的 acceptance_criteria 应支持从 spec 自动提取（不只是手写）
- finding 应能 **反向追溯到具体 requirement ID**
- 这让 verdict 从"我觉得有问题"变成"FR-003 没有被覆盖"

**建议**：在 review_pack schema 中预留 `requirement_refs: list[str]` 字段；Phase 2 与 spec-kit 对接时，自动从 spec.md 提取 acceptance criteria + requirement IDs。

---

### 🔴 3. 合约驱动的验证路由（HelloAgents contract.json → CrossReview Policy）

**来源**：helloagents `plan-contract.mjs` + `delivery-gate.mjs`

**现状差距**：CrossReview 的 policy 是全局配置（`advisory_when / required_when`），没有 **plan 级别的细粒度验证合约**。

**HelloAgents 做法**：
```json
{
  "verifyMode": "review-first|metadata-first|verify-only",
  "reviewerFocus": ["security", "performance"],
  "testerFocus": ["coverage", "edge-cases"],
  "advisor": { "required": true, "focus": ["accessibility"] }
}
```
- 每个 plan 有自己的验证合约
- 合约决定：哪些验证必须做、以什么顺序、聚焦什么方面
- delivery gate 是 **确定性的**：缺哪个证据就 block 哪项

**对 CrossReview 的启发**：
```yaml
# 当前设计（全局 policy）
cross_review:
  policy:
    develop:
      required_when: [auth, schema]

# 建议增强（plan 级合约）
# .sopify-skills/plan/20260420_feature/review-contract.yaml
review_contract:
  mode: review-first          # 先 review 再继续
  required_evidence:
    - type: code_review
      focus: [security, auth]
    - type: spec_compliance
      required: true
  block_without: [code_review]  # 缺这个就 block
```

**建议**：Phase 1 不做；Phase 2 在 plan 目录中支持可选的 `review-contract.yaml`，作为全局 policy 的 plan 级覆盖。

---

### 🔴 4. 工作区指纹与审计链（HelloAgents fingerprint → CrossReview Evidence）

**来源**：helloagents `.ralph-*.json` 的 fingerprint 机制

**现状差距**：CrossReview 的 `review.md` 记录了 finding snapshot，但没有 **review 发生时的工作区快照**。

**HelloAgents 做法**：
```json
{
  "fingerprint": {
    "filesChanged": ["src/api.ts", "test/api.test.ts"],
    "gitCommit": "abc123def",
    "timestamp": "2024-04-20T14:30:00Z",
    "verifyCommandsUsed": ["npm run lint", "npm run test"]
  }
}
```

**对 CrossReview 的启发**：
- review.md 的每次 review run 应记录 `artifact_fingerprint`（diff hash / commit ref）
- 这让 history 中的审计可以回答："这条 finding 是基于哪个版本的代码发现的？"
- 与 Hermes 的 shadow git checkpoint 互补（Hermes 做全量快照，fingerprint 做轻量标识）

**建议**：在 ReviewResultV1 中增加 `artifact_fingerprint: str` 字段（MVP 可以是 git commit hash 或 diff hash）。

---

## 三、高价值机制（应纳入设计考虑范围）

### 🟡 5. 两阶段分离审查（Superpowers → CrossReview Reviewer Pipeline）

**来源**：superpowers `subagent-driven-development/SKILL.md`

**现有 hermes-insights.md 已有类似思路**，但 superpowers 的表述更清晰：
1. **Stage 1: Spec Compliance** — 实现是否匹配需求？（不评判质量）
2. **Stage 2: Code Quality** — 实现质量是否达标？（只有 spec 通过才到这步）

**对 CrossReview 的启发**：
- 当前 develop_quality 已有 `spec_compliance / code_quality` 两段
- CrossReview 的 reviewer 可以按两阶段编排：先 spec 验证 → 通过后再做质量审查
- **阶段 1 用确定性 checker 就足够**（对比 spec 条目），阶段 2 才需要 LLM reviewer

**建议**：在 reviewer orchestration 中支持 `pipeline` 模式（顺序执行、前者阻断后者），与现有 `parallel` 模式并列。

---

### 🟡 6. 错误分类与自适应恢复（Hermes → CrossReview Failure Handling）

**来源**：hermes-agent `error_classifier.py`

**现状差距**：CrossReview 只有 `inconclusive` 作为失败兜底，没有细分失败原因和恢复策略。

**Hermes 做法**：12+ 种 FailoverReason，每种有具体恢复建议：
- `rate_limit` → 等待 + 重试
- `context_overflow` → 压缩 review pack + 重试
- `auth_permanent` → 跳过此 reviewer
- `billing` → 降级到更便宜模型

**建议**：定义 `ReviewerFailureReason` 枚举，至少区分：`timeout / quota_exceeded / context_overflow / model_unavailable / output_malformed`。每种 reason 携带 recovery hint。

---

### 🟡 7. 熔断器模式（HelloAgents Breaker → CrossReview Escalation）

**来源**：helloagents `.ralph-breaker.json`

**现状差距**：CrossReview 没有"连续失败后自动升级"机制。

**HelloAgents 做法**：
- 连续 3 次验证失败 → 触发 breaker
- breaker 建议：重新分析根因 / 检查架构 / 回退并重新开始
- 不是无限重试，而是 **升级为不同类型的干预**

**对 CrossReview 的启发**：
- 如果同一 task 被 review 3 次仍 block → 不再重试，而是生成 `escalation_finding`
- escalation 可以触发 `human_review`（Q: 这个问题是否需要重新设计？）

**建议**：在 adjudicator 中增加 `review_attempt_count` 追踪；超过阈值时 verdict 自动升级为 `inconclusive` + `human_review` action。

---

### 🟡 8. 上下文压缩策略（Hermes → CrossReview Review Pack Budget）

**来源**：hermes-agent `context_compressor.py` + `trajectory_compressor.py`

**现状差距**：CrossReview 的 review pack 没有明确的 budget 约束（Sopify 的 compare 有 `max_chars_total: 12000`）。

**Hermes 三层压缩**：
1. Per-tool 输出截断
2. Per-result 持久化（大输出写磁盘，只保留摘要）
3. Per-turn 聚合预算（超限时逐个溢出最大结果）

**对 CrossReview 的启发**：
- review pack 应有明确 budget（diff 行数、evidence 条目数、总 token 数）
- 超出 budget 时自动截断或摘要化（保留头尾 + 变更密集区）
- compare runtime 的 budget 参数可直接复用

**建议**：在 review_pack schema 中增加 `budget` 子对象，复用 compare runtime 的 `max_files / max_lines_per_snippet / max_chars_total` 参数。

---

## 四、值得借鉴的辅助机制

### 🟢 9. 反合理化表（Superpowers → CrossReview Reviewer Discipline）

**来源**：superpowers 每个 SKILL.md 的 Rationalization Prevention Table

| 自我合理化 | 真实情况 |
|-----------|---------|
| "应该没问题了" | 运行验证命令 |
| "我很有信心" | 信心 ≠ 证据 |
| "就这一次跳过" | 没有例外 |

**对 CrossReview 的启发**：
- reviewer prompt 中应包含类似的反合理化约束
- 例如："不要因为 diff 看起来简单就跳过检查"
- 这属于 reviewer prompt engineering 层面的增强

---

### 🟢 10. Metadata-First 验证模式（HelloAgents → CrossReview Pre-Review Gate）

**来源**：helloagents `verifyMode = "metadata-first"`

**做法**：要求每个 task 的 acceptance criteria + 验证方式在 review 之前就必须完整，否则 gate 直接 block。

**对 CrossReview 的启发**：
- review pack 提交时可以做 **前置完整性检查**
- 如果 acceptance_criteria 为空、artifact 为空、evidence 缺失 → 直接拒绝进入 review 流程
- 避免浪费 reviewer 资源

**建议**：在 review pack normalization 阶段增加 `validate_completeness()` 前置检查。

---

### 🟢 11. 表达式驱动的 Policy 语言（Spec-Kit → CrossReview Policy Expression）

**来源**：spec-kit `expressions.py`

**做法**：Workflow 条件使用 Jinja2 风格表达式：
```
advisory_if: "{{ severity < 'high' }}"
required_if: "{{ risk_tags | contains('auth') }}"
```

**对 CrossReview 的启发**：
- 当前 `advisory_when / required_when` 是硬编码 keyword 列表
- 更灵活的 policy 表达：`required_when: "{{ changed_files > 5 and 'auth' in risk_tags }}"`
- 不是 Phase 1 需要，但长期可以让 policy 更具表达力

---

### 🟢 12. Session 持久化与 FTS5 检索（Hermes → CrossReview Audit Search）

**来源**：hermes-agent `hermes_state.py` + SQLite FTS5

**做法**：所有 session 存 SQLite，用 FTS5 做全文检索。

**对 CrossReview 的启发**：
- CrossReview 的 review history 如果用 SQLite + FTS5 存储，可以查询："所有 auth 模块的历史 review"
- 与 `review.md` 资产面互补：`.md` 是人类可读 + 归档证据，SQLite 是机器检索 + 统计
- Sopify 当前是文件系统为主，但 CrossReview 可以在 core 层选用 SQLite 作为 finding 检索后端

---

## 五、各项目对 CrossReview 的整体定位参照

| 项目 | 核心贡献 | 与 CrossReview 的关系 |
|------|---------|---------------------|
| **Sopify** | 工作流宿主、checkpoint/handoff/gate 基础设施 | CrossReview 的集成宿主 + adapter 层 |
| **Superpowers** | 两阶段审查、反合理化、分块 review、升级机制 | reviewer 编排与 prompt 工程参考 |
| **Spec-Kit** | spec-as-source、acceptance criteria、gate 步骤、workflow 引擎 | review pack 结构化输入的上游来源 |
| **Hermes** | MoA 两层聚合、错误分类、上下文压缩、session 持久化 | 内核执行层参考（aggregation + budget + recovery） |
| **HelloAgents** | contract-based routing、delivery gate、fingerprint、breaker | policy + evidence + 审计链参考 |

---

## 六、建议纳入方案的优先级

### Phase 1（MVP 增强，低成本）
1. ✅ `artifact_fingerprint` — 在 ReviewResultV1 增加一个字段
2. ✅ `validate_completeness()` — review pack 前置检查
3. ✅ `ReviewerFailureReason` — 区分失败原因（至少 5 种）
4. ✅ `review_pack.budget` — 复用 compare runtime 的 budget 参数

### Phase 2（设计增强，需要方案讨论）
5. 🔄 `pipeline` 模式 — spec compliance → code quality 顺序执行
6. 🔄 `synthesizer` adjudicator — 两层聚合模式
7. 🔄 `review-contract.yaml` — plan 级验证合约
8. 🔄 `requirement_refs` — review pack 支持 spec requirement ID 追溯

### Phase 3（长期演进）
9. 📋 `breaker` 熔断器 — 连续失败后自动升级
10. 📋 expression-based policy — 替代硬编码 keyword 列表
11. 📋 FTS5 检索后端 — 历史 finding 全文检索
12. 📋 反合理化 prompt 模板 — reviewer prompt 纪律约束

---

## 七、与已有 hermes-insights.md 的关系

上述 12 个思想中：
- **#1 MoA 两层聚合** 和 **#6 错误分类** 是 hermes-insights.md 的 §6 待补充项的直接答案
- **#8 上下文压缩** 是 hermes-insights.md 的 §6 第四条的直接答案
- 其余 9 项来自 superpowers / spec-kit / helloagents，是 hermes-insights.md 未覆盖的外部项目
- 建议拍板后，将对应条目合并进 design.md 的相应章节

---

## 八、总结一句话

> CrossReview 的核心架构（artifact → finding → verdict → policy）是稳的；最值得补充的不是更多功能点，而是 **三个范式升级**：
> 1. 从扁平合并到 **两层聚合**（Hermes MoA）
> 2. 从全局 policy 到 **plan 级验证合约**（HelloAgents contract）
> 3. 从自由文本 criteria 到 **spec-sourced requirement 追溯**（Spec-Kit）
