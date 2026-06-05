---
title: P8 Protocol Kernel & Runtime Retirement — Tasks
plan_id: 20260605_p8_protocol_kernel_runtime_retirement
status: pending
created: 2026-06-05
---

# Tasks

> 三波次执行顺序严格：W1 → W2 → W3。每波次收口后才启动下一波次。
> 状态标记：`[ ]` 待办 / `[~]` 进行中 / `[x]` 完成 / `[-]` 阻塞 / `[·]` 取消

## Wave 1 — Protocol + State Contract Cutover

### S1.1 Protocol 5 件 Must-Freeze Schema

- [ ] `state/active_plan.json` schema：`{ "plan_id": "<id>" }` 极简
- [ ] `state/current_handoff.json` schema：复用蓝图已定义 handoff schema + required_host_action 字段（复用蓝图 canonical 值：continue_host_develop / answer_questions / confirm_decision / continue_host_consult / resolve_state_conflict）
- [ ] `plan/<id>/plan.md` 8 必备章节定义：Context/Why / Scope / Approach / Waves / Key Decisions / Constraints / Status / Next
- [ ] `plan/<id>/receipts/*.json` schema：命名规范 `exec_NNN / verify_NNN / final`；字段 verdict / evidence / provenance / timestamp
- [ ] `history/<id>/receipt.md` 必备章节：outcome / summary / key_decisions
- [ ] 落到 `sopify_contracts/schemas/`，标注 MUST/SHOULD/MAY（RFC 2119）

### S1.2 protocol.md §2 Plan 包结构升级

- [ ] plan 包文件清单（plan.md + optional tasks/design + receipts/ + optional assets/）
- [ ] plan.md 8 必备章节详细说明
- [ ] 分级（light / standard / architecture）+ 适用场景
- [ ] 明确不加 status.json / plan-level README.md / plan/<id>/handoff.json

### S1.3 protocol.md §6 Verifier Read-Only Contract

- [ ] `verifier_contract` MUST/MUST_NOT 块
- [ ] cross-review Phase 4a advisory 路径增加 read-only 声明消费
- [ ] Validator 消费 verdict 时校验 verifier_contract 声明
- [ ] 违反 read-only → verdict 降级 advisory

### S1.4 protocol.md §8 Host 入口读顺序升级

- [ ] 4 步读顺序：active_plan → plan.md → current_handoff → receipts/
- [ ] 链路失败模式与 fail-open 规则
- [ ] 顺序设计原则说明（语义优先于缓存）

### S1.5 sopify_compliance.py 主链 smoke

- [ ] 新建 `scripts/sopify_compliance.py`
- [ ] 实现 3 场景检查：new-plan / continuation / finalize
- [ ] 输出结构化 report（JSON），可被 CI 消费
- [ ] CLI 接口：`sopify_compliance check --scenario <scenario> --fixture <path>`

### S1.6 最小 Fixture

- [ ] 当前 repo 作为主 fixture（dogfood）
- [ ] 1 个最小 external repo 作为辅助 fixture
- [ ] fixture 不依赖 runtime 进程

### Wave 1 收口

- [ ] Wave 1 验收：文档自洽 + sopify_compliance.py 当前 repo 跑通 3 场景
- [ ] plan.md status 更新为 in_progress（W1 部分）

---

## Wave 2 — Runtime Physical Retirement + State 物理重构

### S2.1 Installer 5 文件解耦

- [ ] `installer/validate.py` 移除 runtime import（消费 sopify_contracts 替代）
- [ ] `installer/bootstrap_workspace.py` 移除 runtime import
- [ ] `installer/inspection.py` 移除 runtime import
- [ ] `scripts/install_sopify.py` 移除 runtime import
- [ ] `scripts/sopify_init.py` 移除 runtime import
- [ ] 每个文件做 import graph 审计（参考 Phase 1 经验）

### S2.2 CLI Helper 迁移

- [ ] `scripts/sopify_status.py` 改为消费 `installer/inspection.py` contract
- [ ] `scripts/sopify_doctor.py` 改为消费 `installer/inspection.py` contract
- [ ] 保持用户入口参数不变（`-h` / `--target` / `--workspace`）

### S2.3 State 物理重构

- [ ] 删除 `state/current_plan.json`（被 active_plan 替代）
- [ ] 删除 `state/current_run.json`（语义下沉到 plan.md status）
- [ ] 删除 `state/current_clarification.json`（折叠到 current_handoff.required_host_action = answer_questions）
- [ ] 删除 `state/current_decision.json`（折叠到 current_handoff.required_host_action = confirm_decision）
- [ ] 删除 `state/current_archive_receipt.json`（真相进 history/receipt.md）
- [ ] 删除 `state/last_route.json`（可从 current_handoff 派生）
- [ ] canonical_writer 适配新结构（只写 active_plan + current_handoff）
- [ ] sopify_contracts 适配新结构

### S2.4 Tests 分类

- [ ] 列出 tests/ 中所有 runtime-coupled 测试
- [ ] 分类：保留 contract 测试 / 删除 runtime 测试 / 迁移到 canonical_writer 测试
- [ ] 删除 runtime-coupled 测试
- [ ] 迁移需要保留的测试到 canonical_writer 测试套件

### S2.5 Runtime 目录删除

- [ ] 最后确认 Wave 1 smoke 全绿
- [ ] 删除 `runtime/` 全目录（~16K LOC / 37 文件）
- [ ] 清理 `pyproject.toml` / `setup.py` 中 runtime 相关入口
- [ ] 清理 README / docs 中对 runtime 的引用

### S2.6 Installer Bundle 清理

- [ ] 删除 `installer/sopify_bundle.py`
- [ ] 删除 `installer/hosts/{codex,claude}/` deep adapter（保留 copilot/）
- [ ] 清理 installer/__init__.py 中的 deep host 导出

### S2.7 Dogfood Smoke

- [ ] 当前 repo 跑 new-plan 场景：创建新 plan → 写 active_plan → 写 plan.md
- [ ] 当前 repo 跑 continuation 场景：中断后新 session 按 4 步读顺序接续
- [ ] 当前 repo 跑 finalize 场景：生成 receipts/final.json → 整包进 history → 生成 receipt.md → 清空 state/

### Wave 2 收口

- [ ] Wave 2 验收：W1 smoke 仍绿 + runtime/ 不存在 + canonical_writer 是唯一写路径 + state/ 只剩 2 文件
- [ ] Dogfood smoke 3 场景全绿

---

## Wave 3 — Host Proof + Docs Cutover

### S3.1 试点宿主选定

- [ ] 确认 Cursor 作为试点宿主（Windsurf 放 P9）
- [ ] 记录选型理由（plan 包内 decision log）

### S3.2 Payload-Capable Adapter

- [ ] 实现 `installer/hosts/cursor/` payload adapter
- [ ] adapter 只调 canonical_writer，不调 runtime
- [ ] payload 分发走 install.sh --target cursor
- [ ] prompt asset 落点符合 design.md §Prompt 镜像治理原则

### S3.3 接续增强接入

- [ ] Cursor adapter 消费 `state/active_plan.json`
- [ ] Cursor adapter 消费 `plan/<id>/plan.md`
- [ ] Cursor adapter 消费 `state/current_handoff.json`
- [ ] Cursor adapter 消费 `plan/<id>/receipts/`

### S3.4 端到端验收

- [ ] fixture repo 上跑通：Cursor 写 handoff → Cursor 新 session 消费 handoff 继续
- [ ] 整条链路不依赖 runtime 进程
- [ ] 录制验收 transcript

### S3.5 文档叙事切换

- [ ] 重写 `README.md` 主流程图（"host executes, Sopify is protocol kernel"）
- [ ] 重写 `README.zh-CN.md` 主流程图
- [ ] 重写 `docs/how-sopify-works.md` 主流程图 + 状态模型
- [ ] 重写 `docs/how-sopify-works.en.md` 主流程图 + 状态模型
- [ ] 更新 `docs/getting-started.md` 新用户引导
- [ ] 画架构图（用 fireworks-tech-graph）：state 2 文件 + plan + history 三层 + host 4 步入口 + 跨宿主接续

### S3.6 Blueprint 回写

- [ ] 更新 blueprint design.md §Runtime 退场路线："runtime 已物理删除"
- [ ] 更新 blueprint design.md §Core State Files 6 → 2
- [ ] 更新 blueprint design.md §State Model：反映新结构（2 文件）
- [ ] 更新 blueprint design.md §Plan Package Structure：反映三档分级 + receipts 条件必备
- [ ] 更新 blueprint tasks.md：Runtime retirement Phase 2 标完成

### Wave 3 收口

- [ ] Wave 3 验收：4 条硬指标全部满足
- [ ] Cursor 消费 active_plan 定位 plan ✓
- [ ] Cursor 读 plan.md 理解进度 ✓
- [ ] Cursor 写 handoff + receipts 可被另一 session 接续 ✓
- [ ] 整条链路不依赖 runtime 进程 ✓

---

## P8 总收口

- [ ] plan.md status 更新为 done
- [ ] 生成 `plan/<id>/receipts/final.json`（finalize 凭证）
- [ ] 移动整包 → `history/2026-MM/20260605_p8_protocol_kernel_runtime_retirement/`
- [ ] 生成 `history/<plan_id>/receipt.md`：outcome / summary / key_decisions
- [ ] blueprint design.md 回写：P8 收口结论
- [ ] blueprint tasks.md 回写：P8 进入"已完成主航道"表
- [ ] blueprint README.md 当前焦点刷新
- [ ] CHANGELOG 条目
