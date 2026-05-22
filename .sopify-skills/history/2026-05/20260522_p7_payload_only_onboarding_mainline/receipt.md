# P7 Receipt: Payload-Only Onboarding Mainline

## 基本信息

| 字段 | 值 |
|------|------|
| Plan ID | 20260521_p7_payload_only_onboarding_mainline |
| 状态 | **代码实现完成** |
| 分支 | plan/p7-payload-only-onboarding-mainline |
| 前置 | P6 Canonical Writer Cutover ✅ |

---

## 核心结论（一句话）

外部仓库可通过 `curl | bash` 一键初始化 Sopify workspace（sopify.json marker + .gitignore managed block + Copilot instruction files），不需要全局安装。Copilot 作为第三个宿主完成了 workspace-level 接入（指令分发 + workspace marker），触发入口（等效于 Codex/Claude `~go`）留待后续版本。

---

## 分支总 diff（vs main）

```
33 files changed, 2,812 insertions(+), 210 deletions(-)
```

---

## 决策记录

| ID | 决策 | 理由 |
|----|------|------|
| DR-1 | 版本锚点 = `.sopify-skills/sopify.json`（极简，~5 字段） | 版本真值只在此文件，不重复 |
| DR-2 | Repo-local pointer 不统一，按宿主需要写入 instruction 文件 | Codex/Claude 用全局 prompt；Copilot 无全局扩展点，需 project-level instruction |
| DR-3 | Bootstrap 入口 = `python3 scripts/sopify_init.py init`，`curl\|bash` 为 convenience | init 最小产出 = sopify.json + ignore block；pointer 按宿主追加 |
| DC-1 | Release asset 包含 bootstrap.sh | 已加入 render-release-installers.py |
| DC-2 | 只做 1 个 external-repo-quickstart example | 不做多宿主矩阵 |
| DC-3 | 不对外暴露 `--host-id copilot` | 对外文案只写 "trigger wiring coming next" |
| DC-4 | ASCII art = 最后 polish，不阻塞主链路 | T5 排最后执行 |

---

## 切片执行历史

| 切片 | 摘要 | Commits |
|------|------|---------|
| S1 | 激活物迁移方案分析 + DR-1/2/3 锁定 + 定性校正 | `1317f58`, `2c45153`, `2461f58` |
| S2 | 统一 marker 迁移 + dual-path detection | `ea7030c` |
| S3 | Bootstrap 入口 + preflight 双路径 + 安装体验优化 | `adab885`, `bbd613a`, `55e7173` |
| S4 | Copilot 指令分发（managed block + owned file + payload 资源） | `3c58c2a` |
| S5 | 发布链 + example + docs + README + ASCII art logo | `0405ebc`, `f025cc5`, `f3e043f` |
| S6 | Smoke test（12 tests 自动化） | `f3e043f` |

---

## 产出文件清单

### 新增文件

| 文件 | 类型 | 说明 |
|------|------|------|
| `scripts/sopify_init.py` | 核心 | 独立 workspace 初始化器（~340 LOC） |
| `bootstrap.sh` | 入口 | curl convenience wrapper |
| `docs/getting-started.md` | 文档 | 权威 onboarding 指南 |
| `examples/external-repo-quickstart/README.md` | 示例 | 最小端到端 demo |
| `examples/external-repo-quickstart/sopify.json.example` | 示例 | 参考 sopify.json 输出 |
| `tests/test_sopify_init_smoke.py` | 测试 | 12 个 smoke tests |
| `installer/resources/copilot/lightweight.md` | 资源 | Copilot managed block 内容（S4） |
| `installer/resources/copilot/full.md` | 资源 | Copilot owned file 内容（S4） |

### 修改文件

| 文件 | 变更 |
|------|------|
| `README.md` | Copilot 行 + Setup Paths 选路表格 + 架构描述 |
| `README.zh-CN.md` | 中文同步 |
| `assets/sopify-architecture.svg` | Copilot Adapter 框 |
| `scripts/render-release-installers.py` | bootstrap.sh 加入 release asset 模板 |
| `installer/bootstrap_workspace.py` | Copilot instruction sync 机制（S4） |
| `installer/payload.py` | Copilot 资源部署（S4） |
| `runtime/workspace_preflight.py` | audit-only host ID 透传（S4） |

---

## 测试验证

| 范围 | 结果 |
|------|------|
| 新增 smoke tests | 12 passed（sopify_init + bootstrap.sh） |
| 全量回归 | 740 passed, 1 pre-existing failure |
| Pre-existing failure | `test_install_payload_bundle_smoke_script_passes`（global payload bundle 版本不匹配，非本分支引入） |

---

## 已知限制

| 限制 | 说明 |
|------|------|
| Copilot 无生产触发入口 | `--host-id copilot` 仅用于内部测试，对外不暴露 |
| 资源同步为只增不减 | payload 侧只 copy 不清理已删除资源 |
| CN 架构图未更新 | `sopify-architecture-cn.jpg` 为 JPG 需外部工具重新生成 |

---

## Follow-up

| 事项 | 来源 |
|------|------|
| 非 Sopify repo 手工全链路验收 | S6 迁移项 |
| Copilot trigger wiring（`~go` 等效入口） | S4 已知限制 |
| CN 架构图重新生成 | S5 遗留 |

---

## 蓝图变更

| 文件 | 变更 |
|------|------|
| `blueprint/README.md` | 最近归档指向 P7（待回写） |
