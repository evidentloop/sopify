# 变更提案: 借鉴 HelloAGENTS 的产品接入增强（阶段一，`helloagents-integration-enhancements`）

## 需求背景

当前 Sopify 的正式宿主接入主线仍聚焦在 `codex` 与 `claude` 两类宿主：

1. 安装器已有 `installer/hosts/codex.py` 与 `installer/hosts/claude.py`
2. runtime 机器契约已经收口到 `manifest-first + handoff-first + checkpoint_request`
3. 验证主线也主要围绕 `codex/claude + payload bundle + runtime smoke`

相比之下，HelloAGENTS 把“产品接入面”做成了用户可感知的能力矩阵。它给当前仓库的主要启发，不是“尽快扩更多宿主名字”，而是：

1. 把“宿主支持矩阵”做成显式产品能力
2. 区分正式支持、基础支持、实验支持，而不是默认所有宿主同等承诺
3. 提供安装后的状态、诊断与修复入口
4. 让文档口径、安装行为与验证链路保持一致

本轮范围收敛为阶段一，只解决当前正式宿主 `codex/claude` 的产品化表达与用户态可见性，不在本轮引入 `opencode/gemini/qwen/grok` scaffold。

评分:
- 方案质量: 8/10
- 落地就绪: 7/10

评分理由:
- 优点: 方向贴合当前仓库已有 `codex/claude` 主线，capability registry 与 `status/doctor` 的关键契约已收口到可实施级别，support_tier 与 install_enabled 的职责拆分明确。
- 扣分: 首轮仍需在实现时验证 registry、CLI 渲染与现有 installer 输出之间不会出现事实漂移；同时需要显式写清“只做产品可观测性增强，不触碰 runtime / develop / distribution 主线”的边界。

## 变更内容

1. 为当前仓库补一套“宿主能力分层 + 验证等级”的正式模型，但首轮只覆盖 `codex/claude`
2. 新增面向用户的 `status/doctor` 能力，让“已安装 / 已配置 / 已接管 / 已验证”可见
3. 重写 README 中的宿主兼容矩阵，让产品口径与实现现状一致
4. 明确把 `opencode/gemini/qwen/grok` 记录为后续候选，不进入本轮交付范围

## 当前范围边界

本轮当前范围只包括：

1. `host capability registry`
2. `sopify status`
3. `sopify doctor`
4. `README.md / README_EN.md` 宿主兼容矩阵
5. 支撑以上能力的最小测试与 smoke 对齐

本轮明确不做：

1. 新增 `opencode/gemini/qwen/grok` scaffold
2. `update / repair / clean` 完整命令面
3. `develop-quality-loop`
4. `runtime-gate-degradation-mode`
5. `one-liner-distribution`
6. 任何需要改动 runtime 核心契约的增强

## 影响范围

- 模块:
  - `installer/`
  - `scripts/`
  - `README.md`
  - `README_EN.md`
  - `tests/`
- 文件:
  - `installer/models.py`
  - `installer/hosts/base.py`
  - `installer/hosts/codex.py`
  - `installer/hosts/claude.py`
  - `installer/hosts/__init__.py`
  - `scripts/install_sopify.py`
  - 新增 `scripts/sopify_status.py`
  - 新增 `scripts/sopify_doctor.py`
  - 文档中的宿主兼容矩阵

## 风险评估

- 风险: 若 capability registry 既描述“支持层级”又直接承担安装准入，容易把文档口径和执行逻辑耦合得过紧。
- 缓解: 先把 registry 作为单一事实源，再明确哪些字段只用于展示，哪些字段参与安装/诊断决策。

- 风险: `status/doctor` 若直接侵入 runtime 深调用，会让本轮范围从 installer 产品化扩成 runtime 重构。
- 缓解: 第一阶段只做静态扫描、manifest 检查和现有 smoke 结果整合，不改 runtime 核心契约。

- 风险: 如果在第一阶段同时引入新宿主 scaffold，会把当前 `codex/claude` 主线验证稀释掉。
- 缓解: 本轮显式排除 `opencode/gemini/qwen/grok` scaffold，只在文档与 registry 中预留延后位。

## 实施前最终收口

为避免进入开发后再次回到“字段含义不清”或“CLI 输出口径不稳”的状态，本轮在编码前固定两条实施约束：

1. capability registry 必须拆开“产品承诺”和“安装准入”，不能由单一字段同时表达
2. `status/doctor` 必须先定义 machine contract，再做文本渲染，测试只对稳定 contract 断言

补充约束：

3. 本轮只允许在 installer / scripts / README / tests 层补产品可观测性，不把需求外溢到 runtime 主链
