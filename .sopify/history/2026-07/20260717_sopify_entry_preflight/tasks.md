# 任务清单: Sopify 会话入口状态预检

目录: `.sopify/plan/20260717_sopify_entry_preflight/`

## 1. 协议边界

- [x] 1.1 对齐 `.sopify/blueprint/protocol.md` 与 `sopify_writer/store.py`：明确入口状态矩阵、主体绑定和单次询问规则；复用现有 MCP 防覆盖语义，同名 receipt 已存在时抛出 `FileExistsError`。
  - 路由验收：consult / quick fix 不进入接续链，new plan 不消费旧 checkpoint，checkpoint response 不重显原问题；无效旧指针遇到明确且有效的 continue 目标时直接激活。
  - 审计验收：非 active plan 审计器保持只读；宿主校验目标 `plan.md` digest 后仅通过 writer 写未占用的 `verify_NNN` receipt，不切换 active plan / handoff；`tests/test_sopify_writer.py` 证明重复写入被拒绝且原证据不变。
- [x] 1.2 对齐 `skills/zh/header.md.template` 与 `skills/en/header.md.template`；验收为不同 session 标识不单独阻断正常接续；只有约定的三类并行推进信号才停止同一 active plan 的有副作用开发，并展示一次简洁提示。不出现自动修复、session 所有权、锁或全局 gate。

## 2. 最小状态事实

- [x] 2.1 在 `scripts/sopify_mcp_server.py` 为现有 `workspace_status_lite` 增加 `active_plan_file_exists`、`active_plan_md_exists`、`handoff_plan_id`、`handoff_matches_active_plan`，并收紧 `plan_id` 子路径校验；验收为污染路径返回结构化 error，不新增 tool、state、workflow verdict 或目录扫描。

## 3. 自动化与真实回放

- [x] 3.1 扩充 `tests/test_sopify_mcp_server.py`，覆盖无 active plan、JSON `null`、数组、缺 `plan_id`、污染路径、有效 plan 缺 handoff / `plan.md`、handoff 一致/失配；验收为只读检查不产生状态写入。
- [x] 3.2 扩充 `tests/test_installer.py` 的宿主资产检查；验收为测试完整规范句而非单个关键词，安装后的 Codex 中文和 Claude 英文 prompt 均精确保留：
  - checkpoint 回答不重问；无效旧指针的新建 / 明确继续不二问；有效旧方案切换仍需确认。
  - MCP 可选，machine truth 只走 writer；`active_plan` 只含 `plan_id`，Wave / 任务进度来自方案文件。
  - 审计非 active plan 时绑定目标 `plan.md` digest，审计器只读、宿主通过 writer 写 `verify_NNN` receipt，active pointer / handoff 不变。
  - 不同 session 标识单独出现不得阻断；仅用户明确同时开发、宿主确认另一任务运行、或写入前出现非本轮已知状态变化时，才停止当前有副作用的开发并提示一次。
- [x] 3.3 在临时 fixture 启动不继承当前讨论的新 Codex 会话，执行一次上下文隔离回放；验收为陈旧 `active_plan` 不劫持普通问答、不自动写入状态，证据包含新会话标识、fixture 问题、执行命令与宿主版本、回答断言及前后 `state/` 文件清单与哈希。

## 4. 文档收口与验证

- [x] 4.1 对齐 `docs/how-sopify-works.md`、`docs/how-sopify-works.en.md`、`docs/getting-started.md` 及 `.sopify/blueprint/{README,design,tasks}.md`，运行定向测试、全量测试、protocol check 和 `git diff --check`；验收为 blueprint 只沉淀 active plan 纯指针、Verifier 只读 / host writer 写 receipt、session 标识仅作 provenance 三条稳定边界，不升格完整 Review Wire，也不扩大到 persistent MCP / doctor / 多宿主注册。

## 验收标准

- [x] 健康状态静默通过，consult / quick fix 不展示无关方案异常。
- [x] 缺 handoff / receipts 不被误判为阻断。
- [x] handoff 失配按 `plan.md` 继续，只提示一次。
- [x] checkpoint 首次出现时只展示一次；用户正在回答匹配 checkpoint 时先消费回答，不重显原问题。
- [x] 有效方案切换仍需用户确认；无效旧指针遇到明确 new plan 或明确且有效的 continue 目标时，不二次询问清理。
- [x] 同一轮同一冲突不重复检查、重复询问或重试。
- [x] `active_plan` 保持纯 `plan_id` 指针，不增加 Wave；Wave 和任务进度继续以方案文件为准。
- [x] 显式审计非 active plan 时，审计器只读并返回证据；宿主校验目标主体后通过 writer 写目标方案未占用的 `verify_NNN` receipt，active plan / handoff 不变；同名 receipt 已存在时拒绝覆盖并保留原证据。
- [x] 不以不同 session 标识误拦正常接续；仅约定的三类并行推进信号触发停止当前有副作用的开发，并展示一次中性提示。
- [x] 用户确认其他开发已停止后，必须重读最新方案状态再继续；不新增所有权、锁、租约或 session state。
- [x] 未注册 MCP 的宿主仍能仅按 4 步文件协议完成 managed action 入口。
- [x] 未新增 state 文件、MCP tool、诊断平台、自动修复或多宿主实测矩阵；单张架构 SVG 仅作总链路导读，不复制状态矩阵。
- [x] 一次 Codex 上下文隔离回放证明新会话未继承当前讨论，且该路径在代表宿主 Codex 中成立；不代表其他宿主已经实测。
