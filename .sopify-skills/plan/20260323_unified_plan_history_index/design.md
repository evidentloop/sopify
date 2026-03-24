# 技术设计: active_plan_human_index_projection

## 设计结论

`plan/index.md` 应该被设计为一个 runtime 维护的人类可读投影视图，而不是把 `_registry.yaml` 直接 Markdown 化。

因此，本方案采用双轨结构:

```text
.sopify-skills/plan/_registry.yaml   -> 机器 registry，保留现状
.sopify-skills/state/current_plan... -> 执行真相，保留现状
.sopify-skills/plan/index.md         -> 人类可读投影视图，新增
```

最终执行版不再保留路径迁移分叉，直接冻结为:

- `_registry.yaml` 保留在 `.sopify-skills/plan/`
- runtime 内部新增一套独立的人类视图写入规则
- `plan/index.md` 作为用户入口
- 默认入口引导用户看 `plan/index.md`，不是直接读目录或 YAML

## 文件关系

```text
.sopify-skills/plan/
├── _registry.yaml       ← 机器 registry，保留现状
├── index.md             ← 新增：人类可读投影视图
├── 20260323_xxx/
└── 20260323_yyy/

.sopify-skills/state/
└── current_plan.json    ← 执行真相之一，保留现状
```

建议把人类视图逻辑从 `plan_registry.py` 的 machine contract 中分离，形成独立模块或独立逻辑层，例如:

```text
runtime/plan_registry.py   ← registry 读写、inspect、priority confirm
runtime/plan_views.py      ← 收集人类视图快照、渲染 plan/index.md
```

## `plan/index.md` 的目标定位

`plan/index.md` 不是:

- 不是执行真相
- 不是新的 registry
- 不是 `history/index.md` 的活动态翻版

`plan/index.md` 是:

- 当前活动方案的人类入口
- 对 registry + current_plan + drift 的聚合视图
- 供用户快速阅读、点击和判断优先级的页面

## 目标格式

```markdown
# 活动方案索引

当前 6 个候选方案，1 个执行中，5 个待确认优先级，1 个漂移提醒。

## 当前执行

- [`20260323_readme-gate-changelog`](20260323_readme-gate-changelog/) - standard - 项目架构优化

## 候选方案

- `2026-03-23 11:03` [`20260323_readme-gate-changelog`](20260323_readme-gate-changelog/) - standard - 建议 p3 - 项目架构优化
- `2026-03-21 15:36` [`20260320_helloagents_integration_enhancements`](20260320_helloagents_integration_enhancements/) - standard - 建议 p3 - 借鉴 HelloAGENTS 的产品接入增强

## 漂移提醒

- 目录存在但 registry 未登记：[`20260323_unified_plan_history_index`](20260323_unified_plan_history_index/)

> 说明：`current_plan` 才是执行真相；候选 priority 仅表示排队建议，不代表已切换执行。
```

空状态建议:

```markdown
# 活动方案索引

当前没有活动方案。
```

## 独立写入规则

这部分是本方案的核心，不沿用 `history/index.md` 的规则。

### 1. 数据来源规则

| 区块 | 数据来源 | 说明 |
|------|---------|------|
| 当前执行 | `state/current_plan.*` | 只反映真实执行对象 |
| 候选方案 | `_registry.yaml` | 只反映 registry 中已知候选 |
| 漂移提醒 | `plan/` 目录扫描 + registry 对比 | 显式暴露漏登记 / 路径漂移 |
| 说明脚注 | 固定文案 | 防止误解 machine truth |

### 2. 字段规则

| 字段 | 来源 | 写入规则 |
|------|------|---------|
| 时间 | `snapshot.created_at` | 保留到分钟：`YYYY-MM-DD HH:MM` |
| 链接 | `snapshot.path` 优先，否则回退 `plan_id/` | 保证点击落到真实目录 |
| level | `snapshot.level` | 原样输出 |
| priority | `governance.priority` / `advice.suggested_priority` | `p1` / `建议 p1`，避免裸 `(建议)` 模糊表达 |
| title | `snapshot.title` | 截断 50 字符，超出加 `...` |
| 当前执行标题 | `current_plan.title` | 不显示建议 priority，避免误导 |
| 漂移提醒 | 扫描差异 | 用单独区块列出，不混入候选列表 |

### 3. 排序规则

候选方案区块:

1. 已确认 priority 优先于系统建议
2. priority 按 `p1 -> p2 -> p3`
3. 同优先级按 `created_at` 降序
4. 若时间缺失，按 `plan_id` 兜底稳定排序

漂移提醒区块:

1. 目录存在但 registry 未登记
2. registry 记录存在但目录缺失
3. snapshot.path 与实际目录不一致

### 4. 头部摘要规则

统一格式:

```text
当前 {candidate_count} 个候选方案，{active_count} 个执行中，{pending_priority_count} 个待确认优先级，{drift_count} 个漂移提醒。
```

如果全部为 0，则直接输出:

```text
当前没有活动方案。
```

### 5. 稳定渲染规则

`plan/index.md` 虽然是 live projection，但更新策略要参考 `history/index.md` 的优点:

- 有统一的 `_update_*` 入口
- 先读已有内容
- 生成新的标准化文本
- 只有 `updated != existing` 时才真正写盘

区别在于:

- `history/index.md` 是 append / reorder 一条归档记录
- `plan/index.md` 是从当前快照全量重建正文

因此建议结构是:

```python
def update_plan_index(*, config: RuntimeConfig) -> Path:
    index_path = config.plan_root / "index.md"
    existing = index_path.read_text(encoding="utf-8") if index_path.exists() else _plan_index_stub(...)
    snapshot = collect_plan_index_snapshot(config)
    updated = render_plan_index(existing=existing, snapshot=snapshot, language=config.language)
    if updated != existing:
        index_path.write_text(updated, encoding="utf-8")
    return index_path
```

关键点:

- `collect_plan_index_snapshot()` 负责采集 registry/current_plan/drift
- `render_plan_index()` 负责稳定排序、规范化标题、摘要、区块顺序和脚注
- 内容不变时不写盘，避免因为数据源检查或重复 hook 导致文件时间戳抖动
- 如需原子写入，可在 `updated != existing` 的分支里采用临时文件替换

## 刷新触发机制

不能只在 registry 写入后刷新，否则 `current_plan` 变化会漏同步。

因此建议引入一个明确的视图刷新入口，例如:

```python
update_plan_index(config)
```

触发点至少覆盖:

1. `upsert_plan_entry`
2. `remove_plan_entry`
3. `confirm_plan_priority`
4. `read_plan_registry(... changed=True)` 导致 registry 被 reconcile/backfill 落盘时
5. `set_current_plan(...)`
6. `clear_current_plan(...)`

这样 `plan/index.md` 才能同时反映:

- registry 候选集变化
- 当前执行 plan 变化
- 漂移提醒变化

并且在重复触发时只在内容变更时写盘。

## 入口接入

如果只生成 `plan/index.md` 但不给入口，这个能力的实际价值会大打折扣。

因此需要补一个轻量入口接入:

- blueprint / kb 的“当前活动方案目录”从纯目录提示升级为优先指向 `../plan/index.md`
- 若 `plan/index.md` 尚不存在，再回退为目录提示

目标不是隐藏目录，而是让用户默认先看到可读入口。

## 边界处理

| 场景 | 行为 |
|------|------|
| `_registry.yaml` 不存在 | 生成空索引，不阻断主流程 |
| `_registry.yaml` 解析失败 | 保留旧 `plan/index.md`，并记录可观察警告 |
| registry 为空但 current_plan 存在 | 渲染“当前执行”区块，同时提示候选为空 |
| 目录里有未登记 plan | 放入“漂移提醒”区块，不静默忽略 |
| `plan/index.md` 写入失败 | 不阻断主流程，但必须有可观察日志或 note |
| 数据源重复触发刷新但内容未变化 | 不写盘，不制造噪音 |
| 当前没有 active plan | `当前执行` 区块输出“暂无”或直接省略并更新摘要 |

## 与 `history/index.md` 的关系

可借鉴点:

- 一行一条的可读格式
- 相对链接可点击
- 适合做“阅读入口”
- 先读 existing，再 render updated，内容无变化则不写盘

不能照搬点:

- `history/index.md` 是 finalize 后 append/update 的归档索引
- `plan/index.md` 是 live projection，必须支持重建、漂移提醒和 current_plan 语义
- `history/index.md` 可以按单条归档插入优化；`plan/index.md` 更适合“采集快照 -> 稳定全量渲染”

所以它们应该“外层更新策略相似，正文生成策略不同”。
