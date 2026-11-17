---
title: DSH 插件开发入门：从 apply 函数到可安装 bundle
date: 2026-11-10
tags:
  - dsh
  - 插件
  - cordis
  - 开发
  - 工具配置
type: note
related: "[[DSH 前端开发插件与 Skill 推荐]] · [[DSH Web 开机静默自启]]"
source:
  - local
---

# DSH 插件开发入门：从 apply 函数到可安装 bundle

> [!important] 核心结论
> 1. DSH 底层是 **Cordis 微内核**——工具、LLM 适配器、文件访问、连 agent 循环本身都是插件。插件 = **导出 `apply(ctx)` 的模块**，可带 `inject`（依赖）和 `Config`（配置）。
> 2. 写插件分三层，别混：
>    - **插件模块**：一个 `apply(ctx)`，是代码的最小单位；
>    - **组合包 bundle**：npm 包里带 `dsh.bundle` → `cordis.patch.yml`，回答"这个包往组合里加什么"；
>    - **profile**：`$DSH_HOME/profiles/<name>`，用户组装的组合，回答"哪些 bundle 按什么顺序叠"。
> 3. 加能力先查「功能→机制映射」（见 §5）：加工具是 `ctx.tools.register(defineTool(...))`，加策略是 `tools/pre-execute` 钩子，加 UI 是 `dsh.client` 双面插件，加模型是 `registerAdapter`。
> 4. **本机最稳的调试路径不是 `dsh plugin` CLI**（全局 CLI 还停在 0.1.1-rc.2，应用已是 2.0.22-next），而是把插件代码落进 profile 目录 + 改 profile 的 `cordis.patch.yml`，HMR 会自动重组合。

## 一、心智模型：一切皆插件

Cordis 提供四样东西，写插件只需要记住这四样：

| 概念 | 一句话 | 在代码里的样子 |
|---|---|---|
| **Context**（`ctx`） | 插件拿到的句柄，能力都挂在上面 | `apply(ctx)` 的参数 |
| **Fiber** | 每个插件的生命周期作用域 | 框架托管，你只写 `apply` |
| **Service** | 挂在 `ctx` 上的能力（`ctx.tools`、`ctx.llm`…） | `inject: ['tools']` 声明依赖 |
| **Event** | 插件间通信，含可短路的 waterfall | `ctx.on('tools/pre-execute', …)` |

插件有三种形态，**函数形式够用**，需要对外提供服务时用类形式：

```ts
// ① 函数形式（最常用）
export const name = 'my-plugin'
export function apply(ctx: Context) { /* ... */ }

// ② 对象形式
export default { name: 'my-plugin', inject: ['tools'], apply(ctx) { /* ... */ } }

// ③ 类形式（要 export 一个 Service 给别人 inject 时）
export default class MyService extends Service {
  static inject = ['tools']
  constructor(ctx: Context) { super(ctx, 'myService') }
}
```

生命周期（框架管，你只需要知道会这样）：

```
PENDING → LOADING → ACTIVE
                 ↘ FAILED
ACTIVE → UNLOADING → DISPOSED
```

- `inject` 里的服务没就绪 → 插件停在 **PENDING**，就绪后自动加载；
- 依赖的服务消失（比如提供方被换掉）→ 自动卸载，恢复后重新加载；
- **卸载即清理**：`ctx.on()` / `ctx.tools.register()` / `ctx.llm.registerAdapter()` 全部自动撤销；需要手动清理的资源（连接、定时器）用 `ctx.effect(() => () => cleanup())`。

## 二、最小可运行插件

一个文件就是完整插件：

```js
// hello.mjs
export const name = 'hello-plugin'
export function apply(ctx) {
  console.log('[hello-plugin] loaded')
}
```

挂载有两种写法：

```yaml
# 写法 A：临时 overlay（源码 checkout 下跑 pnpm dsh web --patch ./my.yml）
- insert:
    - id: hello
      name: 'E:/path/to/hello.mjs'   # 绝对路径最稳

# 写法 B：直接写进 profile 的 cordis.patch.yml（本机推荐，见 §4）
```

> [!warning] 本地插件文件用 `.mjs`，不要用 `.js`
> profile 的 `package.json` **没有 `"type": "module"`**，普通 `.js` 会被当 CommonJS，`export` 直接语法报错。`.mjs` 一定按 ESM 加载。

## 三、最常用：写一个工具插件

工具的"真源"约定在 `docs/cookbook/adding-a-tool.zh.md`。最小形态：

```ts
import type { Context } from '@deepseek-ai/cordis'
import { defineTool } from '@deepseek-ai/dsh-tools'

export const name = 'greet-tool'
export const inject = ['tools']

export function apply(ctx: Context) {
  ctx.tools.register(defineTool({
    name: 'greet',
    description: 'Greet someone by name.',        // 模型看到的就是这句
    parameters: {
      name: { type: 'string', required: true, description: 'The name to greet' },
    },
    output: {
      schema: { type: 'string' },
      render: (_args, value) => [{ type: 'text', text: value }],
    },
    async execute(args) {
      return `Hello, ${args.name}!`
    },
  }))
}
```

几条必须遵守的规则（踩了会出问题）：

| 规则 | 说明 |
|---|---|
| 参数已校验 | `defineTool` 在 `execute` 前按 `parameters` 校验并推导 `args` 类型；schema 表达不了的（非空串、正数、跨字段）还得自己查 |
| 返回**规范值**，不返回内容块 | `execute` 只返回 `output.schema` 声明的值；转成给人看的内容是 `output.render` 的事 |
| 抛异常 = `isError` | 基础设施故障抛异常；业务上的"不理想但成功"写进规范值，由 render 解释 |
| 遵守 `exec.signal` | 取消时中止进行中的工作 |
| 长任务用 `run_in_background` + `ctx.jobs.start` | 别把后台工作挂在前台的 signal 上 |
| 不要内建策略 | 允许/拒绝/询问走 `tools/pre-execute`；截止时间/重试/指标用 `tools/execute` 包裹；审计用 `tools/result` |

工具在 GUI 里长什么样是**另一个关注点**：`presentCall` / `presentResult` 返回 `generic` / `terminal` / `diff` / `read` / `search` / `web` 卡片意图。内置 Web Client 不消费这套，而是在 slot `tool.call.toolview` 里由 client 插件自己渲染。

## 四、从单文件到可安装的组合包

单文件插件只能本地跑。要装进别人的 profile、或者让 `import '@deepseek-ai/dsh-tools'` 正常解析，就要打成 **bundle**：

```
hello-plugin/
├── package.json        # 声明 dsh.bundle
├── cordis.patch.yml    # 这个包贡献的配置层
└── index.js            # 构建产物（ESM）
```

```json
{
  "name": "dsh-hello-plugin",
  "version": "0.1.0",
  "type": "module",
  "main": "index.js",
  "files": ["index.js", "cordis.patch.yml"],
  "dsh": { "bundle": { "patch": "./cordis.patch.yml" } }
}
```

```yaml
# cordis.patch.yml —— 按包名引用自己，Node 才解析得到
- insert:
    - id: hello
      name: dsh-hello-plugin
```

安装与组合：

```sh
dsh plugin --profile demo add ./hello-plugin   # 初始化 profile + pnpm link + 追加 bundles 列表
dsh --profile demo --dump-config               # 先只验证层：# == dsh-hello-plugin
```

**加载顺序（后者按行覆盖前者）**：

1. profile 的 `dsh.profile.bundles`，按列表顺序（先 `@deepseek-ai/dsh-base`，再各已装 bundle）；
2. profile 自己的 `cordis.patch.yml`；
3. `$DSH_HOME/cordis.patch.yml`（跨 profile 的机器级偏好）；
4. 每个 `--patch <path>` overlay，按 argv 顺序。

两个推论：

- 你的 patch 可以按 `id` 覆盖前面的行，但**必须重述该行需要的每个键**——patch 替换整段 `config`，不做深合并；
- 用户可以不改你的包就覆盖你的行，所以默认值要给"用户大概率会留着"的，其余交给 `Config` schema。

## 五、功能 → 机制映射（选错扩展点是最常见的返工）

| 想加的东西 | 扩展点 |
|---|---|
| 模型能调用的工具 | `ctx.tools.register()` |
| 工具的策略 / 审计 / 指标 | `tools/pre-execute`、`ctx.tools.guard()`、`tools/execute`、`tools/post-execute`、`tools/result` |
| 系统提示词片段 | `ctx.systemPrompt.section()` |
| 跨插件能力 | 写 Service（类形式）+ `inject` |
| 事件钩子 | `ctx.on('agent/created' \| 'agent/pre-step' \| 'agent/request' \| 'agent/turn-stopping' …)` |
| 给 GUI 加界面 | `dsh.client` 双面插件 + `ctx.slots.register()` |
| 新模型提供方 | `ctx.llm.registerAdapter()` |
| MCP 服务器 | 每个服务器一个插件：发现工具 → `ctx.tools.register()` |
| 定时任务 | 插件注册调度工具；到点 `followup()` / `inject()` |
| 打包成产品入口（Web/ACP/SDK/headless） | 该入口目录下的 `cordis.patch.yml` |

**UI 插件成本最高**，值得单独了解：一个包在 package.json 里声明 `dsh.client`（`platform: 'web'`、可选 `inject`、可选 `immediately`），并 `exports["./client"]` 导出构建好的浏览器 bundle。宿主侧扫描 Loader 里所有声明了 `dsh.client` 的包，组合出 `window.__DSH_BOOT__` 入口图，在 `/plugins/...` 下提供 combo 脚本。浏览器侧写 `ctx.slots.register(...)`，props 全部是框架派生的五份 share（runtime / slots / factories / store / inject），**组件永远看不到 `ctx`**。

## 六、本机实操（2026-11-10 环境）

| 项 | 值 |
|---|---|
| 应用 | DSH NEXT **2.0.22-next**（portable） |
| DSH_HOME | `C:\Users\guan\.dsh` |
| profile | `desktop`（19 个 bundle，含 dsh-base、dsh-web-app、agent-team、ralph、qqbot…） |
| Web GUI | `http://127.0.0.1:9291` |
| 全局 CLI | `dsh` = **0.1.1-rc.2**（比应用旧一大截，**别用它装插件**） |
| 内置插件管理器 | `@deepseek-ai/dsh-plugin-manager`（GUI 侧边栏「插件」页） |
| HMR | base 里 `root: []`——**默认只监听配置，不监听插件源码** |
| 可参考的成品 | `…\profiles\desktop\node_modules\@linxin666\dsh-ssh\src\`（带完整 TS 源码的第三方双面插件） |

### 路径 A：快速验证一个插件（改 profile patch）

1. 把插件文件放进 profile 目录，例如 `C:\Users\guan\.dsh\profiles\desktop\local-plugins\hello.mjs`（用 `.mjs`）；
2. 在 `C:\Users\guan\.dsh\profiles\desktop\cordis.patch.yml` 末尾加：

```yaml
- insert:
    - id: hello
      name: './local-plugins/hello.mjs'
```

3. HMR 默认监听这份配置，保存后自动重组合；不生效就重启一次应用。

> [!warning] 这条路径的代价
> 纯本地文件插件**不一定能 `import '@deepseek-ai/dsh-tools'`**：profile 的 `node_modules\@deepseek-ai` 下只有 `cosmokit`、`schemastery` 两个 peer。本机 `NODE_PATH` 指向 `D:\node\node_global`（旧版 CLI 的包），能解析到但**版本是 0.1.x**，API 可能与 2.0.22 漂移。所以路径 A 只适合 hello / 事件监听 / 摸底；要写 `defineTool`，走路径 B。

### 路径 B：正经写一个 bundle 并装进 profile

1. 在独立目录建包（§4 的骨架），用 `tsdown`/`tsc` 构建出 `lib/index.js`（`type: module`）；
2. 装进 profile，三选一：
   - GUI「插件」页安装（推荐，避开旧 CLI）；
   - 把包目录 junction 到 `C:\Users\guan\.dsh\profiles\desktop\node_modules\<包名>`，再在 profile patch 里 `- insert:` 一行包名——dsh-ssh 就是这么挂的；
   - `pnpm pack` 出 tarball，用插件的本地安装入口装。

3. 验证：`dsh --profile desktop --dump-config` 看叠加层（仍然受旧 CLI 限制），或者直接看应用日志里的 `[hello-plugin] loaded`。

### 让改代码自动生效

HMR 默认不监听源码。要监听就在 profile patch 覆盖 `hmr` 行（注意整行覆盖）：

```yaml
- id: hmr
  disabled: false
  config:
    root: ["."]          # 相对 profile 目录
```

## 七、坑清单

> [!danger] 这些坑踩一次就够了
> - **版本错配**：全局 `dsh` CLI 0.1.1-rc.2 ≠ 应用 2.0.22-next。`dsh plugin` 的组合语义可能与应用不一致，装插件优先 GUI。
> - **`- insert:` vs 裸 `- id:`**：裸 `- id:` 是**覆盖已有行**，新增插件必须写在 `- insert:` 下，否则报"找不到该行"或不生效。
> - **config 不深合并**：patch 替换目标行的整段 `config`，改一个键要把整行重写全。
> - **`.js` vs `.mjs`**：profile 没有 `type: module`，本地插件用 `.js` 会因 ESM 语法报错。
> - **插件在宿主进程里跑，不受工作区沙箱限制**：装第三方包等于让它以你的用户权限执行代码，只对源码可信的包授权，git 安装要锁 commit。
> - **git 安装没有构建**：git 依赖不跑 `build`/`prepare`，TypeScript 包到手没有 `lib/` 会加载失败；pnpm ≥10 还要在 profile 的 `pnpm-workspace.yaml` 写 `allowBuilds`。
> - **别从 `E:\deepseekHarness\deepseek-harness-master` 跑 `pnpm dsh web`**：从源码起服务会和正在跑的 GUI 抢端口/单实例锁（见 [[DSH Web 开机静默自启]]）。

## 八、参考位置

| 内容 | 路径 |
|---|---|
| 第一个插件 / 工具 / 配置 / 打包 | `deepseek-harness\docs\user\develop\basic\{index,tool,config,publish}.zh.md` |
| 插件生命周期、事件、服务 | `deepseek-harness\docs\user\develop\framework\{index,events,service}.zh.md` |
| 扩展形态实操手册 + 功能→机制映射 | `deepseek-harness\docs\cookbook\extension-cookbook.zh.md` |
| 工具约定真源 | `deepseek-harness\docs\cookbook\adding-a-tool.zh.md` |
| UI / 客户端插件 | `deepseek-harness\docs\subsystems\client-modules.zh.md`、`web-client.zh.md`、`packages\client\AGENTS.md` |
| 底层框架教程（7 章，无需 API key） | `deepseek-harness\docs\cordis-tutorial\` |
| 组合层实例 | `packages\bundle\{base,web-app}\cordis.patch.yml`、`packages\experimental\schedule-bundle\` |
| 带源码的第三方样例 | `…\profiles\desktop\node_modules\@linxin666\dsh-ssh\` |

## 相关

- [[DSH 前端开发插件与 Skill 推荐]] —— 装什么插件 / skill，而不是怎么写
- [[DSH Web 开机静默自启]] —— 本机 DSH 运行方式与端口
