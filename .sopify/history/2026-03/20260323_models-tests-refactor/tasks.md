---
plan_id: 20260323_models-tests-refactor
feature_key: models-tests-refactor
level: standard
lifecycle_state: archived
knowledge_sync:
  project: skip
  background: review
  design: review
  tasks: review
archive_ready: true
---

# 任务清单: runtime models / tests 结构拆分与 bundle smoke 收敛

## Step 1 — 冻结四个实现决策与兼容边界
- [x] 1.1 明确本包只覆盖 `runtime/models.py`、runtime 测试拆分、runner 切换与 bundle smoke 契约，不包含 `engine.py` / `router.py` 子包化
- [x] 1.2 固定 models 方案：保留 `runtime/models.py` facade，内部实现迁移到 `runtime/_models/`，不采用 `runtime/models/` 同名子包
- [x] 1.3 固定测试方案：保持 `unittest`，共享 helper 进入 `tests/runtime_test_support.py`，不引入 `pytest` / `conftest.py`
- [x] 1.4 固定执行方案：repo-local 使用 `python3 -m unittest discover tests -v`；bundle 保留 `.sopify-runtime/tests/test_runtime.py` 稳定路径，但语义收敛为 smoke-only

## Step 2 — 拆分 `runtime/models.py`
- [x] 2.1 创建 `runtime/_models/` 内部模块，并按 `core / decision / artifacts / summary / handoff` 等逻辑分组迁移实现；内部模块总数不超过当前逻辑分组数上限（6 组）
- [x] 2.2 将共享 helper / 常量收敛到 `core.py`、`_compat.py` 或单独共享模块中，但不为极薄工具层额外增加新的碎片模块
- [x] 2.3 将 `runtime/models.py` 改为集中 re-export facade，并维护显式 `__all__`，保持 `from runtime.models import X` 全量兼容
- [x] 2.4 运行 `python3 -c "from runtime.models import RuntimeResult, PlanArtifact, DecisionState"`，验证 facade import gate
- [x] 2.5 运行 `python3 -m unittest discover tests -v`，确保 Step 2 完成后 repo-local 全量测试仍 pass

## Step 3 — 拆分 runtime 测试
- [x] 3.1 创建 `tests/runtime_test_support.py`，提取共享 helper、workspace fixture 构造与 git 辅助函数
- [x] 3.2 按设计映射表将 16 个 `TestCase` 拆分到明确目标文件，避免“例如”式自由命名导致漏拆
- [x] 3.3 新增 repo-local `tests/test_bundle_smoke.py`，只覆盖 bundle 必需 smoke 场景
- [x] 3.4 移除 repo-local 对巨型 `tests/test_runtime.py` 的依赖，确保 discover 模式下不会重复执行或漏跑
- [x] 3.5 运行 `python3 -m unittest discover tests -v`，确保拆分后 repo-local 全量测试仍 pass
- [x] 3.6 验证每个新增或拆分出的 `tests/test_runtime_*.py` 可单独运行，例如 `python3 -m unittest tests/test_runtime_router.py -v`

## Step 4 — 同步 runner、bundle 与工具链
- [x] 4.1 修改 `scripts/release-preflight.sh`，改为 discover 运行 repo-local 全量测试，并确保 `tests/test_runtime_gate.py` 等独立文件被纳入
- [x] 4.2 修改 `scripts/sync-runtime-assets.sh`，从 repo-local `tests/test_bundle_smoke.py` 导出 bundle `tests/test_runtime.py`
- [x] 4.3 复核 `installer/bootstrap_workspace.py`、`installer/runtime_bundle.py`、`installer/validate.py`，继续保持 bundle 侧稳定路径 `tests/test_runtime.py` 的校验契约
- [x] 4.4 修改 `runtime/daily_summary.py` 中对 `runtime/models.py` / `tests/test_runtime.py` 的旧路径特判，按固定规则扩展为 `runtime/models.py` -> facade、`runtime/_models/**` -> models internal、`tests/test_bundle_smoke.py` 与 bundle `tests/test_runtime.py` -> bundle smoke、`tests/runtime_test_support.py` 与 `tests/test_runtime_*.py` -> runtime test suite
- [x] 4.5 修改 `CONTRIBUTING.md` / `CONTRIBUTING_CN.md`，同步 repo-local discover 与 bundle smoke 的新验证命令
- [x] 4.6 运行 `bash scripts/sync-runtime-assets.sh <tmp-target>` 后，验证 bundle `python3 -m unittest discover -s <tmp-target>/.sopify-runtime/tests -p 'test_runtime.py' -v` 与 `bash <tmp-target>/.sopify-runtime/scripts/check-runtime-smoke.sh` 均通过

## Step 5 — 验证
- [x] 5.1 运行 `python3 -m unittest discover tests -v`
- [x] 5.2 运行 `bash scripts/check-runtime-smoke.sh`
- [x] 5.3 验证 `python3 -c "from runtime.models import RuntimeResult, PlanArtifact, DecisionState"` 等兼容 import 不破坏
- [x] 5.4 验证 `bash scripts/sync-runtime-assets.sh <tmp-target>` 后，bundle 内 `python3 -m unittest discover -s <tmp-target>/.sopify-runtime/tests -p 'test_runtime.py' -v` 与 `bash <tmp-target>/.sopify-runtime/scripts/check-runtime-smoke.sh` 均可独立运行

## 实施备注

- 旧 monolith `tests/test_runtime.py` 含 `185` 个 `test_*` 方法。
- 拆分后的 repo-local runtime suite `tests/test_runtime_*.py` 合计 `205` 个 `test_*` 方法，较旧 monolith 增加 `20` 个。
- 新增 repo-local `tests/test_bundle_smoke.py` 含 `5` 个 smoke tests；因此本轮 `discover` 的 `228` 总数不应直接与旧 monolith 的 `185` 对比。
