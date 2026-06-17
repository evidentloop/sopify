# Plan Snapshot

- **Goal**: 给 `installer/hosts/` 下 codex / claude / qoder / copilot 四个宿主适配器文件补模块级 docstring，说明 support_tier / entry mode / 关键特性，不改现有逻辑
- **Status**: planned
- **Next**: Session B 续接，按 Waves/Steps 执行 docstring 插入并跑 smoke 验证
- **Level**: light
- **Plan ID**: 20260617_host_docstrings
- **Host**: Qoder (Session A 创建，待 Session B 续接)

---

## 1. Context / Why

`installer/hosts/` 目录下有四个宿主适配器：`codex.py`、`claude.py`、`qoder.py`、`copilot.py`。每个文件目前只有类定义，缺少模块级 docstring 来说明：

- 该宿主属于哪个 `support_tier`（tier-1 / tier-2 / tier-3）
- 入口模式（`cli` 还是 `ide-extension`）
- 关键特性（tool surface、权限模型差异等）

新贡献者或跨宿主调试时，需要打开文件读代码才能拼出这些信息。本 plan 的目标是在每个文件顶部补一段模块级 docstring，作为"一眼可见"的宿主速查卡。

触发条件：W1a 三宿主冒烟前，需要先让四个适配器有自描述能力，方便后续 S3/S5/S6 场景复用。

## 2. Scope

**做什么：**

- 给 `installer/hosts/codex.py` 补模块级 docstring
- 给 `installer/hosts/claude.py` 补模块级 docstring
- 给 `installer/hosts/qoder.py` 补模块级 docstring
- 给 `installer/hosts/copilot.py` 补模块级 docstring

**每个 docstring 必须包含：**

1. `Support-Tier:` 取值（tier-1 / tier-2 / tier-3）
2. `Entry-Mode:` 取值（cli / ide-extension）
3. `Key-Features:` 1-3 行关键特性

**不做什么：**

- 不改类方法实现
- 不加新函数、新参数
- 不动 `__init__.py`、不改 import 结构
- 不写测试（docstring 插入属于纯文档变更）

## 3. Approach

**方法：** 逐文件插入模块级 docstring，位置在文件首行（在所有 import 之前），符合 PEP 257。

**取值来源：** docstring 内的 `Support-Tier` / `Entry-Mode` 应与文件内现有 `support_tier` / `entry_mode` 类属性保持一致；如类属性缺失，则在 docstring 内标注 `unknown` 并在 Constraints 节登记。

**格式统一：** 四个文件使用相同的 docstring 模板：

```python
"""
{Host} host adapter.

Support-Tier: {tier}
Entry-Mode: {mode}
Key-Features:
  - {feature_1}
  - {feature_2}
"""
```

**验证手段：** 插入后跑 `python -c "import installer.hosts.<name>"` 确保模块可加载；diff 检查未改动类实现。

## 4. Waves / Steps

### Wave 1 · 文档插入（4 个文件）

| # | 文件 | 动作 |
|---|------|------|
| 1.1 | `installer/hosts/codex.py` | 插入模块级 docstring（读现有 `support_tier` / `entry_mode`） |
| 1.2 | `installer/hosts/claude.py` | 同上 |
| 1.3 | `installer/hosts/qoder.py` | 同上 |
| 1.4 | `installer/hosts/copilot.py` | 同上 |

### Wave 2 · Smoke 验证

| # | 动作 |
|---|------|
| 2.1 | `python -c "import installer.hosts.codex"` 通过 |
| 2.2 | `python -c "import installer.hosts.claude"` 通过 |
| 2.3 | `python -c "import installer.hosts.qoder"` 通过 |
| 2.4 | `python -c "import installer.hosts.copilot"` 通过 |
| 2.5 | diff 确认四个文件的类方法体未变 |

### Wave 3 · 写入 evidence

| # | 动作 |
|---|------|
| 3.1 | 写 `plan/<plan_id>/receipts/exec_001.json`（Wave 1 完成） |
| 3.2 | 写 `plan/<plan_id>/receipts/verify_001.json`（Wave 2 通过） |

> 注：本 plan 由 Session A 创建锚点后暂停；Session B 应读回同一 `plan_id`，从 Wave 1 开始执行，追加 `verify_002.json` 作为 continuation receipt。

## 5. Key Decisions

- **KD-1 · docstring 位置**：放在文件首行，所有 import 之前（PEP 257 模块级 docstring 规范）。替代方案"放在 import 后"会增加阅读跳转，放弃。
- **KD-2 · 取值来源**：优先复用文件内已有的 `support_tier` / `entry_mode` 类属性，避免双份事实来源。
- **KD-3 · light plan 不分 tasks.md**：4 个文件 + smoke 验证在单 plan.md 内足够清晰，不升级到 standard。

## 6. Constraints / Not-in-scope

**硬约束：**

- 不得修改任何类方法实现（包括 `install` / `invoke`）
- 不得新增文件（docstring 全部嵌入现有 .py）
- 不得改动 `installer/__init__.py` 或 `installer/hosts/__init__.py`

**延后项（Not-in-scope）：**

- 不写单元测试（docstring 无运行时行为）
- 不做 finalize（finalize 是 S7 场景，本 plan 只作 S5 锚点）
- 不引入类型注解或 linter 配置

## 7. Status / Progress

| 阶段 | 状态 | 备注 |
|------|------|------|
| Plan 创建（Session A） | done | 8 章节就绪，锚点写入 `.sopify/state/active_plan.json` |
| Wave 1 · 文档插入 | pending | 待 Session B 续接执行 |
| Wave 2 · Smoke 验证 | pending | 待 Session B 续接执行 |
| Wave 3 · evidence 写入 | pending | 待 Session B 续接执行 |

> Session A 到此为止。Session B 续接时先读 `state/active_plan.json` → `plan/20260617_host_docstrings/plan.md`，然后从 Wave 1 开始。

## 8. Next

- **Session B 续接动作**：读取 `state/active_plan.json`，确认 `plan_id == 20260617_host_docstrings`，读回本 plan.md，从 Wave 1.1 开始执行
- **Session B 不得**：重建 plan、覆盖 plan.md、新建 plan_id
- **Session B 产出**：在 `plan/20260617_host_docstrings/receipts/` 下追加 `exec_001.json` + `verify_001.json` + `verify_002.json`（continuation receipt，scenario: S5_same_host_continuation）
- **完成后**：保留 `active_plan.json` + `plan.md` + `verify_002.json` 三个原始工件，回传到 P9 `assets/qoder_s5_artifacts/`
