---
plan_id: 20260520_p6_canonical_writer_cutover
feature_key: p6_canonical_writer_cutover
level: standard
lifecycle_state: active
---

# 任务清单

## S1: writer_input 契约规格

- [ ] 逐方法列出 StateStore 每个 set 方法的入参类型 + 必要字段 + 前置条件
- [ ] 分离 writer-side invariant（writer 自行校验）vs caller-side precondition（caller 负责）
- [ ] IO 契约文档：文件路径 convention、atomic write 语义、JSON encoding
- [ ] Observability 契约：writer stamp、timestamp、provenance 规则
- [ ] 输出 `writer_input_contract.md`

## S2: 物理提取

- [ ] 确认提取方案（方案 A: `canonical_writer/` 顶层模块 vs 方案 B: `runtime/writer/`）
- [ ] 创建新模块目录 + `__init__.py`
- [ ] 从 state.py 提取 StateStore 类 → `store.py`
- [ ] 从 state.py 提取 IO helpers（_read_json, _write_json）→ `store.py`
- [ ] 迁移 state_invariants.py → `invariants.py`
- [ ] 提取 iso_now → `_time.py`（5 处重复的统一源）
- [ ] 提取其他必要辅助（normalize_session_id, _stamp_provenance, _validate_resume）
- [ ] 从 checkpoint_request.py 提取 `CheckpointRequestError` + `validate_develop_resume_context` (~37 LOC) → canonical_writer 内部
- [ ] import 审计：确认新模块无 runtime 回指依赖

## S3: 消费者重接线

- [ ] runtime 核心文件（engine, gate, bridges 等 ~10 文件）import 路径切换
- [ ] installer/inspection.py import 路径切换
- [ ] scripts/ import 路径切换
- [ ] tests/ import 路径切换
- [ ] state.py 临时迁移桥：re-export StateStore + 标 deprecated（仅保行为不变，不是长期设计）

## S4: 验证 + 清理

- [ ] 全量测试回归：721+ tests 全过
- [ ] iso_now 重复清理：4 处重复统一为从 `_time.py` 导入
  - `runtime/handoff.py:_iso_now` (line 168)
  - `runtime/decision.py:iso_now` (line 609)
  - `runtime/clarification.py:iso_now` (line 389)
  - `runtime/state.py:iso_now` (line 317) → 迁入 canonical_writer/_time.py
- [ ] state.py 瘦身确认：只保留非 StateStore 逻辑（迁移桥在所有消费者切换后移除）
- [ ] 移除迁移桥：确认无旧路径引用后删除 state.py 中的 re-export
- [ ] canonical_writer/ import 审计：无 engine/gate/router 等 runtime 核心依赖
- [ ] 蓝图同步：design.md 三层分离表 canonical writer 列标"已提取"

## S5: 结论报告

- [ ] 标准 receipt 格式
- [ ] 提取前后 LOC 对比
- [ ] canonical_writer/ 依赖图
- [ ] writer_input contract 可用性评估
- [ ] 归档至 history/
