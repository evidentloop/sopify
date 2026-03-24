# 技术设计: 默认启用宿主桥接的一键安装（`default-host-bridge-install`）

## 设计目标

在不破坏现有 Sopify runtime 控制面与 installer core 边界的前提下，把 `codex` / `claude` 的默认安装语义升级为：

1. 用户仍执行一条安装命令
2. 安装后默认具备 turn-level host bridge
3. 宿主每轮优先执行：
   - workspace preflight / bootstrap
   - preferences preload
   - default runtime entry
   - handoff-first continuation
4. 用户不再需要理解或配置 `bridge`
5. 宿主差异被收敛在薄 adapter，而不是复制两套完整实现

## 总体设计

### 0. 产品入口

对外安装命令保持不变：

```bash
bash scripts/install-sopify.sh --target codex:zh-CN
bash scripts/install-sopify.sh --target claude:zh-CN
```

不新增：

```bash
--bridge auto
--bridge off
--bridge supervisor
```

bridge 选择逻辑完全内收为宿主适配逻辑。

### 1. 分层架构

推荐分成三层：

#### A. installer core

继续保留当前职责：

- host prompt install
- payload install
- optional workspace bootstrap

该层继续由现有 [`scripts/install_sopify.py`](/Users/weixin.li/Desktop/vs-code-extension/sopify-skills/scripts/install_sopify.py) 与 `installer/*` 承担。

#### B. shared bridge core

新增独立模块，负责所有宿主共享的 turn-level 逻辑：

- workspace preflight / bootstrap
- preferences preload
- runtime dispatch
- handoff-first continuation
- checkpoint resume helpers
- trace / smoke markers

建议目录：

```text
host_bridge/
├── models.py
├── install.py
├── doctor.py
├── core/
│   ├── preflight.py
│   ├── preferences.py
│   ├── dispatch.py
│   ├── handoff_loop.py
│   ├── checkpoint_resume.py
│   └── trace.py
└── hosts/
    ├── claude.py
    └── codex.py
```

#### C. façade install entry

新增顶层 façade，默认串起：

1. core install
2. bridge deploy
3. optional workspace bootstrap
4. bridge doctor

建议入口：

```text
scripts/install_with_bridge.py
```

`scripts/install-sopify.sh` 最终改为默认调用 façade，而不是直接调用旧 installer。

## 为什么不把 bridge 塞进现有 installer core

当前 [`InstallResult`](/Users/weixin.li/Desktop/vs-code-extension/sopify-skills/installer/models.py) 的语义已经很清楚：

- `host_install`
- `payload_install`
- `workspace_bootstrap`

如果把 bridge 强行揉进去，会出现两个问题：

1. 旧 installer 变成“安装期 + 会话期行为”的混合抽象
2. 老的 core smoke 与结果渲染都会被破坏

因此本设计明确：

- 旧 core install API 尽量不变
- façade 通过组合结果暴露新的 bridge 安装阶段

## 安装命令与内部调用关系

### 外部命令

```bash
bash scripts/install-sopify.sh --target codex:zh-CN [--workspace <path>]
```

### 内部调用链

```text
install-sopify.sh
  -> scripts/install_with_bridge.py
     -> core.run_install(...)
     -> bridge.install_default_for_host(...)
     -> optional core.run_workspace_bootstrap(...)
     -> bridge.doctor(...)
```

关键要求：

- 用户命令面不暴露 bridge 选项
- 旧 [`scripts/install_sopify.py`](/Users/weixin.li/Desktop/vs-code-extension/sopify-skills/scripts/install_sopify.py) 继续可作为内部 core entry 使用
- façade 负责组合显示新语义

## 宿主接法

本轮不再用“所有宿主都走 `hook | supervisor`”来抽象 bridge。

### 1. `claude v1 = minimal hooks bridge`

bridge kind:

- `claude_hooks`

真实接法：

1. 安装 bridge 资产到 `~/.claude/sopify/bridge/`
2. 在 Claude 配置侧注册最小 hooks 集
3. `UserPromptSubmit` 负责 turn ingress
4. `Stop` 负责 fail-closed 与 pending checkpoint 阻断

v1 固定挂载事件：

- `UserPromptSubmit`
- `Stop`

本轮暂不进入默认值的事件：

- `PreToolUse`
- `PermissionRequest`
- `PostToolUse`
- `SubagentStop`

设计理由：

- 先拿到“每轮输入稳定先走 Sopify runtime”
- 把 `clarification / decision / execution_confirm` 的 fail-closed 先做稳
- 避免一开始把 Claude hooks 面铺得过宽

### 2. `codex v1 = launcher bridge`

bridge kind:

- `codex_launcher`

真实接法：

1. 安装 bridge 资产到 `~/.codex/sopify/bridge/`
2. 安装一个 Sopify 管理的 launcher 到 `~/.codex/sopify/bin/`
3. launcher 接管 Sopify 会话的 turn ingress
4. launcher 在把请求交给宿主前先跑 shared bridge core

launcher 必须先做：

1. workspace preflight / bootstrap
2. preferences preload
3. default runtime dispatch
4. handoff-first continuation

本轮明确不做的假设：

- 不假设 `codex` stock CLI 存在稳定的 Claude-style hooks
- 不依赖隐藏 hook / 私有环境变量 / 未公开配置点

### 3. `codex v2 = app-server bridge`（预留）

后续方向保留为：

- `codex_app_server`

但本轮不进入默认安装主链，原因如下：

1. 需要额外处理 richer session lifecycle
2. 会拉高 rollout 与 doctor/smoke 的一次性复杂度
3. 当前目标是先补齐默认入口，不是重写 Codex 宿主链

## bridge 核心状态机

bridge 只消费现有机器契约，不重写 runtime 语义。

### 1. request ingress

输入：宿主收到的原始用户请求

处理顺序：

1. 解析当前 workspace
2. 检查 `.sopify-runtime/manifest.json`
3. 若缺失或不兼容，则调用 bootstrap helper

### 2. preferences preload

在每次准备进入 Sopify LLM 回合前：

1. 从 manifest 读取 `limits.preferences_preload_entry`
2. 执行 preload helper
3. 仅在 `status=ready && preferences.status=loaded && injected=true` 时注入 `injection_text`

### 3. runtime dispatch

bridge 必须先把原始请求交给：

- repo-local `scripts/sopify_runtime.py`
或
- vendored manifest 指向的 `default_entry`

而不是直接把原始请求交给宿主模型。

### 4. handoff loop

runtime 结束后，bridge 必须优先读取：

```text
.sopify-skills/state/current_handoff.json
```

并按 `required_host_action` 分流：

- `answer_questions`
- `confirm_decision`
- `confirm_execute`
- `continue_host_workflow`
- `continue_host_develop`
- `continue_host_quick_fix`
- `host_compare_bridge_required`
- `host_replay_bridge_required`
- `continue_host_consult`

### 5. shared trace markers

为避免 doctor / smoke 只停留在概念层，shared bridge core 统一输出可验证的 trace marker：

- `preflight_started`
- `preflight_completed`
- `preferences_preload_started`
- `preferences_preload_completed`
- `runtime_dispatch_started`
- `runtime_dispatch_completed`
- `handoff_loop_started`
- `handoff_loop_completed`

宿主 smoke 只验证“如何进入”，顺序 correctness 统一由 shared trace marker 证明。

## 组合结果模型

不建议直接改旧 [`InstallResult`](/Users/weixin.li/Desktop/vs-code-extension/sopify-skills/installer/models.py) 语义。

建议 façade 新增两层结果：

```python
@dataclass(frozen=True)
class BridgeInstallResult:
    kind: str                 # claude_hooks | codex_launcher
    action: str               # installed | updated | skipped
    host: str
    root: Path
    launcher_path: Path | None
    doctor_status: str
    doctor_summary: str


@dataclass(frozen=True)
class UnifiedInstallResult:
    core: InstallResult
    bridge: BridgeInstallResult
```

设计要求：

- `core` 继续保持老语义
- 新结果只在 façade 层组合
- 便于保留旧 smoke / 旧 installer API

## 安装落点

推荐把 bridge 资产放进宿主本地 Sopify payload 下，避免再发散新的全局目录：

```text
~/.codex/sopify/bridge/
~/.claude/sopify/bridge/
```

最小建议结构：

```text
sopify/
├── payload-manifest.json
├── bundle/
├── helpers/
├── bridge/
│   ├── bridge-manifest.json
│   ├── core/
│   ├── hosts/
│   └── doctor/
└── bin/
    └── ...
```

其中：

- `codex` 可在 `bin/` 下安装 launcher
- `claude` 不要求 launcher，但 hook handler 也复用 `bridge/` 下的 shared core

要求：

- bridge 资产跟随 host-local Sopify 一起安装和升级
- 不额外引入新的跨产品全局目录

## 文案与结果渲染

当前 [`scripts/install_sopify.py`](/Users/weixin.li/Desktop/vs-code-extension/sopify-skills/scripts/install_sopify.py) 的结果渲染只有：

- Host
- Payload
- Workspace
- Smoke check

新 façade 需要补一段：

- Bridge

最小展示项：

- `action`
- `kind`
- `root`
- `doctor_status`
- `doctor_summary`

### 示例

```text
Bridge:
  action: installed
  kind: codex_launcher
  root: ~/.codex/sopify/bridge
  doctor: ready
  summary: Sopify launcher now owns Codex session ingress before runtime dispatch
```

## 校验链路

### 1. 保留 core smoke

旧 [`scripts/check-install-payload-bundle-smoke.py`](/Users/weixin.li/Desktop/vs-code-extension/sopify-skills/scripts/check-install-payload-bundle-smoke.py) 继续存在，职责不变：

- 验证 prompt / payload / bundle bootstrap
- 验证 default entry / plan-only entry / bundle 完整性

### 2. 新增 bridge doctor

建议新增：

```text
python3 scripts/check-host-bridge-doctor.py --target codex:zh-CN
```

#### Claude doctor contract

至少检查：

1. `~/.claude/sopify/bridge/` 已部署
2. 最小 hooks 集已注册
3. `UserPromptSubmit` handler 可执行
4. `Stop` handler 可执行
5. handler 能发现 preload entry / default entry / handoff file

ready 的最低条件：

- `bridge_root_exists`
- `user_prompt_submit_registered`
- `stop_registered`
- `handler_paths_resolved`
- `runtime_entries_resolved`

#### Codex doctor contract

至少检查：

1. `~/.codex/sopify/bridge/` 已部署
2. `~/.codex/sopify/bin/` 下 launcher 存在且可执行
3. launcher 能解析 workspace / manifest / preload entry / default entry
4. launcher dry-run 能输出 shared trace markers 的预备信息

ready 的最低条件：

- `bridge_root_exists`
- `launcher_exists`
- `launcher_executable`
- `runtime_entries_resolved`
- `launcher_dry_run_ready`

### 3. 新增 bridge smoke

建议新增：

```text
python3 scripts/check-host-bridge-smoke.py --target codex:zh-CN
```

#### Claude smoke contract

最小覆盖：

1. 模拟 `UserPromptSubmit`，验证先执行 `preflight -> preload -> runtime dispatch`
2. runtime 产出 handoff 后，验证宿主优先消费 handoff 而不是输出文案
3. 在 `clarification_pending / decision_pending / execution_confirm_pending` 下，模拟 `Stop`，验证 fail-closed

判定标准：

- trace marker 顺序正确
- handoff-first 生效
- pending checkpoint 不能被视为已完成

#### Codex smoke contract

最小覆盖：

1. 通过 launcher 发起测试输入，验证先执行 `preflight -> preload -> runtime dispatch`
2. runtime 产出 handoff 后，验证 launcher 优先消费 handoff
3. 在 `clarification_pending / decision_pending / execution_confirm_pending` 下，launcher 必须 fail-closed 并向用户展示 checkpoint 摘要

判定标准：

- trace marker 顺序正确
- launcher 不直接把原始请求交给宿主
- pending checkpoint 不能绕过为普通开发入口

## rollout 策略

### Phase 1

- 新增 façade install entry
- 新增 shared bridge core
- 新增 `claude` / `codex` host adapter 骨架
- 对外安装入口切换为 façade

### Phase 2

- 接通 `claude` 最小 hooks 集
- 接通 `codex` launcher bridge
- 补 bridge doctor / smoke

### Phase 3

- 评估 `codex app-server bridge`
- 评估 `claude` 扩展 hooks 集

## 设计结论

本轮不应该把“bridge 参数化”，而应该把“默认宿主桥接”提升为新的基础设施。

实现结论如下：

1. 用户入口继续一键安装
2. bridge 默认安装，不暴露参数
3. 旧 installer core 保持职责不变
4. 新 façade 默认编排 `core install + bridge deploy + doctor`
5. bridge 采用“一套共享 core + 两个薄 adapter”
6. `claude v1` 走 `minimal hooks bridge`
7. `codex v1` 走 `launcher bridge`
8. 校验链路拆成 `core smoke + bridge doctor + bridge smoke`
