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
- [ ] 错误路径覆盖：未初始化 / 版本不匹配 / payload 缺失
- [ ] status 命令适配外部 repo 场景
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
- 错误路径覆盖：未初始化 / 版本不匹配 / payload 缺失。
- status 命令适配外部 repo 场景。
- Copilot instruction 决策 spike。

**并行决策 spike（只出结论，不实现）：**
- [ ] Copilot instruction 决策 spike：验证 `.github/copilot-instructions.md` / `.github/instructions/*.instructions.md` 在目标运行面（VS Code Chat / Cloud Agent / Code Review）是否真的生效
- [ ] 内容来源与边界：从 `Copilot/Skills/CN/COPILOT.md` seed 提炼，还是从全局 bundle 运行时复制
- [ ] frontmatter / `applyTo` 策略、源 repo 是否生成 instruction 文件、path-specific fallback 策略
- [ ] managed block 更新、冲突、覆盖、卸载/回滚策略
- [ ] 产出验证记录，为 S4 实现提供依据

## S4: Copilot instruction 分发实现

**前置：** S3 决策 spike 已完成内容来源、frontmatter/applyTo、源 repo 策略、运行面验证、managed block 策略。

- [ ] repo-local activation adapter：按宿主类型决定是否写本地 instruction 文件
  - 全局 prompt 型（Codex/Claude）：默认不写 repo-local header
  - 本地 instruction 文件型（Copilot）：managed block upsert 到 `.github/copilot-instructions.md` / `.github/instructions/sopify.instructions.md`
  - 若目标运行面不读取 path-specific instructions，重说明内联到轻入口
- [ ] Copilot 资产重构：从 `Copilot/Skills/CN/COPILOT.md`（P4d seed）提炼 bootstrap 产物
  - 拆成轻入口 + 重说明两层
  - 去掉 pilot-only 语气，对齐 sopify.json + bootstrap/install 叙事
  - 原 COPILOT.md 保留为 source seed / reference
- [ ] managed block 边界、升级/覆盖策略、冲突处理、卸载/回滚

## S5: 发布链 + example

- [ ] release asset 结构定义
- [ ] install/bootstrap 命令文档
- [ ] examples/ 包含至少 1 个可独立跟随的端到端 demo
- [ ] README 更新（含接入步骤 + 视觉资产）
- [ ] polish：Sopify ASCII art logo（45 列，仅 interactive terminal，`isatty()` 门控）

## S6: Smoke test + 验收

- [ ] 机器 smoke test：bootstrap → state write → handoff consume（端到端）
- [ ] 至少 1 个非 Sopify repo 走通全链路
- [ ] receipt + 蓝图同步 + history 归档
