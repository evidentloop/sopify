# 技术设计: runtime gate 证据对齐与诊断硬化

## 技术方案

- 核心技术: Python runtime contract、JSON receipt、unittest
- 实现要点:
  - 将“证据收集”与“是否 ready”解耦，避免 source kind 只停留在 observability
  - 明确“当前请求产出 handoff 但持久化缺失”“persisted handoff 与当前请求不匹配”“handoff normalize 为空”的不同错误面
  - receipt 写入前读取旧 receipt，输出结构化 `previous_receipt` 诊断对象，而不是只给一个布尔 stale 标记
  - 保持 `status / gate_passed / allowed_response_mode / evidence` 宿主契约稳定

## 默认策略

- `reused_prior_state` 默认保持 `ready`，只增强可见性，不提升为错误面
- 理由：这类路径常见于 `~summary`、状态查看等不产出新 handoff 的只读路由；当前阶段先保证可观测，不额外收紧

## 诊断维度拆分

本方案显式区分两个正交维度：

1. `source_kind`
   - 来源：`_handoff_source_kind()`
   - 值域：`missing / current_request_not_persisted / reused_prior_state / current_request_persisted / persisted_runtime_mismatch`
2. `normalized_valid`
   - 来源：`_normalize_handoff()`
   - 值域：`true / false`

`handoff_normalize_failed` 不是新的 `source_kind`，而是 `normalized_valid=false` 时的正式错误面。

## 真值表

| source_kind | normalized_valid | strict_runtime_entry | status | error_code |
|-------------|------------------|----------------------|--------|------------|
| `missing` | `false` | - | `error_visible_retry` | `handoff_missing` |
| `current_request_not_persisted` | `true` | `true` | `error_visible_retry` | `current_request_not_persisted` |
| `current_request_not_persisted` | `false` | - | `error_visible_retry` | `handoff_normalize_failed` |
| `current_request_persisted` | `true` | `false` | `error_visible_retry` | `strict_runtime_entry_missing` |
| `current_request_persisted` | `true` | `true` | `ready` | - |
| `current_request_persisted` | `false` | - | `error_visible_retry` | `handoff_normalize_failed` |
| `reused_prior_state` | `true` | `false` | `error_visible_retry` | `strict_runtime_entry_missing` |
| `reused_prior_state` | `true` | `true` | `ready` | - |
| `reused_prior_state` | `false` | - | `error_visible_retry` | `handoff_normalize_failed` |
| `persisted_runtime_mismatch` | `true` | `true` | `error_visible_retry` | `persisted_runtime_mismatch` |
| `persisted_runtime_mismatch` | `false` | - | `error_visible_retry` | `handoff_normalize_failed` |

判定优先级：

- `strict_runtime_entry=false` 优先返回 `strict_runtime_entry_missing`
- 在 `strict_runtime_entry=true` 前提下，`normalized_valid=false` 进入 `handoff_missing / handoff_normalize_failed`
- 只有 `strict_runtime_entry=true` 且 `normalized_valid=true` 时，才继续由 `source_kind` 决定 `ready / error`
- `runtime_result.handoff` 只参与诊断归因，不参与“成功证据”判断

## Source Kind -> 判定映射（摘要）

| source kind / 场景 | 预期结果 | 错误码 |
|--------------------|----------|--------|
| `current_request_persisted` | `ready` | - |
| `reused_prior_state` | `ready`，但保留可见性 | - |
| `missing` | `error_visible_retry` | `handoff_missing` |
| `handoff normalize` 后为空 | `error_visible_retry` | `handoff_normalize_failed` |
| `current_request_not_persisted` | `error_visible_retry` | `current_request_not_persisted` |
| `persisted_runtime_mismatch` | `error_visible_retry` | `persisted_runtime_mismatch` |

说明：

- `persisted handoff` 继续作为正向机器证据
- `runtime_result.handoff` 只用于诊断归因，不作为“可替代 persisted handoff 的成功证据”
- 不在 gate 内补写 persisted handoff，保持持久化责任仍在 runtime / engine

## 宿主兼容性 Contract

实现时保持以下兼容约束：

- 保留现有顶层字段语义：`status`、`gate_passed`、`allowed_response_mode`
- 保留现有 `evidence` 字段语义：`handoff_found`、`strict_runtime_entry`、`handoff_source_kind`、`current_request_produced_handoff`、`persisted_handoff_matches_current_request`
- 保留现有 `preferences` 字段语义，不改变 preload 判定方式
- 只新增：
  - `error_code` 的枚举值
  - `observability.previous_receipt.*`
- 不删除、不重命名现有字段，不把已有字段改成新的含义

## previous_receipt 结构

建议写入 `observability.previous_receipt`：

```json
{
  "exists": true,
  "written_at": "...",
  "request_sha1_match": false,
  "route_name_match": true,
  "stale_reason": "request_sha1_mismatch"
}
```

最小字段：

- `exists`
- `written_at`
- `request_sha1_match`
- `route_name_match`
- `stale_reason`

建议稳定枚举：

| stale_reason | 条件 |
|--------------|------|
| `not_stale` | `request_sha1_match=true` 且 `route_name_match=true` |
| `request_sha1_mismatch` | 仅请求摘要不匹配 |
| `route_name_mismatch` | 仅路由名不匹配 |
| `both_mismatch` | 请求摘要与路由名都不匹配 |
| `parse_error` | 旧 receipt 无法解析或结构不合法 |

补充约束：

- 当 `exists=false` 时，`written_at / request_sha1_match / route_name_match / stale_reason` 允许写 `null`
- `previous_receipt` 只服务诊断，不反向修正主判定

## 重构建议

- 可抽出纯函数，例如 `evaluate_gate_evidence(...)`，负责把 source kind、normalize 结果、strict entry 一次性映射到最终 contract
- 如果确认 `run_runtime()` 不会修改 preferences 文件，则删除同一入口里的第二次 `preload_preferences()`

## 落地阶段

### Stage 1 — Additive

- 新增 `evidence / observability` 字段
- 新增结构化 `previous_receipt`
- 补 `current_request_not_persisted / persisted_runtime_mismatch` 相关测试和观测字段
- 不改变 `ready/error` 行为

### Stage 2 — Behavior Promotion

- 将 `source_kind + normalized_valid + strict_runtime_entry` 提升为正式判定输入
- 让 `current_request_not_persisted / persisted_runtime_mismatch / handoff_normalize_failed` 成为正式错误面
- 跑全量 gate 回归，确认不误伤 `reused_prior_state`

## 测试策略

- fresh workspace 新请求: 仍然返回 `ready`
- `missing`: 继续 fail-closed
- `current_request_not_persisted`: 返回正式错误码，而不是只写 source kind
- `persisted_runtime_mismatch`: 返回正式错误码，而不是只写 source kind
- `handoff_normalize_failed`: 有候选 handoff 但 normalize 为空时返回正式错误码
- `previous_receipt` stale: 不改变主判定，但结构化诊断字段稳定

## 测试构造建议

- `current_request_not_persisted`: 优先用 mock / fixture 让 `runtime_result.handoff` 存在但 `StateStore.get_current_handoff()` 返回空，避免依赖不稳定的自然路径
- `persisted_runtime_mismatch`: 先写入一份旧的 persisted handoff 或通过 fixture 伪造 mismatch，再运行当前请求，稳定触发 mismatch 分支
- `previous_receipt` stale: 优先手工预写旧 receipt，分别覆盖 `request_sha1_mismatch / route_name_mismatch / both_mismatch / parse_error`
- `strict_runtime_entry=false`: 至少保留一条回归用例，钉住它仍优先返回 `strict_runtime_entry_missing`
