# 项目技术约定

## Runtime 快照
- 项目名：sopify
- 工作目录：项目根目录
- 运行时目录：`.sopify`
- 根配置：`sopify.config.yaml`
- 已识别清单：暂未识别
- 已识别顶层目录：tests、docs、scripts

## 使用约定
- 这里只沉淀可复用的长期技术约定。
- 一次性实现细节不默认写入本文件。
- 当约定发生变化时，应以代码现状为准并同步更新。

## Plan 归档约定
- Plan 归档到 `history/` 后，`plan/` 下的同名原件**必须删除**，避免双驻留。
- `lifecycle_state` 在 history 副本中须改为 `archived`（或 `completed`，视收口结论）。
- 唯一例外：`lifecycle_state: deferred` 的 plan 尚未归档，保留在 `plan/` 下。

## 文档边界
- `project.md`：只放跨任务可复用的技术约定。
- `blueprint/background.md`：放长期目标、范围与非目标。
- `blueprint/design.md`：放模块、宿主、目录与知识消费契约。
- `blueprint/tasks.md`：只保留未完成长期项与明确延后项。

## Protocol Kernel 实现与测试约定

- `sopify_writer/` 是 protocol state 与 receipts 的唯一写路径；`ProtocolStore` 通过 `sopify_writer.store` 访问。
- `sopify_contracts/` 定义 schema 与共享数据结构（`RuntimeHandoff` 等），是所有写回操作的契约基线。
- `installer/` 负责 payload 分发、workspace bootstrap、doctor/inspection；不再打包 `runtime/` 目录。
- repo-local 测试统一使用 `python3 -m pytest tests -v`；测试文件按 `test_sopify_writer` / `test_installer` / `test_distribution` / `protocol/` 分组。
- `runtime/` 目录已在 P8 W2.10 物理删除（46 文件 / ~15.6K LOC）；不再存在 runtime facade、runtime engine、runtime gate。
- `scripts/sopify_protocol_check.py` 是 CI/preflight 协议合规 smoke（3 场景：new-plan / continuation / finalize）；不得 import runtime。

## MCP Tool Plane 约定

- repo-local MCP server 固定为 `scripts/sopify_mcp_server.py`；它只暴露确定性协议能力，不承接工作流判断或用户拍板。
- Codex-first 注册试点入口为 `scripts/sopify_mcp_register.py`，配置写入必须委托宿主官方 CLI，不直接改写用户配置文件。
- 当前试点消费已有 Python 3.11+ 与 `mcp[cli]>=1.27,<2` 环境。依赖供给、payload 打包、doctor 集成及其他宿主自动注册须先有跨宿主实测证据，不作为现阶段产品契约。

## Develop 质量约定

- `continue_host_develop` 仍是宿主负责真实代码修改的正式模式；sopify_writer 负责 handoff 落盘与 receipts 写回。
- develop 质量循环的正式发现顺序固定为：`.sopify/project.md verify` > 项目原生脚本/配置 > `not_configured` 可见降级。
- develop 质量结果的正式字段固定为：`verification_source / command / scope / result / reason_code / retry_count / root_cause / review_result`。
- `result` 的稳定值域固定为：`passed / retried / failed / skipped / replan_required`；`root_cause` 的稳定值域固定为：`logic_regression / environment_or_dependency / missing_test_infra / scope_or_design_mismatch`。
- 当 `result == replan_required` 或 `root_cause == scope_or_design_mismatch` 时，宿主不得继续盲修；必须停下来向用户报告根因并等待方向指示。
- 当前仓库暂不在 `project.md` 固定单一默认 verify 命令；在解释器基线统一到 Python 3.11+ 之前，未识别到稳定命令时应走 `not_configured` 可见降级，而不是假定默认测试入口存在。
