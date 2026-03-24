# 变更提案: runtime models facade / unittest 拆分 / bundle smoke 契约收敛

## 需求背景

当前 runtime 代码和测试已经出现明显的“单文件过重 + 路径契约耦合”问题：

- `runtime/models.py` 约 1500+ 行，承载 39 个 dataclass / contract，阅读与增量修改成本过高
- `tests/test_runtime.py` 约 5700+ 行，聚合 16 个 `unittest.TestCase` 与 180+ 测试方法，定位回归困难
- bundle 侧仍同步整份 runtime 测试，但实际对外只需要 smoke 级验证
- 发布、安装、摘要与文档链路仍硬编码旧路径，导致“单纯拆文件”会连带破坏 bundle / preflight / summary 契约

本包的目标不只是把文件拆小，而是先把四个实现决策固定下来：

1. `models facade + internal modules`
2. `unittest support module`
3. `discover runner`
4. `bundle smoke contract`

评分:
- 方案质量: 8/10
- 落地就绪: 7/10

评分理由:
- 优点: 关键技术决策已经明确，兼容路径、测试执行方式与 bundle 契约都有保守落地方案。
- 扣分: 影响面横跨 runtime、tests、installer、scripts 与文档，仍需一次性完成多处同步才能避免漂移。

## 变更内容

1. 保留 `runtime/models.py` 作为公开 facade，把真实模型实现下沉到 `runtime/_models/` 内部模块，避免 `runtime/models.py` 与 `runtime/models/` 同名冲突
2. 保持 `unittest` 体系不变，共享 helper 统一提取到 `tests/runtime_test_support.py`，不引入 `pytest` / `conftest.py`
3. repo-local 全量测试改用 `python3 -m unittest discover tests -v`，不再手写 `tests/test_runtime.py` 单文件入口
4. bundle 契约收敛为 smoke-only：repo-local 新增 `tests/test_bundle_smoke.py` 作为源文件，同步时导出到 bundle 稳定路径 `.sopify-runtime/tests/test_runtime.py`
5. 同步修正 `daily_summary`、installer、sync 脚本、release preflight 与 CONTRIBUTING 中对旧文件名的硬编码依赖

## 非目标

- 不在本包中推进 `runtime/engine.py` / `runtime/router.py` 子包化
- 不把现有测试体系迁移到 `pytest`
- 不修改 runtime 对外 import contract，例如 `from runtime.models import RuntimeResult`
- 不在本轮把 bundle 对外测试路径从 `tests/test_runtime.py` 改名为 `tests/test_bundle_smoke.py`

## 影响范围

- 模块: `runtime/models.py`, `runtime/_models/`, `runtime/daily_summary.py`
- 文件: `tests/test_runtime.py`, `tests/test_bundle_smoke.py`, `tests/runtime_test_support.py`, `tests/test_runtime_*.py`, `scripts/sync-runtime-assets.sh`, `scripts/release-preflight.sh`, `installer/bootstrap_workspace.py`, `installer/runtime_bundle.py`, `installer/validate.py`, `CONTRIBUTING.md`, `CONTRIBUTING_CN.md`

## 风险评估

- 风险: facade re-export 不完整、bundle 导出路径不一致，或 discover / smoke 契约切换不彻底，会导致安装、发布或外部 vendored runtime 静默失效。
- 缓解: 先冻结四个决策，再按“models -> tests -> runner -> bundle/tooling”顺序实施；bundle 对外保留 `tests/test_runtime.py` 稳定路径，本地全量验证与 bundle smoke 验证分层执行。

## 决策状态

- 当前无阻塞性的用户拍板项。
- 已确认采用“保守兼容”策略：bundle 继续暴露 `tests/test_runtime.py`，仅语义收敛为 smoke-only，不再同步 repo-local 全量回归测试。
- 当前不做破坏式改名；若后续确认不存在外部依赖，再单独评估移除 bundle `tests/` 或改名为 `test_bundle_smoke.py` 的独立 plan。
