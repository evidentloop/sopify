# 任务清单: MCP Tool Plane Pilot

目录: `.sopify/plan/20260626_mcp_tool_plane_pilot/`

## S1 Build + Test

- [ ] 1.1 确认官方 Python `mcp` SDK 的最小 stdio server 示例和依赖声明方式。
- [ ] 1.2 新增单文件 `scripts/sopify_mcp_server.py`，不新增 `sopify_mcp/` 包。
- [ ] 1.3 实现 `sopify.get_active_plan` 和 `sopify.get_current_handoff`，复用 `ProtocolStore`。
- [ ] 1.4 实现 `sopify.workspace_status_lite`，只做 `.sopify/` 基础结构和 active plan 指向检查。
- [ ] 1.5 在 `scripts/sopify_protocol_check.py` 抽取 `run_protocol_check(workspace_root, scenario)`。
- [ ] 1.6 实现 `sopify.protocol_check`，返回现有 `{scenario, verdict, failures, evidence}` 结构。
- [ ] 1.7 保持 `sopify_protocol_check.py` CLI 行为、exit code 和 JSON 输出兼容。
- [ ] 1.8 为 MCP tool 输入校验、lite status、protocol check 补测试。
- [ ] 1.9 启动 MCP server，通过 stdio client smoke 调用 S1 tool。
- [ ] 1.10 跑 `python3 -m pytest tests -v`，确认现有测试不回退。
- [ ] 1.11 在 Qoder 手动注册 MCP server，验证 AI 能通过 MCP 读取 active plan 和执行 protocol check。

### S1 go/no-go

- [ ] AI 能通过 MCP 完成 active plan 读取和 protocol check。
- [ ] Qoder 手动观察中，AI 对同类动作不再优先拼 shell 命令。
- [ ] MCP server 启动和响应没有明显拖慢对话体验。
- [ ] pytest 与 MCP stdio smoke 稳定通过。

若任一项失败，先停在 S1，调整 tool 名称、描述、依赖或错误处理，不进入 S2。

## S2 Write Tools

- [ ] 2.1 设计写入 tool 描述，明确 tool 只执行已确认的协议写入，不负责决策授权。
- [ ] 2.2 实现 `sopify.write_plan_receipt`，委托 `ProtocolStore.write_plan_receipt`。
- [ ] 2.3 实现 `sopify.write_history_receipt`，委托 `ProtocolStore.write_history_receipt`。
- [ ] 2.4 实现 `sopify.finalize_plan`，委托 `ProtocolStore.finalize_plan`。
- [ ] 2.5 补写入 tool 的不变量测试和 checkpoint 绕过风险测试说明。
- [ ] 2.6 Qoder 手动验证：重要拍板仍先停下来确认，不通过 MCP tool 一步跳过。

### S2 go/no-go

- [ ] 写入 tool 不手写 JSON / Markdown，只调用 `ProtocolStore`。
- [ ] 不提供 `approve_and_finalize`、`continue_and_finalize` 等高层工作流 tool。
- [ ] 手动试点未观察到 AI 绕过 checkpoint。

## S3 Multi-host

- [ ] 3.1 设计 `register_mcp_config(host_id)`，把多宿主差异限制在配置路径和格式。
- [ ] 3.2 Qoder 自动注册落地。
- [ ] 3.3 Claude / Codex / Copilot 配置路径实测后接入。
- [ ] 3.4 更新 host capability 声明和 doctor 检查。
- [ ] 3.5 S3 通过后再更新 README / docs / blueprint 长期说明。

## 验收标准

- [ ] 首版 MCP server 可通过 stdio 启动。
- [ ] S1 只读 tool 均返回结构化 JSON，且不依赖 shell 命令拼接。
- [ ] 现有 CLI 行为保持兼容。
- [ ] 不修改四个 host adapter 的能力声明。
- [ ] 不写入或清理 `.sopify/state/active_plan.json`。
