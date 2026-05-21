# 技术设计: P7 Copilot Payload-Only Onboarding Mainline

## 范围边界

**在范围内**：
- 外部 repo 接入路径产品化（Copilot + payload-only）
- 版本锚点从 `.sopify-runtime/manifest.json` 迁入 `.sopify-skills/` 结构
- prompt asset 分发机制（不碰 `.github/copilot-instructions.md`）
- 外部 repo bootstrap 命令 + diagnostics
- 发布链 + examples + smoke test
- 吸收 First-Use Adoption Proof 的 examples/视觉资产部分

**不在范围内**：
- Deep runtime 改动（runtime/ 目录本体不动）
- 多宿主适配（只押 Copilot 一条路）
- protocol.md 修改
- 大规模 installer 重写
- 人工试点验证（用机器 smoke 替代）

## 当前状态分析

### .sopify-runtime/ 在外部 repo 中的角色

当前 bootstrap 后外部 repo 会有：
```
workspace/
├── .sopify-skills/          ← 用户工作空间（state, plan, blueprint 等）
└── .sopify-runtime/         ← thin stub（manifest.json 仅 ~8 字段）
    └── manifest.json        ← 版本锚定 + 能力声明 + locator_mode
```

`.sopify-runtime/manifest.json` thin stub 字段：
- `schema_version`: "1"
- `stub_version`: "1"
- `bundle_version`: 版本号
- `required_capabilities`: 能力声明
- `locator_mode`: "global_first"
- `legacy_fallback`: false
- `ignore_mode`: gitignore 策略
- `written_by_host`: true

### 问题

- 用户看到两个 `.sopify-*` 目录，心智负担
- `.sopify-runtime/` 这个名字暗示"这里有 runtime"，实际只是一个 JSON stub
- 外部 repo 不跑 deep runtime，这个目录的存在误导性强

## 设计方向（S1 决策后细化）

### 方案空间

| 方案 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| A: 迁入 .sopify-skills/ | 版本锚点改为 `.sopify-skills/sopify.json` | 一个目录、直觉 | 需改 detection 逻辑 |
| B: 保留 stub 但改名 | `.sopify-runtime/` → `.sopify-version` 或类似 | 改动最小 | 还是两个目录 |
| C: 嵌入 prompt asset | 版本信息写入 AGENTS.md 头部 | 零额外文件 | prompt asset 承载非 prompt 信息 |

### 决策记录

（S1 分析后填充）

## 接入路径目标态

```
外部 repo 接入后：
workspace/
├── .sopify-skills/
│   ├── sopify.json          ← 版本锚点 + 能力声明（从 .sopify-runtime/ 迁入）
│   ├── state/               ← canonical_writer 写入的状态
│   ├── prompts/             ← prompt asset（AGENTS.md / CLAUDE.md）
│   └── ...
└── (NO .sopify-runtime/)
```

> 以上为设计方向草案，S1 决策后确认最终形态。

## Prompt Asset 分发

### 约束
- 不碰 `.github/copilot-instructions.md`（那是用户的）
- Copilot 需要在 repo 内有可发现的 instruction 文件

### 方案空间

（S1 分析后细化 — 需确认 Copilot 的 prompt discovery 机制）

## 发布链

### 最小交付
- Release asset（prompt assets + canonical_writer + sopify_contracts）
- 一条 bootstrap 命令
- examples/ 端到端 demo

### Smoke Test 覆盖

```
bootstrap → .sopify-skills/ 初始化
         → version anchor 写入
         → state write via canonical_writer
         → handoff consume 验证
```
