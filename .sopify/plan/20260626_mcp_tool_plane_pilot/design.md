# 技术设计: MCP Tool Plane Pilot

## 技术方案

- 核心技术: Python MCP server over stdio，复用现有 Python 模块。
- 实现要点:
  - S1 使用单文件 `scripts/sopify_mcp_server.py`，不新增 `sopify_mcp/` 包；文件内部按 workspace 校验、纯业务函数、MCP tool 绑定三层组织，保留后续拆包空间但不提前抽象。
  - MCP SDK 选型为官方 Python `mcp` SDK 稳定线（`mcp[cli]>=1.27,<2`）；v2 仍为预发布线，不作为 S1 基线。
  - 不重写 installer，不改变当前 prompt-only 宿主安装路径。
  - MCP tool 只包确定性能力，不把 `analyze/design/develop` 推理工作流做成 tool。
  - S1 不 import `installer.inspection`；`workspace_status_lite` 只检查 `.sopify/` 基础结构、active plan、handoff 和 plan 目录。
  - 协议检查 tool 复用 `scripts/sopify_protocol_check.py` 中的 runner 函数，明确抽取 `run_protocol_check(workspace_root, scenario)`。
  - S2 写入类 tool 统一委托 `ProtocolStore`，不得手写 JSON / Markdown。

## 架构设计

```text
Host LLM
  ├─ prompt / skill: 工作流判断、checkpoint、用户沟通
  ├─ shell / CLI: 安装、CI、人类运维
  └─ MCP tool plane
       └─ scripts/sopify_mcp_server.py
            ├─ workspace_status_lite: lightweight workspace inspection
            ├─ scripts.sopify_protocol_check: protocol_check
            └─ sopify_writer.ProtocolStore: state / receipts
```

### 边界划分

| 能力 | 保留 CLI | 暴露 MCP | 原因 |
|------|----------|----------|------|
| install / update / uninstall | 是 | 否 | MCP 不能安装自己，也不适合做用户运维入口 |
| full status / doctor | 是 | 否 | installer 级诊断依赖链重，S1 不引入 |
| workspace_status_lite | 否 | 是 | S1 只提供最小结构检查，避免混淆完整 status/doctor 语义 |
| protocol_check | 是 | 是 | CI 继续走 CLI，AI 通过 MCP 降低调用摩擦，不再拼 shell 命令或猜参数 |
| active_plan / current_handoff 读取 | 否 | 是 | AI 接续时高频需要，结构化读取更稳 |
| plan receipt 写入 | 暂保留库调用 | S2A | 只开放 `write_plan_receipt`，先验证低层写入 tool 是否稳定 |
| history receipt / finalize 写入 | 暂保留库调用 | 后续阶段 | 独立 history receipt 语义不清；finalize 需要先明确 tool 如何承接 host 已完成的收口决策 |
| analyze / design / develop | 否 | 否 | 推理型工作流保留 prompt/skill 形态 |
| host MCP 注册 | installer 后续支持 | 否 | S1 只做手动注册观察，不改 installer |

### S1 工具清单

1. `sopify.protocol_check`
   - 输入: `workspace_root`、`scenario` (`new-plan` / `continuation` / `finalize`)
   - 输出: `{protocol_check: {scenario, verdict, failures, evidence}, error: null|{code, message}}`

2. `sopify.get_active_plan`
   - 输入: `workspace_root`
   - 输出: `active_plan.json` 内容或 `null`

3. `sopify.get_current_handoff`
   - 输入: `workspace_root`
   - 输出: `current_handoff.json` 内容或 `null`

4. `sopify.workspace_status_lite`
   - 输入: `workspace_root`
   - 输出: `.sopify/` 是否存在、`blueprint/` / `plan/` / `history/` / `state/` 是否存在、active plan 指向的 plan 目录是否存在、handoff 是否存在

### S1 go/no-go 标准

| 信号 | 判定 |
|------|------|
| Codex / Qoder 中 AI 能通过 MCP 完成 active plan 读取和 protocol check | go S2 |
| Codex / Qoder 中 AI 仍优先拼 shell 命令完成同类动作 | stop，先调整 tool 名称和描述 |
| MCP server 启动或响应延迟明显影响对话体验 | stop，先排查依赖和启动开销 |
| pytest / MCP stdio smoke 不稳定 | stop，先补测试和错误处理 |

说明：`AI 优先调 MCP` 是手动试点观察项，不属于 pytest 自动化验收。Codex / Qoder 为主观察对象；Claude / Copilot 参与兼容性观察，但不阻塞 S1 收口，观察结论作为 S3 输入。

### S2A 写入工具

S2A 只开放一个低层写入 tool：

1. `sopify.write_plan_receipt`

该工具不得手写 JSON / Markdown 文件，必须调用 `ProtocolStore.write_plan_receipt`。

S2A 的核心风险不是“写入 tool 有没有价值”，而是写入 tool 是否让 AI 绕过协议中的 `required_host_action`、用户明确指令或 finalize 意图分叉。工具设计必须满足：

- 不提供 `approve_and_finalize`、`continue_and_finalize` 等高层工作流 tool。
- tool description 明确：工具只执行已确认的协议写入，不负责决策授权。
- 写入前提来自 host / skill / protocol 已完成的判断，而不是 MCP tool 自行判断。
- `write_history_receipt` 不在 S2A 独立暴露；当前只允许作为后续 finalize 语义的一部分再设计。
- `finalize_plan` 不在 S2A 暴露；暂缓原因是需要明确 tool 如何承接 host 已完成的收口决策，而不是底层清理动作本身不安全。

#### S2A `write_plan_receipt` 合约

`write_plan_receipt` 的 MCP tool 层必须在调用 `ProtocolStore.write_plan_receipt` 前执行以下 guard。任一 guard 不满足时，必须返回结构化 `{write_plan_receipt: null, error: {code, message}}`，不得 best-effort 写入。

| Guard | 合约 |
|-------|------|
| workspace root 合法 | 复用 S1 `resolve_workspace_root`，要求路径存在且为目录 |
| active plan 存在 | `.sopify/state/active_plan.json` 缺失时拒绝写入 |
| plan id 匹配 | 输入 `plan_id` 必须等于 active plan 中的 `plan_id` |
| plan.md 存在 | `.sopify/plan/<plan_id>/plan.md` 必须存在 |
| receipt 不覆盖 | 目标 receipt 文件已存在时拒绝写入 |

S2A 明确不做 receipt 序号连续校验。`exec_` / `verify_` 双序列、失败重试和人工补写的语义留到 S2A 观察后再决定。

S2A 不引入并发锁。顺序调用下必须保证 no-overwrite；并发写入同一 receipt id 时的强一致行为留到后续阶段评估。

### S3 Multi-host 注册

S3 在 S1/S2 证明 MCP 价值后进行。目标是让 installer 增加 MCP config 注册能力，覆盖已支持宿主的配置差异。MCP server 仍是一份代码，多宿主差异只落在配置路径和格式。

## 安全与性能

- 安全:
  - `workspace_root` 必须 resolve 后存在且为目录。
  - 写入工具 S1 不开放；S2A 只开放 `write_plan_receipt`，禁止绝对路径目标参数，只接受 workspace root + active plan id + receipt 字段。
  - MCP tool 错误返回要包含可恢复原因，不直接吞异常。
- 性能:
  - S1 不 import `installer.inspection`，降低启动依赖面。
  - `workspace_status_lite` / `protocol_check` 都是本地文件扫描，首版无需缓存。
  - MCP server 常驻后避免 AI 每次通过 shell 启动 Python 脚本，但不要为此引入复杂状态。

## 测试策略

1. 单元测试:
   - tool 输入校验。
   - `workspace_status_lite` 输出结构测试。
   - `protocol_check` 三种 scenario 输出保持现有语义。

2. 集成测试:
   - 启动 MCP server 后通过 stdio client 调用 S1 只读 tool。
   - fixture 覆盖 active plan 存在、handoff 缺失、protocol fail 三类场景。

3. 回归测试:
   - `python3 -m pytest tests -v`
   - 保留现有 CLI 测试，确保 CLI 输出不因 MCP 模块化回退。

4. S2A 写入测试:
   - `write_plan_receipt` 正常写入当前 active plan。
   - `active_plan.json` 不存在时拒绝。
   - 输入非 active plan id 时拒绝。
   - 目标 receipt 已存在时拒绝。
   - active plan 指向的 `plan.md` 不存在时拒绝。
   - workspace root 不合法时沿用 S1 结构化错误 envelope。
   - 并发写入同一 receipt id 不作为 S2A 强一致验收；至少不得破坏已有 receipt。

## 非目标

- 不在首版修改四个 host adapter。
- 不在首版把 installer 写 MCP 配置。
- 不在首版引入完整 status / doctor。
- 不把 Sopify workflow prompt 改写为 MCP tool。
- 不引入 hook 拦截能力；hook 与 MCP 属于不同平面。
- S2A 不开放 `write_history_receipt` / `finalize_plan` / `set_active_plan` / `set_current_handoff`。
