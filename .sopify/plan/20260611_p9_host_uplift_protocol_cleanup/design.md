# P9 Design Baseline

本文定位：P9 方案级设计基线。只放 P9 特有的架构裁定、波次契约与边界声明。长期架构真相以 `blueprint/design.md` 为准，本文不重复。

## 1. 定位锚点

> runtime 曾经是真实产品形态；P8/P9 不是否定 runtime，而是把 runtime 里验证过的流程纪律，从中心化控制进程迁移到轻量协议资产和验收矩阵里。

P9 的产品判断：

- runtime 的"中心化控制进程"形态被宿主吸收（Codex / Claude / Qoder / Copilot 都在做 session resume / memory / review / orchestration）
- runtime 证明过的 6 条流程纪律（意图分流 / 复杂度先 plan / 缺事实就停 / handoff 恢复 / evidence before done / stale guard）是真实需求
- P9 用 W1 验收矩阵把这 6 条纪律折叠进协议层验收，不需要 runtime 复活

## 2. 架构裁定

### 2.1 真相源继承 P8，不新加

| 真相 | 归属 | P9 动作 |
|---|---|---|
| 协议规范 | `blueprint/protocol.md` | W3 重写活跃 prose |
| state 写入 | `sopify_writer` | 不动 |
| schema | `sopify_contracts` | 不动 |
| receipts / handoffs / history | `plan/<id>/receipts/` + `history/<id>/receipt.md` | W1/W2 产出 evidence |
| 宿主 adapter | `installer/hosts/{codex,claude,qoder,copilot}.py` | W2 改 copilot.py |
| 薄工具 | `scripts/sopify_{status,doctor,protocol_check,init}.py` | W4 审计决策 |

### 2.2 版本模型先裁定，再修复

P9 暴露出的版本漂移不是单个文件问题，而是三层版本语义未闭环：

| 层 | 字段 | 当前问题 | P9 裁定 |
|---|---|---|---|
| release/payload | `payload_version` | 能是当前 release | 表示安装 payload 版本 |
| bundle | `active_version` + bundle `manifest.json.bundle_version` | 可能落到 `0.0.0-dev` | stable/release/dogfood 不得静默 dev fallback |
| workspace marker | `.sopify/sopify.json.bundle_version` | 可能长期 pin 旧版本 | 必须明确 exact pin / host-delegated / dogfood release-sync 三种合法状态 |

P9 不直接把 `.sopify/sopify.json` 改成当前 release 来制造表面一致；先确定合法模式，再改实现、文档和诊断。

**范围声明（受控改 Sopify-core）**：W0 允许对 Sopify-core 安装器做**最小受控修复**——因为外部用户安装最新 Sopify 也会遇到同类漂移，只修 Sopify 自身 dogfood 仓库是治标不治本。允许修改的模块：

- `installer/sopify_bundle.py`（bundle manifest 版本来源语义）
- `scripts/sopify_init.py`（已有 marker 的升级行为）
- `installer/bootstrap_workspace.py`（stale workspace pin 处理与诊断）
- `scripts/sopify_status.py` / `scripts/sopify_doctor.py`（drift 展示）

**不允许**：安装器整体重构、新增 install 子命令、改变宿主 adapter 语义、重写 `sopify_writer` / `sopify_contracts`。所有修复必须先写清规则（W0B 裁定），再补最小回归测试，再改代码。

### 2.3 不新增 machine truth

P9 不得新增：

- state 文件（保持 `active_plan.json + current_handoff.json` 2 文件）
- action / route / checkpoint 类型
- receipt 字段（P8 已定型）
- 宿主能力 tier（沿用 `installer.models.SupportTier` 现有枚举：`PROTOCOL_VERIFIED / BASELINE_SUPPORTED / DOCUMENTED_ONLY / EXPERIMENTAL`）

W2 Copilot 的目标是提供足够证据支持升到 `PROTOCOL_VERIFIED`；若平台硬限制导致证据不足，保持 `BASELINE_SUPPORTED` 并记录缺口，不新增 tier。

### 2.4 CLI 边界声明

P9 W4 决策前的默认立场：

**允许讨论**：

- `sopify status`：薄封装 `sopify_status.py`
- `sopify doctor`：薄封装 `sopify_doctor.py`
- `sopify protocol-check --ci`：薄封装 `sopify_protocol_check.py`
- `sopify init`：薄封装 `sopify_init.py`

**显式排除**：

- `sopify run` / `sopify route` / `sopify gate`
- 任何自动决定工作流路线的 CLI
- 替代宿主执行任务的 CLI
- 替宿主写 state/receipt 的默认路径（`sopify_writer` 库 API 是默认路径；CLI wrapper 只在宿主不便 import Python 时存在）

**第一价值**：人和 CI。第二价值：宿主执行流。

## 3. 波次契约

### 3.1 W0 → W1 gate

W0 完成且以下条件成立，方可启动 W1：

- active truth drift gate 4 条全 PASS
- workspace marker 版本语义已裁定：exact pin / host-delegated / dogfood release-sync
- payload / bundle / marker 5 个版本锚点审计全 PASS
- release/stable/dogfood 场景未静默落到 `0.0.0-dev`；若 local dev 允许 `0.0.0-dev`，必须显式标记 dev channel
- Sopify-core 安装器最小修复（`sopify_bundle.py` / `sopify_init.py` / `bootstrap_workspace.py` / `status` / `doctor`）已实现并补回归测试；或显式登记进 W4 决策表（若判定应延后）
- `.github/copilot-instructions.md` 与安装源一致
- `plan/20260418_cross_review_engine/` 状态已裁定（deferred 归档或写明保留原因）

### 3.2 W1 → W2 gate

W1 完成且以下条件成立，方可启动 W2：

- 4 宿主 × 7 场景的 evidence 已落 `assets/w1_gaps.md`
- Copilot gap 已分类（平台硬限制 vs 可修 gap）
- W1 结论不假装 4 宿主等价（Copilot 是 BASELINE，其他 3 是 VERIFIED）

### 3.3 W2 → W3 gate

W2 完成且以下条件成立，方可启动 W3：

- Copilot 可修 gap 已处理
- Copilot 复跑 S1-S7，并形成明确结论：7/7 PASS 后升 `PROTOCOL_VERIFIED`；否则保持 `BASELINE_SUPPORTED` 并记录平台限制、用户影响、后续触发条件
- W1/W2 累积 evidence 已够驱动 prose 重写

### 3.4 W3 → W4 gate

W3 完成且以下条件成立，方可启动 W4：

- `protocol.md` / `design.md` / `background.md` 活跃 prose 不再靠术语映射兜底
- 完成 asset inventory 全量扫描：`assets/` + `assets/readme-visuals/` + README/docs 实际引用的所有图逐项裁定（重画 / 保留 / 历史标注 / 删除），不预设具体数量
- 至少 2 张正式 SVG 图产出（产品形态图 + 协议资产图），数量上不封顶（依赖 W3.3 全量扫描结论）；`assets/p9-product-form-v2-draft.svg`（V2 草稿，Style 8 手写）仅作内部草图，不作为正式图基线
- `blueprint/README.md` 当前焦点区块已刷新

### 3.5 W4 → Finalize gate

W4 完成且以下条件成立，方可 finalize：

- 4 脚本审计表进 `assets/w4_tooling_audit.md`
- 3 选项对比表 + 推荐项 + 理由已写
- `sopify_protocol_check.py --ci` 是否纳入 workspace pin vs payload active_version drift 检查已有明确结论
- ADR 草稿（若推荐封装）已进 `blueprint/architecture-decision-records/`
- 所有波次 acceptance 全 PASS

## 4. 与长期蓝图的关系

P9 产出回写蓝图的位置：

| P9 产出 | 回写目标 |
|---|---|
| W3 重写的活跃 prose | `blueprint/background.md` / `protocol.md` / `design.md` |
| W3 新图 | `assets/*.svg` + `README.md` / `README.zh-CN.md` 引用 |
| W4 ADR 草稿（若） | `blueprint/architecture-decision-records/ADR-0XX.md` |
| P9 结论 | `blueprint/README.md` 当前焦点区块 |
| P9 归档 | `history/2026-06/20260611_p9_host_uplift_protocol_cleanup/` |

P9 **不**回写：

- `blueprint/tasks.md` 主航道（P8 已是 P0→P8 最后一条主航道；P9 不拿 P 编号）
- `blueprint/design.md` 核心契约（除非 W4 ADR 需要）

## 5. 风险与边界

- **不补"强制力焦虑"**：P8 的 trade-off 是用强制力换可移植性，P9 不应偷偷复活。W4 决策时必须显式回答"是否引入了新的流程强制力"。
- **不预设 CLI 一定要做**：W4 允许"不封装"结论。审计结果可能就是"4 个独立脚本 + 文档够用"。
- **不扩宿主面**：P9 使命是证明 P8 后的 4 宿主协议能跑，第 5 个宿主是 P10 的事。
- **不做 normative 升格**：P8 刚 freeze 协议内核，P9 不应再开 normative 面。
