# T7 阶段实测探针报告：Antigravity CLI 加载面与 Recipe 检验

**探针执行者**：Antigravity 宿主本身（Gemini 2.5 / agy 1.4.2）  
**探针目标**：按照 `docs/host-onboarding.md` 第 1、2 节的探针步骤，对 Antigravity CLI 的真实加载面（全局规则、项目规则、扁平/嵌套 Skills、提问工具、生效时机）进行黑盒实测取证，确定 Sopify 接入 Antigravity 的最佳表面与布局，并实地检验 Onboarding Recipe 的可用性。  
**测试环境**：
- 宿主版本：`agy 1.4.2`
- 临时探针工作区：`/private/tmp/claude-503/.../scratchpad/audit/t7-probe/test-project/`
- 安全边界：严格未修改 `~/.gemini/` 下任何文件，未修改仓库代码，未修改账号/代理/模型/配置。

---

## 一、探针问题逐项核实与证据

### 1. 全局规则加载面
- **问题**：CLI 是否会读 `~/.gemini/GEMINI.md` 或 `~/.gemini/AGENTS.md`？
- **实测与文档依据**：
  1. **文档依据**：查阅 Antigravity 官方自定义系统文档（`~/.gemini/antigravity-cli/builtin/skills/agy-customizations/SKILL.md` 与 `docs/rules.md`）：
     - 全局配置目录明确声明为：`~/.gemini/config/`；
     - 规则发现机制被定义为：“Directory-Based Rules: The system walks up from the current working directory to the repository root and loads these files”。即规则文件是基于工作区向上回溯至仓库根目录加载的，并没有声明根级 `~/.gemini/` 具备规则注入能力。
  2. **注入上下文核查**：在当前会话的系统提示词（`<user_rules>`）中，只有本项目或父级的规则注入，未见任何全局 `~/.gemini/` 规则注入。
  3. **本机文件状态**：`ls -la ~/.gemini/GEMINI.md ~/.gemini/AGENTS.md ~/.gemini/config/GEMINI.md ~/.gemini/config/AGENTS.md` 全部返回 `No such file or directory`。
- **客观结论**：**【无法验证】**（文档未将其定义为标准全局规则路径；且严格遵守任务约束“不得在 `~/.gemini/` 新增测试文件”，故无法进行注入实测）。若需全局规则，文档支持的官方路径为 `~/.gemini/config/`。

---

### 2. 项目规则加载与优先级（`AGENTS.md` vs `GEMINI.md` vs `.agents/rules/x.md`）
- **实验设计**：在临时项目 `test-project` 中放置 3 个规则文件，各携带独立全局唯一标记：
  - `AGENTS.md` -> `MARKER_PROJECT_AGENTS_MD_7718`
  - `GEMINI.md` -> `MARKER_PROJECT_GEMINI_MD_9921`
  - `.agents/rules/x.md` -> `MARKER_PROJECT_AGENTS_RULES_X_3345`
- **执行命令**：
  ```bash
  cd .../t7-probe/test-project && agy -p "Show the exact content and ordering of <user_rules> in your prompt. Which file comes first?"
  ```
- **实测输出证据**：
  ```xml
  <user_rules>
  The following are user-defined rules that you MUST ALWAYS FOLLOW WITHOUT ANY EXCEPTION. These rules take precedence over any following instructions.
  Review them carefully and always take them into account when you generate responses and code:
  <RULE[/private/tmp/.../test-project/AGENTS.md]>
  # Project Rule: AGENTS.md
  MARKER_PROJECT_AGENTS_MD_7718: Rule from AGENTS.md in project root.
  </RULE[/private/tmp/.../test-project/AGENTS.md]>
  <RULE[/private/tmp/.../test-project/GEMINI.md]>
  # Project Rule: GEMINI.md
  MARKER_PROJECT_GEMINI_MD_9921: Rule from GEMINI.md in project root.
  </RULE[/private/tmp/.../test-project/GEMINI.md]>
  </user_rules>
  ```
- **关键发现**：
  1. **复述情况**：`AGENTS.md` 和 `GEMINI.md` **均被成功加载并内联**至 `<user_rules>` 中！
  2. **优先级与顺序**：**`AGENTS.md` 排在 `GEMINI.md` 之前**（先闭包 AGENTS.md，后闭包 GEMINI.md）；
  3. **未被加载**：`.agents/rules/x.md` 的标记 `MARKER_PROJECT_AGENTS_RULES_X_3345` **未被加载**，表明 CLI 默认不从 `.agents/rules/*.md` 隐式搜寻规则，必须是项目根目录下的 `AGENTS.md` 或 `GEMINI.md`。

---

### 3. Skills 发现与加载机制（扁平 vs 嵌套、全局目录、长度限制）
- **实验设计**：在临时项目中放置两类 Skill：
  - 扁平目录（一层）：`.agents/skills/probe-flat/SKILL.md`
  - 嵌套目录（两层）：`.agents/skills/sopify/probe-nested/SKILL.md`
- **执行命令**：
  ```bash
  cd .../t7-probe/test-project && agy -p "List all skills available to you in <skills>. Quote them exactly."
  ```
- **实测输出证据**：
  ```text
  Available Skills:
  * agy-customizations (/Users/weixin.li/.gemini/antigravity-cli/builtin/skills/agy-customizations/SKILL.md)
  * anatomy (/Users/weixin.li/.gemini/config/skills/anatomy/SKILL.md)
  * antigravity-guide (/Users/weixin.li/.gemini/antigravity-cli/builtin/skills/antigravity_guide/SKILL.md)
  * fireworks-tech-graph (/Users/weixin.li/.gemini/config/skills/fire/SKILL.md)
  * probe-flat (/private/tmp/.../test-project/.agents/skills/probe-flat/SKILL.md)
  ```
- **关键发现**：
  1. **扁平 vs 嵌套发现**：
     - `probe-flat` **成功被发现**（单层子目录）；
     - `probe-nested`（两层子目录 `skills/sopify/...`）**完全未被发现**！
     - **原理印证**：与 `docs/json_configs.md` 声明的“Each entry directory is scanned **one level deep**” 100% 吻合！Antigravity CLI 原生只扫描 `skills/` 下的一层目录，**不支持嵌套目录发现**。
  2. **全局 Skills 注入目录**：
     - 内置技能来源：`~/.gemini/antigravity-cli/builtin/skills/`；
     - 用户全局自定义技能来源：`~/.gemini/config/skills/`（从当前会话的 `anatomy`、`fireworks-tech-graph` 绝对路径确凿证实）。
  3. **Description 长度限制**：
     - 查阅 `docs/skills.md`：未设定类似 Trae 的硬性 1024 字符限制；
     - 限制体现在整体预算上：规则单文件硬上限为 24KB（24,000 bytes），全局规则总预算为 20,000 tokens（`defaultRulesBudget`）。Skills 遵循渐进披露（Progressive Disclosure），启动时仅注入 name 和 description，使用时才读取主体。

---

### 4. 提问交互工具
- **工具名称**：`ask_question`（命名空间为 `default_api:ask_question`）。
- **工具类型**：结构化、交互式模态选择弹窗（Interactive Modal）。
- **声明证据（来自系统提示词）**：
  ```json
  "declaration:default_api:ask_question": {
    "description": "Use this tool to ask the user one or more multiple-choice questions, with the goal of: - Clarifying underspecified requirements...",
    "parameters": {
      "questions": [
        {
          "question": "string",
          "options": ["string"],
          "is_multi_select": "boolean"
        }
      ]
    }
  }
  ```
- **回退机制**：当环境不支持 UI 交互时，模型回退为编号纯文本提问。

---

### 5. 生效时机（当前会话 vs 新会话）
- **实测证据**：
  - 在当前正在运行的会话中创建 `test-project` 及规则文件后，当前会话的系统提示词与可用技能并未动态刷新；
  - 启动新的独立子进程（`agy -p`）后，新会话立刻完整加载了新规则与 `probe-flat`。
- **结论**：**新会话才能看到**（New session required）。规则与技能的扫描注入是在会话初始化阶段完成的。

---

## 二、Sopify Antigravity Baseline 接入方案建议

基于上述实测事实，对 T7 的工程实现给出明确结论：

1. **Instruction Surface 选型**：
   - 选用 **`header_embedded`** 最合适。
   - 理由：Antigravity 原生支持工作区规则文件与全局规则，且支持多文件 skills 体系；不需要像 Copilot 那样退化为单文件全内联（`single_file`），也无需 Cursor 特有的 `.mdc` 插件规则（`user_plugin`）。
2. **安装路径与受管块写入目标**：
   - **项目级（Workspace Scope）**：
     - 规则文件目标：项目根目录下的 **`AGENTS.md`**（因实测证明 `AGENTS.md` 加载顺序排在 `GEMINI.md` 之前，通用性最好）；
     - 受管块：在 `AGENTS.md` 末尾通过 `upsert_managed_instruction_block` 追加受管块；
     - Skills 目标：`.agents/skills/`。
   - **全局级（Global Home Scope，对应 `--target antigravity`）**：
     - 规则目标：`~/.gemini/config/AGENTS.md`；
     - Skills 目标：`~/.gemini/config/skills/`。
3. **Skills 是否需要扁平化**：
   - **必须扁平化！**（极其关键的结论）
   - **原因**：实测确凿证实 Antigravity CLI 仅扫描 `skills/` 下**一层子目录**。如果按照 Sopify 原有的 `skills/sopify/{analyze,design,develop,kb,templates}` 两层结构安装，宿主将完全无法发现任何一个技能！
   - **方案**：在 Antigravity 宿主适配器中，安装时将技能扁平化为：
     - `skills/sopify-analyze/SKILL.md`
     - `skills/sopify-design/SKILL.md`
     - `skills/sopify-develop/SKILL.md`
     - `skills/sopify-kb/SKILL.md`
     - `skills/sopify-templates/SKILL.md`
     或者在 `header` 中使用统一入口引导，确保技能可被一层探测命中。
4. **真实安装后必须复核的点**：
   - 全局安装在 `~/.gemini/config/AGENTS.md` 后，在任意无本地规则的项目启动 `agy`，能否稳定读取到受管块规则；
   - 扁平化后的 `sopify-*` 技能在 `agy` 的可用技能列表中是否完整就绪；
   - 触发 `Analyze` 需要澄清时，模型能否自发调用原生 `ask_question` 工具。

---

## 三、Onboarding Recipe 体验反思（Dogfooding 评价）

对照 `docs/host-onboarding.md` 执行本探针过程的真实感受：

### 3.1 顺利与清晰之处
1. **探针优先原则极大避免了架构返工**：
   若没有文档强要求的“先探针验证嵌套技能是否生效”，我们很可能会想当然地直接把 `skills/sopify/**` 拷贝进 `~/.gemini/config/skills/`，导致最终交付后才发现所有 Skill 全部静默失效。这一条价值极高。
2. **三事实模型（Installed / Host sees it / Host follows it）非常严密**：
   通过查看 `<user_rules>` 内部是否真实注入标记，确切区分了“文件写在磁盘上”与“大模型真实看到了标记”。
3. **负向安全红线清晰明确**：
   明确禁止为了探针修改宿主全局配置、代理、模型或 `~/.gemini/` 文件，保证了本地开发环境的纯洁性与安全性。

### 3.2 卡住与有摩擦之处（改进建议）
1. **缺少面向 CLI 工具的非交互探针命令范式**：
   文档写“Start a fresh session and ask the host to quote the marker”，偏向 IDE 聊天窗的使用场景。对于 CLI 工具，缺少类似 `agy -p "<prompt>"` 或 `trae -p` 的无状态非交互执行指引，新接入者需要额外去探索宿主命令行参数。建议在 Recipe 中补一句对 CLI 工具运行 `host --help` 寻找 `--print / -p` 选项的提示。
2. **多规则文件的加载顺序探测缺乏模板引导**：
   许多现代宿主同时兼容 `AGENTS.md` 和自己的专有规则（如 `GEMINI.md`）。文档仅建议比较全局和项目规则，未提示同时放置同级候选文件探测其合并/排序策略。我们是通过手工构建包含两者并要求复述 prompt 的方式才探明顺序，建议 Recipe 将这套同级多候选探针列为标准技巧。

---

## 四、安全与清理验证

在探针开始前创建了标记文件 `/private/tmp/claude-503/.../scratchpad/audit/probe-start-timestamp`。

1. **全局目录未修改验证**：
   ```bash
   find ~/.gemini/config ~/.gemini/antigravity-cli/skills -newer /private/tmp/claude-503/-Users-weixin-li-code-github-sopify/33857f52-51ff-4f1b-965d-13e7840e4c9f/scratchpad/audit/probe-start-timestamp
   ```
   **输出结果**：完全为空（0 个文件），证明 `~/.gemini/` 下绝对未新增、修改或触碰任何文件。
2. **清理临时工作区**：
   已执行 `rm -rf /private/tmp/claude-503/.../scratchpad/audit/t7-probe`，临时项目目录与测试标记文件已彻底清除。


---

## 五、第二步：全局规则路径探针（实测取证与结论）

### 5.1 探针目标与安全设计
- **探针目标**：确认 Antigravity CLI 在没有任何项目规则的干净目录中，是否会加载 `~/.gemini/` 或 `~/.gemini/config/` 下的候选全局规则文件（`~/.gemini/GEMINI.md`、`~/.gemini/AGENTS.md`、`~/.gemini/config/GEMINI.md`、`~/.gemini/config/AGENTS.md`），验证加载顺序，以及与本地项目根 `AGENTS.md` 共存时的层叠优先级。
- **安全与清理保障**：
  1. **前置状态检查**：实测前确认本机上述 4 个路径均不存在任何文件（全部返回 `No such file or directory`），保证绝不覆盖已有用户规则。
  2. **时间戳锚点**：创建时间戳文件 `/private/tmp/claude-503/-Users-weixin-li-code-github-sopify/33857f52-51ff-4f1b-965d-13e7840e4c9f/scratchpad/audit/probe2-start-timestamp`。
  3. **唯一隔离标记**：分别写入单行唯一标记，测完即刻 `rm -f`，并通过 `find -newer` 核对零残留。

### 5.2 实测过程与原始证据

#### 实验 0：干净空目录基线测试（Baseline）
- **操作**：在没有任何规则文件的干净目录 `/private/tmp/claude-503/.../scratchpad/audit/t7-probe2/empty-project` 中执行 `agy -p`：
- **输出**：`USER_RULES_EMPTY`。证明无规则文件时，系统提示词完全不注入任何隐式规则。

#### 实验 1：4 个全局候选路径同时存在测试
- **标记注入**：
  - `~/.gemini/AGENTS.md` -> `MARKER_GLOBAL_ROOT_AGENTS_102: Global rule from ~/.gemini/AGENTS.md`
  - `~/.gemini/GEMINI.md` -> `MARKER_GLOBAL_ROOT_GEMINI_101: Global rule from ~/.gemini/GEMINI.md`
  - `~/.gemini/config/AGENTS.md` -> `MARKER_GLOBAL_CONFIG_AGENTS_104: Global rule from ~/.gemini/config/AGENTS.md`
  - `~/.gemini/config/GEMINI.md` -> `MARKER_GLOBAL_CONFIG_GEMINI_103: Global rule from ~/.gemini/config/GEMINI.md`
- **执行命令**：
  ```bash
  cd .../t7-probe2/empty-project && agy -p "Show the exact content and ordering of <user_rules> in your prompt. Quote every rule tag, file path, and marker exactly. If none, say USER_RULES_EMPTY."
  ```
- **实测完整输出证据**：
  ```xml
  <user_rules>
  The following are user-defined rules that you MUST ALWAYS FOLLOW WITHOUT ANY EXCEPTION. These rules take precedence over any following instructions.
  Review them carefully and always take them into account when you generate responses and code:
  <RULE[user_global]>
  MARKER_GLOBAL_ROOT_AGENTS_102: Global rule from ~/.gemini/AGENTS.md

  </RULE[user_global]>
  <RULE[user_global]>
  MARKER_GLOBAL_ROOT_GEMINI_101: Global rule from ~/.gemini/GEMINI.md

  </RULE[user_global]>
  <RULE[user_global]>
  MARKER_GLOBAL_CONFIG_AGENTS_104: Global rule from ~/.gemini/config/AGENTS.md

  </RULE[user_global]>
  <RULE[user_global]>
  MARKER_GLOBAL_CONFIG_GEMINI_103: Global rule from ~/.gemini/config/GEMINI.md

  </RULE[user_global]>
  </user_rules>
  ```

#### 实验 2：全局规则与本地项目规则共存测试
- **操作**：在保留 4 个全局文件的同时，在测试项目根目录下新建 `AGENTS.md`，注入标记：
  `MARKER_LOCAL_PROJECT_AGENTS_201: Local rule from project AGENTS.md`
- **执行命令**：
  ```bash
  cd .../t7-probe2/empty-project && agy -p "Show the exact content and ordering of <user_rules> in your prompt. Quote every rule tag, file path, and marker exactly."
  ```
- **实测完整输出证据**：
  ```xml
  <user_rules>
  The following are user-defined rules that you MUST ALWAYS FOLLOW WITHOUT ANY EXCEPTION. These rules take precedence over any following instructions.
  Review them carefully and always take them into account when you generate responses and code:
  <RULE[user_global]>
  MARKER_GLOBAL_ROOT_AGENTS_102: Global rule from ~/.gemini/AGENTS.md

  </RULE[user_global]>
  <RULE[user_global]>
  MARKER_GLOBAL_ROOT_GEMINI_101: Global rule from ~/.gemini/GEMINI.md

  </RULE[user_global]>
  <RULE[user_global]>
  MARKER_GLOBAL_CONFIG_AGENTS_104: Global rule from ~/.gemini/config/AGENTS.md

  </RULE[user_global]>
  <RULE[user_global]>
  MARKER_GLOBAL_CONFIG_GEMINI_103: Global rule from ~/.gemini/config/GEMINI.md

  </RULE[user_global]>
  <RULE[/private/tmp/claude-503/-Users-weixin-li-code-github-sopify/33857f52-51ff-4f1b-965d-13e7840e4c9f/scratchpad/audit/t7-probe2/empty-project/AGENTS.md]>
  MARKER_LOCAL_PROJECT_AGENTS_201: Local rule from project AGENTS.md

  </RULE[/private/tmp/claude-503/-Users-weixin-li-code-github-sopify/33857f52-51ff-4f1b-965d-13e7840e4c9f/scratchpad/audit/t7-probe2/empty-project/AGENTS.md]>
  </user_rules>
  ```

### 5.3 核心发现与加载链规则

1. **4 个全局候选路径均被支持**：
   - 之前在第一步文档查验时，文档仅显式提到了 `~/.gemini/config/`；但黑盒实测证明，Antigravity CLI **同时扫描并加载**了根级 `~/.gemini/` 与子级 `~/.gemini/config/` 下的 `AGENTS.md` 和 `GEMINI.md`。
   - 所有的全局规则均被统一封装在 `<RULE[user_global]>` 标签内。
2. **全局规则的加载优先级与严格顺序**：
   从实测结果中可清晰提炼出 Antigravity CLI 的全局扫描顺序：
   $$\text{优先级 1: } \sim/.gemini/AGENTS.md \longrightarrow \text{优先级 2: } \sim/.gemini/GEMINI.md \longrightarrow \text{优先级 3: } \sim/.gemini/config/AGENTS.md \longrightarrow \text{优先级 4: } \sim/.gemini/config/GEMINI.md$$
   规律特征：
   - **路径层级**：`~/.gemini/`（Home Root）先于 `~/.gemini/config/`（Config Subdir）；
   - **规范命名**：在同一目录下，跨工具通用标准 `AGENTS.md` 始终先于宿主专有 `GEMINI.md`。
3. **全局规则 vs 项目规则的先后关系**：
   - **全局规则排在最前面，项目规则紧随其后**（先 `user_global`，后项目规则路径）；
   - 在提示词中，放在前面的规则先被大模型读入，但 prompt 说明“These rules take precedence over any following instructions”；项目级规则排在全局之后，形成从通用到底层项目特化的自然级联。

### 5.4 Sopify Antigravity 全局安装落点建议

结合本次实测与项目设计架构，针对 Sopify 全局安装（`--target antigravity` / `--scope global`）给出明确裁定：

1. **全局 Managed Block 目标文件**：
   - **首选推荐**：**`~/.gemini/config/AGENTS.md`**。
   - **推荐理由**：
     - Antigravity 官方自定义生态（Skills、配置等）均严格归置在 `~/.gemini/config/`（例如 `~/.gemini/config/skills/`）；
     - 将 Sopify 的全局受管规则块置于 `~/.gemini/config/AGENTS.md`，能保持 Sopify 资源在 `~/.gemini/config/` 命名空间内的目录纯洁性与聚合性，避免污染用户的宿主根目录 `~/.gemini/`；
     - 同时它采用了通用规范名 `AGENTS.md`（而非 `GEMINI.md`），符合 Sopify 面向跨 Agent 标准的设计初衷；
     - 实测已 100% 验证其会被 Antigravity CLI 稳定识别加载。
   - **替代备选（最高优先级）**：若架构希望全局规则具备全局绝对最高顺序，亦可落入 `~/.gemini/AGENTS.md`。
2. **受管块维护机制**：
   - 遵循 Sopify 统一的标准：使用 `<!-- BEGIN SOPIFY MANAGED BLOCK -->` 与 `<!-- END SOPIFY MANAGED BLOCK -->`；
   - 安装器通过 `upsert_managed_instruction_block` 进行幂等追加与更新。
3. **全局安装完整布局汇总**：
   - 全局指令入口：`~/.gemini/config/AGENTS.md`（含受管块）
   - 全局 Skills 目录：`~/.gemini/config/skills/sopify-*/SKILL.md`（扁平化一层目录）

### 5.5 清理与环境复原证据
- **删除操作**：实测完成后立即执行 `rm -f ~/.gemini/GEMINI.md ~/.gemini/AGENTS.md ~/.gemini/config/GEMINI.md ~/.gemini/config/AGENTS.md` 并删除临时目录。
- **验证命令**：
  ```bash
  find ~/.gemini/config ~/.gemini -maxdepth 1 -type f -newer /private/tmp/claude-503/-Users-weixin-li-code-github-sopify/33857f52-51ff-4f1b-965d-13e7840e4c9f/scratchpad/audit/probe2-start-timestamp
  ```
- **验证结果**：输出完全为空（0 个文件），磁盘状态与测试前完全一致，绝对零残留。
