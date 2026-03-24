---
plan_id: 20260323_runtime-gate-diagnostics
feature_key: runtime-gate-diagnostics
level: standard
lifecycle_state: archived
knowledge_sync:
  project: skip
  background: review
  design: review
  tasks: review
archive_ready: true
---

# 任务清单: runtime gate 证据对齐与诊断硬化

## Step 1 — 冻结证据模型与判定边界
- [x] 1.1 明确 5 类 `handoff_source_kind` 的期望结果：哪些允许 `ready`，哪些必须 `error_visible_retry`
- [x] 1.2 固定 4 个正式错误码：`handoff_missing`、`handoff_normalize_failed`、`current_request_not_persisted`、`persisted_runtime_mismatch`
- [x] 1.3 保持 `strict_runtime_entry`、checkpoint only、error visible retry 的既有宿主语义不变
- [x] 1.4 明确 receipt stale 只做诊断可见性，不作为自动放行依据
- [x] 1.5 明确 gate 不负责补写 persisted handoff，持久化缺口必须显式暴露
- [x] 1.6 固定默认策略：`reused_prior_state` 保持 `ready`，只增强可见性
- [x] 1.7 在设计文档中补充 `source_kind / normalized_valid / strict_runtime_entry -> status/error_code` 真值表，并显式固定 `strict_runtime_entry=false` 的优先级
- [x] 1.8 在设计文档中补充宿主兼容性 contract：保留旧字段语义，只新增 error_code 枚举值与 `observability.previous_receipt.*`
- [x] 1.9 在设计文档中枚举 `previous_receipt.stale_reason` 的稳定值域与 `exists=false` 时的空值约束

## Step 2A — Stage 1 Additive 落地
- [x] 2A.1 在 `runtime/gate.py` 中新增或整理 `evidence / observability` 字段，不改变现有 `ready/error` 行为
- [x] 2A.2 在写入当前 receipt 前读取旧 receipt，并产出结构化 `previous_receipt`
- [x] 2A.3 至少记录 `exists / written_at / request_sha1_match / route_name_match / stale_reason`
- [x] 2A.4 将 `stale_reason` 收口为固定枚举：`not_stale / request_sha1_mismatch / route_name_mismatch / both_mismatch / parse_error`
- [x] 2A.5 如实现复杂度合适，抽出纯函数承载“证据收集 -> 判定”的核心逻辑，但先只服务 additive 观测层
- [x] 2A.6 评估并移除同一入口里的重复 `preload_preferences()` 调用

## Step 2B — Stage 2 Behavior Promotion
- [x] 2B.1 在 `runtime/gate.py` 中将 `source_kind + normalized_valid + strict_runtime_entry` 提升为最终 `ready/error` 判定输入
- [x] 2B.2 实现 `handoff_normalize_failed`，区分“没有 handoff”和“有候选 handoff 但 normalize 失败”
- [x] 2B.3 实现 `current_request_not_persisted`，显式暴露“runtime 产出了 handoff 但未持久化”
- [x] 2B.4 实现 `persisted_runtime_mismatch`，显式暴露“persisted handoff 与当前请求/运行结果不匹配”
- [x] 2B.5 确认 `reused_prior_state` 仍保持 `ready`，不被 Stage 2 行为变更误伤

## Step 3 — 补齐测试矩阵
- [x] 3.1 保留 fresh workspace 新请求返回 `ready` 的回归用例
- [x] 3.2 在 Stage 1 先补 `previous_receipt` stale 用例和 additive 观测断言，至少覆盖 `request_sha1_mismatch / route_name_mismatch / both_mismatch / parse_error`
- [x] 3.3 在 Stage 1 补 `current_request_not_persisted / persisted_runtime_mismatch` 的观测层用例，必要时通过 mock / fixture 直接构造
- [x] 3.4 在 Stage 2 补 `handoff_normalize_failed` 的正式错误面用例
- [x] 3.5 在 Stage 2 将 `current_request_not_persisted / persisted_runtime_mismatch` 升级为正式错误面断言
- [x] 3.6 确认 `reused_prior_state` 仍是允许的可见性路径，不被误伤为错误
- [x] 3.7 保留至少一条 `strict_runtime_entry=false` 的优先级回归，确认它仍先于 source kind 返回 `strict_runtime_entry_missing`
- [x] 3.8 跑现有 smoke / gate 断言，确认旧字段消费面未破坏

## 验证清单
- [x] V1 `python3 -m unittest tests/test_runtime_gate.py -v` 通过
- [x] V2 `python3 scripts/runtime_gate.py enter --workspace-root . --request "test"` 在 fresh workspace 返回可解释 contract
- [x] V3 手动确认 `evidence` / `observability` 字段仍与宿主当前消费方式兼容
- [x] V4 手动确认 Stage 1 完成后没有行为变更，Stage 2 完成后 `current_request_not_persisted / persisted_runtime_mismatch` 不再只是 source kind，而是正式错误面
- [x] V5 手动确认 `previous_receipt.stale_reason` 仅输出约定枚举或 `null`
