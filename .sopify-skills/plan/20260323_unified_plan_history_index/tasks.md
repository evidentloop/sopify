---
plan_id: 20260323_unified_plan_history_index
feature_key: active_plan_human_index_projection
level: standard
lifecycle_state: active
knowledge_sync:
  project: skip
  background: review
  design: review
  tasks: review
archive_ready: false
plan_status: on_hold
---

# 任务清单: active_plan_human_index_projection

## 当前状态

- `2026-03-24` 基线清理：本 plan 保留内容，但暂标记为 `on_hold`，不进入当前执行序列。
- 恢复条件：确认 `plan/index.md` 的 human projection 重新排期后再恢复实施。

## Step 1 — 冻结目录与职责边界
- [ ] 1.1 固定 `.sopify-skills/plan/_registry.yaml` 继续作为 in-plan 机器 registry
- [ ] 1.2 明确 `current_plan` 仍是执行真相，`plan/index.md` 只是 human projection
- [ ] 1.3 在实现文案和页面脚注中固定说明：priority 不等于切换执行

## Step 2 — 建立 `plan/index.md` 的稳定更新管线
- [ ] 2.1 新增 `update_plan_index(config)` 作为唯一更新入口
- [ ] 2.2 新增 `collect_plan_index_snapshot(...)`，统一采集 `current_plan`、registry 候选和 drift 提醒
- [ ] 2.3 新增 `render_plan_index(existing, snapshot, language)`，统一负责标题、摘要、区块和脚注渲染
- [ ] 2.4 约束为“先读 existing，再 render updated，只有 `updated != existing` 才写盘”
- [ ] 2.5 需要时采用原子写入，避免半写文件；但不得在内容不变时重写文件

## Step 3 — 固化人类可读规则
- [ ] 3.1 页面固定三段：`当前执行` / `候选方案` / `漂移提醒`
- [ ] 3.2 候选项字段固定为：时间、链接、level、priority、title
- [ ] 3.3 priority 显示固定为 `pX` 或 `建议 pX`，不再使用裸 `(建议)` 写法
- [ ] 3.4 排序固定为：已确认优先于建议，priority 升序，同 priority 按创建时间降序
- [ ] 3.5 空状态、registry 损坏、registry 为空但 current_plan 存在等场景都给出稳定文案

## Step 4 — 绑定数据源变化触发点
- [ ] 4.1 在 `upsert_plan_entry` / `remove_plan_entry` / `confirm_plan_priority` 后调用 `update_plan_index`
- [ ] 4.2 在 registry reconcile / backfill 真正导致 registry 落盘后调用 `update_plan_index`
- [ ] 4.3 在 `set_current_plan` / `clear_current_plan` 对应运行时链路后调用 `update_plan_index`
- [ ] 4.4 触发失败不阻断主流程，但要留下可观察信号，不允许完全静默

## Step 5 — 调整用户入口
- [ ] 5.1 blueprint / kb 的默认阅读入口优先指向 `../plan/index.md`
- [ ] 5.2 当 `plan/index.md` 尚未生成时，回退为 `../plan/` 目录提示
- [ ] 5.3 保持 `history/index.md` 入口不受影响，避免活动态与归档态入口混淆

## Step 6 — 测试
- [ ] 6.1 测试：2 个候选 plan + 1 个 current_plan → 页面同时包含“当前执行”和“候选方案”
- [ ] 6.2 测试：priority 已确认与系统建议混合时，排序和显示正确
- [ ] 6.3 测试：目录存在但 registry 未登记时，出现“漂移提醒”区块
- [ ] 6.4 测试：registry 损坏时，旧 `plan/index.md` 保留且有可观察信号
- [ ] 6.5 测试：重复触发更新但内容不变时，不发生写盘
- [ ] 6.6 测试：`clear_current_plan` 后，`当前执行` 区块正确消失或变为暂无
- [ ] 6.7 测试：kb / blueprint 入口优先指向 `plan/index.md`
- [ ] 6.8 测试：`history/index.md` 的既有行为和输出不受影响

## 验证清单
- [ ] V1 `python3 -m unittest discover tests/ -v` 全量通过
- [ ] V2 手动触发创建 plan、切换 current_plan、确认 priority、finalize，确认 `plan/index.md` 始终同步
- [ ] V3 手动验证“内容不变不写盘”，确认时间戳不会因重复 hook 无意义变化
- [ ] V4 验证 `plan/index.md` 相对链接可在 GitHub / 编辑器中点击跳转
