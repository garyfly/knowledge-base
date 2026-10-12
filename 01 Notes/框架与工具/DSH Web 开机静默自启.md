---
title: DSH Web 开机静默自启
date: 2026-09-17
tags:
  - dsh
  - windows
  - 任务计划程序
  - 工具配置
type: note
related: "[[03 Atlas (MOC)/首页]]"
source:
  - local
---

# DSH Web 开机静默自启

> [!important] 核心结论
> Windows 上用「任务计划程序 + 登录触发 + `-WindowStyle Hidden`」实现 `dsh web` 开机（登录）后**后台静默**运行：不弹任何窗口，崩溃自动重启最多 3 次。
>
> **最大的坑**：`dsh web` 是**全机器单实例**——第二个实例启动时会因 task-board 插件的排他锁直接崩溃退出。所以不能无脑拉起，必须先确认端口空闲。

## 环境事实（本机实测，2026-09-17）

| 项 | 值 |
|----|----|
| 启动命令 | 全局 `dsh web`，即 `C:\Program Files\nodejs\node.exe` + `D:\node\node_global\node_modules\@deepseek-ai\dsh\lib\bin.js web` |
| dsh 版本 | `@deepseek-ai/dsh` 0.1.1-rc.2（全局 npm 安装） |
| DSH_HOME | `C:\Users\guan\.dsh` |
| Web UI | http://127.0.0.1:3080 |
| 工作区（GUI 打开的目录） | `E:\deepseekHarness\我的知识库` |
| PowerShell | **只有 5.1**，`pwsh`（PS7）**没装** → 命令一律写 `powershell.exe` |

> [!warning] 不要从 `E:\deepseekHarness\deepseek-harness-master` 跑 `pnpm dsh web`
> 该目录**没有 package.json**，且 pnpm 会提示锁文件不兼容、问你要不要把 `node_modules` 整个删掉重装（历史上真卡在这一步，见 `~\.dsh\profiles\web\restart-web.log`）。静默自启走全局 `dsh`，与仓库目录无关。

## 为什么必须先查端口：单实例锁

同时启动两个 `dsh web`，第二个会抛：

```
dsh: plugin tree failed to load: failed to apply loader entry web-ui-task-board
  (@linxin666/dsh-client-ui-task-board): task-board ledger is already owned by process <PID>
  ...
Node.js v24.19.0
```

`HostTaskLedger.acquireLock` 是排他锁（`~\dsh\profiles\web\node_modules\@linxin666\dsh-client-ui-task-board`）。**这不是 bug，是设计**，但也意味着：

- 想切回"前台窗口调试"时必须**先停后台服务**，反之亦然；
- 自动化脚本里必须有"端口已占用就跳过并记日志"的守卫，否则每次开机/重试都会多崩一个进程。

## 文件落点

| 文件 | 作用 |
|------|------|
| `C:\Users\guan\.dsh\dsh-web-serve.ps1` | 后台 worker：守卫检查 → 启动 GUI → 等待端口 → 作为父进程存活 |
| `C:\Users\guan\.dsh\dsh-web-autostart.ps1` | 安装/管理入口：`install`/`uninstall`/`status`/`run`/`stop`/`logs` |
| `C:\Users\guan\.dsh\logs\dsh-web.log` | worker 自身日志（启动、就绪、跳过、退出码） |
| `C:\Users\guan\.dsh\logs\dsh-web.out.log` / `.err.log` | `dsh web` 的 stdout / stderr |
| `C:\Users\guan\.dsh\logs\dsh-web.pid` | 当前 worker 记录的 GUI pid |
| 计划任务名 | `dsh-web-autostart`（当前用户级，**无需管理员**） |

worker 关键设计：

- `-NoProfile -NonInteractive -WindowStyle Hidden`：不弹窗、不加载 profile、不等人输入；
- 启动参数带 `--no-open`：开机不会自动弹浏览器；
- 启动前校验 node.exe / dsh bin.js / 工作区三处路径存在，缺失则写日志退出（exit 2）；
- 端口已监听 → 写 `SKIP: ... single-instance` 并 **exit 0**（不算失败，避免任务计划反复重试）；
- 启动后最多等 60 秒探测端口；子进程提前退出则记录 `ExitCode` 并 exit 1；
- 最后 `WaitForExit()` 挂住：worker 就是 GUI 的父进程，GUI 一死 worker 就退出，任务计划的 `RestartCount` 才会拉起来。

## 计划任务配置（实测值）

| 设置 | 值 | 说明 |
|------|-----|------|
| 触发器 | `AtLogOn`，当前用户 | 登录触发（非开机触发：需要用户会话与 `.credentials.yaml`） |
| 延迟 | `PT30S` | 等 30 秒，避开登录时的资源争抢 |
| 操作 | `powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File ...` | 隐藏窗口 |
| 主体 | 当前用户 / `Interactive` / `Limited` | 用户级运行，不需要管理员也不需要存密码 |
| 空闲 | `ExecutionTimeLimit = PT0S` | 永不因超时被杀 |
| 电源 | `DisallowStartIfOnBatteries = False`、`StopIfGoingOnBatteries = False` | 笔记本上也照跑、切电池不停 |
| 重启 | `RestartCount 3` / 间隔 1 分钟 | GUI 崩溃自动拉起 |
| 实例 | `IgnoreNew` | 不会叠实例（叠加会撞单实例锁） |

## 常用命令

```powershell
# 看状态：任务状态 / 端口占用 / 最近日志
powershell.exe -NoProfile -File C:\Users\guan\.dsh\dsh-web-autostart.ps1 status

# 立刻启动（端口必须空闲）
powershell.exe -NoProfile -File C:\Users\guan\.dsh\dsh-web-autostart.ps1 run

# 立刻停掉 GUI（含清理计划任务当前实例）
powershell.exe -NoProfile -File C:\Users\guan\.dsh\dsh-web-autostart.ps1 stop

# 看 worker 日志全文尾部
powershell.exe -NoProfile -File C:\Users\guan\.dsh\dsh-web-autostart.ps1 logs

# 模拟"开机自动执行"那一步
Start-ScheduledTask -TaskName 'dsh-web-autostart'

# 撤销开机自启（停任务 + 删启动文件夹 shim，保留脚本与日志）
powershell.exe -NoProfile -File C:\Users\guan\.dsh\dsh-web-autostart.ps1 uninstall

# 排查
Get-ScheduledTask -TaskName 'dsh-web-autostart' | Select-Object TaskName,State
Get-ScheduledTaskInfo -TaskName 'dsh-web-autostart' | Select-Object LastRunTime,LastTaskResult
Get-NetTCPConnection -LocalPort 3080 -State Listen
Get-Content C:\Users\guan\.dsh\logs\dsh-web.err.log -Tail 40
```

### 切换到后台服务的正确顺序

因为单实例锁，顺序不能反：

1. 在你自己那个跑着 `dsh web` 的窗口按 `Ctrl+C`（或关窗口）；
2. `Get-NetTCPConnection -LocalPort 3080 -State Listen` → **必须无输出**；
3. `Start-ScheduledTask -TaskName 'dsh-web-autostart'`；
4. 等 20~30 秒，看 `status` 或日志出现 `ready: http://127.0.0.1:3080`。

### 想临时回到"有窗口"的前台模式

```powershell
powershell.exe -NoProfile -File C:\Users\guan\.dsh\dsh-web-autostart.ps1 stop
cd E:\deepseekHarness\我的知识库
dsh web          # 前台、可见，方便看报错；调完再 Start-ScheduledTask 交回去
```

## 验证记录（2026-09-17）

```
[2026-09-17 21:51:07] starting: node "...\@deepseek-ai\dsh\lib\bin.js" web --no-open --port 3080  (cwd: E:\deepseekHarness\我的知识库)
[2026-09-17 21:51:07] launched pid 26320
[2026-09-17 21:51:10] ready: http://127.0.0.1:3080  (pid 26320)
```

- 3080 监听进程 = 26320，其父进程 = worker（powershell.exe），符合"worker 挂住 GUI"的设计；
- `Invoke-WebRequest http://127.0.0.1:3080` → **200**，页面 21560 字节；
- `dsh-web.err.log` 为空 = 无报错；
- 计划任务状态 `Ready`。

## 其他可选方案

| 方案 | 优点 | 缺点 |
|------|------|------|
| **任务计划程序**（本笔记采用） | 隐藏窗口、崩溃自动重启、可控延迟、能查询状态 | 配置项略多 |
| 启动文件夹 shim（`install -Mode StartupFolder`） | 更简单 | 无自动重启；会在启动文件夹留一个 `.cmd` |
| 注册表 `HKCU\...\Run` | 最简单 | 无自动重启、无状态查询，命令行长度有限 |

三者都**必须**用 `-WindowStyle Hidden`（否则闪黑框），且都受单实例锁约束。

## 踩坑清单

1. **参数名不能叫 `-Action`**：会和 `New-ScheduledTaskAction` 的返回值变量 `$action` 撞车（PowerShell 变量名不区分大小写），报错 `MSFT_TaskExecAction is not a valid value for the Action variable`。本脚本已改用 `-Command`。
2. **本机没有 `pwsh`**：文档里的 `pwsh -File ...` 要换成 `powershell.exe -NoProfile -File ...`（脚本内部会自动探测：优先 pwsh，否则回落 5.1）。
3. **别用旧的 `~\dsh\profiles\web\restart-web.ps1`**：它走仓库目录 + pnpm，会踩到 "modules directory will be removed and reinstalled, Proceed?"，且自带"杀掉所有 dsh web 再重启"的暴力逻辑。
4. **日志会无限增长**：worker 在超过 5MB 时自动轮转为 `dsh-web.log.old`。
5. **端口被占时 worker 是 exit 0**（视为正常跳过），别把它当失败去反复重试。

## 相关

- [[01 Notes/框架与工具/Obsidian Copilot + opencode 配置]]
