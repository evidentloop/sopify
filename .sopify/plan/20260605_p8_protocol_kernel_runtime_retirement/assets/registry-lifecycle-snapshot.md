# Registry Lifecycle Snapshot

> Exported from `.sopify/plan/_registry.yaml` before W2.6 registry retirement.
> Source: `p8-runtime-retirement-baseline` tag (commit `ed57992`).
> Registry mode: `observe_only` / selection: `explicit_only` / priority: `heuristic_v1`

## Plan Entries

| plan_id | title | lifecycle_state | priority | created_at | archived_path |
|---|---|---|---|---|---|
| `20260418_cross_review_engine` | Cross-Review 独立内核方案 | deferred | — (suggested p2) | 2026-05-04 | — (active plan dir) |
| `20260526_pre_launch_host_and_bundle_unification` | 推广前宿主分发与 Bundle 统一 | completed | p0 (explicit) | 2026-05-26 | `history/2026-05/` |
| `20260527_skill_writing_quality` | Skill 写作质量收敛 | archived | p1 (user) | 2026-05-27 | `history/2026-05/` |
| `20260529_pre_launch_consolidation` | 推广前收口整合 | archived | p1 (user) | 2026-05-29 | `history/2026-06/` |

## Summary

- **4 entries total**: 1 deferred, 1 completed, 2 archived
- **deferred**: `cross_review_engine` — priority未确认，runtime 退场后该 plan 如需重启须另走新方案包
- **completed/archived**: 3 条均已归档到 `history/`，receipt.md 保留了最终审计记录

## Original Field Summary

`_registry.yaml` 原始结构包含以下字段层级（不逐条复制，仅记录 schema）：

- `version` / `mode` / `selection_policy` / `priority_policy` / `priority_fallback` — registry 级元数据
- `plans[]` — plan 列表，每条含：
  - `snapshot`: `plan_id` / `path` / `title` / `level` / `topic_key` / `lifecycle_state` / `created_at`
  - `governance`: `priority` / `priority_source` / `priority_confirmed_at` / `status` / `note`
  - `advice`: `suggested_priority` / `suggested_source` / `suggested_reason` / `suggested_at`
  - `meta`: `source` / `updated_at`

Post-P8 这些字段全部随 `_registry.yaml` 删除。如需多 plan backlog，另走 human-readable index（见 design.md §4.3）。
