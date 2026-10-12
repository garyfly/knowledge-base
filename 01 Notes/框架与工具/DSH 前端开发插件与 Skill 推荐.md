---
title: DSH 前端开发插件与 Skill 推荐
date: 2026-10-12
tags:
  - dsh
  - 前端
  - 插件
  - skill
  - 工具配置
type: note
related: "[[DSH Web 开机静默自启]]"
source:
  - local
---

# DSH 前端开发插件与 Skill 推荐

> [!important] 核心结论
> 用 DSH 做前端开发，收益最大的三件事按顺序是：
> 1. **打开 LSP 行**（`dsh-lsp` + `dsh-lsp-stdio` + `dsh-tool-lsp`）——官方已随应用打包，零下载成本，只是默认没开；
> 2. **接 MCP 与浏览器验证**（`dsh-mcp-client`、`dsh-browser-use` + playwright/chrome-devtools provider）——让"改完 UI 能自己截图、看 console"闭环；
> 3. **自建项目级 Skill**（`<repo>/.agents/skills/*/SKILL.md`）——把团队约定、验收清单固化下来，这才是长期杠杆。
>
> 第三方 npm 生态很大（`keywords:dsh-plugin` 有 **8103** 个包），但大多与前端无关，别贪多。

## 环境事实（本机实测，2026-10-12）

| 项 | 值 |
|----|----|
| 应用 | DeepSeek Harness Desktop **0.2.0-rc.2**，profile `desktop` |
| DSH_HOME | `C:\Users\guan\.dsh` |
| profile 目录 | `C:\Users\guan\.dsh\profiles\desktop` |
| 已启用 bundle | dsh-base、dsh-web-app、agent-team、auto-review、schedule、voice-input、dsh-remote-plugin、@vectorize-io/hindsight |
| 全局 CLI | `dsh` = **0.1.1-rc.2**（比应用旧）→ 装插件优先走 GUI，CLI 易踩版本语义差异 |
| 工作区 | `E:\deepseekHarness\我的知识库` |
| 本机 Skill 根 | `<repo>/.agents/skills`（已有 obsidian-*、copilot-*、json-canvas 等） |

官方 0.2.0-rc.2 共 **316 个包**；其中 LSP / MCP / 浏览器 / 终端 / office / skill 这些插件**已打包在 `app.asar` 内**，不需要重新下载，只需在组合里把对应的行打开（我按包名字符串在 asar 里逐个确认过）。

> [!warning] 两个容易踩的坑
> - **全局 CLI 落后**：`dsh plugin --profile desktop ...` 走的是 0.1.1-rc.2，和应用的 0.2.0-rc.2 组合语义可能不一致。能用 GUI 侧边栏「插件」页就用 GUI。
> - **插件在宿主进程里跑，不受工作区沙箱限制**（官方 plugin-manager 文档原话）。装第三方包 = 让它以你的用户权限执行代码，只看 npm 下载量不够，尽量选有仓库、有更新记录的。

## 一、官方内置：改配置即可，零安装

| 能力 | 组合行 | 对前端的具体价值 |
|---|---|---|
| **代码导航** | `dsh-lsp` + `dsh-lsp-stdio` + `dsh-tool-lsp` | 定义/引用/实现/hover，基于真实 TS 项目语义而非文本搜索 |
| **LSP 动作面** | 第三方 `dsh-lsp-actions` | diagnostics、format、completion、code action、符号、rename |
| MCP 客户端 | `dsh-mcp-client`（`dsh-mcp-resources` 已随附） | 接 Context7 / Figma / Chrome DevTools / GitHub 等 MCP 服务 |
| 浏览器验证 | `dsh-browser-use` + `dsh-experimental-browser-use-playwright-mcp`（备选 `-chrome-devtools-mcp`、`-stagehand-native`） | 打开 `localhost:5173`、截图、读 console、点交互 |
| 常驻终端 | `dsh-terminal-bash` + `dsh-tool-terminal`（`dsh-tool-jobs` 已在预设内） | dev server 常驻，watch 输出不丢 |
| 复用 Claude Code hooks | `dsh-hooks-claude-code` / `dsh-hooks-codex` | 直接跑已有的 eslint / prettier / tsc hook，不用重写 |
| 侧边栏预览 | `dsh-client-ui-sidebar-browser`、`-documentpreview` | desktop profile 下**已开启**，可直接开本地页面 |
| 交付证据 | `dsh-tool-present`、`dsh-tool-ask-user` | 截图/HTML/文件直接给人看 |
| 跨模型交叉评审 | `dsh-subagent-claude-code` / `-codex`、`dsh-workflow` | UI 改动交给另一个模型 review |
| 会话全文检索 | `dsh-session-query-sqlite`（把 `openAt` 改 `first-search` + 持久 `path`） | 默认 `never`，长项目里搜历史很有用 |
| 搜索源替换 | `dsh-web-search-exa` / `-perplexity` | 官方 DeepSeek 搜索额度/结果不满意时的替代 |

### LSP 最小可用配置

写进 profile 的 `cordis.patch.yml`（`insert`），或用 Web 的「智能体预设」编辑器加到当前预设：

```yaml
- insert:
    - id: lsp
      name: '@deepseek-ai/dsh-lsp'
    - id: lsp-stdio
      name: '@deepseek-ai/dsh-lsp-stdio'
      config:
        servers:
          typescript:
            command: typescript-language-server
            args: ['--stdio']
            extensionToLanguage:
              '.ts': typescript
              '.tsx': typescriptreact
              '.js': javascript
              '.jsx': javascriptreact
          css-html-json:
            command: vscode-langservers-extracted   # 或分别配 css/html/json server
            args: ['--stdio']
            extensionToLanguage:
              '.css': css
              '.scss': scss
              '.html': html
              '.json': json
          vue:
            command: vue-language-server
            args: ['--stdio']
            extensionToLanguage:
              '.vue': vue
    - id: tool-lsp
      name: '@deepseek-ai/dsh-tool-lsp'
```

两个前提：`dsh-lsp-stdio` 必须与 `fs`、`subprocess` **位于同一执行世界**（本 profile 中两者都在 host 层，预设可见）；语言服务器本体不自带，要自己 `npm i -g typescript-language-server` 之类准备好。

### MCP：每台服务器一条记录

```yaml
- id: mcp-context7
  name: '@deepseek-ai/dsh-mcp-client'
  config:
    serverName: context7
    transport: stdio
    command: npx
    args: ['-y', '@upstash/context7-mcp']

- id: mcp-chromedevtools
  name: '@deepseek-ai/dsh-mcp-client'
  config:
    serverName: chrome
    transport: stdio
    command: npx
    args: ['-y', 'chrome-devtools-mcp@latest']
```

字段：`transport`（`stdio` / `streamable-http`）与 `serverName` 必填；stdio 用 `command`/`args`/`env`/`cwd`，远端用 `url`/`headers`；`toolCallTimeoutMs` 默认 60s，`failOnStartupError` 默认 false。工具名形如 `mcp__context7__resolve-library-id`。

**前端值得接的 MCP**（转发版，装前确认包名/地址）：

| 服务 | 用途 |
|---|---|
| Context7 | 查库的最新文档（React/Tailwind/Vite 版本差异） |
| chrome-devtools-mcp | CDP：性能 trace、console、网络、截图 |
| @playwright/mcp | 也可用官方内置 provider 代替 |
| Figma Dev Mode MCP（本地 `127.0.0.1:3845/mcp`） | 设计稿 → 代码 |
| figma-console-mcp | design token / variables / 组件 / a11y 审计 |
| shadcn MCP | 组件 registry 检索与安装 |
| GitHub MCP | PR、issue、CI 日志 |

## 二、第三方插件：从 npm 生态里挑

> `keywords:dsh-plugin` 共 **8103** 个包，`keywords:dsh-skill` 只有 **15** 个。下面是核实过存在的、与前端相关的。

| 包 | 版本 | 作用 |
|---|---|---|
| `dshmarket` | 1.66.17 | GUI 内可视化插件市场，搜索 + 一键安装（profile 里的 `.dsh-market` 就是它留下的） |
| `@michengai/dsh-skills-manager` | 1.1.15 | 统一加载并管理本机 Agent Skills |
| `dsh-lsp-actions` | 0.5.12 | LSP 动作面：诊断/格式化/补全/code action/符号/rename——比官方 `tool-lsp` 宽 |
| `@evaldock/dsh-top100-plugin` | 1.3.14 | Top100 榜单 + 一键装插件与 Skill，用来持续发现 |
| `dsh-web-artifact-designer` | 1.0.0 | 生成自包含 HTML/SVG 设计稿（海报/落地页/组件稿） |
| `dsh-github-skills` | 0.2.1 | PR / CI / review 工作流 skill |
| `dsh-mnemon` | 0.5.28 | 分层长期记忆 |
| `@roarpeng/graphflow` | 2.2.0 | 本地优先记忆与上下文（本机已在用） |
| `dsh-free-search` | 0.8.8 | 24 引擎免费搜索 |
| `@liustack/modsearch` | 5.10.6 | 免密钥网页搜索/X 搜索/抓取 |
| `@nanmicoder/dsh-agent-teams` | 0.1.23 | 多 agent 团队面板 |
| `dsh-cost-meter` | 1.8.21 | 会话费用统计（170+ 模型价格） |
| `@linxin666/dsh-web-ui-all` | — | 之前装过的全家桶（skill-explorer、task-board、git-graph、doctor…） |

安装路径：

1. **GUI 侧边栏 →「插件」→ 安装**（推荐）：粘包名 / GitHub / tarball / 本地路径，装完勾选启用；peer 不兼容会在 pnpm 运行前直接拦下；`node-pty`、`ssh2`、`cloudflared` 这类构建脚本要显式批准（`allowBuilds`）。
2. **CLI**：`dsh plugin --profile desktop add <pkg>`（注意版本差，见上文警告）。
3. 失败的安装会回滚 `package.json` 与 `pnpm-lock.yaml`，日志留在 profile 的 `.plugin-manager/logs`。

## 三、Skill：前端开发的真正杠杆

### 3.1 放哪、谁优先

| Rank | 来源 | 根目录 |
|---|---|---|
| 100 | project-dsh | `<projectRoot>/.dsh/skills` |
| 200 | project-agents | `<projectRoot>/.agents/skills` |
| 300 | custom | 配置的 `customSkillDirs` |
| 400 | user-dsh | `~/.dsh/skills`（跳过其 `.system`） |
| 500 | user-agents | `~/.agents/skills` |
| 600 | bundled | 随包（office、badge 等） |

项目根 = 最近的含 `.git` 的祖先目录。**同层内 rank 小者胜**；跨层是最内层 scope 直接覆盖。

### 3.2 文件格式

- 目录包 `<name>/SKILL.md`，或扁平 `<name>.md`；**不支持递归 `**/SKILL.md`**。
- 名称 kebab-case：`^[a-z0-9]+(?:-[a-z0-9]+)*$`。
- frontmatter：`name`、`description`（必填，决定模型能否路由到它）、可选 `when-to-use`、`disable-model-invocation`、`user-invocable`（省略均为 true）、`metadata`（任意对象）。
- 正文里用相对路径引用脚本/参考资料；`resourceBase` 只在显式引用时按需读取。
- 改正文只影响后续 `skill` 工具调用；改 `name`/`description` 会触发会话目录（`<available_skills>`）刷新。

### 3.3 建议的 7 个前端 skill

| # | Skill | 触发时机 | 正文要点 |
|---|---|---|---|
| 1 | `frontend-conventions` | 任何前端代码改动 | 技术栈、目录结构、命名、import 别名、状态管理、请求层封装、禁止事项。**第一个就该写它** |
| 2 | `design-tokens` | 涉及颜色/间距/字号 | token 来源与"禁止硬编码"；附 `references/tokens.md`（颜色、间距、圆角、字号、暗色规则） |
| 3 | `component-workflow` | 新建/修改组件 | props 类型、a11y、loading/empty/error 三态、响应式断点、i18n、story |
| 4 | `ui-verify` | 任何 UI 改动完成后 | 起 dev server → 浏览器截图 → 查 console/network → 375/768/1440 × 深浅色 → 产出证据 |
| 5 | `frontend-testing` | 写测试或改测试基建 | vitest/playwright 命令、测试放置、MSW、覆盖率门槛 |
| 6 | `perf-budget` | 依赖或首屏改动 | bundle 分析、Lighthouse/预算、图片与字体策略、代码分割 |
| 7 | `release-check` | 提交/发版前 | lint → typecheck → unit → build → preview 一条链，失败即止 |

可选第 8 个：`api-contract`（OpenAPI → 客户端类型生成 + mock 同步）。

### 3.4 SKILL.md 模板

```markdown
---
name: ui-verify
description: 改完前端 UI 后必须执行的浏览器验证流程：起 dev server、截图、查 console 与网络、跨视口与深浅色核对。
when-to-use: 任何涉及组件、样式、路由或交互的改动完成后。
---

# UI 验证

## 步骤
1. 复用/启动 dev server（`pnpm dev`），端口以终端输出为准，不要假设 5173。
2. 用浏览器 provider 打开目标路由，等待 networkidle。
3. 截图 375 / 768 / 1440 三个视口，浅色 + 深色各一次。
4. 抓 console error/warning 与失败请求，逐条对照本次 diff。
5. 把截图与结论写进回复；有失败必须给复现路径。

## 反例
- 只跑 `tsc` 就宣称"UI 已改好"。
- 用生产构建掩盖 dev-only 报错。
```

## 四、落地顺序

- [ ] 1. 挂 `dsh-lsp` + `dsh-lsp-stdio` + `dsh-tool-lsp`（收益最大，约 10 分钟）
- [ ] 2. 装 `dshmarket` + `@michengai/dsh-skills-manager`（把市场与 skill 管理界面拿回来）
- [ ] 3. 加 MCP：Context7 + chrome-devtools-mcp
- [ ] 4. 写 `frontend-conventions` 与 `ui-verify` 两个 skill，其余按需
- [ ] 5. 打开会话全文检索（`session-query-sqlite` 的 `openAt: first-search` + 持久 `path`）
- [ ] 6. 需要"改完自己截图验证"时，再挂 `dsh-browser-use` + playwright provider

## 相关

- [[DSH Web 开机静默自启]]
- 官方源码清单位置：`E:\deepseekHarness\deepseek-harness-master\deepseek-harness\packages`
- 关键参考文件：`packages\bundle\web-app\cordis.patch.yml`（web 组合行）、`packages\bundle\web-app\presets\standard.patch.yml`（默认预设）、`packages\boot\app-boot\src\profile.ts`（`OPTIONAL_BUNDLES`）、`docs\subsystems\skills.zh.md`（skill 优先级）
- npm 检索：`https://registry.npmjs.org/-/v1/search?text=keywords:dsh-plugin`
