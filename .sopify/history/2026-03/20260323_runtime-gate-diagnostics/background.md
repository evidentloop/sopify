# 变更提案: runtime gate 证据对齐与诊断硬化

## 需求背景

runtime gate 是宿主进入 Sopify 的第一跳。当前实现已经具备一部分正确行为：

- fresh workspace 中的新请求已经可以正常返回 `ready`
- `_handoff_source_kind()` 已经能区分 `missing / current_request_not_persisted / reused_prior_state / current_request_persisted / persisted_runtime_mismatch`

真正的缺口不再是“普通冷启动普遍坏掉了”，而是“证据已经被收集，但还没有被提升为主判定”：

- gate 主判定仍主要只看 `handoff` 非空和 `strict_runtime_entry`
- `current_request_not_persisted` 与 `persisted_runtime_mismatch` 目前只出现在 `evidence / observability`，不会改变 `ready/error`
- 宿主约束强调 persisted handoff 才是正向机器证据，但 gate 当前仍会在某些“runtime 产出了 handoff 但没落盘”的场景下过于宽松
- receipt 还没有结构化的“上一份 receipt 为什么 stale”诊断面

因此，这个包更准确的目标应是“证据对齐 + 诊断硬化”，而不是笼统的“冷启动修复”。

评分:
- 方案质量: 9/10
- 落地就绪: 9/10

评分理由:
- 优点: 目标已经从模糊“冷启动修复”收敛为 gate 证据提升、正式错误码和测试补全；真值表、`stale_reason` 枚举和测试构造策略也已补齐，执行歧义显著下降。
- 扣分: Stage 2 仍属于真实行为变更，必须靠回归测试确认没有误伤 `reused_prior_state` 与既有宿主消费面。

## 变更内容

1. 将 `handoff source kind` 从纯观测信息提升为 `ready/error` 判定输入
2. 正式收口 4 个错误码：`handoff_missing`、`handoff_normalize_failed`、`current_request_not_persisted`、`persisted_runtime_mismatch`
3. 在写入新 gate receipt 前读取旧 receipt，并输出结构化 `previous_receipt` 诊断信息
4. 将现有测试矩阵从“正常路径 + missing”扩展到覆盖全部关键 source kind 与 receipt stale 场景
5. 视实现复杂度，将“证据收集 + 判定”抽为纯函数，并移除重复的 `preload_preferences()` 调用

## 非目标

- 不修改 README / CHANGELOG / CONTRIBUTING
- 不在本包中做 `runtime/models.py` 或测试结构拆分
- 不改变 `strict_runtime_entry`、checkpoint only、error visible retry 的既有宿主契约
- 不在 gate 层补写 persisted handoff 来“自动修复”持久化问题

## 影响范围

- 模块: `runtime/gate.py`
- 文件: `tests/test_runtime_gate.py`

## 风险评估

- 风险: 过度收紧 gate 判定，误伤 `reused_prior_state` 等合法恢复路径。
- 缓解: 显式定义每种 `handoff_source_kind` 的允许结果，只把 `current_request_not_persisted / persisted_runtime_mismatch / handoff_normalize_failed / missing` 提升为错误面。
