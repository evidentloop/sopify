# 技术设计: 宿主偏好预载入（`preferences-preload-v1`）

## 设计目标

在不改动 Sopify runtime 主链路语义的前提下，给宿主增加一段稳定、可观察、可测试的 preflight 能力：

1. 解析当前工作区下真实的 `preferences.md` 路径
2. 在合适时机尝试读取长期偏好
3. 以固定格式注入 LLM
4. 用固定状态表达读取结果，但不阻断主链路

本设计刻意保持“窄”：

- 不新增 runtime stage
- 不修改 `RecoveredContext`
- 不引入新的 checkpoint 或 artifact
- 不做自动归纳、自动提炼或字段级解析

## 定位

`preferences-preload-v1` 是宿主 preflight 能力，不是 runtime 流程状态。

职责边界：

- 宿主负责读取并注入长期偏好
- runtime 继续负责路由、state、handoff、plan 与恢复逻辑
- `preferences.md` 代表 workspace-scope durable collaboration rules，而不是当前执行态

## 路径解析规则

### 配置优先级

宿主必须先按与 runtime 相同的优先级解析 `plan.directory`：

1. 项目根 `sopify.config.yaml`
2. 全局 `~/.codex/sopify.config.yaml`
3. 默认值 `.sopify-skills`

然后再计算：

```text
preferences_path = workspace_root / plan.directory / "user/preferences.md"
```

### 设计要求

- 不允许宿主硬编码 `.sopify-skills/user/preferences.md`
- 不允许跳过 `plan.directory` 解析直接猜路径
- 若配置解析失败，可回退默认值，但宿主必须可观测

### 推荐伪代码

```python
def resolve_preferences_path(workspace_root: Path) -> tuple[Path, str]:
    config = load_sopify_config(workspace_root)
    plan_directory = config.plan.directory or ".sopify-skills"
    preferences_path = workspace_root / plan_directory / "user" / "preferences.md"
    return preferences_path, plan_directory
```

## 载入时机

宿主在以下时机必须尝试读取：

1. 每次原始用户请求准备进入 Sopify router 之前
2. 每次需要恢复 Sopify 主链路之前
3. 每次准备再次发起新的 Sopify LLM 回合之前

当前范围外：

- 纯 helper / bridge 的无 LLM 机器调用
- 与 Sopify 无关的普通宿主功能

### 设计原则

- 读取时机按“进入 LLM 前”定义，而不是按某个具体命令定义
- 只要本轮会让 Sopify LLM 消费上下文，就应先尝试载入长期偏好

## 失败策略

首版采用 `fail-open with visibility`。

### 状态枚举

| 状态 | 含义 | 是否继续主链路 | 是否注入偏好 |
| --- | --- | --- | --- |
| `loaded` | 文件存在且成功读取 | 是 | 是 |
| `missing` | 文件不存在 | 是 | 否 |
| `invalid` | 文件存在但格式或编码异常 | 是 | 否 |
| `read_error` | 文件存在但读取失败 | 是 | 否 |

### 关键约束

- `preferences` 不是 checkpoint，不得 fail-closed
- 宿主不能静默吞掉状态，至少要保留内部可观测结果
- 首版不要求把状态做成 runtime artifact

## 注入格式

首版不做复杂解析，直接注入原文，并包一层稳定前缀：

```text
[Long-Term User Preferences]
Scope: current workspace
Priority: current task explicit request > this preferences file > default rules

Apply these as durable collaboration rules for this Sopify run.
If a rule conflicts with the current explicit task, follow the current task.

<raw preferences.md content>
```

### 设计要求

- 首版不做自动摘要
- 首版不做字段级结构化映射
- 首版不自动猜测哪条偏好更重要
- 先保证“稳定读到并注入”，再谈更复杂消费

## 优先级契约

固定优先级：

1. 当前任务明确要求
2. `preferences.md`
3. 默认规则

这意味着：

- “当前任务明确要求”指用户在当前任务中显式给出的临时执行指令；冲突时它优先于 `preferences.md`，不冲突时与长期偏好叠加生效，且默认不回写为长期偏好
- 长期偏好可以稳定覆盖默认协作风格
- 不允许把 `preferences.md` 提升为强于当前任务的硬约束

## 宿主内部最小返回契约

首版虽然不引入 `preferences_artifact`，但建议宿主内部统一一个最小返回值，便于测试与日志观察：

```json
{
  "status": "loaded",
  "workspace_root": "/abs/workspace",
  "plan_directory": ".sopify-skills",
  "preferences_path": "/abs/workspace/.sopify-skills/user/preferences.md",
  "injected": true,
  "error_code": null
}
```

约束说明：

- 这是宿主内部 contract，不是 runtime 对外 artifact
- `injected=true` 只在 `status=loaded` 且实际注入成功时成立
- `error_code` 仅在 `invalid / read_error` 时填充

推荐 dataclass 形态：

```python
from dataclasses import dataclass
from typing import Literal

PreloadStatus = Literal["loaded", "missing", "invalid", "read_error"]


@dataclass(frozen=True)
class PreferencesPreloadResult:
    status: PreloadStatus
    workspace_root: str
    plan_directory: str
    preferences_path: str
    injected: bool
    error_code: str | None = None
```

## 为什么不进入 `RecoveredContext`

当前不建议把 `preferences.md` 塞进 `RecoveredContext`，原因有三点：

1. `RecoveredContext` 的语义是 active-flow recovery
2. `preferences.md` 的语义是 workspace-scope durable rules
3. 两者层级不同，强行合并只会让状态模型更模糊

因此，首版只做宿主 preflight 注入；若后续需要更强可观测性，再考虑独立结构化暴露。

## 推荐测试面

### 1. 路径解析

- 默认 `plan.directory` 命中 `.sopify-skills/user/preferences.md`
- 自定义 `plan.directory` 仍命中正确路径

### 2. 读取状态

- `loaded / missing / invalid / read_error` 四态都能稳定区分
- 非 `loaded` 不阻断主链路

### 3. 注入与优先级

- 成功读取时注入固定前缀与原文
- 当前任务显式要求能覆盖偏好

## 后续延展

以下能力全部延后，不能抢占首版范围：

- runtime 独立 `preferences_artifact`
- 轻量结构化解析
- 偏好分类、自动归纳、自动提炼
- 面向可观察性的独立 preferences 调试面板

## 设计结论

首版的正确做法不是“做复杂”，而是“把宿主读取偏好的入口做稳”：

1. 先稳定解析路径
2. 再稳定定义载入时机
3. 再稳定定义注入格式与优先级
4. 最后用 `fail-open with visibility` 保证主链路不被协作偏好误伤
