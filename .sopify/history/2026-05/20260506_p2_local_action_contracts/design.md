# 技术设计: P2 Local Action Contracts on Bound Subjects

## 核心策略

以 plan_subject 复用为基础，把 modify_files / checkpoint_response 从上下文推导收敛为 machine contract，cancel_flow 收敛为条件性 bound contract。同时引入 side_effect_delta 作为结构化变更清单，action-effect canonical pairing 作为 admission 闭合。不新增 action_type、route family、host action、checkpoint type、state file。P2 scope 为 admission contract；execution routing 收敛属于 P3a。

## Plan Intake Checklist

1. **命中蓝图里程碑**：P2（主）
2. **改动性质**：contract acceptance boundary（进 blueprint）+ 最小 runtime 实现
3. **新增 machine truth**：否 — 复用 plan_subject 已有 shape
4. **新增 schema 字段**：是 — ActionProposal 增加 `side_effect_delta`（可选）
5. **Legacy surface 影响**：P2 定义替代 contract，P3a 执行 legacy 清理
6. **Core promotion rule 影响**：无 — plan_subject 已是 Core contract
7. **Hard max 影响**：无 — 不新增 route family / host action / checkpoint type / state file

---

## Slice A: 蓝图 Spec

### A1: Action Applicability Matrix

| action_type | plan_subject | archive_subject | side_effect_delta | 宿主动词映射 |
|---|---|---|---|---|
| `consult_readonly` | 禁止 | 禁止 | 禁止 | inspect (alias) |
| `propose_plan` | 禁止 | 禁止 | 禁止 | — (新建主体) |
| `execute_existing_plan` | **MUST** | 禁止 | 禁止 (P2); future hook | continue |
| `modify_files` | **MUST** | 禁止 | SHOULD (`write_files` 时) | continue |
| `checkpoint_response` | **MUST** | 禁止 | 禁止 | revise |
| `cancel_flow` | 条件性 | 禁止 | 禁止 | cancel |
| `archive_plan` | 禁止 | **MUST** | 禁止 | — (独立 lifecycle) |

**Bound-subject actions**（plan_subject MUST，缺失 → REJECT）: `execute_existing_plan`, `modify_files`, `checkpoint_response`

**条件性 bound-subject action**: `cancel_flow` — 当取消目标是 bound plan flow 时 MUST 携带 plan_subject；parser 允许、validator 验证（如提供则全套 admission check），但缺失时不 REJECT

**Subject-free actions**: `consult_readonly`, `propose_plan`

**独立主体 action**: `archive_plan`（使用 `archive_subject`，不使用 `plan_subject`）

**宿主动词说明**：continue / revise / cancel / inspect 是宿主层 local verbs，不是 action_type。不新增 action_type 与之对应。

- **continue** = `execute_existing_plan`（执行 plan）/ `modify_files`（代码修改）
- **revise** = `checkpoint_response`（回应 pending clarification / decision checkpoint）
- **cancel** = `cancel_flow`（条件性 bound — 取消 bound plan flow 时必须带 subject，其他取消场景不强制）
- **inspect** = `consult_readonly` + optional bound-subject filter（P2 只做蓝图声明，不进 runtime acceptance）

### A2: plan_subject 复用契约

Bound-subject actions 复用 `PlanSubjectProposal`（`action_intent.py:67`），shape 不变：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `subject_ref` | string | MUST | workspace-relative plan 目录路径 |
| `revision_digest` | string | MUST | plan.md 的 SHA-256 hex digest |

**Validator admission 复用**：`_validate_plan_subject()` 的全部检查对 bound-subject actions（`execute_existing_plan`, `modify_files`, `checkpoint_response`）生效。`cancel_flow` 在 plan_subject 存在时走同一检查，缺失时不 REJECT。以下列表仅适用于 bound-subject actions（不含 cancel_flow）：

- 缺失 → REJECT
- 绝对路径 → REJECT
- `..` 穿越 → REJECT
- 不以 `.sopify-skills/plan/` 开头 → REJECT
- plan 目录/文件不存在 → REJECT
- revision_digest 与实际内容不匹配 → REJECT

### A3: side_effect_delta Schema

新增 `ActionProposal` 可选字段 `side_effect_delta`：

```json
{
  "side_effect_delta": [
    {"path": "src/auth.py", "change_type": "modified"},
    {"path": "src/new_module.py", "change_type": "added"},
    {"path": "tests/old_test.py", "change_type": "removed"}
  ]
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `path` | string | MUST | workspace-relative 文件路径 |
| `change_type` | enum | MUST | `added` \| `modified` \| `removed` |

**默认与范围**：

- `side_effect_delta` 缺失 = `None`，等同 legacy 无 delta 行为
- 第一版只做 workspace-relative scoping：
  - 路径 MUST NOT 是绝对路径
  - 路径 MUST NOT 包含 `..` 组件
  - Validator 做 workspace scoping 检查，**不做** plan-scope 判定
- `change_type` 枚举值借鉴 OpenSpec ADDED/MODIFIED/REMOVED delta 语义（T1 Adoption）

**side_effect_delta 与标量 side_effect 的关系**：

- 标量 `side_effect` 保留为粗粒度权限/副作用级别（不替换）
- `side_effect_delta` 是结构化变更清单（新增字段，并行存在）
- **P2 第一版只让 `modify_files` 消费 delta**：
  - `modify_files` + `side_effect = "write_files"` 时，`side_effect_delta` SHOULD 非空
  - 其他 action_type 的 delta 在 P2 不做 runtime acceptance，parser 拒绝
- `execute_existing_plan` 的 delta 支持是 future hook，蓝图留口但 P2 不进 runtime

**Applicability 约束**（见 A1 Matrix）：P2 第一版 `side_effect_delta` 仅对 `modify_files` 生效。其余 action_type 禁止携带 delta。

### A4: protocol.md 修正清单

1. **protocol.md:250**：
   - 现文案："每个 side-effecting action 必须携带明确的主体身份"
   - 修正为："每个 bound-subject side-effecting action 必须携带明确的主体身份"
   - 补充 bound-subject action 集合引用

2. **protocol.md:272-298**：
   - 现标题："execute_existing_plan 场景的 Subject Binding"
   - 修正标题："Bound-Subject Local Actions 的 Subject Binding — *normative*"
   - 扩展覆盖范围到 `modify_files` / `checkpoint_response` / `cancel_flow`
   - 保持最小字段不变：`subject_ref + revision_digest`
   - 保持 `.sopify-skills/plan/` 前缀约束

3. **protocol.md** 新增 Action Applicability Matrix 引用（见 A1）

### A5: Action-Effect Canonical Pairing

每个 action_type 有且仅有一个合法 side_effect。Validator 在 subject/delta check 之后、evidence check 之前做 pairing 校验，不匹配 → DECISION_REJECT（fail-close，不 downgrade）。

| action_type | canonical side_effect |
|---|---|
| `consult_readonly` | `none` |
| `propose_plan` | `write_plan_package` |
| `execute_existing_plan` | `write_files` |
| `modify_files` | `write_files` |
| `checkpoint_response` | `write_runtime_state` |
| `cancel_flow` | `none` |
| `archive_plan` | `write_files` |

**设计理据**：

- action_type 表达意图语义，side_effect 表达权限层级。1:1 pairing 防止 action_type 退化为标签
- 不引入新常量类型或 schema 字段 — 只是一个 dict 常量 + validator 函数
- 线上无用户，hard reject 窗口最佳

### A6: side_effect_delta 空列表归一化（显式声明）

`side_effect_delta = []`（空列表）在 parser 层归一化为 `None`，语义等同于"未提供 delta"。这是有意的设计选择：空列表不表达"声明不改任何文件"的语义。如后续需区分"未提供"与"显式声明为空"，须引入新的 sentinel 值。

---

## Slice B: Runtime 最小实现

### B1: Parser 变更（action_intent.py）

**放宽 plan_subject 约束**：

```python
# 新增常量
BOUND_SUBJECT_ACTIONS = frozenset({
    "execute_existing_plan", "modify_files", "checkpoint_response",
})
SUBJECT_CAPABLE_ACTIONS = BOUND_SUBJECT_ACTIONS | {"cancel_flow"}

# from_dict() 修改 (原 line 215-216):
# Before: if action_type != "execute_existing_plan":
# After:
if action_type not in SUBJECT_CAPABLE_ACTIONS:
    raise ValueError(
        f"plan_subject is only valid for subject-capable actions: "
        f"{sorted(SUBJECT_CAPABLE_ACTIONS)}"
    )
```

Bound-subject actions 的 `plan_subject = None` 在 **parser 层不 reject**，由 Validator 层 REJECT（与 execute_existing_plan 一致）。`cancel_flow` 的 `plan_subject = None` 在 parser 和 validator 层均不 reject。

**新增 side_effect_delta 解析**：

```python
SIDE_EFFECT_DELTA_CHANGE_TYPES = ("added", "modified", "removed")
DELTA_CAPABLE_ACTIONS = frozenset({"modify_files"})

# ActionProposal 新增字段
side_effect_delta: tuple[dict[str, str], ...] | None = None
```

**Parser 职责边界**（只做 shape + enum）：
- 缺失 → `None`（legacy 兼容）
- 非 list → `ValueError`
- 每项必须是 `{path: str, change_type: str}`
- `change_type` 不在枚举内 → `ValueError`
- 非 DELTA_CAPABLE_ACTIONS 的 action 携带非空 delta → `ValueError`

**Workspace scoping 不在 parser 层做**——路径合法性（绝对路径、`..` 穿越）属于 validator admission。

### B2: Validator 变更（action_intent.py）

**_validate_plan_subject 泛化**：

- 从 execute_existing_plan 专用改为 BOUND_SUBJECT_ACTIONS + cancel_flow 通用
- 对 BOUND_SUBJECT_ACTIONS：plan_subject 缺失 → REJECT
- 对 `cancel_flow`：plan_subject 缺失 → 不 REJECT；如提供则走全套 admission check
- `reason_code` 从 `validator.execute_existing_plan_*` 泛化为 `validator.bound_subject_*`
- 全部检查逻辑不变

**新增 _validate_side_effect_delta()**：

- 仅对 `modify_files` 调用（DELTA_CAPABLE_ACTIONS）
- **Workspace scoping**（validator 层，不在 parser 层）：
  - 路径 MUST NOT 是绝对路径 → REJECT
  - 路径 MUST NOT 包含 `..` 组件 → REJECT
- `side_effect = write_files` + delta 非空 → 通过
- `side_effect = write_files` + delta 空/缺失 → 通过（delta 可选）
- 不做 plan scope check

**validate() 主路径集成**：

在现有 `consult_readonly` check 之后、side-effecting evidence check 之前，插入：
1. bound-subject admission（对 BOUND_SUBJECT_ACTIONS 调 `_validate_plan_subject`；对 cancel_flow 条件性调用）
2. delta workspace scoping（对 DELTA_CAPABLE_ACTIONS 调 `_validate_side_effect_delta`）

### B3: 测试策略

- `BOUND_SUBJECT_ACTION × plan_subject 状态`（missing / valid / invalid_ref / invalid_digest）— parametrized tests
- `side_effect_delta` parser 测试（valid / invalid schema / wrong action_type）
- `side_effect_delta` validator 测试（workspace scoping: absolute path / traversal / valid path）
- 现有 632 tests 回归验证

---

## 不做清单

| 不做 | 原因 | 归属 |
|------|------|------|
| 删除 `review_or_execute_plan` | P3a legacy cleanup | P3a |
| 合并 `continue_host_quick_fix/workflow` → `continue_host_develop` | P3a legacy cleanup | P3a |
| Plan scope 机器定义 | 无稳定定义，硬上引入新抽象 | 未定 |
| inspect runtime acceptance | P2 只做蓝图声明 | 后续 |
| 扩 plan_subject 字段（plan_id / workspace_path） | 可从 subject_ref 派生 / 冗余 | — |
| 新增 route family / host action / checkpoint type / state file | P2 scope 约束 | — |
| side_effect 标量替换 | 已嵌入 gate schema / proposal_id 指纹 | — |
| generate_proposal_id 纳入 delta | 可选字段进指纹扩大兼容面，收益不明 | 后续增量决策 |
| execute_existing_plan 消费 delta | P2 第一版只做 modify_files；蓝图留 hook | P3+ |
