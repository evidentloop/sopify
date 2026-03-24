# 变更提案: 第一性原理协作规则分层落地

## 需求背景
用户希望把“第一性原理 + 谨慎挑战 + 两段式输出”写进类似 `claude.md` 的长期协作层，同时明确它应该落在当前仓库的 `preferences.md`，还是下沉成 Sopify 底层默认能力，供所有接入仓库共享。

本次规划需要回答 4 个问题：

1. 第一性原理规则应写入哪一层，作用域多大。
2. 这套思路与 SMART 的结合点是什么。
3. 当前 skills 应如何拆分接入，哪些放 `analyze`，哪些不应放。
4. 其他仓库接入本 skills 后，会出现哪些典型使用场景、收益与副作用。

评分:
- 方案质量: 9/10
- 落地就绪: 8/10

评分理由:
- 优点: 先把“个人协作偏好”和“可复用默认能力”分层，能避免一次性把探索中的方法论固化为全局契约。
- 扣分: 若后续要把“两段式回答”推广到所有问答，还需要额外定义 `consult` 或 host 输出层契约，当前规划只把这件事明确为二期能力。

## 变更内容
1. 明确 `v1` 范围：当前 workspace 的长期协作风格只落在 `.sopify-skills/user/preferences.md`，不写入 `project.md` 或 blueprint。
2. 仅把可复用的稳定子集下沉到 `analyze`：目标与路径分离、目标模糊时先停下补事实、路径明显次优时给低成本替代、用 SMART 风格收口成功标准。
3. 明确深度交互默认强度：只在“明显信号”命中时触发，不对所有请求强制展开。
4. 为后续跨仓库推广定义可审计的 promotion gate：先 pilot、再评估、满足门槛后才允许提升到 `analyze` 默认规则。
5. 把“元评审问题不应生成新 plan”拆成独立 issue，避免与 `v1` 主方案耦合。
6. 把“严格单 active plan + plan reuse + duplicate merge”拆成独立 issue，并把当前工作区的重复 plan 收敛到一个 canonical plan。
7. 在 `45` 样本 / `3` 类环境的 round-1 证据完成后，单独做一次 `decision pass`，正式确认 `propose-promotion`；Batch 2/3 的 caution 只作为后续 wording/examples 优化，不再阻塞本轮收口。

## 影响范围
- 模块:
  - workspace preference preload
  - analyze prompt-layer rules
  - promotion gate and evaluation criteria
  - docs and mirror sync
  - meta-review route guard issue
  - single-active-plan reuse / plan merge policy
  - runtime plan selection and state rebinding
- 文件:
  - `.sopify-skills/user/preferences.md`
  - `Codex/Skills/CN/skills/sopify/analyze/references/analyze-rules.md`
  - `Codex/Skills/EN/skills/sopify/analyze/references/analyze-rules.md`
  - `Claude/Skills/CN/skills/sopify/analyze/references/analyze-rules.md`
  - `Claude/Skills/EN/skills/sopify/analyze/references/analyze-rules.md`
  - `.sopify-skills/plan/20260321_go-plan/issue_meta_review_no_new_plan.md`
  - `.sopify-skills/plan/20260321_go-plan/issue_single_active_plan_reuse_with_topic_key.md`
  - `runtime/plan_scaffold.py`
  - `runtime/engine.py`
  - `runtime/router.py`
  - `runtime/models.py`
  - `tests/test_runtime.py`
  - `README.md`
  - `README_EN.md`
  - `scripts/sync-skills.sh`
  - `scripts/check-skills-sync.sh`

## 风险评估
- 风险: promotion gate 若定义不清，会让“是否能从 pilot 升级”为主观判断，后续持续优化时难以复盘。
- 缓解: 在方案中固定可升级规则清单、触发信号定义、样本规模、通过阈值、回滚条件和迭代节奏，保证后续每轮优化都可审计。
- 风险: 元评审类请求仍会被误判为 workflow，从而污染当前 active plan。
- 缓解: 将其拆为独立 issue，后续单独修复 route classifier / guard 顺序，不与 `v1` 主体实现绑死。
- 风险: 当前 runtime 以“每次 planning 请求都新建 scaffold”为默认行为，会让 `current_plan.json` 的单 active plan 语义失真，累计产生重复 plan 目录与错误 handoff。
- 缓解: 固定“严格单 active plan”规则，先复用当前 active plan；只有显式新建或显式切换到其他 plan 时才允许偏离。若当前没有 active plan，则默认新建 scaffold；`topic_key` 暂只保留为元数据，不参与自动复用。
- 风险: 该问题是最近在 runtime-first guard、planning scaffold、state lifecycle 相继收紧后被放大的，若只修其中一层会再次回归。
- 缓解: 同时修文档约束、router guard、planning reuse 与回归测试，并把当前工作区状态重新绑定到 canonical plan。
