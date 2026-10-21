# README（中英文）与 Pages 整体验收独立报告

**验收者**：独立验收官（兼新用户冷读诊断员，Antigravity / Gemini 3.8 Flash）  
**候选版本**：提交 [`b81b93e`](file:///Users/weixin.li/code/github/sopify)（分支 `feat/sopify-narrow-focus`，工作区干净）  
**交付清单**：
- 文字与大纲：[`README.md`](file:///Users/weixin.li/code/github/sopify/README.md)、[`README.zh-CN.md`](file:///Users/weixin.li/code/github/sopify/README.zh-CN.md)、[`index.html`](file:///Users/weixin.li/code/github/sopify/index.html)、[`zh-CN.html`](file:///Users/weixin.li/code/github/sopify/zh-CN.html)、[`docs/how-sopify-works.md`](file:///Users/weixin.li/code/github/sopify/docs/how-sopify-works.md)（Qoder 撰写，报告 `$SP/t10-qoder.md`）
- 视觉与配图：5 张更新图档（Codex 交付，报告 `$SP/visuals-codex.md`）
**验收基准**：`tasks.md` T10、`plan.md` 统一验收标准与 D5 标语、R5 冷读诊断报告（`$SP/gemini-r5.md`）。

---

## 一、综合验收结论

| 验收模块 | 裁决 | 核心结论 |
|---|:---:|---|
| **README & Pages 整体** | **【有条件通过】** | **质的飞跃**。首屏 5 问冷读从旧版的 **2/10 分** 飙升至 **8/10 分**（全文满分 **10/10 分**）；彻底摒弃了“开发过程协议层”抽象黑话，给出具象物理形态（规则 + Skill）、物理落盘点（`.sopify/`）以及不可辩驳的 T9 真实接力证据；全量测试 420 项与链接检查全部绿灯。**唯一条件项**为快速开始 target 表需补齐新版发布的 `Antigravity` 与 `Trae（预览）`，并校准发版后的安装说明时效。 |

---

## 二、第一部分：新版 README 5 问冷读复评（对比旧版 2/10）

在 R5 审计（`gemini-r5.md`）中，旧版 README 针对新用户 5 问的首屏总分仅为 **2 / 10 分**（概念极度抽象、痛点说教、缺乏免责清单、无首屏安装、无真实业务代入）。

本次针对候选版本 [`README.zh-CN.md`](file:///Users/weixin.li/code/github/sopify/README.zh-CN.md) 与 [`README.md`](file:///Users/weixin.li/code/github/sopify/README.md) 重测，评分矩阵如下（0-2 分制）：

### 2.1 5 问复评对比矩阵

| 核心问题 | 旧版首屏 | 新版首屏（前 40 行）得分与依据 | 新版全文得分与依据 | 冷读直观感受评价 |
| :--- | :---: | :---: | :---: | :--- |
| **1. 它是什么？** | **1** | **2 / 2 分**<br>依据：`README.zh-CN.md:24`：“Sopify 是一套规则和 Skill，装进你已经在用的 AI 编程工具。需要方案的工作，它会把方案、决策和验收证据作为普通文件保存在仓库的 `.sopify/` 里……不是新编辑器，也不是新 CLI。” | **2 / 2 分**<br>依据：导语 + `how-sopify-works.md` 产品形态。 | **【具象立体，一眼看懂】** 彻底告别抽象黑话，直接告诉开发者：它是装在现有工具里的规则和技能，产物是仓库里的普通文件，不改变开发习惯。 |
| **2. 对我有什么价值、解决什么痛？** | **1** | **2 / 2 分**<br>依据：`README.zh-CN.md:5,7,24`。主标语“方案和验收证据存进仓库，换工具、换人、换 agent 都能接着做”；副标语“问答和小修照常，不强制走流程”；导语“从这份记录接着做，而不是靠记忆重来”。 | **2 / 2 分**<br>依据：`README.zh-CN.md:68-85`（价值场景）。 | **【真实有力，直击痛点】** 价值场景用三组极具场景感的 Before / After 呈现（长任务打断、换工具接手、多 agent 分工），并直接用 T9 真实跨宿主案例作为证据，真实可信。 |
| **3. 什么时候该用、什么时候不用？** | **0** | **1 / 2 分**<br>依据：`README.zh-CN.md:7`。副标语首屏直接给出定心丸：“问答和小修照常，不强制走流程。” | **2 / 2 分**<br>依据：`README.zh-CN.md:87-94`（什么时候不用）。 | **【边界明晰，消除恐慌】** 首屏有定心丸，正文设立专门的「什么时候不用」清单（问答/读代码、小修、一次性脚本直接处理），彻底消除用户“被繁重流程卡死”的顾虑。 |
| **4. 怎么开始？能否 3 步内跑出结果？** | **0** | **2 / 2 分**<br>依据：`README.zh-CN.md:26-41`。第 26 行直接切入快速开始，第 30-32 行给出一行安装命令，第 34-40 行紧跟工具与 `--target` 对照表。 | **2 / 2 分**<br>依据：`README.zh-CN.md:44-59`。 | **【路径极短，零查找成本】** 新用户前 40 行内即可找到自己工具的安装参数；接着 3 步跑通完整生命周期（1. 安装，2. `~go plan <需求>`，3. `~go` 实施与归档）。 |
| **5. 用起来长什么样？有完整示例吗？** | **0** | **1 / 2 分**<br>依据：`README.zh-CN.md:19,46-57`。首屏手绘封面，下文给出明确的命令行输入与 `.sopify/plan/.../plan.md` 路径期待。 | **2 / 2 分**<br>依据：`README.zh-CN.md:117-130`。 | **【图文并茂，有始有终】** 保留了真实的 Codex 任务 GIF 动图，且附带真实历史归档方案与收据链接；重绘的 cross-host 场景图完全对齐 T9 真实轨迹。 |
| **总分汇总** | **2 / 10** | **首屏：8 / 10 分（优异）** | **全文：10 / 10 分（满分）** | **[彻底逆转]** 结构紧凑、信噪比极高。 |

---

## 三、第二部分：事实核对与承诺证据审查

### 3.1 承诺与证据核对
1. **“换工具接着做” / T9 真实案例**：
   - README 承诺：“Claude Code 写的方案，由一个只收到 `~go` 的全新 Qoder 会话接着做下去。”
   - 核验事实：完全对齐 T9 审计报告（`t9-accept-gemini.md`），真实冷启动无任何提示，起止 SHA 确为 `a9a0f95` $\to$ `4b27f17`，证据铁证如山。
2. **Antigravity 状态与 Dogfood 记录**：
   - README 承诺：“基线；已在真实会话中 dogfood”；
   - 核验事实：完全对齐 T7/T8 验收报告（`t7t8-accept-gemini.md` 四大场景验证）与 T3b 首次绑定复测报告（`t3b-accept-gemini.md` 真实 `agy -p` 独立验证）。
3. **首次 `~go` 自动设置项目文件**：
   - README 承诺：首次受管写入前自动设置项目文件；
   - 核验事实：T3b 提交 `1ae94c2` 已经正式修复，`t3b-accept-gemini.md` 证实宿主按入口规则先调 helper，Doctor 诊断中 `workspace_bundle_manifest` 确为 `pass`。
4. **宿主分类与 Doctor 一致性**：
   - README 区分“已验证”、“基线”与“预览”，与 `sopify_doctor.py` 输出的内部状态及说明完全同构。

---

### 3.2 安装 Target 表审查（核心条件项）

对比发现两处表格存在明显的策略脱节：
- **位置 A（快速开始第 34-41 行）**：
  仅列出 Codex、Claude Code、Qoder、Copilot、Cursor 5 个宿主，**遗漏了 Antigravity 和 Trae**。
- **位置 B（支持的宿主第 103-114 行）**：
  列出了 7 个宿主，但 Antigravity 和 Trae 的安装列写为：
  `从源码克隆安装：--target antigravity:zh-CN / antigravity:en-US`
  `从源码克隆安装：--target trae:zh-CN / trae:en-US`
  下文说明文字为：“Antigravity 和 Trae 需要克隆本仓库后用 python3 scripts/install_sopify.py --target <target> 安装。”

#### 审计定性与修正要求：
- **任务目标冲突**：任务要求明确指出——*“新版 release 发布后，这两个 target 就能从 latest 安装；README 与新版同时发布，所以应列出，Trae 标为预览”*。
- **用户体验卡点**：如果 README 随新版发布后，快速开始表中依然缺少这两个 target，使用 Antigravity 的用户在首屏第一眼会认为自己的工具还不支持；而在宿主表中要求用户“从源码克隆安装”，实际上在 release 发布后用户直接通过 `curl ... | bash -s -- --target antigravity:zh-CN` 即可安装。
- **修正动作（见下文最小修改清单）**：
  1. 在快速开始 target 表中补齐 `Antigravity` 与 `Trae（预览）`；
  2. 将宿主表中 Antigravity 与 Trae 的安装列改为标准的 `--target antigravity:...` 与 `--target trae:...`，去掉“需克隆源码”的临时说明。

---

### 3.3 链接有效性复核
运行官方检查脚本：
```bash
/opt/homebrew/opt/python@3.11/libexec/bin/python3 scripts/check-readme-links.py
```
**输出**：`README validation passed: README.md body lines: 115, README.zh-CN.md body lines: 115`（退出码 0）。
测试套件 `pytest tests/test_check_readme_links.py -q`：**4 passed**。所有相对文件路径、锚点与图片链接全部真实有效。

---

## 四、第三部分：中英文一致性与技术写作风格（zh-tech-writing）

1. **行数与结构镜像对齐**：
   - 中英文 README 均为 **151 行**（正文 115 行，完全符合 ≤ 250 行预算）；
   - 10 个二级章节完全 1:1 严格对齐，中英文表格行数与参数完全一致。
2. **中文技术写作规范（zh-tech-writing）审查**：
   - 彻底摒弃了旧版的空话套话与营销口吻（如“无缝”、“最强协议”、“自动化闭环”）；
   - 动词引领、平实克制：“存进仓库”、“换工具接着做”、“问答和小修照常，不强制走流程”；
   - 标点与格式考究：中英文混排空格得当，代码符号正确加反引号，无任何 AI 机械翻译痕迹。

---

## 五、第四部分：Pages 静态页面核验

通过对 `index.html` 与 `zh-CN.html` 的源码审查及本地无头 Chrome 真实渲染（截图已落盘）：
- **元数据同步**：`<title>`、`meta description`、`og:title`、`og:description` 100% 更新为 D5 选定的主副标语。
- **Hero 区域**：标语、副标语、lede 说明文字与 README 严格一致。
- **宿主清单**：完整包含 7 个宿主（含 Antigravity · 基线支持，Trae · 预览），Claude 正式统一为 Claude Code。
- **视觉风格**：保持经典暖白（`#f7f3ea`）工程技术手账风格，卡片间距舒朗，图表文字清晰无缺字裁切。
- **资源与截图**：
  - 中文页面截图：[`/private/tmp/claude-503/-Users-weixin-li-code-github-sopify/33857f52-51ff-4f1b-965d-13e7840e4c9f/scratchpad/audit/pages-zh-cn.png`](file:///private/tmp/claude-503/-Users-weixin-li-code-github-sopify/33857f52-51ff-4f1b-965d-13e7840e4c9f/scratchpad/audit/pages-zh-cn.png)
  - 英文页面截图：[`/private/tmp/claude-503/-Users-weixin-li-code-github-sopify/33857f52-51ff-4f1b-965d-13e7840e4c9f/scratchpad/audit/pages-en.png`](file:///private/tmp/claude-503/-Users-weixin-li-code-github-sopify/33857f52-51ff-4f1b-965d-13e7840e4c9f/scratchpad/audit/pages-en.png)

---

## 六、第五部分：统一验收标准核查（仅风险与待收尾项）

1. **时效性与 Target 完整性（主要条件项）**：
   快速开始 target 表未列 Antigravity 与 Trae，且宿主表中写了“克隆源码安装”，将在发布新安装器后立即过时。
2. **Windows 安装块位置（设计取舍）**：
   Windows PowerShell 安装块放在快速开始第 3 步之后（第 61-66 行）。这是为了保证 macOS/Linux 绝大多数用户前 40 行极速阅读体验所作的合理取舍，属于可接受范畴。
3. **OG 分享卡片图片（历史遗留）**：
   `assets/sopify-og-*.jpg` 仍带有旧版标语文字。由于本轮重画清单仅覆盖场景图与架构/产品形态图，封面与 OG 卡片未做重绘，建议在后续发版时视需要做一次性更新。
4. **Pages `#why` 区块表述（口径微差）**：
   网页端 `#why` 区块保留了旧的三卡结构（“防止过早开写 / 防止接力断档 / 防止决策失忆”），虽然语义与 README 的 Before/After 兼容，但叙事形式略有不同。建议保持现状，无需在 release 前大动 HTML 结构。

---

## 七、第六部分：全量测试与校验复跑记录

在当前干净的主工作区（HEAD `b81b93e`）执行全部自动化检验：
- **全量测试套件**：
  ```bash
  PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS="-p no:cacheprovider" \
    /opt/homebrew/opt/python@3.11/libexec/bin/python3 -m pytest tests -q
  ```
  **结果**：`420 passed, 97 subtests passed in 45.26s`（退出码 0）。
- **链接与锚点检查**：
  ```bash
  /opt/homebrew/opt/python@3.11/libexec/bin/python3 scripts/check-readme-links.py
  ```
  **结果**：通过（退出码 0）。
- **格式与空白符检查**：
  `git diff --check b81b93e^..b81b93e`：退出码 0。

---

## 八、第七部分：最小修改清单（Actionable Checklist）

建议在合入主分支 / Release 前执行以下微调：

### 1. `README.zh-CN.md`
- **第 34-41 行（快速开始 target 表）**：补入 Antigravity 与 Trae（预览）：
  ```markdown
  | 你用哪个工具 | `--target` |
  |---|---|
  | Codex | `codex:zh-CN` / `codex:en-US` |
  | Claude Code | `claude:zh-CN` / `claude:en-US` |
  | Qoder | `qoder` |
  | Copilot | `copilot:zh-CN` / `copilot:en-US` |
  | Cursor | `cursor:zh-CN` / `cursor:en-US` |
  | Antigravity | `antigravity:zh-CN` / `antigravity:en-US` |
  | Trae（预览） | `trae:zh-CN` / `trae:en-US` |
  ```
- **第 112-115 行（支持的宿主表及说明）**：
  将安装列的“从源码克隆安装：”移除，改为标准的 `--target antigravity:zh-CN` 与 `--target trae:zh-CN`；删除末尾“Antigravity 和 Trae 需要克隆本仓库后用 python3 scripts/install_sopify.py 安装”的说明文字。

### 2. `README.md`
- **第 34-41 行（Quick Start target table）**：
  同上补入：
  ```markdown
  | Antigravity | `antigravity:en-US` / `antigravity:zh-CN` |
  | Trae (Preview) | `trae:en-US` / `trae:zh-CN` |
  ```
- **第 112-115 行（Supported Hosts table）**：
  同上移除 `from a clone:` 前缀与末尾克隆源码安装说明。

完成上述微调后，文档即可直接进入新手测试与用户最终验收！
