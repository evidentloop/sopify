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

- [x] 3.1 设计 Codex-only `register_mcp_config("codex")`：Codex MCP config matrix、注册边界、dry-run/apply 边界、冲突处理。
- [ ] 3.1R 评审 S3.1 设计，确认后再进入实现。
- [ ] 3.2 实现 Codex-only MCP config 注册。
- [ ] 3.3 Qoder / Claude / Copilot 配置路径实测后接入矩阵。
- [ ] 3.4 更新 host capability 声明和 doctor 检查。
- [ ] 3.5 S3 通过后再更新 README / docs / blueprint 长期说明。

### S3.1 设计记录 (2026-07-07)

- Codex 应用注册目标为用户级 `CODEX_HOME/config.toml`，默认 `~/.codex/config.toml`；项目级 `.codex/config.toml` 只做诊断输入，不写入仓库。
- 目标 server 为 `[mcp_servers.sopify]` stdio 配置，使用已验证 Python `>=3.11`、`args = ["scripts/sopify_mcp_server.py"]`、`cwd = "<workspace-root>"`。
- 注册默认 dry-run；apply 后续实现必须先备份/预检，且只在 server 缺失时追加 block，已有不同配置时 fail closed。
- 停止点：当前只完成设计，不实现 installer 注册，不扩展其他宿主。

## 验收标准

- [x] 首版 MCP server 可通过 stdio 启动。
- [x] S1 只读 tool 均返回结构化 JSON，且不依赖 shell 命令拼接。
- [x] 现有 CLI 行为保持兼容。
- [x] 不修改四个 host adapter 的能力声明。
- [x] `sopify.write_plan_receipt` 不写入或清理 `.sopify/state/active_plan.json`。
