# T4：中等档冗余清理

**T4 已完成，待大脑审 diff 和独立验收。** 本轮涉及 **22 个仓库文件：删除 7 个、修改 15 个，净减 2,292 行**；全量 **386 passed, 97 subtests passed**，preflight、公开文档检查和 `git diff --check` 均退出 0。未 commit、push 或操作真实用户 home。

基线：`feat/sopify-narrow-focus@a9f6825174c1d4cc4717b730c2e33bf8d099af35`。行数仅统计本轮写集，排除执行期间外部修改的 `plan.md`、`tasks.md`。

## 1. 删除前的引用检查

每项删除前都执行了 `git grep -n -E <对应路径或符号> -- .`。完整查询、退出码和命中行保存在 [deletion-references-before.json](./t4-evidence/deletion-references-before.json)，删除后复查见 [deletion-references-after.json](./t4-evidence/deletion-references-after.json)。

| 删除文件 | 删除前发现 | 处理 |
|---|---|---|
| `sopify_writer/_resume.py` | 路径及导出符号共 38 处命中；当前代码的 17 处全部在文件自身，未发现外部导入或调用；其余为受保护的计划/审计记录。 | 删除私有残留；writer 公开导出、schema、store 均未改。 |
| `scripts/w33_qoder_proof.py` | 4 处均为计划/审计记录，没有当前入口调用。 | 删除模拟会话试点脚本，保留 history 中原始证明材料。 |
| `scripts/check-enhancement-declaration.py` | 4 处均为计划/审计记录，没有当前调用。 | 删除只输出 advisory 的旧检查，不删能力模型或 Doctor。 |
| `scripts/sync-skills.sh` | 当前外部引用为 CONTRIBUTING 双语、pre-commit 白名单、release-hook 夹具、renderer 注释；另有脚本自身 usage 和历史 CHANGELOG。 | 改为现有 renderer 的 `--output` 预览，删除旧白名单项，夹具复制共享 YAML loader；历史 CHANGELOG 保留。 |
| `.sopify/blueprint/skill-standards-refactor.md` | 唯一现行链接在 blueprint README；其余为计划/历史记录。 | 删除旧蓝图，索引改指现有 host-onboarding。 |
| `docs/dev/development-guidelines.md` | 无现行入链，2 处为受保护计划/审计记录。 | 项目特有协作规则并入 CONTRIBUTING 双语后删除。 |
| `examples/external-repo-quickstart/sopify.json.example` | 无现行读取或链接，1 处为受保护审计记录。 | 删除含旧 capabilities 的示例，不再让用户复制固定版本 marker。 |

删除后，当前代码、执行入口、安装、测试和现行文档中没有上述失效调用或链接。剩余名称只在受保护的 plan/history/ADR 记录及 CHANGELOG 退场说明中；新 Unreleased 提及旧命令是迁移说明，不是调用。没有为消除 grep 命中而改历史或当前方案。

## 2. 具体改动与净减行数

按 `git diff --numstat --no-renames` 统计，包含注释和空行：新增 **290**、删除 **2,582**，净减 **2,292**。逐文件指纹与前后行数见 [final-inventory.json](./t4-evidence/final-inventory.json)。

| 文件 | 净变化 | 本轮变化 |
|---|---:|---|
| `sopify_writer/_resume.py` | −84 | 删除私有旧恢复校验。 |
| `scripts/w33_qoder_proof.py` | −405 | 删除模拟会话试点。 |
| `scripts/check-enhancement-declaration.py` | −78 | 删除旧 advisory。 |
| `scripts/sync-skills.sh` | −99 | 删除本地缓存树生成命令。 |
| `scripts/render-host-skills.py` | −59 | 复用 `_yaml_subset.load_yaml`；保留 stdout、`--output`、`--verify-all`。 |
| `.githooks/pre-commit` | 0 | 从发布相关路径白名单移除已删脚本。 |
| `tests/test_release_hooks.py` | 0 | 夹具由复制 sync-skills 改为复制 `_yaml_subset.py`，保留 renderer 所需依赖。 |
| `.sopify/blueprint/protocol.md` | −86 | 删除 Runtime 对照列、旧 EAR 字段展开和陈旧实现映射，压缩 draft 叙述并链接历史。 |
| `.sopify/blueprint/design.md` | −565 | 714→149 行；保留模块、部署、所有权、预算和取舍，规范链接 Protocol，旧架构表回到归档。 |
| `.sopify/blueprint/tasks.md` | −142 | 168→26 行；只保留符合当前定位的未完成项及有重访条件的延后项。 |
| `.sopify/blueprint/skill-standards-refactor.md` | −260 | 删除旧提案全文。 |
| `.sopify/blueprint/README.md` | −2 | 修复删除后的索引，当前焦点改指实际方案/长期任务/历史索引，不复制旧版本快照。 |
| `.sopify/project.md` | −5 | 澄清项目资产称谓；重复的 Develop 质量字段说明改指实际规则来源。 |
| `CONTRIBUTING.md` | −96 | 合入项目协作边界，提供单文件预览命令，发布只链接 release-process。 |
| `CONTRIBUTING_CN.md` | −97 | 同步中文规则与入口；保留现有章节结构。 |
| `docs/dev/development-guidelines.md` | −81 | 合并后删除。 |
| `docs/dev/release-process.md` | −111 | 200→89 行；唯一维护 hook、版本同步、assets、发布、远端 smoke 与调试开关。 |
| `docs/how-sopify-works.md` | −6 | 安装策略链接 getting-started，宿主表链接 README，完整读链只展开一次。 |
| `docs/how-sopify-works.en.md` | −6 | 同步英文去重，保留既有结构和图片。 |
| `examples/external-repo-quickstart/README.md` | −102 | 132→30 行；改为安装入口链接、真实任务/接续例子和保留证据的卸载说明。 |
| `examples/external-repo-quickstart/sopify.json.example` | −10 | 删除失效 JSON。 |
| `CHANGELOG.md` | +2 | Unreleased 增加一条维护者命令迁移说明及空行。 |

维护者替代命令为：

```bash
python3 scripts/render-host-skills.py --host codex --lang zh --output /tmp/sopify-preview/AGENTS.md
```

它只预览 header，不再复制一套 Skill 缓存树；Skill 正文直接查规范源。实际 `--output` 验证使用临时目录，未向用户目录写入。

## 3. 解析与规范保护

### Renderer 零漂移

修改前先比较旧 parser 与 `_yaml_subset` 对当前 `skills/hosts.yaml` 的结果，再保存五宿主 × 两语言的输出指纹。修改后：

- 五个宿主的解析值完全一致，包括 null、布尔和引号字符串。
- 十份 header 的 UTF-8 字节数与 SHA-256 完全一致。
- `--verify-all` stdout 完全一致。
- `--output` 临时文件 smoke 退出 0，内容与对应指纹一致。

因此保留共享 loader 改法，没有刷新 golden。证据：[renderer-before.json](./t4-evidence/renderer-before.json)、[renderer-after.json](./t4-evidence/renderer-after.json)。

### 现行协议不变

保存并逐字核对了五个规范块：

1. §6 Verifier 全文；
2. §7 Subject Identity 与 Bound-Subject Binding；
3. §7 Action Applicability Matrix；
4. §8.1–§8.9；
5. §8.11 ActionProposal 角色声明。

这五块未变。§8.10 仅把退场历史压为一句归档链接；其他调整是旧 Runtime 列、EAR 历史字段、informative 实现映射和外围读者说明。生命周期样例明确由用户发起 finalize，遵循已有 §8。

旧字段名若属于仍保留的公开契约或负向边界，没有因包含 runtime/legacy 字样被删除。history、ADR、writer/contracts 公开导出、legacy bundle 回归、独立 helper/Hook fallback、MCP 脚本均未改。

## 4. 文档职责与检查

- 开发协作边界只在双语 CONTRIBUTING：主分支与短期主题分支、PR 合入、最小修复、显式纳入新文件及相关回归。
- 发布步骤只在 release-process：实际 preflight 项目、正常 hook 与显式 release-sync、stable assets、发布和远端 smoke。删除不存在的 eval gate 说明及第二套快速参考；本地源码 smoke 不再被写成正式远端 smoke 的替代。
- How 文档保留机制解释和一次读链，安装与支持表改为链接。
- External quickstart 不再出现 `.sopify-runtime`、`runtime_gate`、`preferences_preload` 的假示例，也不再指导删除 `.sopify/` 或整份共享指令文件。
- 11 个改动文档的本地相对链接与锚点检查无错误，见 [doc-check.json](./t4-evidence/doc-check.json)。现行文档中的旧路径/实现映射扫描无命中，见 [retired-live-scan.txt](./t4-evidence/retired-live-scan.txt)。

## 5. 验证

使用指定 Python 3.11 解释器，设置 `PYTHONDONTWRITEBYTECODE=1`、`PYTEST_ADDOPTS=-p no:cacheprovider`；shell 子进程 PATH 选择同一解释器。

| 命令 | 退出码 | 结果 |
|---|---:|---|
| `python3 -m pytest tests -q` | 0 | **386 passed, 97 subtests passed in 40.82s** |
| `bash scripts/release-preflight.sh` | 0 | golden 24 项；全量再次 **386 passed, 97 subtests passed in 33.57s**；catalog、五个协议 smoke、payload smoke 全通过。 |
| `python3 scripts/check-readme-links.py` | 0 | `README validation passed`，中英文 body 158/155 行。 |
| `git diff --check` | 0 | 无输出。 |

日志：[全量](./t4-evidence/full-suite.txt)、[preflight](./t4-evidence/preflight.txt)、[公开文档](./t4-evidence/readme-links.txt)、[diff](./t4-evidence/diff-check.txt)。测试和 preflight 期间 index、golden 均未变；收尾的纯文字精简后再次跑了文档和 diff 检查。

## 6. 需内部审计的既有摩擦

`render-host-skills.py:98` 的 `--verify-all` 显示值使用 `len(rendered)` 却标作 bytes，中文实际上是字符数。本轮遵守输出零漂移，没有顺手修改这项显示；对照证据另用 UTF-8 编码长度和完整 SHA-256，不依赖该标签。它不影响本轮解析/产物相等的结论，可由 owner 决定是否另行处理。

## 7. 作为使用者的体验

- 本轮顶部的唯一输入清单让基线、写集和报告入口更明确；但清理规范仍必须先区分现行规则、历史解释和负向约束，不能把所有 runtime 字样一删了之。
- 实际引用检查发现 sync-skills 的 hook 命中是白名单，不是调用；先看调用关系避免了虚构迁移工作。单文件 `--output` 预览已能满足这轮调试，不需要继续生成传统缓存树。
- 发布说明原先分散在贡献指南和 release-process，还混有不存在的 gate 与不同 smoke 的等同表述；合并后的价值是维护一套可实际执行的步骤，而不是增加发布机制。

## 8. 并行改动与交接

执行期间方案 `plan.md`、`tasks.md` 出现了外部更新（T6b、T8/T9 安排），本轮未写这两个文件，已原样保留并排除统计；另外 **277 个受保护 plan/state/history/ADR 文件**相对开始快照未变。HEAD、index 未变，其余未授权文件未改。

用户随后直接要求 **Trae/T8 照常推进、agy 作为主要 dogfood、后续问题再提 PR**，已通过 Orca 原文转达大脑；本报告不代写方案，也不把先前的 T8 延期记载当作最新裁定。

T4 本地完成定义均已满足，剩余为大脑审 diff、独立验收和 owner 写回。报告及证据留在指定 scratch 目录，由 owner 按既有波次收口约定归档。
