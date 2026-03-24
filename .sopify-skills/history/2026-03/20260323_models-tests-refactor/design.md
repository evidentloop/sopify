# 技术设计: models facade + unittest support + discover runner + bundle smoke contract

## 技术方案

- 核心技术: Python facade 模块、内部私有子模块、`unittest` 拆档、discover runner、bundle smoke 校验
- 实现要点:
  - 公开导入入口保持 `runtime.models`
  - 内部实现迁移到 `runtime/_models/`
  - repo-local 全量回归与 bundle smoke 验证分层
  - 对外 bundle 路径优先保守兼容，避免一次重构带入额外破坏

## 决策 1: models facade + internal modules

- 保留 `runtime/models.py` 作为唯一公开 facade。
- 不采用 `runtime/models/` 同名子包方案，避免与 `runtime/models.py` 形成同名 module/package 冲突。
- 新增内部目录 `runtime/_models/`，按职责拆分实现，逻辑分组上限保持在 6 组以内，避免“为了拆分而继续碎片化”：
  - `core.py`: `RuntimeConfig`, `SkillMeta`, `RouteDecision`, `ExecutionGate`, `ExecutionSummary`, `RunState`
  - `decision.py`: `Decision*`, `ClarificationState`
  - `artifacts.py`: `PlanArtifact`, `KbArtifact`
  - `summary.py`: `Summary*`, `DailySummaryArtifact`
  - `handoff.py`: `RecoveredContext`, `RuntimeHandoff`, `SkillActivation`, `ReplayEvent`, `RuntimeResult`
  - 共享 helper / 常量模块: `_json_value`, `_json_mapping`, `_normalize_keyword` 与常量可落在 `core.py`、`_compat.py` 或单独共享模块，但不应为极薄工具层额外增加第 7 个内部模块
- `runtime/models.py` 只负责集中 re-export 全部公开名称，不承载主要实现逻辑。
- `runtime/models.py` 必须维护显式 `__all__`，把 facade 的公开 surface 固定为受控列表。

## 决策 2: unittest support module

- 保持当前 `unittest` 体系，不引入 `pytest` 与 `conftest.py`。
- 新增 `tests/runtime_test_support.py` 作为共享 helper 模块。
- 优先迁移下列共享辅助逻辑：
  - `_FakeInteractiveSession`
  - `_rewrite_background_scope`
  - `_prepare_ready_plan_state`
  - `_git_subprocess_env` / `_run_git`
  - `_assert_rendered_footer_contract`
- 所有新拆分测试文件显式 `from tests.runtime_test_support import ...`。

### TestCase -> 目标文件映射

- `RuntimeConfigTests` -> `tests/test_runtime_config.py`
- `YamlLoaderTests` -> `tests/test_runtime_config.py`
- `RouterTests` -> `tests/test_runtime_router.py`
- `DecisionContractTests` -> `tests/test_runtime_decision.py`
- `SummaryContractTests` -> `tests/test_runtime_summary.py`
- `PlanScaffoldTests` -> `tests/test_runtime_plan_scaffold.py`
- `PlanRegistryTests` -> `tests/test_runtime_plan_registry.py`
- `PlanReuseRuntimeTests` -> `tests/test_runtime_plan_reuse.py`
- `ExecutionGateTests` -> `tests/test_runtime_execution_gate.py`
- `ReplayWriterTests` -> `tests/test_runtime_replay.py`
- `SkillRegistryTests` -> `tests/test_runtime_skill_registry.py`
- `SkillRunnerTests` -> `tests/test_runtime_skill_runner.py`
- `KnowledgeBaseBootstrapTests` -> `tests/test_runtime_kb.py`
- `KnowledgeLayoutTests` -> `tests/test_runtime_knowledge_layout.py`
- `PreferencesPreloadTests` -> `tests/test_runtime_preferences.py`
- `EngineIntegrationTests` -> `tests/test_runtime_engine.py`

## 决策 3: discover runner

- repo-local 全量测试统一切换为：
  - `python3 -m unittest discover tests -v`
- `scripts/release-preflight.sh` 不再手写 `tests/test_runtime.py` 列表，改为 discover 入口，避免新增测试文件后遗漏校验。
- `CONTRIBUTING.md` / `CONTRIBUTING_CN.md` 中 repo-local 验证命令同步改成 discover。
- bundle 不使用 discover 作为对外交互主入口；bundle 继续通过单文件 smoke 测试与 `scripts/check-runtime-smoke.sh` 暴露最小验证契约。

## 决策 4: bundle smoke contract

- repo-local 新增 `tests/test_bundle_smoke.py`，仅覆盖 bundle 必需的 import / route / gate / config / helper 可用性。
- `scripts/sync-runtime-assets.sh` 在导出 bundle 时，不再同步 repo-local 全量 runtime 测试，只导出 smoke 测试。
- smoke 断言覆盖清单以测试代码本身为准，不在方案文档里维护第二份展开列表；断言粒度应通过测试函数命名直接表达，例如 `test_import_runtime_entry`、`test_gate_available`。
- 为保持对外兼容，本轮 bundle 继续暴露稳定测试路径：
  - `.sopify-runtime/tests/test_runtime.py`
- 实现方式采用“源文件与导出文件分离”：
  - repo-local 源文件名：`tests/test_bundle_smoke.py`
  - bundle 导出文件名：`tests/test_runtime.py`
- installer 与 bootstrap 的 bundle 必需文件清单继续校验 bundle 侧 `tests/test_runtime.py`，不直接依赖 repo-local 文件名。
- 该决策已确认：本轮保留 bundle `tests/test_runtime.py` 路径，仅替换文件内容，不调整对外 bundle tests 目录契约。

## 依赖盘点

在正式拆分前，先修订所有显式依赖旧路径或旧执行方式的入口：

- `scripts/sync-runtime-assets.sh`
- `scripts/release-preflight.sh`
- `runtime/daily_summary.py`
- `installer/bootstrap_workspace.py`
- `installer/runtime_bundle.py`
- `installer/validate.py`
- `CONTRIBUTING.md`
- `CONTRIBUTING_CN.md`

## 兼容与迁移策略

- `from runtime.models import X` 必须在整个重构过程中持续可用。
- repo-local 可删除原始巨型 `tests/test_runtime.py`，但前提是 discover runner、拆分测试文件与 bundle smoke 导出同时到位。
- `runtime/daily_summary.py` 中对 `runtime/models.py` / `tests/test_runtime.py` 的特判，不应再只依赖单一路径名，需扩展为明确的路径归类规则：
  - `runtime/models.py` -> `change_runtime_models_facade`
  - `runtime/_models/**` -> `change_runtime_models_internal`
  - `tests/test_bundle_smoke.py` 与 bundle 导出的 `tests/test_runtime.py` -> `change_runtime_bundle_smoke`
  - `tests/runtime_test_support.py` 与 `tests/test_runtime_*.py` -> `change_runtime_test_suite`
- bundle 语义收敛与路径兼容分开处理：这轮先收敛语义，不做对外路径破坏式改名。

## 中间态 Gate

- Step 2 完成后，必须至少通过：
  - `python3 -c "from runtime.models import RuntimeResult, PlanArtifact, DecisionState"`
  - `python3 -m unittest discover tests -v`
- Step 3 完成后，必须至少通过：
  - `python3 -m unittest discover tests -v`
  - 每个新增或拆分出的 `tests/test_runtime_*.py` 可单独执行并通过，例如 `python3 -m unittest tests/test_runtime_router.py -v`
- Step 4 完成后，必须至少通过：
  - `bash scripts/sync-runtime-assets.sh <tmp-target>`
  - `python3 -m unittest discover -s <tmp-target>/.sopify-runtime/tests -p 'test_runtime.py' -v`
  - `bash <tmp-target>/.sopify-runtime/scripts/check-runtime-smoke.sh`

## 后续事项

- `engine.py` / `router.py` 的子包化改为下一轮独立 plan
- 若后续要把 bundle 测试文件正式改名为 `tests/test_bundle_smoke.py`，应单独评估外部使用方与文档迁移成本
