# Develop 规则

按已批准的任务实现、验证和复审，再更新任务状态及 `knowledge_sync`。没有验证证据，不算完成。

## 1. 选择与执行

从当前方案的 `tasks.md`（light 为 `plan.md`）提取 `[ ]` 项，按依赖和编号执行。定位文件、理解当前实现，再修改、发现验证命令、运行验证、处理失败并复审；满足下面的质量契约后才改状态。

- Bug 或共享边界变更先检查受影响调用方，在最窄的共同根因处修复，并验证同类路径。
- 可逆实现细节在已批准边界内决定；只有新事实会改变范围、方案路径或验收标准时才重新规划。
- Quick Fix 无 Design 产物时只做当前请求所需的局部选择，不补建方案或复制 Design 流程。
- 不把 `overbuild`、`underbuild`、应该没问题等主观判断当证据；不静默跳过验证，不无限重试。保持兼容、安全和仓库约定。

### Bug 调查分支

修 bug 时，先在出现问题的同一界面（如 UI、CLI 或 API）记录最小复现与失败证据，再根据调用方和观测定位共同根因并修复；修后用同一复现证明症状消失，并检查受影响的同类路径。不能复现时写明环境、缺失输入或原因，不把未复现说成修好。便宜且明确的本地回归可先写失败测试，但不要求所有任务都走 TDD；单元测试通过不能代替原界面的验证。

## 2. 验证记录

验证来源依次为：项目已声明的约定（如 `.sopify/project.md` 的 `verify`）→ 项目原生命令 → 未配置。前者存在时优先，但不为当前任务预建配置系统。

| 字段 | 约束 |
|---|---|
| `verification_source` | `project_contract` / `project_native` / `not_configured`，只表达来源 |
| `command` | 实际执行命令；没有稳定命令时可空，但须说明原因 |
| `scope` | 验证覆盖的任务、文件或模块 |
| `result` | `passed` / `retried` / `failed` / `skipped` / `replan_required` |
| `reason_code` | 无法执行、降级、跳过或回退 plan review 时必填 |
| `retry_count` | 只允许 `0` 或 `1` |
| `root_cause` | 失败收口或重试时必填，取值见下表 |
| `review_result` | 分别记录 `spec_compliance` 与 `code_quality` |

沿用上述字段，不另造同义字段。来源不是结果；未配置不能伪装为通过。`reason_code` 是内部字段，用户回复用人话解释。

## 3. 失败处理

首次验证失败可带失败上下文自动重试一次；第二次失败停止自动重试。第二次失败或放弃重试必须记录根因，按以下边界处理；不得盲修或降低验收标准。

| `root_cause` | 处理 |
|---|---|
| `logic_regression` | 带失败证据修复，再验证 |
| `environment_or_dependency` | 说明环境无法证明通过 |
| `missing_test_infra` | 保留未验证状态及补测要求 |
| `scope_or_design_mismatch` | 回到 plan review、决策 checkpoint 或宿主确认链 |
| `human_action_required` | 标 `[!]`，说明需要人工执行的凭证、迁移或审批步骤 |

## 4. 复审与任务状态

- `spec_compliance`：核对目标、范围和验收；是否做多、做少，或出现需用户拍板的分叉。
- `code_quality`：核对既有风格、兼容性、安全、稳定性、可维护性，以及必要的测试与知识同步。

只有验证与两项复审均满足契约时，才将任务改为 `[x]`；跳过为 `[-]`，阻塞为 `[!]`，未执行保持 `[ ]`。所有验证行 `result=passed` 且 `reason_code=—` 时才能使用 `✓`，否则用 `!`。

回复按共享输出契约和本 Skill 的输出模板：成功包含两项复审依据与验证摘要，部分完成还要说明未完成项和原因；简单小修只给必要验证，不机械加表格。最后检查状态、证据、Changes 与 Next 是否一致。

## 5. 知识同步与完成态

收尾调用 KB，按方案声明的 `knowledge_sync` 执行；读取、保留及偏好策略由 KB 唯一维护。
任务、验证和所需知识同步完成后，将 `plan.md` 元数据置为 `lifecycle_state: ready_to_archive`、`archive_ready: true`，方案继续保留在 `.sopify/plan/`。
`ready_to_archive` 不是自动归档；只有显式 `~go finalize` 通过 `sopify_writer` 校验最新 `plan_version` 后迁移至 history 并更新索引。Develop 不直接迁移、不模拟 finalize。

中断时保留已完成标记，当前项保持 `[ ]`，交接实际完成、待做事项和证据；失败时标 `[!]` 并保留根因与复审结果，只继续不依赖该阻塞的任务。只有用户明确要求时才用 Git 回滚，保留可追溯记录，方案留在 `plan/`。
