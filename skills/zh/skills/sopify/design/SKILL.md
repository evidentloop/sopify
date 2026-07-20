---
name: design
description: 方案设计阶段入口；聚合方案分级、任务拆分与方案包输出规则，按需加载 references/assets/scripts。
---

# Design（入口文档）

> 先核对现状，再选择最小充分路径。

## 何时激活

- 进入方案设计阶段（`workflow` / `plan_only` / `light_iterate`）。
- 需要把需求转换为可执行方案包与任务清单。

## 执行骨架

1. 加载 `references/design-rules.md`。
2. 核对现有实现、正式契约、适用的原生能力和已安装依赖。
3. 选择最小充分路径，并判定 `light/standard/architecture`。
4. 按级别选取 `assets/` 中对应模板生成方案文件。
5. 产出任务清单，确认每项可验证、依赖明确。
6. 给出 `Ready` 或 `Needs decision` 及依据，格式参考 `assets/output-summary.md`。

## 资源导航

- 长规则：`references/design-rules.md`
- 共享写作规范：`../references/shared-writing-dna.md`（所有输出遵循）
- 输出契约：`../references/output-contract.md`（必需 section、条件增强、自检）
- 模板：`assets/*.md`
- 确定性分级脚本：`scripts/select_plan_level.py`

## 确定性逻辑（脚本优先）

当 `plan.level=auto` 时，优先调用：

```bash
python3 skills/zh/skills/sopify/design/scripts/select_plan_level.py \
  --file-count 6 \
  --new-feature \
  --cross-module
```

脚本输出 JSON，包含：建议级别与触发原因。

## 边界

- 不直接执行代码任务（交给 `develop`）。
- 不负责路由或协议状态写入，仅提供方案结构与任务拆分契约。
