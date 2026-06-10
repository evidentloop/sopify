---
plan_id: 20260323_plan_registry_governance
feature_key: plan-registry-governance
level: standard
lifecycle_state: archived
knowledge_sync:
  project: review
  background: review
  design: review
  tasks: review
blueprint_obligation: review_required
archive_ready: true
---

# 任务清单: plan registry 治理层（`plan-registry-governance`）

## A. 已冻结决策

- [x] A.1 总表命名固定为 `.sopify-skills/plan/_registry.yaml`
- [x] A.2 registry 归属 `plan` 层，不进入 `blueprint/*`
- [x] A.3 registry 只做多 plan 治理，不替代 `current_plan`
- [x] A.4 `plan` 真相字段与 `registry` 治理字段严格分层
- [x] A.5 第一版只做自动登记、自动收口、读取时校准，不自动消费
- [x] A.6 `priority` 不再默认落最终值；系统先给 `suggested_priority`，最终由用户确认
- [x] A.7 `priority_source` 至少区分 `null` 与 `user_confirmed`
- [x] A.8 reconcile 只允许覆盖 `snapshot.*`，不能覆盖 `governance.*`
- [x] A.9 建议阶段只输出候选与理由，执行切换仍交给 runtime
- [x] A.10 建议优先级可基于现有 plan、`current_plan` 与请求信号自动生成

冻结标准：

- 文档中不再把 registry 描述成“总 plan 文档”
- 文档中不出现“registry 直接切换 current_plan”的表述
- 文档中明确 `priority` 的最终决定权归用户

## B. 待实施任务

### 1. registry 契约与模型

- [x] 1.1 新增 `runtime/plan_registry.py`，定义 registry 结构与读写 API
- [x] 1.2 固定 `snapshot / governance / advice / meta` 四层结构
- [x] 1.3 支持 `suggested_priority`、`suggested_reason`、`priority_source` 与 `priority_confirmed_at`
- [x] 1.4 定义 `mode=observe_only`、`selection_policy=explicit_only` 与 `priority_policy=heuristic_v1`

验收标准：

- registry 文件结构稳定且可扩展
- 字段归属与覆盖边界可由代码显式表达

### 2. create / finalize 事件同步

- [x] 2.1 在 `runtime/plan_scaffold.py` 成功创建 plan 后自动 upsert registry
- [x] 2.2 为新 plan 写入初始治理字段：`priority=null`、`priority_source=null`、`status=todo`
- [x] 2.3 为新 plan 生成 `suggested_priority/suggested_reason`
- [x] 2.4 在 `runtime/finalize.py` 成功 finalize 后自动从活动 registry 收口对应条目
- [x] 2.5 registry 缺失时支持一次性 backfill 已有 `plan/` 目录

验收标准：

- 新建 plan 后 registry 自动出现记录
- 新建 plan 后可看到建议优先级与解释理由
- finalize 后活动池不会残留已归档条目
- 不会因为重复 create / read 导致重复条目

### 3. reconcile 与 drift 可见性

- [x] 3.1 读取 registry 时自动对齐 `title/level/path/topic_key/lifecycle_state`
- [x] 3.2 生成读时 `drift_notice`
- [x] 3.3 reconcile 只能改 `snapshot.*`
- [x] 3.4 reconcile 不能覆盖 `priority/status/note`
- [x] 3.5 建议优先级刷新逻辑与 snapshot reconcile 分离，避免误覆盖用户确认值

验收标准：

- plan 标题或路径变化后，registry 能最终对齐
- 已确认优先级不会被后续读取覆盖

### 4. priority 建议与用户确认

- [x] 4.1 在设计与输出中明确 `suggested_priority` 只是建议，不是最终业务优先级
- [x] 4.2 支持基于现有 plan、`current_plan` 与请求信号生成建议优先级
- [x] 4.3 支持用户把某个 plan 的 `priority_source` 从 `null` 改成 `user_confirmed`
- [x] 4.4 记录 `priority_confirmed_at`
- [x] 4.5 输出摘要提示“建议优先级待用户确认”

验收标准：

- 新 plan 的建议优先级不会被误解成最终业务优先级
- 用户确认后的优先级会稳定持久化

### 5. 只读建议与后续消费边界

- [x] 5.1 设计只读建议规则，输入至少包含 `priority/priority_source/suggested_priority/status/current_plan`
- [x] 5.2 建议输出必须带解释理由
- [x] 5.3 确认式消费阶段只把候选排序交给 registry
- [x] 5.4 真正执行切换继续通过 runtime 更新 `current_plan`

验收标准：

- 建议可以解释“为什么推荐/不推荐某个 plan”
- 已确认优先级高于建议优先级
- registry 不会直接越权写执行态

### 6. 文档与测试

- [x] 6.1 在 `README.md` 增加 registry 层职责说明
- [x] 6.2 增加新建 plan 自动入 registry 的测试
- [x] 6.3 增加 finalize 后 registry 收口的测试
- [x] 6.4 增加 reconcile 不覆盖治理字段的测试
- [x] 6.5 增加建议优先级生成与 `priority_source=user_confirmed` 的持久化测试

验收标准：

- 文档明确区分 `blueprint / registry / current_plan`
- 核心同步和覆盖规则都可测试

## C. 推荐实施顺序

1. 先补 `runtime/plan_registry.py` 与 registry schema
2. 再接 create / finalize 事件同步
3. 然后补读取时 reconcile 与 `drift_notice`
4. 再补建议优先级生成与用户确认路径
5. 最后加只读建议、README 和测试收口

## D. 宿主侧接入任务清单

说明：

- 本节是下一阶段宿主接入清单，不回退当前已完成的 registry/runtime 实现
- 第一版只接 `registry inspect + confirm-priority`
- 不新增新的 `required_host_action`
- 不让 registry 直接切换 `current_plan`
- 本仓库已完成宿主接入 contract / docs / manifest hints；宿主实际调用落点属于外部宿主采纳范围

### 7. inspect 触发时机

- [-] 7.1 宿主在“新 plan 生成后进入 review”时自动调用一次 `plan_registry_runtime.py inspect`
- [-] 7.2 宿主在“用户主动查看 plan 列表/优先级”时允许再次调用 `inspect`
- [x] 7.3 第一版只把 `inspect` 挂在 review/治理视图，不嵌入 develop/execute 主链

验收标准：

- inspect 只在 review/治理场景出现
- 不会因为 inspect 改变执行态

### 8. inspect 结果展示

- [x] 8.1 宿主默认展示 `current_plan`
- [x] 8.2 宿主默认展示 `selected_plan`
- [x] 8.3 宿主默认展示 `selected_plan.advice.suggested_priority`
- [x] 8.4 宿主默认展示 `recommendations` 的前 3 个候选
- [x] 8.5 宿主在有内容时展示 `drift_notice`
- [x] 8.6 第一版不直接把 `registry.plans` 全量原始结构暴露给用户

验收标准：

- 用户能看到“当前 active plan / 当前评审 plan / 建议优先级 / 建议理由”
- 展示层不会把 registry 误导成执行真相

### 9. 用户确认交互

- [x] 9.1 宿主提供 `确认建议 / 改成 P1 / 改成 P2 / 改成 P3 / 暂不确认` 五类动作
- [x] 9.2 用户改优先级时，宿主允许附带可选 `note`
- [x] 9.3 宿主文案明确“系统建议不等于最终业务优先级”
- [x] 9.4 宿主文案明确“确认优先级不会切换当前执行 plan”

验收标准：

- 用户可以确认建议，也可以覆盖建议值
- 用户不会把“确认优先级”理解成“切换 current_plan”

### 10. confirm-priority 调用与回写

- [-] 10.1 宿主在用户确认后调用 `plan_registry_runtime.py confirm-priority`
- [x] 10.2 宿主向 helper 传递 `plan_id`、`priority` 与可选 `note`
- [x] 10.3 宿主成功后刷新当前卡片，而不是整页强制跳转
- [x] 10.4 宿主成功后只提示“已写入 registry”，不自动触发执行

验收标准：

- 用户确认后，registry 中 `priority / priority_source / priority_confirmed_at` 被更新
- 宿主成功回写后仍停留在 review 上下文

### 11. 失败与降级

- [x] 11.1 `inspect` 失败时，宿主允许隐藏该治理卡片，不阻断 plan review
- [x] 11.2 `confirm-priority` 失败时，宿主提示“优先级写入失败，请稍后重试”
- [x] 11.3 第一版不支持宿主直接编辑 `_registry.yaml` 原文

验收标准：

- registry helper 故障不会拖垮主 review 流程
- 宿主与用户都不会绕过 helper 直接改 registry 原文

### 12. 宿主文案模板

- [x] 12.1 补一版标准标题：`Plan 优先级建议`
- [x] 12.2 补一版标准说明：当前 active plan、当前评审 plan、建议优先级
- [x] 12.3 补一版标准提示：`确认优先级只会更新 registry，不会切换 current_plan`
- [x] 12.4 补一版成功提示：`已记录到 plan registry`
- [x] 12.5 补一版未确认提示：`已保留系统建议，暂未写入最终优先级`

验收标准：

- CLI/UI/宿主桥接都能复用同一套文案语义
- 用户能清楚区分“建议态”和“确认态”

### 13. 推荐落地顺序

- [x] 13.1 先接 `inspect` 触发与展示
- [x] 13.2 再接用户确认动作与 `confirm-priority`
- [x] 13.3 然后补失败降级与统一提示文案
- [-] 13.4 最后再考虑是否把这套交互推广到更多宿主

验收标准：

- 宿主接入可以以最小闭环逐步上线
- 第一版接入完成后，仍保持 runtime 主链与执行真相不变

## E. 收口说明

- [x] 本仓库范围内的 registry 治理层、helper、manifest hints、README 与 CN 宿主文档已完成
- [x] `_registry.yaml` 的定位已固定为 plan 治理层底账，默认通过 `inspect` 摘要消费
- [x] inspect-only 宿主消费约定已稳定：review-only、原文 advanced-only、不得切换 `current_plan`
- [-] 外部宿主的真实调用落点与 UI 采纳不在本仓库内，作为后续采纳事项保留

收口结论：

- 当前方案包已达到 `ready_for_verify / archive_ready=true`
- 若后续需要正式归档，应由活动 runtime 主链在合适时机执行 finalize，而不是直接绕过当前 active plan 状态强行迁移
