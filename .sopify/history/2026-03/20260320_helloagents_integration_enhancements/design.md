# 技术设计: 借鉴 HelloAGENTS 的产品接入增强（阶段一，`helloagents-integration-enhancements`）

## 技术方案

- 核心技术: Python stdlib-only installer/runtime、host adapter、宿主能力注册表、文档矩阵、状态诊断
- 实现要点:
  - 保持 `runtime` 的 `manifest-first + handoff-first + checkpoint_request` 主线不变
  - 在 `installer` 层引入“宿主支持分层”与“用户态状态/诊断”能力
  - 第一阶段只覆盖 `codex/claude`，不引入新增宿主 scaffold

## 设计原则

### 1. 不牺牲当前仓库强项

当前仓库的强项不是“目标数量”，而是：

1. manifest-first
2. handoff-first
3. checkpoint contract
4. execution gate
5. preferences preload

因此增强方向必须是“在外层做产品化”，而不是把 runtime 核心改成 HelloAGENTS 式分发器。

### 2. 支持矩阵必须先服务当前正式宿主

第一阶段只给现有正式宿主建模：

1. `codex`
2. `claude`

宿主能力模型建议至少包含：

1. `host_id`
2. `support_tier`
3. `verified_features`
4. `declared_features`
5. `entry_modes`
6. `doctor_checks`
7. `smoke_targets`

其中：

- `support_tier` 第一阶段只需要覆盖当前正式宿主的稳定值
- `verified_features` 与现有测试/验证链路绑定
- `declared_features` 用于 README 与 `status`
- 暂不因为“未来可能支持的宿主”扩展安装主链

### 3. 用户看到的应是产品能力，而不是内部实现细节

第一阶段对外补齐最小生命周期入口：

1. `install`
2. `status`
3. `doctor`

`update / clean / repair` 保留为后续演进，不进入本轮必须交付。

### 4. 本轮实现边界必须足够硬

本轮实现边界固定为：

1. `host capability registry`
2. `status`
3. `doctor`
4. README 宿主矩阵
5. 支撑这些能力的测试与 smoke 对齐

这意味着：

1. 测试属于当前范围内的必要交付，不是额外扩张
2. 文档矩阵属于当前范围内的产品表达，不是独立副线
3. 任何触碰 runtime 核心契约、develop 执行规则或分发渠道的增强，都视为超范围

## 架构设计

### A. Host Capability Registry

在 `installer/models.py` 与 `installer/hosts/base.py` 增加统一宿主能力模型，并让 `installer/hosts/__init__.py` 提供结构化注册表。

第一阶段目标：

1. `parse_install_target()` 继续只允许正式支持宿主
2. registry 成为 README 兼容矩阵与 `status/doctor` 的单一事实源
3. `codex/claude` 的声明能力与验证能力可以结构化读取

#### A.1 字段职责边界

为避免一个字段同时承担“产品表达”和“执行准入”两种语义，registry 必须拆开以下职责：

1. `support_tier`
2. `install_enabled`
3. `declared_features`
4. `verified_features`
5. `entry_modes`
6. `doctor_checks`
7. `smoke_targets`

约束：

1. `support_tier` 只表示产品承诺层级，不直接参与安装准入
2. `install_enabled` 才决定 `parse_install_target()` 是否允许该宿主进入安装主链
3. `declared_features` 只用于 README / `status`
4. `verified_features` 只记录已有测试、smoke 或稳定验证链路覆盖的能力
5. `doctor_checks` 与 `smoke_targets` 使用稳定 ID，而不是自由文本

#### A.2 建议值域

第一阶段先固定最小值域，避免实现时继续自由扩散：

1. `support_tier = deep_verified | baseline_supported | documented_only | experimental`
2. `entry_modes = prompt_only | launcher | hooks | app_server | manual`
3. `feature_id = prompt_install | payload_install | workspace_bootstrap | runtime_gate | preferences_preload | handoff_first | host_bridge | smoke_verified`

补充约束：

1. `codex/claude` 在本轮必须显式设置 `install_enabled = true`
2. 未正式支持宿主即使将来进入 registry，也不应因为存在 `support_tier` 而自动变成 installable
3. `HostAdapter` 继续只负责路径与安装布局，不在其中混入产品能力声明

#### A.3 Registry 消费方式

第一阶段建议把 registry 作为唯一事实源，统一供以下入口消费：

1. `parse_install_target()` 的 installability 判定
2. `scripts/sopify_status.py`
3. `scripts/sopify_doctor.py`
4. `README.md`
5. `README_EN.md`

建议在 `installer/hosts/__init__.py` 提供：

1. `get_host_capability(host_id)`
2. `iter_installable_hosts()`
3. `iter_declared_hosts()`

### B. Installer Status / Doctor

在不破坏现有 `scripts/install_sopify.py` 主入口的前提下，补充用户态命令：

1. `scripts/sopify_status.py`
2. `scripts/sopify_doctor.py`

`status` 至少回答：

1. 当前正式支持哪些宿主
2. 每个宿主属于哪个 `support_tier`
3. 哪些能力是声明支持，哪些能力已验证
4. 当前 workspace / payload / bundle / manifest 是否健康

`doctor` 至少检查：

1. 宿主提示层是否已安装
2. payload 是否完整
3. workspace bundle 是否满足 manifest 要求
4. 现有 smoke 是否通过

#### B.1 输出 contract 先于文本渲染

`status/doctor` 必须先定义稳定 machine contract，再做 CLI 文本渲染。

约束：

1. 两个命令都支持 `--format json|text`
2. 默认输出 `text`
3. 测试与后续自动化只对 `json` contract 断言
4. 顶层固定包含 `schema_version`

#### B.2 `status` 最小 contract

`status` 负责聚合事实，不负责复杂诊断推理。建议最小结构如下：

```json
{
  "schema_version": "2",
  "hosts": [
    {
      "host_id": "codex",
      "support_tier": "deep_verified",
      "install_enabled": true,
      "declared_features": ["prompt_install", "payload_install", "runtime_gate"],
      "verified_features": ["prompt_install", "payload_install", "runtime_gate", "smoke_verified"],
      "state": {
        "installed": "yes",
        "configured": "yes",
        "workspace_bundle_healthy": "yes"
      }
    }
  ],
  "state": {
    "overall_status": "ready",
    "installable_hosts": ["codex", "claude"],
    "installed_hosts": ["codex"],
    "configured_hosts": ["codex"],
    "workspace_bundle_healthy_hosts": ["codex"]
  },
  "workspace_state": {
    "sopify_skills_present": true,
    "active_plan": "20260320_helloagents_integration_enhancements",
    "current_run_stage": "design",
    "pending_checkpoint": null
  }
}
```

`workspace_state` 通过读取 `.sopify-skills/state/current_run.json` 与 `current_handoff.json` 聚合，属于纯静态文件检查，不引入 runtime 深调用。

固定约束：

1. `state` 只使用 `installed / configured / workspace_bundle_healthy`
2. 状态值统一使用稳定枚举，不使用临时自然语言
3. `verified` 不作为 live state 出现在 `status.state`；产品级验证覆盖继续通过 `verified_features` 暴露，现场诊断进入 `doctor`
4. `status` 不额外发明与 registry 重复的宿主说明文本

#### B.3 `doctor` 最小 contract

`doctor` 负责输出检查结果、`reason_code` 与修复建议。建议最小结构如下：

```json
{
  "schema_version": "1",
  "host_id": "codex",
  "checks": [
    {
      "check_id": "host_prompt_present",
      "status": "pass",
      "reason_code": "ok",
      "evidence": ["~/.codex/AGENTS.md"]
    },
    {
      "check_id": "workspace_bundle_manifest",
      "status": "warn",
      "reason_code": "missing_required_capability",
      "recommendation": "refresh workspace bundle"
    }
  ],
  "summary": {
    "overall_status": "warn"
  }
}
```

固定约束：

1. `doctor` 复用现有安装、manifest、bundle 检查语义，不另造一套错误码
2. 第一阶段只做静态文件检查、manifest 检查与现有 smoke 结果整合
3. `doctor` 不主动引入深 runtime 调用

补充说明：

- 本轮 `doctor` contract 继续保持 `schema_version = 1`
- `reason_code / evidence` 当前仍复用既有 `InstallError` 文案推导；后续应升级为结构化错误字段，避免字符串解析脆弱性

#### B.4 与现有 installer 输出的对齐

为了避免 `install/status/doctor` 三者分别维护不同事实，按 C 节约束抽出共享 inspection helper，统一提供：

1. 宿主提示层事实
2. payload 事实
3. workspace bundle 事实
4. smoke 事实

`scripts/install_sopify.py` 继续保留当前安装路径，但其已知结果应能被 `status/doctor` 复用，而不是再次手写定义。

### C. 安装入口约束

本轮不改变 `scripts/install_sopify.py` 的安装主链路。`install/status/doctor` 三者需要共享同一份宿主与 workspace 事实，通过共享 inspection helper 实现，而不是各自手写检查逻辑。

约束：
1. 现有 repo-local runtime 与 payload bootstrap 逻辑保持不变
2. `HostAdapter` 继续只负责路径与安装布局，不混入产品能力声明
3. 共享 inspection helper 从 `install_sopify.py` 已有检查逻辑中提取，不额外发明新检查

### D. 文档矩阵

在 `README.md` 与 `README_EN.md` 中新增统一宿主兼容矩阵，字段建议包括：

1. host
2. support tier
3. entry mode
4. verified features
5. declared features
6. verification level

文档必须明确：

1. 当前正式支持仍只有 `codex/claude`
2. 本轮不新增 `opencode/gemini/qwen/grok`
3. “已声明能力”与“已验证能力”不是同义词

## 非目标

本轮不做：

1. `develop-quality-loop`
2. `runtime-gate-degradation-mode`
3. `one-liner-distribution`
4. `lightweight-skill-registration`
5. `update / clean / repair` 完整生命周期命令面
6. 任何新增宿主的正式安装与 release gate 接入

## 中间态 Gate

- Group 1 完成后，必须至少通过：
  - `python3 -c "from installer.hosts import get_host_capability; c = get_host_capability('codex'); assert c.support_tier and c.install_enabled is not None"`
  - `python3 -c "from installer.hosts import iter_installable_hosts; hosts = list(iter_installable_hosts()); assert len(hosts) >= 2"`
- Group 2 完成后，必须至少通过：
  - `python3 scripts/sopify_status.py --format json` 输出包含 `schema_version`、`hosts`、`workspace_state`
  - `python3 scripts/sopify_doctor.py --format json` 输出包含 `schema_version`、`checks`、`summary`
- Group 4 完成后，必须至少通过：
  - `python3 -m unittest discover tests -v` 中 registry 与 status/doctor 相关用例全部 pass

## 安全与性能

- 安全:
  - 不把文档声明直接当成正式支持承诺
  - 不允许 installer 产品化改动绕过现有 runtime 契约
  - `doctor` 必须区分“已安装”与“已接管入口”
- 性能:
  - registry 与 `status/doctor` 以静态扫描和轻量文件检查为主
  - 不把第一阶段做成昂贵的 runtime 深调用

## 方案结论

本轮正确的落地方式不是“先把宿主数量做大”，而是先把当前正式宿主的产品表达补齐：

1. `host capability registry`
2. `status`
3. `doctor`
4. README 宿主兼容矩阵

等这条主线稳定后，再讨论是否值得为 `opencode/gemini/qwen/grok` 建立独立 scaffold。
