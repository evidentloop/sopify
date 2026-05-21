# P7 Background: Copilot Payload-Only Onboarding Mainline

## 一句话

P6 切出了 canonical writer；P7 把外部 repo 接入做成产品 — 一条官方默认路、一套 bootstrap 动作、一个最小 smoke 验证。

## 动机

- P4d 证明了 repo-local 手工接入可行
- P6 把 StateStore/invariants/IO 切成独立包，新宿主可直接 import
- 但当前的 installer/bootstrap 路径仍默认落 `.sopify-runtime/`，外部 repo 还是看到两个目录
- 缺少一条"外部 repo + Copilot + payload-only"的产品化接入路

## 目标态

外部 repo 接入 Sopify 后：

1. 只有 `.sopify-skills/` 一个 Sopify 目录（用户心智负担最小）
2. 版本锚点 + 能力声明从 `.sopify-runtime/manifest.json` 迁入 `.sopify-skills/` 结构
3. prompt asset 分发有官方默认做法（不碰 `.github/copilot-instructions.md`）
4. 首次进入工作流有明确的 bootstrap 命令 + diagnostics 反馈
5. 接续链路可走通（handoff 消费 + state 写入 via canonical_writer）

## 不在范围

- Deep runtime 的改动（runtime/ 目录本体不动）
- 多宿主适配（只押 Copilot 一条路）
- protocol.md 修改（P7 是产品化，不是协议修订）
- 大规模 installer 重写（只做外部 repo 路径的最小增量）
- 人工试点验证（用机器 smoke 替代）

## 前置

| 依赖 | 状态 |
|------|------|
| P4d Copilot CLI Pilot | ✅ |
| P5 Contract Surface Shrinkage | ✅ |
| P6 Canonical Writer Cutover | ✅ |

## 最小交付证据

1. 至少 1 个非 Sopify repo 完成 Copilot + Sopify workspace 初始化并走通接续消费
2. 接入后只有 `.sopify-skills/` 一个 Sopify 目录（或明确记录为何 `.sopify-runtime/` stub 仍需保留）
3. 机器 smoke test 覆盖接入 happy path（bootstrap → state write → handoff consume）
4. README / examples 包含可独立跟随的端到端 demo

## 吸收项

- **Copilot Payload-Only Onboarding Proof**（原证据候选，tasks.md L97-103）→ 升级为 P7 主体
- **First-Use Adoption Proof**（原证据候选，tasks.md L69-79）→ 发布链 + examples + 视觉资产部分并入 P7
