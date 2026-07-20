# Develop 详细规则

## 目标

按任务清单实施开发，维护任务状态，按 `knowledge_sync` 同步 V2 长期知识，并通过 task-level 质量循环确保“有验证证据才算完成”。

## 总流程

1. 读取任务清单。
2. 对每个任务按固定质量循环执行：实现修改 -> 发现验证 -> 执行验证 -> 必要时一次重试 -> 两阶段复审。仅在质量结果满足最小 contract 后更新任务状态。
3. 按 `knowledge_sync` 同步知识库与偏好信息。
4. 将完成方案更新为 `ready_to_archive`，保留在 `plan/`。
5. 输出执行结果摘要。

## 步骤 1：读取任务清单

来源：

- `.sopify/plan/{current_plan}/tasks.md`
- `.sopify/plan/{current_plan}/plan.md`（light）

处理规则：

1. 提取 `[ ]` 待执行任务。
2. 按任务编号顺序执行。
3. 先检查显式依赖再执行。

## 步骤 2：执行任务

### 2.1 任务级质量循环

每个任务按以下顺序执行：

1. 定位目标文件。
2. 理解当前实现。
3. 实施修改。
4. 发现验证命令。
5. 执行验证。
6. 首次失败时允许带失败上下文自动重试一次。
7. 对失败收口做结构化根因分类。
8. 执行两阶段复审：`spec_compliance` -> `code_quality`。
9. 只有质量结果满足最小 contract 后才更新状态。

硬性约束：

- 没有验证证据，不算完成。
- `overbuild`、`underbuild`、`应该没问题` 这类主观判断不能替代验证或复审结果。
- 不允许静默跳过验证，也不允许无限重试。
- Bug 或共享边界变更先检查受影响调用方，在最窄的共同根因处修复，并验证同类路径。
- 批准范围内的可逆实现细节由 Develop 处理；只有新事实会改变范围、方案路径或验收标准时才重新规划。
- Quick Fix 没有 Design 产物时，只做完成当前请求所需的局部选择，不补建方案或复制 Design 规则。

### 2.2 最小 verify contract

develop 阶段统一使用以下字段名，不再混用 `discovery_source`、`status`、`configured`、`discovered` 等别名：

1. `verification_source`
   - 只表达验证来源，允许值固定为：
   - `project_contract`
   - `project_native`
   - `not_configured`
2. `command`
   - 记录本次尝试执行的验证命令。
   - 若没有稳定命令，允许为空，但必须补 `reason_code`，不能伪装为已验证。
3. `scope`
   - 记录验证覆盖的任务、文件或模块范围。
4. `result`
   - 固定使用：
   - `passed`
   - `retried`
   - `failed`
   - `skipped`
   - `replan_required`
5. `reason_code`
   - 当无法执行、显式降级、跳过或回退 plan review 时必须存在。
6. `retry_count`
   - v1 只允许 `0` 或 `1`。
7. `root_cause`
   - 失败收口或重试路径上必须存在。
8. `review_result`
   - 必须至少包含 `spec_compliance` 与 `code_quality` 两阶段结论。

补充说明：

- `.sopify/project.md` 的 `verify` 约定是后续长期落点；当它已存在时，作为最高优先级来源，但不是当前 v1 落地前提。
- `verification_source` 只表示来源，不复用为结果态；“是否跳过/为何降级”统一通过 `result + reason_code` 表达。
- `reason_code` 是内部验证字段，最终用户输出不得展示原始值；需要解释时用人话填入"说明"列。

### 2.3 验证发现顺序

固定优先级：

1. `project_contract`
   - 即 `.sopify/project.md` 中已显式定义的 `verify` 约定。
2. `project_native`
   - 项目原生脚本或配置，例如 `package.json`、`pyproject.toml`、`Makefile`、`justfile` 中稳定的验证入口。
3. `not_configured`
   - 当仓库没有稳定命令时，必须可见降级，并写明 `reason_code`；不能把“没有找到命令”视为默认通过。

### 2.4 失败处理与根因分类

失败处理口径：

1. 第一次验证失败后，允许自动重试一次。
2. 第二次仍失败时，必须停止自动重试。
3. 第二次失败或显式放弃重试时，必须写入 `root_cause`。

`root_cause` 允许值固定为：

- `logic_regression`
- `environment_or_dependency`
- `missing_test_infra`
- `scope_or_design_mismatch`
- `human_action_required`

分流约束：

- `logic_regression`：允许继续 develop，但必须带失败上下文修复。
- `environment_or_dependency`：可见标记环境无法证明通过，不把任务伪装为已验证完成。
- `missing_test_infra`：允许保留任务未验证完成，并显式写出补测要求。
- `scope_or_design_mismatch`：不得继续盲修，应优先回到 plan review、decision checkpoint 或其他宿主确认链路。
- `human_action_required`：需要人工物理动作（写凭证、手跑 migration、外部审批），AI 无法代劳；标记 `[!]` 并明确写出人工操作步骤。

### 2.5 两阶段复审

Stage A `spec_compliance` 至少检查：

1. 是否满足当前任务目标与边界。
2. 是否存在明显 `overbuild` 或 `underbuild`。
3. 是否引入新的范围变化或需要用户拍板的分叉。

Stage B `code_quality` 至少检查：

1. 是否与现有代码风格一致。
2. 是否存在明显安全性、稳定性或可维护性回退。
3. 修改面、注释、测试与知识同步是否达到当前任务最低标准。

状态迁移：

- 成功：只有当 `verification_source / result / review_result` 满足最小 contract 时，才允许 `[ ] -> [x]`
- 跳过：`[ ] -> [-]`
- 阻塞：`[ ] -> [!]`

安全底线：

- 不引入常见漏洞（XSS / SQL 注入等）。
- 不破坏既有功能。
- 保持项目代码风格一致。

输出状态符约束：

- `✓` 仅当所有验证行 `result=passed` 且 `reason_code=—`
- 否则必须使用 `!`

### 2.6 输出前自检

完成两阶段复审后，输出最终摘要前必须检查：

1. 状态符是否正确：`✓` 仅当全部 `result=passed` 且 `reason_code=—`；否则必须 `!`。
2. 必需表格是否存在：success/partial 必须有验证摘要表；partial 必须有未完成项表。
3. 复审结论行是否存在：success 必须有 `spec_compliance` + `code_quality` 各一句依据。
4. footer 是否完整：`Changes:` + `Next:` 必须存在。

## 步骤 3：知识库同步

实施收尾时调用 KB，按当前方案声明的 `knowledge_sync` 执行并记录结果。同步目标、长期知识判据和偏好写入政策由 KB 唯一负责；Develop 不在这里重新定义。

## 步骤 4：方案完成态

任务、验证和 `knowledge_sync` 均完成后：

1. 在 `plan.md` 中把 `lifecycle_state` 更新为 `ready_to_archive`，并设置 `archive_ready: true`。
2. 方案目录继续保留在 `.sopify/plan/YYYYMMDD_feature/`。
3. develop 不迁移目录、不更新 history index，也不直接模拟 finalize。

`ready_to_archive` 只是方案语义元数据，不是新的 state 文件或生命周期引擎。只有用户显式运行 `~go finalize` 时，宿主才通过 `sopify_writer` 校验最终 `plan_version`、迁移目录并更新 history index。

## 输出模板

按结果类型选择 `assets/`：

1. `assets/output-success.md`
2. `assets/output-partial.md`
3. `assets/output-quick-fix.md`

## 特殊情况

执行中断：

1. 已完成任务标记 `[x]`。
2. 当前任务保持 `[ ]`。
3. 输出中断摘要，等待宿主恢复。

任务失败：

1. 标记 `[!]` 并注明原因。
2. 若存在失败收口，必须补 `reason_code`，并在需要时补 `root_cause` 与 `review_result`。
3. 仅继续不受阻塞的独立任务。

回滚请求：

1. 使用 git 回滚（仅在用户明确要求时）。
2. 保留方案包在 `plan/`，不迁移。
3. 输出回滚确认。
