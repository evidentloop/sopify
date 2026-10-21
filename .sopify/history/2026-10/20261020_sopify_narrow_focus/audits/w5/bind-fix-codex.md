# T3b：首次项目绑定与 writer 入口说明修复

结论：已在共同 header 的受管入口加入两条明确操作说明，并在 Cursor Rule 使用相同说明；从安装产物解析 helper 和 writer 路径的 14 个参数化用例通过。Codex、Antigravity 的隔离实测已完成“绑定 → 从同一 payload 当前 bundle 导入 writer → 写 state → Doctor workspace 检查通过”。全量测试 **420 passed, 97 subtests passed**；release preflight 与 `git diff --check` 均通过。

基线：`feat/sopify-narrow-focus@32687ae0ba9e80f6122c2b907239b98a6b5d34d3`。本轮改 10 个仓库文件，另原样保留上一轮 `docs/antigravity-host.md` 的未提交改动；没有 commit、push、改本仓库 `.sopify/**` 或写真实 home。README.md、README.zh-CN.md、index.html、zh-CN.html 四个并行写集文件未由本轮修改。

## 1. 新增原文与字节变化

共同 header 的「受管方案入口」仅新增以下两行；Cursor 薄 Rule 的 managed 入口采用逐字相同的两行，不复制 helper 内部判定规则。

中文：

```text
- 首次受管写入前，若 `.sopify/sopify.json` 缺失，调用 `python3 {{config_dir}}/sopify/helpers/bootstrap_workspace.py --workspace-root <project_root> --request <current_request> --interaction-mode <interactive|non_interactive>`，传入本轮完整请求和实际交互模式；仅绑定成功后继续，非交互模式不会创建标记，其他结果按返回提示停车。
- writer 导入：读取 `{{config_dir}}/sopify/payload-manifest.json` 的 `bundle_template_dir`，相对该 manifest 所在目录解析并展开 `~`，将结果加入 Python `sys.path` 后 `from sopify_writer import ProtocolStore`；只用库 API，非 CLI。
```

英文：

```text
- Before the first managed write, if `.sopify/sopify.json` is absent, call `python3 {{config_dir}}/sopify/helpers/bootstrap_workspace.py --workspace-root <project_root> --request <current_request> --interaction-mode <interactive|non_interactive>` with the full current request and actual interaction mode. Continue only after binding succeeds; non-interactive mode creates no marker, and other outcomes require stopping as directed.
- Writer import: read `bundle_template_dir` from `{{config_dir}}/sopify/payload-manifest.json`, resolve it relative to that manifest directory and expand `~`, prepend the result to Python `sys.path`, then `from sopify_writer import ProtocolStore`. Use the library API, not a CLI.
```

`<project_root>`、`<current_request>` 和交互模式由宿主填为本轮实际值，请求作为单个 argv 参数传入。使用的三个 flag 均来自现有 helper CLI；writer 位置从同一 payload 的 `payload-manifest.json` 中读取 `bundle_template_dir`，没有写死版本号，没有新增 writer CLI。

| 源文件 | 修复前 → 后 UTF-8 字节 | 增量 | 行数 |
|---|---:|---:|---:|
| 中文 header | 5357 → 6008 | +651 | 60 → 62 |
| 英文 header | 6257 → 6970 | +713 | 60 → 62 |
| 中文 Cursor Rule | 3897 → 4548 | +651 | 39 → 41 |
| 英文 Cursor Rule | 4339 → 5052 | +713 | 39 → 41 |

前后源文件快照在 `bind-fix-evidence/before/`，完整统计见 [entry-size-review.json](./bind-fix-evidence/entry-size-review.json)。header 体积基线已按审阅后的实际值手工更新；没有调宽或删除已有体积约束。

## 2. 宿主一致性与 Copilot 例外

| 宿主 | 入口与 payload 解析 |
|---|---|
| Claude / Codex / Qoder | 同一 header，通过各自 config_dir 指向对应宿主的 helper 和 manifest |
| Antigravity / Trae | 继续由已有扁平安装实现渲染共同 header；分别落到 `.gemini/config/sopify`、`.trae/sopify`，不复制新绑定实现 |
| Cursor IDE / Agent CLI | 同一薄 Rule 加同样两行；Agent CLI 顶层 Skill 已明确先实际读取该 Rule，因此没有重复修改两份 CLI Skill 模板 |
| Copilot 平铺 | 没有全局 payload；渲染时移除两条 payload 专用说明，保留原有 machine-truth 语义边界，不产生 `/sopify/helpers` 或无法执行的 payload 导入说明 |

**有依据的写集补充：**原任务未列 `installer/hosts/base.py`，但原渲染器只清空 config_dir，会让新增说明变成 `/sopify/...`。先通过本 Dispatch 的 Orca ask 得到协调者明确答复：“允许最小渲染过滤：只在 render_single_file 的无全局 payload 分支跳过这两条 payload 专用说明……不新增标记语法或配置。”因此仅在该分支增加四行过滤，以模板中现有 `{{config_dir}}/sopify/` 路径识别两条说明；没有改 helper、writer、contracts 逻辑或 schema。

Copilot 渲染结果与旧版逐字节一致：中文 27690 bytes / 627 行、英文 31000 bytes / 626 行，两个对应 golden 未变化。阶段 Skill 源树也未变化。

安装输出已将“第一次输入 ~go 自动初始化”改为首次受管写入前由宿主按入口规则调用 helper，并明确非交互模式停车；`docs/getting-started.md` 同步说明绑定及 writer 库来源。

## 3. 最小路径一致性测试

新增一个参数化测试 `tests/test_payload_entry_paths.py::test_installed_entry_payload_paths`，七宿主 × 两语言共 14 例：

- 六个有 payload 的宿主：临时 home 安装，读取实际入口文件，从文字解析 helper 和 manifest 路径；验证二者同属该 payload、helper 确实存在，以及 manifest 的 `bundle_template_dir` 中存在 writer 库；同时确认提示提供 `sys.path` 和真实的 ProtocolStore 导入。
- Copilot：实际渲染 workspace 入口，断言不含 `/sopify/helpers`、`payload-manifest.json`、`bundle_template_dir` 或不可用的全局 writer 导入说明。

这条测试检查的是安装产物与资源路径的一致性，不据此声称模型已经遵循新入口。两种实际库导入与 state 写入另由下述隔离实测覆盖。

## 4. Codex / Antigravity 实测命令与输出

实验脚本：[smoke.py](./bind-fix-evidence/smoke.py)；完整命令、stdout/stderr、marker、writer 模块路径和 Doctor JSON 摘要：[smoke-results.json](./bind-fix-evidence/smoke-results.json)。所有路径都在本报告旁的 `bind-fix-evidence/smoke/<host>/` 下；没有使用真实 `~/.codex`、`~/.gemini` 或覆盖 HOME。

先安装到显式临时 home，直接从安装后 header 中解析路径，再按其提示执行：

### codex

```bash
/opt/homebrew/opt/python@3.11/bin/python3.11 /private/tmp/claude-503/-Users-weixin-li-code-github-sopify/33857f52-51ff-4f1b-965d-13e7840e4c9f/scratchpad/audit/bind-fix-evidence/smoke/codex/home/.codex/sopify/helpers/bootstrap_workspace.py --workspace-root /private/tmp/claude-503/-Users-weixin-li-code-github-sopify/33857f52-51ff-4f1b-965d-13e7840e4c9f/scratchpad/audit/bind-fix-evidence/smoke/codex/ordinary-go-plan --request '~go plan 增加除零保护' --interaction-mode interactive
```

工具返回（state=MISSING 表示调用前分类，action=bootstrapped 是完成结果）：

```json
{
  "action": "bootstrapped",
  "state": "MISSING",
  "reason_code": "STUB_SELECTED",
  "to_version": "2026-08-30.001152",
  "ignore_mode": "exclude"
}
```

### antigravity

```bash
/opt/homebrew/opt/python@3.11/bin/python3.11 /private/tmp/claude-503/-Users-weixin-li-code-github-sopify/33857f52-51ff-4f1b-965d-13e7840e4c9f/scratchpad/audit/bind-fix-evidence/smoke/antigravity/home/.gemini/config/sopify/helpers/bootstrap_workspace.py --workspace-root /private/tmp/claude-503/-Users-weixin-li-code-github-sopify/33857f52-51ff-4f1b-965d-13e7840e4c9f/scratchpad/audit/bind-fix-evidence/smoke/antigravity/ordinary-go-plan --request '~go plan 增加除零保护' --interaction-mode interactive
```

工具返回（state=MISSING 表示调用前分类，action=bootstrapped 是完成结果）：

```json
{
  "action": "bootstrapped",
  "state": "MISSING",
  "reason_code": "STUB_SELECTED",
  "to_version": "2026-08-30.001152",
  "ignore_mode": "exclude"
}
```

随后在对应临时项目中运行的 writer Python 命令，按 header 执行相同解析步骤：

```python
manifest = Path(manifest_argument).expanduser()
bundle = (manifest.parent / json.loads(manifest.read_text())["bundle_template_dir"]).expanduser()
sys.path.insert(0, str(bundle))
from sopify_writer import ProtocolStore
import sopify_writer
assert Path(sopify_writer.__file__).is_relative_to(bundle)
ProtocolStore(Path(".sopify")).set_active_plan(plan_id="20261021_bind_smoke")
```

`manifest_argument` 是从该入口路径映射到显式临时 home 的实际 manifest，完整 `python -B -c ... <manifest>` 命令保存在 JSON；fixture 先创建一个 light plan，然后只执行一次 active_plan 写入。两个宿主实际模块路径分别位于各自的 `sopify/bundles/2026-08-30.001152/sopify_writer/__init__.py`，返回：

```json
{"plan_id": "20261021_bind_smoke"}
```

两者 Doctor 均返回：

```text
workspace_bundle_manifest: pass / STUB_SELECTED
workspace_handoff_first: pass / ok
workspace_state.version_state: up_to_date
```

### 忽略策略与非交互分支

任务提到 `.gitignore`，但 helper 现行策略必须如实保留：

| 本轮完整请求 / 模式 | Codex 与 Antigravity 结果 |
|---|---|
| `~go plan 增加除零保护` / interactive | marker 生成；受管忽略块在 `.git/info/exclude`，不擅自新增 `.gitignore`；writer state 与 Doctor 检查通过 |
| `~go init commit-lock` / interactive，另一个新 Git 仓库 | 使用同一 header 命令填入本轮请求，marker 和 `.gitignore` 受管块均生成；writer state 与 Doctor 检查通过 |
| `~go plan 增加除零保护` / non_interactive，另一个新 Git 仓库 | helper 返回 `NON_INTERACTIVE`，不创建 marker，不绕过或更改策略 |

因此已经实际验证 `.gitignore` 受管块分支；没有为“所有首次 ~go 都必须写 .gitignore”修改既有策略，也没有向产品新增 `~go init`——本次仅调用 helper 已有的显式确认分支。新 header 不复制这些内部判定，而是要求按实际模式及返回结果停止或继续。

## 5. Golden 审阅与完成检查

| 检查 | 结果 |
|---|---|
| 路径一致性专项 | 14 passed |
| 全量测试 | 420 passed, 97 subtests passed，53.48 秒；[日志](./bind-fix-evidence/pytest-full.log) |
| release preflight | All checks passed；含 28 项 golden、catalog drift、全量测试和全部现有 smoke；[日志](./bind-fix-evidence/release-preflight.log) |
| git diff --check | 通过 |
| 保护范围 | helper / writer / contracts 与执行前 SHA-256 一致；上一轮 Antigravity 文档也逐字节保留 |

手工审阅后，仅更新八项预期变化的 golden：Codex/Claude 双语 header 四项，Antigravity/Trae 双语安装入口树四项。共同阶段树、Copilot 两个产物共四项保留原 hash；没有用生成器直接覆盖失败来放行。候选值见 [golden-candidates.json](./bind-fix-evidence/golden-candidates.json)，before 快照和最小测试互相佐证；体积基线只更新 header_after 的实测值。

## 6. 统一验收标准：仅风险与未验证项

1. 本轮是入口指令修复及确定性工具实测，未启动真实模型验证其会自动执行新增两行。不能将手工按指令调用成功写成真实宿主完整协议已认证；后续须在新会话中 dogfood，行为项维持既有 BLACK_BOX_NOT_VERIFIED。
2. 非交互首写仍按现有 helper 返回 NON_INTERACTIVE；此次明确写入提示，未扩大为绕过边界。原普通 headless 计划样本不能自动等同于完成项目绑定。
3. `.gitignore` 只有现有显式确认策略才生成，默认 Git 项目仍写 `.git/info/exclude`。任务文字与默认策略的差异已用双分支实测交代，不改变用户原有忽略语义。

未发现其他验收不通过项。没有新增 CLI、配置、schema、runtime、Hook 或重复的绑定实现。

## 7. 文件范围

本轮实际修改 10 个文件：
- `skills/zh/header.md.template`
- `skills/en/header.md.template`
- `skills/zh/cursor-plugin-rule.mdc.template`
- `skills/en/cursor-plugin-rule.mdc.template`
- `installer/hosts/base.py`
- `installer/distribution.py`
- `docs/getting-started.md`
- `tests/test_payload_entry_paths.py`
- `tests/golden-snapshots.json`
- `tests/behavior-scenarios/plain-language-output-v1.json`

另保留前轮 `docs/antigravity-host.md` 的未提交改动；本轮没有再次修改它。回传 files-modified 只列本轮上述 10 个文件。

## 本轮变化

按大脑审查意见，将最终用户安装提示改为：

- English: `Sopify sets up project files the first time you run ~go in a project.`
- 中文：`在项目里第一次输入 ~go 时，Sopify 会自动设置项目文件。`

不再向最终用户展示 managed write、binding helper、项目标记或非交互模式术语；非交互边界保留在 `docs/getting-started.md`，本轮未修改该文档、T3b 入口或绑定逻辑。复用现有安装展示测试，增加中英文用户文案与不泄露上述术语的断言，没有新增测试流程。

本轮仅修改 `installer/distribution.py`、`tests/test_distribution.py`，不 commit、不 push；README/Pages 四文件及并行执行方的 `scripts/check-readme-links.py` 均未触碰。

验证结果：

| 检查 | 结果 |
|---|---|
| 分发相关测试 | 20 passed；[日志](./bind-fix-rework-evidence/pytest-distribution.log) |
| 隔离全量测试 | 420 passed, 97 subtests passed，56.09 秒；[日志](./bind-fix-rework-evidence/pytest-isolated.log) |
| 隔离 release preflight | All checks passed；[日志](./bind-fix-rework-evidence/preflight-isolated.log) |
| git diff --check | 通过 |

隔离验收背景：首次在主工作区跑全量得到 414 passed / 6 failed，失败来自并行 README/链接检查器改动（锚点、路径别名及产品图示引用），并非本轮安装提示；原始失败日志保留在 [pytest-full.log](./bind-fix-rework-evidence/pytest-full.log)。协调者明确安排从 HEAD 建临时工作树，只复制 T3b 及本轮文件后验收，再移除工作树；本轮据此使用 detached HEAD `32687ae` 的 `t3b-wt`，复制了 12 个明确文件，没有复制 README、Pages 或链接检查器的并行改动。复制清单与哈希见 [isolation-files.json](./bind-fix-rework-evidence/isolation-files.json)。因此，以上通过结论针对隔离后的 T3b 与本轮改动，不代表主工作区并行改动已经通过统一验收。

临时隔离工作树 `t3b-wt` 已移除；验证日志与复制清单保留在 scratchpad，主工作区及既有其他 worktree 保持原状。
