# 变更提案: active_plan_human_index_projection

## 方案评分

- 方案质量: 8/10
- 落地就绪: 8/10
- 评分理由: 保留 `_registry.yaml` 现有消费链，只新增 runtime 管理的人类可读投影视图，兼容性和可用性平衡较好。

## 需求背景

当前 `history/index.md` 已经证明了一件事: 人类可读、可点击、可快速扫读的索引对日常协作是有价值的。

但 `plan/` 目录目前只有 `_registry.yaml` 可作为活动方案入口。这个文件适合 runtime / host / CLI 消费，不适合用户阅读:

- 信息层级深，人工扫读成本高
- 只看文件内容时，难以快速回答“当前有哪些候选方案、哪个在执行、哪些只是建议优先级”
- 用户需要一个和 `history/index.md` 类似、但语义更适合“活动态”的入口

同时，用户明确给出三个约束:

- 不希望破坏 `_registry.yaml` 的现有消费
- 新的 `plan/index.md` 要有自己独立、专业的人类写入规则
- 可以消费 YAML，但最终产物必须是面向用户阅读的 Markdown，而不是把 YAML 原样搬运

## 核心判断

本方案的最终执行决策已经固定:

- `_registry.yaml` 继续保留在 `.sopify-skills/plan/`
- 不再讨论迁移到 `state/`、`governance/` 或其他目录
- runtime 负责新增并维护 `plan/index.md`
- `plan/index.md` 是投影视图，不是新的 machine truth
- `current_plan` 仍是执行真相；registry 仍是 observe-only 的候选集合

补充说明:

- 本轮直接改写现有方案包内容
- 为避免目录、引用和可能的外部链接抖动，目录与 `plan_id` 暂时保持不变
- 方案的人类名称与 feature 方向更新为 `active_plan_human_index_projection`

## 变更目标

1. 为 `plan/` 提供和 `history/index.md` 类似的用户入口，但保持语义独立
2. 让用户能在一页内看清:
   - 当前执行中的 plan
   - 当前候选 plan 列表
   - 优先级是“已确认”还是“系统建议”
   - registry 与目录/状态的漂移提醒
3. 保持 `_registry.yaml` 的路径、格式、inspect 契约与既有调用方式不变
4. 让 `plan/index.md` 的渲染规则明确、稳定、可测试
5. 让 `plan/index.md` 在数据源变化时像 `history/index.md` 一样做到“有更新再写盘”，避免无意义重写

## 非目标

- 不迁移 `_registry.yaml` 的物理位置
- 不改 `_registry.yaml` 的对外消费契约
- 不让 `plan/index.md` 替代 `current_plan` / `state` 的执行真相职责
- 不照搬 `history/index.md` 的 append 模式；`plan/index.md` 应是 live projection
- 不在本次方案中引入数据库、额外缓存层或外部依赖

## 影响范围

- 模块: `runtime/plan_registry.py`
- 模块: 新增或内聚一个专门的人类视图生成逻辑模块，例如 `runtime/plan_views.py`
- 模块: `runtime/kb.py` 或相关阅读入口生成逻辑
- 文件: `.sopify-skills/plan/index.md`（新增，自动生成）
- 测试: `tests/test_runtime.py`

## 风险评估

| 风险 | 等级 | 缓解 |
|------|------|------|
| 投影视图让用户误以为它是执行真相 | 中 | 在页面头部和脚注明确标注 `current_plan` 才是执行真相 |
| registry 漏项导致 `plan/index.md` 静默漏 plan | 中 | 视图中显式加入“漂移提醒”区块，不再只做静默缺失 |
| 只在 registry 写入后刷新会漏掉 `current_plan` 变化 | 中 | 把刷新触发点覆盖到 registry 写入和 current_plan 变更路径 |
| 新入口做出来但用户找不到 | 低 | 在 blueprint / kb 的阅读入口中加入 `plan/index.md` |
| 数据源轻微变化导致 index 频繁重写 | 中 | 采用稳定渲染 + `updated != existing` 才写盘 |
| 全量重建性能 | 低 | 当前 plan 量级下可接受；先保证正确性与可读性 |
