---
plan_id: 20260320_helloagents_integration_enhancements
feature_key: helloagents-integration-enhancements
level: standard
lifecycle_state: archived
knowledge_sync:
  project: review
  background: review
  design: review
  tasks: review
blueprint_obligation: review_required
archive_ready: true
---

# 任务清单: 借鉴 HelloAGENTS 的产品接入增强（`helloagents-integration-enhancements`）

目录: `.sopify-skills/plan/20260320_helloagents_integration_enhancements/`

## A. 已确认分析结论

- [x] A.1 HelloAGENTS 当前声明支持 6 个 CLI 产品：`codex / claude / opencode / gemini / qwen / grok`
- [x] A.2 `codex` 与 `claude` 属于深度接入
- [x] A.3 `gemini` 与 `qwen` 更接近基础接入 + 顺序降级
- [x] A.4 `opencode` 已进入目标列表，但更接近规则级/协议级支持，未见对等深接 adapter
- [x] A.5 `grok` 为实验性目标，不应与正式宿主并列承诺
- [x] A.6 当前仓库更适合先补"产品化安装层"和"支持层级"，再讨论扩宿主范围
- [x] A.7 本轮只做阶段一，交付范围限定为 `codex/claude` 的 capability registry、`status/doctor` 与文档矩阵
- [x] A.8 本轮不引入 `opencode/gemini/qwen/grok` scaffold，只保留延后位
- [x] A.9 `install_sopify.py` 与 `status/doctor` 存在事实重叠，需通过共享 inspection helper 对齐，不应各自手写检查逻辑
- [x] A.10 方法论借鉴方向已评估：渐进式降级、质量循环、低门槛扩展、分发即产品均需独立 plan，详见 `future_directions.md`

## B. 待实施任务

依赖关系: Group 2 依赖 Group 1（status/doctor 消费 registry）；Group 3 依赖 Group 1 + Group 2（文档矩阵从 registry 取数据，诊断命令作为文档示例）；Group 4 依赖 Group 1 + Group 2。

当前范围只包括：

1. `host capability registry`
2. `status`
3. `doctor`
4. README 宿主矩阵
5. 支撑以上能力的测试与 smoke 对齐

## Group 1 — 宿主能力模型

- [x] 1.1 在 `installer/models.py` 中新增 host capability / support tier 数据模型
- [x] 1.2 在 `installer/hosts/base.py` 中统一宿主元信息契约
- [x] 1.3 对现有 `installer/hosts/codex.py` 与 `installer/hosts/claude.py` 补齐 `verified_features`
- [x] 1.4 在 `installer/hosts/__init__.py` 中提供统一 registry 读取入口：`get_host_capability(host_id)`、`iter_installable_hosts()`、`iter_declared_hosts()`
- [x] 1.5 固定 `support_tier`、`entry_modes`、`feature_id` 的最小值域，并写成稳定枚举
- [x] 1.6 拆分 `support_tier` 与 `install_enabled`，避免产品承诺与安装准入混用

**Gate — Group 1 完成后：**
- [x] 1.G `python3 -c "from installer.hosts import get_host_capability; c = get_host_capability('codex'); assert c.support_tier and c.install_enabled is not None"`
- [x] 1.H `python3 -c "from installer.hosts import iter_installable_hosts; hosts = list(iter_installable_hosts()); assert len(hosts) >= 2"`

验收标准:

- `codex/claude` 的正式能力与验证等级可结构化读取
- `parse_install_target()` 仍只允许当前正式支持宿主
- 文档与状态命令不再手写散落的宿主说明
- `HostAdapter` 不承担产品能力声明职责

## Group 2 — 用户态状态与诊断（依赖 Group 1）

- [x] 2.1 抽出共享 inspection helper，供 `install/status/doctor` 复用同一份宿主、payload、bundle、smoke 事实
- [x] 2.2 新增 `scripts/sopify_status.py`，仅消费 shared inspection helper + registry，输出宿主支持矩阵、当前安装状态与 workspace 工作区状态
- [x] 2.3 在 `status` 中聚合 `workspace_state`：读取 `.sopify-skills/state/current_run.json`（活动 plan）与 `current_handoff.json`（pending checkpoint），纯静态文件检查
- [x] 2.4 固定 `status` 的 JSON contract：`schema_version + hosts[*] + state + workspace_state`
- [x] 2.5 新增 `scripts/sopify_doctor.py`，仅消费 shared inspection helper + registry，检查 payload、bundle、manifest、handoff、preferences preload 健康度
- [x] 2.6 `status` 只表达"已安装""已配置""workspace bundle 健康"三类 live state；已验证能力继续通过 `verified_features` 与 `doctor` 表达
- [x] 2.7 固定 `doctor` 的 JSON contract：`schema_version + checks[*] + summary`
- [x] 2.8 为后续自愈提供 reason code 与修复建议文本
- [x] 2.9 为两个命令统一支持 `--format json|text`
- [x] 2.10 复用现有安装与 manifest 检查 reason code，不另造平行错误码

**Gate — Group 2 完成后：**
- [x] 2.G `python3 scripts/sopify_status.py --format json` 输出包含 `schema_version`、`hosts`、`workspace_state`
- [x] 2.H `python3 scripts/sopify_doctor.py --format json` 输出包含 `schema_version`、`checks`、`summary`

验收标准:

- 用户能直接看到当前仓库正式支持哪些产品及当前工作区状态
- `status/doctor` 能区分 claim 与 verified
- 测试只对稳定 JSON contract 断言
- 第一阶段不引入深 runtime 调用
- `status/doctor` 不再各自手写宿主、payload、bundle、smoke 检查逻辑

## Group 3 — 文档与兼容矩阵（依赖 Group 1 + Group 2）

- [x] 3.1 在 `README.md` 中新增宿主兼容矩阵：`support tier`、`verification level` 与面向用户的一句话说明
- [x] 3.2 在 `README_EN.md` 中同步英文矩阵
- [x] 3.3 明确当前正式支持仍只有 `codex/claude`
- [x] 3.4 文档中删除任何会误导成"所有宿主等价支持"的表述

验收标准:

- 文档口径与实现状态一致
- 用户能一眼看懂当前仓库与 HelloAGENTS 的差异化策略

## Group 4 — 测试（依赖 Group 1 + Group 2）

- [x] 4.1 为 capability registry 增加单测，至少断言：registry 返回 codex/claude 完整 capability；`support_tier` 与 `install_enabled` 是独立字段；`iter_installable_hosts()` 只返回 `install_enabled=true` 的宿主
- [x] 4.2 为 `status` 增加单测，至少断言：JSON 输出包含 `schema_version`/`hosts`/`workspace_state`；`hosts[*].state` 只使用 `installed/configured/workspace_bundle_healthy` 枚举
- [x] 4.3 为 `doctor` 增加单测，至少断言：JSON 输出包含 `schema_version`/`checks`/`summary`；`checks[*]` 包含 `check_id`/`status`/`reason_code`；reason code 复用现有错误码
- [x] 4.4 为 `codex/claude` 保持正式 smoke
- [x] 4.5 明确第一阶段不为新增宿主增加发布准入测试

**Gate — Group 4 完成后：**
- [x] 4.G `python3 -m unittest discover tests -v` 中 registry 与 status/doctor 相关用例全部 pass

验收标准:

- 测试体系能体现"声明能力"和"已验证能力"的差异
- 不会把未正式支持宿主带进 release gate

## 5. 明确延后项（超出当前范围）

- [-] 5.1 `installer/hosts/opencode.py`
- [-] 5.2 `installer/hosts/gemini.py`
- [-] 5.3 `installer/hosts/qwen.py`
- [-] 5.4 `installer/hosts/grok.py`
- [-] 5.5 `update / repair / clean` 的完整生命周期命令面
- [-] 5.6 `develop-quality-loop`（独立 plan，详见 `future_directions.md`）
- [-] 5.7 `runtime-gate-degradation-mode`（独立 plan，详见 `future_directions.md`）
- [-] 5.8 `one-liner-distribution`（独立 plan，详见 `future_directions.md`）
- [-] 5.9 `lightweight-skill-registration`（独立 plan，详见 `future_directions.md`）
- [-] 5.10 plan lifecycle / history / index 的进一步元系统扩张
- [-] 5.11 `doctor` 改为结构化 `InstallError`：直接携带 `reason_code / evidence`，替换 `inspection.py` 中的字符串解析

## C. 推荐实施顺序（当前范围内）

1. Group 1: host capability registry
2. Group 2: shared inspection helper → status/doctor（blocked by Group 1）
3. Group 3: README 兼容矩阵（blocked by Group 1 + Group 2）
4. Group 4: 单测与 smoke 对齐（blocked by Group 1 + Group 2）
5. 本轮完成后再评估延后项是否需要独立立项
