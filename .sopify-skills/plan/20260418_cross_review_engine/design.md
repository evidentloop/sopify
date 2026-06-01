# 技术设计: CrossReview Sopify 集成

## 集成架构

```text
Sopify develop 完成
    ↓
SKILL.md 触发条件判断（Step 0: diff source 选择）
    ↓
CrossReview CLI pipeline:
  pack → render-prompt → host isolated review → ingest
    ↓
Advisory verdict 展示给用户
    ↓
用户决定（继续 / 修改 / 忽略）
```

## Phase 4a: Advisory 集成（当前）

宿主（LLM）读取 `.agents/skills/cross-review/SKILL.md` 后自主执行 CrossReview CLI 四步流程：

1. **pack**：从 git diff 构建 ReviewPack（确定性，无 LLM 调用）
2. **render-prompt**：将 ReviewPack 渲染为 canonical reviewer prompt（确定性）
3. **host isolated review**：在 fresh/isolated context 中执行审查（宿主提供隔离环境）
4. **ingest**：将原始审查输出归一化为结构化 ReviewResult（确定性）

关键约束：
- 不改 Sopify runtime state
- 不写 checkpoint
- verdict 仅供参考（advisory only）
- 执行失败不阻断主流程

## Phase 4b: Runtime Bridge（暂缓）

```text
CrossReview CLI ingest
    ↓
bridge.py（待实现）
    ↓
review_result + checkpoint_proposal
    ↓
Sopify Core validates
    ↓
Core materializes checkpoint（若通过验证）
```

设计约束（来自 CrossReview 蓝图 ADR）：
- CrossReview bridge 只能 propose checkpoint，不能直接写入 Sopify state
- Pipeline hook 检查由 Sopify Plugin Runtime / Core validation layer 负责
- CrossReview 不理解 Sopify 内部 action/state/checkpoint 语义

## Verdict 映射

| CrossReview Verdict | Sopify 行为 (4a advisory) | Sopify 行为 (4b bridge) |
|---|---|---|
| `pass_candidate` | 告知用户，继续 | auto-continue |
| `concerns` | 展示 findings，用户决定 | checkpoint proposal |
| `needs_human_triage` | 展示 findings，等待用户 | blocking checkpoint |
| `inconclusive` | 警告，继续 | log + continue |

## 与 Sopify 现有能力的关系

| Sopify 能力 | 与 CrossReview 的分工 |
|---|---|
| `develop_quality` | spec_compliance / code_quality 两段复审 → Phase 4b 后可映射 CrossReview verdict |
| `~compare` | 多模型候选答案对比 → CrossReview 是验证已有产物，不是生成候选 |
| `execution_gate` | 阶段转换守门 → CrossReview verdict 可作为 gate 输入信号之一 |

## review.md 资产（Phase 4b 预留）

未来 plan 目录可增加 `review.md` 作为一等资产：
- 懒加载：首次 review 运行后创建
- finalize 时包含 finding snapshot（category / severity / description）
- 随 plan 一起进入 history，形成可审计证据
