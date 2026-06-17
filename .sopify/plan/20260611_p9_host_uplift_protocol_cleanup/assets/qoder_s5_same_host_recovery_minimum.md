# Qoder S5 Same-Host Recovery Minimum

目标：只证明 **Qoder 同宿主恢复** 能成立，不顺带证明 W1a 全量完成，不触碰当前 P9 active plan。

## 边界

- 使用 **独立临时 workspace** 或临时仓库副本执行；不要在当前 Sopify 工作区直接跑。
- 场景保持最小：复用 `w1_gaps.md` 的 S3 light-plan 任务即可。
- 不新增 schema、脚本、状态文件、CLI 包装。
- 不做 finalize；S5 只证明“中断后还能继续读回同一个 plan”。

## Session A（Qoder）

1. 在临时 workspace 内创建一个新的 light plan。
2. 至少留下以下锚点后立即停止会话：
   - `state/active_plan.json`
   - `plan/<id>/plan.md`
3. 推荐额外留下：
   - `state/current_handoff.json`
   - `plan/<id>/receipts/verify_001.json`
4. 停止前不得清理上述工件，不得宣告 PASS。

## Session B（仍然是 Qoder）

1. 用自然语言恢复 prompt 继续上一个 plan。
2. 必须读回 Session A 留下的同一个 `plan_id`。
3. 不得新建第二个 plan，不得覆盖原 `plan.md`。
4. 追加一个新的 receipt，例如 `plan/<id>/receipts/verify_002.json`，证据里写清：
   - `scenario: S5_same_host_continuation`
   - `host_role: same_host_session_b`
   - 消费了哪些 Session A 工件
   - 结论：恢复发生在同一个 `plan_id` 上

## 最小留痕

完成后至少保留或回传以下原始工件，避免只剩 prose：

- Session A 的 `state/active_plan.json`
- Session A 的 `plan/<id>/plan.md`
- Session B 的 `plan/<id>/receipts/verify_002.json`

如果临时 workspace 需要销毁，先把这 3 个原始文件复制到 P9 `assets/` 目录下再清理。

## PASS / FAIL 口径

PASS：

- Session B 明确消费了 Session A 的同一 `plan_id`
- 原 plan 工件未被重建或覆盖
- 存在新的 continuation receipt

FAIL：

- 仍在同一 session 内“假装中断恢复”
- Session B 重新生成新 plan
- 只有 prose 自述“恢复成功”，没有原始工件
- 为了验证 S5 改动当前 P9 的 `active_plan.json`
