# 变更提案: P2 Local Action Contracts on Bound Subjects

## 需求背景

P1 建立了 Subject Identity 和 execute_existing_plan 的 plan_subject binding。P1.5 建立了授权脊柱（reject surface、authorization receipt、verifier normative contract）。

当前 runtime 中 7 个 action_type，只有 2 个携带 subject identity：

- `execute_existing_plan` — via `plan_subject`（subject_ref + revision_digest）
- `archive_plan` — via `archive_subject`（独立 shape）

其余 5 个 action 的路由仍靠 intent + evidence 上下文推导，validator 无法基于确定性主体做 admission。

### 现状精确表述

- **Parser 硬约束**：`action_intent.py:215-216` 拒绝非 execute_existing_plan 的 plan_subject
- **side_effect 是标量枚举**：`none|write_runtime_state|write_plan_package|write_files|execute_command`（`action_intent.py:33-39`），无结构化变更清单
- **protocol.md:250 过度宽泛**："每个 side-effecting action 必须携带明确主体"——实际只有 bound-subject actions 需要
- **Sunset 表中 3 项指向 P2**：`review_or_execute_plan`、`continue_host_quick_fix`、`continue_host_workflow` 的替代 contract 标注为 "P2 local action contracts"（`design.md:244-246`）

## 蓝图依据

- `blueprint/tasks.md:56-64` — P2 定义
- `blueprint/design.md:230-248` — Canonical host actions + Sunset 表
- `blueprint/protocol.md:248-270` — Subject Identity 通用定义
- `blueprint/protocol.md:272-298` — execute_existing_plan Subject Binding（normative）

## 决策记录

| ID | 决策 | 理由 |
|----|------|------|
| D1 | 复用 plan_subject（subject_ref + revision_digest），不新建 bound_subject | 当前 shape 已最小，新概念增加 migration 负担 |
| D2 | 缺 subject 的 bound-subject action → REJECT | fail-close，不伪装成正常只读 |
| D3 | side_effect_delta validator 做 workspace scoping，不做 plan scope check | 无稳定的 plan scope 机器定义，硬上会引入新抽象 |
| D4 | 一步到位，无显式迁移期 | side_effect_delta 缺失 = 空（legacy 兼容）；subject 规则立即收紧 |
| D5 | 两切片：A（蓝图 spec）→ B（runtime 最小实现） | 拆三片过细，增过场文档不增质量 |
| D6 | protocol.md 随 P2 修正 | P2 contract 的前提修正，不是附带优化 |
| D7 | plan_subject 不扩字段，保持 subject_ref + revision_digest | plan_id 可从 subject_ref 派生；workspace_path 冗余 |
| D8 | _validate_plan_subject 的 `.sopify-skills/plan/` 前缀约束保持 | bound subject = 活跃 plan；归档主体不接受 modify/checkpoint/cancel |
| D9 | action-effect 1:1 canonical pairing，不匹配 → REJECT | 防止 action_type 退化为标签；线上无用户，hard reject 窗口最佳 |
| D10 | side_effect_delta 空列表归一化为 None | 空列表不表达"声明不改任何文件"；如需区分须引入 sentinel |
| D11 | P2 scope = admission contract；execution routing 收敛 = P3a | 避免方案包口径与蓝图 tasks.md 产生歧义 |

## 触发事件

P1.5 四个子方案包全部完成并归档（`history/2026-05/`），按 tasks.md 串行依赖，P2 前置条件已满足。
