---
plan_id: 20260521_p7_payload_only_onboarding_mainline
feature_key: p7_payload_only_onboarding_mainline
level: standard
lifecycle_state: active
---

# 任务清单

## 决策记录

| DR | 决策 | 约束 |
|----|------|------|
| DR-1 版本锚点 | `.sopify-skills/sopify.json`（极简，~5 字段） | 版本真值只在此文件，不重复 |
| DR-2 Repo-local 激活载体 | repo-local pointer 不是统一文件模型；仅在宿主需要 repo-local discovery 时，写入宿主原生 instruction 文件 | Codex/Claude 默认不写 repo-local header；具体文件名到实现切片再落 |
| DR-3 Bootstrap 入口 | `python3 -m sopify_bootstrap` canonical，`curl\|bash` convenience | init 最小产出 = sopify.json + ignore block；pointer 按宿主需要追加，不是默认产物 |

**定性：** P7 不是从 0 到 1 的全局化。全局发动机已就位，P7 只替换 repo 内的 legacy 激活物（`.sopify-runtime/manifest.json` → 统一 workspace marker）。统一的只有 sopify.json；本地 pointer 不是统一文件模型，而是宿主适配策略。

## S1: 激活物迁移方案分析 + 新 marker/pointer 模型定义

- [x] 现状全链路走读：全局发动机 + repo thin stub 的消费者全景
- [x] `.sopify-runtime/manifest.json` thin stub 字段清单 + 6 个生产消费者映射
- [x] 版本锚点迁移方案评估 → DR-1 APPROVED: `.sopify-skills/sopify.json`
- [x] prompt 分发模型修订 → DR-2 APPROVED: 全局 prompt + repo 轻量 pointer
- [x] bootstrap 入口决策 → DR-3 APPROVED: `python3 -m sopify_bootstrap` canonical
- [x] P7 定性校正：不是 greenfield 全局化，而是 repo 激活物迁移
- [x] 决策拍板（DR-1/2/3 全部 APPROVED，含约束条件）

## S2: 激活物迁移实现（统一 marker + dual-path detection）

- [x] `.sopify-skills/sopify.json` schema + 读写逻辑
- [x] 6 个生产消费者检测路径迁移（`.sopify-runtime/manifest.json` → `sopify.json`，dual-path fallback）
- [x] workspace detection 锚点切换（祖先扫描改为 `sopify.json`）
- [x] dual-write 过渡期：bootstrap 同时写 sopify.json + legacy stub
- [x] legacy field merge：sopify.json 为 primary marker 时，从 legacy stub 补入 `legacy_fallback`/`ignore_mode` 等字段
- [x] 全量回归：721 passed

## S3: Bootstrap diagnostics + 安装体验优化 + Copilot 决策 spike

**范围：** 只改 curl/bootstrap 默认输出、失败提示、help 文案、verbose 诊断保留；Copilot 只做决策 spike。不改变运行时行为，不引入 Copilot instruction 分发实现。

**验收标准（scope 卡死）：**
- curl 安装成功时，默认输出只回答：装好了什么、有没有改项目、下一步输入什么
- 错误时先给人话原因和修复动作，再给 reason_code
- 现有完整诊断通过 `--verbose` 或 `sopify doctor` 保留
- macOS/Linux shell 和 PowerShell 文案能力对齐
- 不带 `--workspace` 时仍然不写项目目录

**任务：**
- [x] `installer/distribution.py`: `render_distribution_result()` 重写
  - 成功输出：已安装 → 项目状态 → 下一步（3 秒可读）
  - 失败输出：人话错误 + 怎么修 + 诊断码保留
  - 语言按 `--target <host:lang>` 渲染，不引入完整 i18n 框架
  - 成功默认隐藏 source/ref/asset/reason_code/完整 check 列表；失败保留 reason_code 但放在修复动作之后
- [x] 默认成功输出补齐 bundle 版本时间戳原样显示（宿主/语言/运行时路径已保留）
- [x] `--verbose` / `SOPIFY_DEBUG=1` 保留完整诊断输出
- [x] `install.sh` / `install.ps1` 增加阶段提示（检查依赖 → 下载 release → 解压 → 安装）
- [x] `scripts/install_sopify.py` help 文案从维护者口吻改为用户安装说明
- [x] 外部 repo 首次 bootstrap diagnostics：无宿主 payload 时输出 checked manifest paths + 安装/显式 payload_root hint，保持 warn 非阻断
- [x] 错误路径覆盖：MISSING_BUNDLE 接入 outcome_contract (fail_closed) + gate_output hint；STUB_INVALID hint 改双路径表述
- [x] status 命令适配外部 repo 场景：CLI 已支持 `--workspace-root`；inspection.py sopify.json 适配 defer 到双写结束后
- [x] 更新 `tests/test_distribution.py` 渲染断言
- [x] 约束：S3 不实现 Copilot instruction 分发，不加入 ASCII art，不动 deep installer doctor 逻辑

**本轮收口（已落盘）：**
- curl/bootstrap 默认安装输出从维护者诊断面改成人话摘要：装好了什么、是否修改项目、下一步输入什么。
- 完整诊断面未删除，收敛到 `--verbose` / `SOPIFY_DEBUG=1`，默认成功输出隐藏 source/ref/asset/reason_code/check list。
- 默认失败输出改为先给原因和修复动作，再保留 `reason_code` / `phase`。
- shell / PowerShell one-liner 入口补齐阶段提示和用户向 help 文案。
- 删除旧的 `scripts.install_sopify.render_result()` renderer，避免生产路径之外继续维护重复输出。
- 外部 repo 首次触发时，无宿主 payload 的诊断输出 checked manifest paths 和安装/显式 `payload_root` hint，并保持 warn 非阻断。

**本轮验证：**
- `python3 -m py_compile scripts/install_sopify.py installer/distribution.py installer/outcome_contract.py runtime/workspace_preflight.py runtime/gate_output.py`
- `bash -n install.sh`
- `python3 -m unittest tests.test_runtime_gate tests.test_distribution tests.test_installer tests.test_installer_status_doctor tests.test_installer_validate`
- `git diff --check`

**仍未收口：**
- S3 全部任务已完成。进入 S4。

**并行决策 spike（只出结论，不实现）：**
- [x] Copilot instruction 决策 spike：验证 `.github/copilot-instructions.md` / `.github/instructions/*.instructions.md` 在目标运行面（VS Code Chat / Cloud Agent / Code Review）是否真的生效
- [x] 内容来源与边界：从全局 bundle 预分发，不从 seed 运行时解析
- [x] frontmatter / `applyTo` 策略：`applyTo: "**"` 全匹配；源 repo 不生成（P4d 裁定）；外部 repo 生成
- [x] managed block 更新、冲突、覆盖、卸载/回滚策略：轻入口用 managed block，重说明用 owned file
- [x] 产出验证记录：`copilot_instruction_spike.md`

## S4: Copilot instruction 分发实现

**前置：** S3 决策 spike 已完成内容来源、frontmatter/applyTo、源 repo 策略、运行面验证、managed block 策略。

**实现方案：** 不注册 HostAdapter（Copilot 无 `~/.copilot/` 全局目录）；用 audit-only allowlist 透传 preflight；payload 预分发资源文件；bootstrap 双路径插桩。

- [x] T0: preflight 透传 — `_AUDIT_ONLY_HOST_IDS` allowlist + 双变量拆分 (`detected_host_id` / `bootstrap_host_id` / `payload_host_id`)
  - `runtime/workspace_preflight.py`: `_ensure_supported_host_id()` 跳过 audit-only；`_validate_host_id_alignment()` 跳过 audit-only
  - 结果 contract: `preflight.host_id`=实际 payload 属主, `preflight.bootstrap_host_id`=copilot, `preflight.payload_host_id`=实际 payload 属主
- [x] T2: 内容 & payload 资源部署
  - `installer/resources/copilot/lightweight.md` (1128B，< 4K Code Review cap) — 轻入口 managed block 内容
  - `installer/resources/copilot/full.md` (6199B，含 `applyTo: "**"` frontmatter) — 重说明 owned file 内容
  - `installer/payload.py`: `_ensure_copilot_instruction_resources()` 绕过 `_payload_is_current` early return
- [x] T3: managed block 机制 — `_write_managed_instruction_block` / `_remove_managed_instruction_block` / `_sync_copilot_instruction_assets`
  - `installer/bootstrap_workspace.py`: 7 个新函数，双路径插桩 (READY + MISSING/OUTDATED)
  - READY 路径：instruction sync 在 `request_authorization_mode` 写入门控内执行
- [x] T1: 路由 — `host_id == "copilot"` 字符串判断，不进 host registry
- [x] 测试：8 个新测试 (6 bootstrap + 2 preflight)，全量 723 passed + 51 subtests

**已知限制（S5+ 解决）：**
- 仓内无生产入口传 `--host-id copilot`。S4 只实现分发机制，Copilot 侧触发入口（如 copilot-setup-steps / custom instruction 引导）属于 S5/S6 范围
- 资源同步为"只增不减"：payload 侧只 copy 不清理已删除资源，workspace 侧不主动清理旧指令文件。资源改名/回退场景需手动清理或后续加 reconcile 逻辑

## S5: 发布链 + example

**设计结论（4 项锁定）：**

### DC-1: Release asset 范围

**包含：**
- `install.sh` / `install.ps1`（已有 `render-release-installers.py` 渲染 stable channel）
- `bootstrap.sh`（convenience wrapper：`curl|bash` 一键 init workspace）
- CHANGELOG.md release notes（已有 `release-draft-changelog.py`）

**不包含：**
- 不新增 tarball / wheel / binary 分发（当前 git clone + curl install 已满足最小接入）
- 不做 PyPI / npm 发布（超出 P7 范围）
- 不改动 CI release workflow（ci.yml 当前已覆盖 preflight + smoke + gate）

### DC-2: Example 范围

- 只做 1 个最小外部 repo example（`examples/external-repo-quickstart/`）
- 目标：展示 Copilot + Sopify 全链路（bootstrap → 首次 `~go` → state 写入 → handoff 消费）
- 不做多宿主矩阵（Codex/Claude 的接入已在 README 现有 Install targets 覆盖）
- 不做 monorepo / polyglot 等高级场景

### DC-3: README / docs 入口顺序

现有 README 已覆盖 Codex/Claude 的 deep install 路径。P7 新增：
1. README 新增 "External Repo (Copilot)" 段落在 Install targets 表后，展示 `bootstrap.sh` 一键接入
2. 保留 `docs/how-sopify-works.en.md` 作为深入入口，不重构
3. S4 已知限制的对外表述：
   - Copilot 触发入口尚未就绪 → 对外文案只写 "Copilot trigger wiring is coming next"，不暴露 `--host-id copilot` 等内部实现细节
   - sync 只增不减 → 不面向用户暴露（内部实现细节，不影响首次接入）

### DC-4: ASCII art 降级

- 明确为最后 polish，不阻塞 S5 主链路
- 实现顺序排在 README 更新之后
- 如果时间不够，可推迟到 S6 后或独立 patch

**实现顺序：**

- [ ] T2: `bootstrap.sh` convenience wrapper — curl one-liner 下载并执行 `python3 -m sopify_bootstrap init`（先落实入口，后续 example 基于真实入口写）
- [ ] T1: `examples/external-repo-quickstart/` — 最小端到端 demo（基于 T2 真实入口）
- [ ] T4: install/bootstrap 命令文档 — `docs/` 下新增或更新接入文档（完整步骤）
- [ ] T3: README 更新 — Install targets 表增加 Copilot 行 + External Repo 段落（docs 压缩版）
- [ ] T5: polish — Sopify ASCII art logo（45 列，仅 interactive terminal，`isatty()` 门控）

**验收标准：**
- `examples/external-repo-quickstart/` 包含可独立跟随的步骤说明
- README 中 Copilot 接入路径可发现
- `bootstrap.sh` 可从空 repo 产出 `.sopify-skills/sopify.json` + `.gitignore` managed block
- 全量测试无回归

## S6: Smoke test + 验收

- [ ] 机器 smoke test：bootstrap → state write → handoff consume（端到端）
- [ ] 至少 1 个非 Sopify repo 走通全链路
- [ ] receipt + 蓝图同步 + history 归档
