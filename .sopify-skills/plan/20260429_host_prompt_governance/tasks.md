# Tasks: Host Prompt Governance

## 任务列表

### T1: 审计与原则沉淀

- [ ] T1-A: 标注 4 个 prompt variant 中所有重复区块（行号 + 内容分类）
- [ ] T1-B: 识别唯一事实源 vs 重复引用
- [ ] T1-C: 撰写 `.sopify-skills/blueprint/prompt-governance.md`（6 条工程原则）
- [ ] T1-D: 用户确认原则

### T2: Prompt 架构分层

- [ ] T2-A: 设计分层结构（6 个区块定义 + 行数预算）
- [ ] T2-B: 重构 Claude CN prompt（目标 ≤400 行）
- [ ] T2-C: 同步 Claude EN / Codex CN / Codex EN
- [ ] T2-D: 跑全量测试确认 prompt 变更不影响 runtime
- [ ] T2-E: Dogfood 验证

### T3: 准入脚本

- [ ] T3-A: 实现 `check-prompt-governance.py`
- [ ] T3-B: 集成到 pre-commit hook
- [ ] T3-C: 跑全量测试确认

### T4: 收口

- [ ] T4-A: 更新 blueprint README 焦点
- [ ] T4-B: 更新总纲 tasks.md 状态
- [ ] T4-C: 归档至 history

## 依赖关系

```
T1 → T2 → T3 → T4
T1-D (用户确认) gates T2
```
