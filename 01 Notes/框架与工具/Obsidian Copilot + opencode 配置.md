---
title: Obsidian Copilot + opencode 配置
date: 2026-08-13
tags:
  - obsidian
  - ai
  - opencode
  - 工具配置
type: note
related: "[[03 Atlas (MOC)/首页]]"
source:
  - https://www.obsidiancopilot.com/docs/agent-mode-and-tools
  - https://github.com/logancyang/obsidian-copilot
---

# Obsidian Copilot + opencode 配置

> [!important] 核心结论
> Obsidian Copilot **4.0 起被彻底重写**：不再是一个单一内置 AI 助手，而是引入 **Agent Mode（代理模式）**，可运行**前沿 CLI 编码 agent** —— **OpenCode**、**Claude Code**、**Codex**。其中 **OpenCode 是官方推荐首选**。
>
> opencode 是**本地运行**的 CLI 编码 agent，确实需要本地安装（详见下方「安装」一节）。

## 为什么需要本地安装 opencode

Copilot 的 Agent Mode 是「代理模式」：它不在云端帮你跑代码，而是调用你**本机**的 agent 工具来读写库、执行命令。opencode 就是这样一个工具，因此必须存在于本地。

> [!info] 官方说明
> **OpenCode — recommended**。Copilot 可以**自动为你下载并管理 opencode**，也可以使用你已有的安装。
>
> —— [Agent Mode and Tools 官方文档](https://www.obsidiancopilot.com/docs/agent-mode-and-tools)

## 版本要求

| 项 | 要求 |
|----|------|
| Obsidian Copilot | **4.0+**（3.x 没有 Agent Mode） |
| Node.js | 需要（opencode 通过 npm 安装） |
| opencode | 全局安装，或由 Copilot 自动下载管理 |
| LLM Provider | 需配置 API key（Anthropic / OpenAI / DeepSeek 等） |

## 安装步骤

### 1. 检查环境

```powershell
node -v
npm -v
```

若没有 Node.js，先到 [nodejs.org](https://nodejs.org/) 安装 LTS 版本。

### 2. 安装 opencode

```powershell
npm install -g opencode-ai
```

> [!tip] 自动管理
> Copilot 也能自动帮你下载、管理 opencode，不一定要手动全局安装。二者可任选其一。

### 3. 在 Copilot 中选择 Agent

1. Obsidian 设置 → 社区插件 → 安装并启用 **Copilot**（4.0+）
2. 进入 Agent Mode（首次使用会引导你选择 agent）
3. 选择 **OpenCode**
4. Copilot 会自动识别本机 opencode，或引导你下载

### 4. 配置 LLM Provider（API key）

opencode 本身不含模型，需要配置一个模型提供商。以 DeepSeek 为例，在 opencode 配置中加入 API key 即可（不同 provider 配置方式略有差异，见官方文档）。

## 常用命令速查

```powershell
# 查看 opencode 版本
opencode --version

# 全局安装
npm install -g opencode-ai

# 更新
npm update -g opencode-ai

# 卸载
npm uninstall -g opencode-ai
```

## 参考链接

- [Agent Mode and Tools 官方文档](https://www.obsidiancopilot.com/docs/agent-mode-and-tools)
- [Copilot for Obsidian 仓库（GitHub）](https://github.com/logancyang/obsidian-copilot)
- [Copilot 4.0.0 Release](https://github.com/logancyang/obsidian-copilot/releases/tag/4.0.0)
- [Windows 环境 Agent Mode 设置指南](https://github.com/logancyang/obsidian-copilot/blob/67e06f33/docs/agent-mode-windows-setup.md)
