# Issue: 将当前修复从 7/10 提升到 8.5+

## 当前评估

当前 `d2f8df7` 这轮修复已经解决两条主链：

1. active plan 的 meta-review 不再误生成新 scaffold
2. decision resume 会优先复用现有 active plan

但从工程质量角度看，仍有两条中等级别残留问题，因此整体只能给到 `7/10`：

- planning clarification 仍会清空 `current_plan`
- `explicit new plan` 的文案边界仍偏激进，存在误判

## 提升目标

用最小代码面把本轮修复提升到 `8.5+/10`，不扩张为新架构改造，不引入多 active plan，也不恢复 `topic_key` 自动复用。

## 最小修补范围

### A. Clarification 路径保留 / 重绑 Active Plan

目标：

- 当 planning 请求命中 clarification 时，如果当前已有 active plan，默认保留该 plan 上下文
- 只有在用户显式要求“新建 plan”或显式切到其他 plan 时，才允许清空或切换

建议改动：

- 在 `runtime/engine.py` 中，把 clarification 分支从“无条件 `clear_current_plan()`”改为与 decision 分支一致的 preserve / rebind 逻辑
- 优先复用已存在的 `current_plan`
- clarification 回答恢复后，应继续走已有的 active plan，而不是重新落 sibling scaffold

非目标：

- 本轮不做 clarification 多 plan registry
- 本轮不做跨工作区 plan 检索

### B. 收紧 `explicit new plan` 文案边界

目标：

- 只把真正的“新建一个新 plan”强信号识别为新 scaffold 请求
- 避免把“比较其他 plan / 看看别的 plan / 分析这个方案和其他 plan 的差异”误判成新建

建议改动：

- 在 `runtime/plan_scaffold.py` 中去掉或收紧 `其他 plan` 这类高歧义模式
- 保留强信号：
  - `new plan`
  - `create a new plan`
  - `新 plan`
  - `新的 plan`
  - `另起一个 plan`
  - `新增一个 plan`

说明：

- “切到某个 plan”应继续通过显式 `plan_id / plan path` 引用完成
- “其他 plan”若没有明确 id/path，不应直接触发新 scaffold

### C. 增补最小回归测试

至少新增以下样本：

1. active plan + clarification + answer 后，仍复用同一个 plan id
2. active plan + clarification + 显式新建 plan 时，允许创建新 scaffold
3. 包含“其他 plan”但无显式新建含义的评审语句，不得触发新 scaffold
4. 强信号“新建一个 plan”仍然能正常创建新 scaffold

## 验收标准

满足以下条件即可把这轮修复提升到 `8.5+/10`：

1. 已有 active plan 时，planning clarification 不再导致 sibling scaffold 增长
2. “分析这个方案和其他 plan 的差异”这类语句不再被判成 explicit new plan
3. 真正的“新建一个 plan”语义仍保持可用
4. `RouterTests / PlanReuseRuntimeTests / EngineIntegrationTests` 的相关回归样本全部通过
5. 再补一轮 `pytest` 运行，保证 `unittest` 与 `pytest` 两套入口都可执行

## 验证建议

优先级：

1. 先补单测
2. 再运行 `python3 -m unittest`
3. 再安装并运行 `pytest`

建议命令：

```bash
python3 -m unittest tests.test_runtime.PlanReuseRuntimeTests -q
python3 -m unittest tests.test_runtime.RouterTests -q
python3 -m unittest tests.test_runtime.EngineIntegrationTests -q
python3 -m pip install pytest
python3 -m pytest -q tests/test_runtime.py
```

## 预期收益

- 把“单 active plan”语义从 decision 分支扩展到 clarification 分支
- 把 plan 误增殖再压掉一层
- 让“显式新建”和“评审 / 对比其他 plan”边界更清楚
- 以最小改动换取更高稳定性，而不是继续扩大会话状态模型
