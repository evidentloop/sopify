# 任务清单: MCP Tool Plane Pilot

目录: `.sopify/plan/20260626_mcp_tool_plane_pilot/`

## S1 Build + Test

- [x] 1.1 确认官方 Python `mcp` SDK 的最小 stdio server 示例和依赖声明方式。
- [x] 1.2 新增单文件 `scripts/sopify_mcp_server.py`，不新增 `sopify_mcp/` 包。
- [x] 1.3 实现 `sopify.get_active_plan` 和 `sopify.get_current_handoff`，复用 `ProtocolStore`。
- [x] 1.4 实现 `sopify.workspace_status_lite`，只做 `.sopify/` 基础结构和 active plan 指向检查。
- [x] 1.5 在 `scripts/sopify_protocol_check.py` 抽取 `run_protocol_check(workspace_root, scenario)`。
- [x] 1.6 实现 `sopify.protocol_check`，返回现有 `{scenario, verdict, failures, evidence}` 结构。
- [x] 1.7 保持 `sopify_protocol_check.py` CLI 行为、exit code 和 JSON 输出兼容。
- [x] 1.8 为 MCP tool 输入校验、lite status、protocol check 补测试。
- [x] 1.9 启动 MCP server，通过 stdio client smoke 调用 S1 tool。
- [x] 1.10 跑 `python3 -m pytest tests -v`，确认现有测试不回退。
- [x] 1.11 在 Codex / Qoder 手动注册 MCP server 作为主观察，验证 AI 能通过 MCP 读取 active plan 和执行 protocol check。
- [ ] 1.12 让 Claude / Copilot 参与兼容性观察，记录为 S3 输入。

### S1.11 手动观察记录

- [x] Codex 主观察：已发现并调用 Sopify MCP tools，未走 shell；`get_active_plan` 返回 `null`，`protocol_check(continuation)` 返回预期 `FAIL: Missing state/active_plan.json`，`workspace_status_lite` 返回结构化 workspace 状态。
- [x] Qoder 主观察：已验证 active plan、handoff、workspace status、三种 protocol_check scenario、错误处理和测试套件；Qoder 能通过 Sopify MCP/业务工具完成协议读取和检查，不需要拼 shell。
- [ ] Claude 兼容性观察：待验证。
- [ ] Copilot 兼容性观察：待验证。

### S1 go/no-go

- [x] Codex / Qoder 中 AI 能通过 MCP 完成 active plan 读取和 protocol check。
- [x] Codex / Qoder 手动观察中，AI 对同类动作不再优先拼 shell 命令。
- [ ] Claude / Copilot 参与兼容性观察；不阻塞 S1，记录为 S3 输入。
- [x] MCP server 启动和响应没有明显拖慢对话体验。
- [x] pytest 与 MCP stdio smoke 稳定通过。

若任一项失败，先停在 S1，调整 tool 名称、描述、依赖或错误处理，不进入 S2。

## S2A Write Plan Receipt

- [x] 2.1 收窄 S2A 范围：只做 `sopify.write_plan_receipt`，不做 `write_history_receipt` / `finalize_plan`。
- [x] 2.2 定义写入 tool 描述，明确 tool 只执行已确认的协议写入，不负责决策授权。
- [x] 2.3 定义 MCP tool 层 guard：workspace 合法、active plan 存在、plan id 匹配、plan.md 存在、receipt 不覆盖。
- [x] 2.4 实现 `sopify.write_plan_receipt`，guard 通过后委托 `ProtocolStore.write_plan_receipt`。
- [x] 2.5 补 S2A 写入 tool 测试：正常写入、active plan 缺失拒绝、非 active plan 拒绝、重复 receipt 拒绝、plan.md 不存在拒绝、workspace root 不合法错误格式。
- [x] 2.6 MCP stdio smoke 调用 `write_plan_receipt`，确认成功返回结构化 receipt 路径，guard 失败返回结构化 error。
- [x] 2.7 Qoder 手动验证：AI 能通过 MCP 写 plan receipt，不退回 shell 写文件，且重要拍板仍先停下来确认。

### S2A.2.6 stdio smoke 记录

- [x] 2026-07-07 使用临时 fixture `/private/tmp/sopify-mcp-fixture-*` 启动 `scripts/sopify_mcp_server.py` stdio server。
- [x] `sopify.write_plan_receipt` 成功写入临时 `exec_001.json`，返回 `{write_plan_receipt: {path}, error: null}`。
- [x] 重复写入同一 receipt 返回结构化 `{write_plan_receipt: null, error: {code: "FileExistsError", ...}}`，验证 no-overwrite guard。
- [x] 当前仓库活动 plan receipts 未写入或清理。

### S2A.2.7 Qoder 手动验证记录 (2026-07-07)

**调用的 MCP tool**:
- `sopify.write_plan_receipt` (主要验证目标)
- `sopify.workspace_status_lite` (辅助确认 fixture 状态)
- `sopify.get_active_plan` (辅助确认 active plan 读取)
- `sopify.protocol_check` (辅助确认协议检查)

**使用的 fixture 路径**:
- 主 fixture: `/Users/weixin.li/.qoder/tmp/-Users-weixin-li-code-github-sopify/sopify-s2a-fixture/`
  - `.sopify/state/active_plan.json`: plan_id = `test-plan-001`
  - `.sopify/plan/test-plan-001/plan.md`: 测试 plan 文档
- 缺 active_plan fixture: `sopify-s2a-no-active/`
- 缺 plan.md fixture: `sopify-s2a-no-planmd/`

**成功写入返回**:
```json
{
  "write_plan_receipt": {
    "path": ".../sopify-s2a-fixture/.sopify/plan/test-plan-001/receipts/verify_001.json"
  },
  "error": null
}
```
Receipt 内容包含 `verdict: "pass"`, `evidence`, `provenance`, `timestamp`，符合 ProtocolStore 规范。

**Guard 失败返回**:
1. **重复 receipt**: `{error: {code: "FileExistsError", message: "plan receipt already exists: ..."}}`
2. **非 active plan**: `{error: {code: "ValueError", message: "plan_id must match active plan: test-plan-001"}}`
3. **缺 active_plan.json**: `{error: {code: "ValueError", message: "active plan is missing"}}`
4. **缺 plan.md**: `{error: {code: "ValueError", message: "active plan plan.md not found: ..."}}`

**绕过倾向观察**:
- ✓ 未尝试绕过 `required_host_action` 直接调用写入
- ✓ 未尝试跳过用户确认步骤
- ✓ 未尝试调用不存在的 `finalize_plan` 或 `write_history_receipt`
- ✓ 未尝试建议新增高层工作流 tool
- ✓ 所有写入均通过 MCP tool，未退回 shell `echo` / `cat <<EOF` 手写 JSON

**验证方法**:
1. 直接 Python 调用 `write_plan_receipt` 函数：5/5 通过
2. MCP stdio client 调用：5/5 通过
3. 当前仓库 `.sopify/plan/20260626_mcp_tool_plane_pilot/receipts/` 未写入任何测试 receipt

### S2A go/no-go

- [x] `write_plan_receipt` 不手写 JSON / Markdown，只调用 `ProtocolStore.write_plan_receipt`。
- [x] guard 不满足时必须拒绝写入并返回结构化 error。
- [x] 不独立暴露 `write_history_receipt`。
- [x] 不暴露 `finalize_plan`。
- [x] 不提供 `approve_and_finalize`、`continue_and_finalize` 等高层工作流 tool。
- [x] Qoder 手动试点未观察到 AI 绕过 `required_host_action`、用户明确指令或 finalize 意图分叉。
- [x] **S2A go**: 所有验证通过，MCP tool 行为符合设计，guard 严格，无绕过倾向。

## S3 Multi-host

- [x] 3.1 设计 Codex-first `register_mcp_config("codex")`：最小注册入口、dry-run/apply 边界、冲突处理。
- [x] 3.1R 完成 S3.1 评审：Codex 是首个验证对象，不是唯一满足条件的宿主；删除自动依赖安装、payload 改造和自建 TOML 合并器等超前设计。
- [x] 3.2A 实现预检与 dry-run：验证 Codex CLI、现有 Python/MCP 环境和绝对 server 路径，使用 `codex mcp get sopify --json` 判定状态。
- [x] 3.2B 实现显式 apply：仅 absent 时调用 `codex mcp add`，same 时 no-op，conflict 时拒绝覆盖。
- [x] 3.2C 补最小单元测试与一次 Codex 手动注册 smoke，记录证据后暂停。
- [-] 3.3 基于 Codex 试点证据继续验证 Qoder / Claude / Copilot；转入蓝图长期待办，延后不代表不满足接入条件。
- [-] 3.4 更新 host capability 声明和 doctor 检查；当前证据不足，不为 repo-local 试点改变产品能力声明。
- [x] 3.5 同步 maintainer docs、CHANGELOG、project 与 blueprint；公开 README 保持不变，因为当前仍是 repo-local 维护者试点。

### S3.1 评审记录 (2026-07-16)

- Codex 是首个验证对象，用于先形成一条注册证据；不是对其他宿主能力的排他判断。
- 注册复用 `codex mcp get/add`，使用绝对 Python 与 server 路径，不手写或 round-trip 用户 TOML。
- 试点只消费现有 Python/MCP 环境；缺依赖时可见失败，不自动安装、不改 payload。
- 默认 dry-run；apply 必须显式触发，已有不同配置时 fail closed。
- 停止点已兑现：S3.2 经用户确认后完成 Codex smoke；扩展其他宿主前回到蓝图证据项重新评估。

### S3.2 实施与验证记录 (2026-07-16)

- [x] `scripts/sopify_mcp_register.py` 已实现：默认 dry-run，显式 `--apply`，配置相同 no-op，配置冲突 fail closed。
- [x] 目标单元测试 21 passed；全量测试 216 passed，另含 28 passed subtests。
- [x] public docs check、continuation protocol check、`py_compile` 与 `git diff --check` 均通过。
- [x] 使用 `/Users/liweixin/.local/sopify-py311` 的 Python 3.11 环境验证 `mcp==1.28.1`；依赖安装是本次环境准备，不进入注册脚本产品边界。
- [x] 真实 Codex 用户级注册成功；`codex mcp get sopify --json` 确认启用且 command/args 与期望一致，再次 dry-run 返回 `noop`。
- [x] MCP stdio smoke 列出 5 个 tools，并成功调用 `sopify.get_active_plan`，返回当前活动 plan 且 `is_error=false`。
- [-] CrossReview advisory：本机 CLI 仅支持 `pack --diff`，不支持 skill 要求的 staged/unstaged 隔离输入；按技能前置条件明确跳过，不伪造审查结果，也不创建临时 commit。
- [x] `ProtocolStore.finalize_plan` 写入 final/history receipts 并清空活动状态；仅包含本次归档的 finalize fixture 检查 PASS。
- [-] 仓库级 finalize checker 会同时审计全部 pre-P8 history，因旧归档缺新式 receipts 而失败；这是既有历史债，不在本次试点中批量回填或改造 checker。

### S3.2 独立审查后最小修复 (2026-07-16)

- [x] disabled 的同路径配置不再误报 `noop`，而是 fail closed 为 conflict；不自动改回用户开关。
- [x] Python / Codex 可执行文件启动失败统一进入现有结构化 JSON error，不再泄漏 traceback。
- [x] preflight 与 server 声明对齐，只接受 Python 3.11+、`mcp[cli]>=1.27,<2` 且可导入 `FastMCP` 的已有环境。
- [x] 测试保持局部：新增 3 个测试方法；定向 24 passed + 2 subtests，全量 219 passed + 30 subtests。
- [x] 真实 Codex dry-run 仍为 `noop`，MCP stdio smoke 仍列出 5 个 tools 且调用成功。
- [x] 通过 `ProtocolStore` 写入 `verify_002` 并重发 final/history receipts；final 使用稳定相对引用 `receipts/verify_002.json`。
- [x] 未加入依赖安装、完整握手、并发锁、doctor 或多宿主抽象。

## 验收标准

- [x] 首版 MCP server 可通过 stdio 启动。
- [x] S1 只读 tool 均返回结构化 JSON，且不依赖 shell 命令拼接。
- [x] 现有 CLI 行为保持兼容。
- [x] 不修改四个 host adapter 的能力声明。
- [x] `sopify.write_plan_receipt` 不写入或清理 `.sopify/state/active_plan.json`。
