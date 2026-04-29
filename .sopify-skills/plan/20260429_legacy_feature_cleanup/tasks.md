# Tasks: Legacy Feature Cleanup

## 任务列表

### T1: explain_only_override 删除

- [ ] T1-A: 审计 `router.py` 中 `_classify_explain_only_override` 完整调用链
- [ ] T1-B: 审计 `engine.py` 中 plan materialization bypass 分支的独立性
- [ ] T1-C: 删除 router.py callsite + 函数
- [ ] T1-D: 删除 engine.py callsite
- [ ] T1-E: 删除 5 个关联测试
- [ ] T1-F: 跑全量测试确认无回归

### T2: ~compare 模块移除

- [ ] T2-A: 列出所有 `~compare` / `model_compare` / `compare_decision` 引用（代码 + 提示 + 配置）
- [ ] T2-B: 删除 `scripts/model_compare_runtime.py`
- [ ] T2-C: 删除 `runtime/compare_decision.py`
- [ ] T2-D: 清理 router.py / engine.py / gate.py 引用
- [ ] T2-E: 清理提示层 `~compare` 命令定义
- [ ] T2-F: 清理 `multi_model.*` 配置项模板
- [ ] T2-G: 删除关联测试
- [ ] T2-H: 跑全量测试确认无回归

### T3: 收口

- [ ] T3-A: 更新 blueprint README 焦点
- [ ] T3-B: 更新总纲 tasks.md 状态
- [ ] T3-C: 归档至 history

## 依赖关系

```
T1-A, T1-B → T1-C, T1-D → T1-E → T1-F
T2-A → T2-B~T2-G → T2-H
T1-F, T2-H → T3
```
