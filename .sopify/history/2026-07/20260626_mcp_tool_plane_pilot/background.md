# 变更提案: MCP Tool Plane Pilot

## 需求背景

Sopify 当前是 Protocol-first / Convention 模式：宿主通过 prompt 消费工作流规则，确定性写入由 `sopify_writer` 和脚本承担。这个形态便携，但 AI 在执行协议检查、状态读取、receipt 写入时仍可能通过 shell 拼命令或手工写文件，存在参数误用和协议绕行风险。

用户明确提出 MCP 与 CLI / hook 的边界问题，并希望在不一次性改造四个宿主的前提下，评估把 Sopify 的确定性能力暴露为 MCP tool 的方案。

评分:
- 方案质量: 8/10
- 落地就绪: 7/10

评分理由:
- 优点: 方案沿用现有 `sopify_writer` 与 `sopify_protocol_check`，先做单文件只读 pilot，不推翻 CLI / prompt 架构。
- 扣分: MCP SDK、Qoder 配置路径和模型是否优先调用 tool 需要实测确认；首版不承诺 installer 自动注册。

## 变更内容

1. S1 Build + Test：新增单文件 `scripts/sopify_mcp_server.py`，先暴露只读/检查类工具：`protocol_check`、`get_active_plan`、`get_current_handoff`、`workspace_status_lite`。
2. S1 只做 Qoder 手动注册试点，不新增 `sopify_mcp/` 包，不改 installer，不改 host adapter 声明。
3. S2A Write Plan Receipt：Codex / Qoder 主观察通过后，先只开放 `write_plan_receipt` 一个低层写入 tool；`write_history_receipt` 与 `finalize_plan` 暂缓，等写入观察和授权承接方式明确后再决策。
4. S3 Codex-first 注册：写入 tool 稳定后，先在 Codex 验证最小注册路径，再用实测结果扩展其他已支持宿主；这是验证顺序，不是宿主能力排他判断。
5. 保留 CLI 作为安装、CI、人类运维入口；MCP 作为 AI tool plane，不替代 CLI / installer。

## 影响范围

- 模块:
  - `sopify_writer/`
  - `sopify_contracts/`
  - `scripts/sopify_protocol_check.py`
  - `tests/`
- 文件:
  - 新增 `scripts/sopify_mcp_server.py` 作为 stdio 启动入口
  - 可能小幅调整 `scripts/sopify_protocol_check.py`，抽取可 import 的 `run_protocol_check(...)`
  - 新增 MCP server 测试文件
  - S3 才可能改 `installer/` 和 host capability 声明

## 风险评估

- 风险: 一次性把四个宿主都改成 MCP 注册会扩大 blast radius，并引入宿主配置差异。
- 缓解: S1 只交付可手动运行的 MCP server 和测试，只在 Qoder 手动注册验证。

- 风险: 写入类 MCP tool 可能让 AI 绕过现有 prompt checkpoint。
- 缓解: S1 只读；S2 写入工具必须保持低层语义，只写 state / receipt，不提供 `approve_and_finalize` 这类高层工作流 tool，并继续依赖 prompt 的“重要拍板先停”规则。

- 风险: CLI / MCP 两套入口产生逻辑分叉。
- 缓解: CLI 与 MCP 共用 Python 函数，CLI 只负责 argparse/render，MCP 只负责 JSON-RPC tool schema。

- 风险: MCP pilot 只证明“能跑”，不能证明“值得产品化”。
- 缓解: S1 设置 go/no-go 标准：AI 能通过 MCP 完成 active plan 读取和 protocol check；没有明显启动/响应延迟；Codex / Qoder 主观察中 AI 不再优先拼 shell 命令完成同类动作。当前 Codex / Qoder 主观察已通过，Claude / Copilot 兼容性观察作为 S3 输入，不阻塞 S2A。
