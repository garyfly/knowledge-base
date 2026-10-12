# 我的知识库 · Knowledge Base

> 一个用 [Obsidian](https://obsidian.md/) 搭建的**程序员知识库**：PARA 简化版目录 + MOC 导航，再用 Dataview 把首页做成「游戏任务栏 + 技能树进度条」。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

---

## 为什么开源

这个库原本只是我给自己留的台阶。开源出来有三个理由：

1. **目录结构和插件配置可以直接抄** —— 省掉搭库时最耗人的试错。
2. **学习路线是完整的** —— 两套从 0 到上线的实战计划（Node 后端、独立游戏到 Steam），每一步都有验收标准。
3. **互相纠正** —— 笔记里如果有过时结论或错误认知，欢迎开 Issue 打脸。

---

## 目录结构

```
我的知识库/
├── 00 Inbox/          # 随手抓进来的东西，不分类，先囤着            (3 篇)
├── 01 Notes/          # 永久笔记，按主题原子化，一条解决一个问题      (9 篇)
│   ├── 编程语言.md
│   └── 框架与工具/
├── 02 Projects/       # 当前在做的项目，按项目名命名                (28 篇)
│   ├── Nodejs 后端实战学习计划/
│   ├── 独立游戏开发到 Steam 上线/
│   └── 前端职位技术信息采集系统/
├── 03 Atlas (MOC)/    # 地图/入口页 —— 真正的「门面」所在           (2 篇)
│   ├── 首页.md
│   └── 技能树.md
├── 04 Templates/      # Templater 模板                           (3 篇)
├── 05 Archive/        # 完成、过期、不再维护的内容                    (空)
├── Daily/             # 每日任务
└── md-stats.mjs       # 自制笔记统计脚本
```

共 **47 篇笔记、约 22 万字符**。

> [!tip] 关键认知
> **文件夹只是存放位置，MOC 才是导航。** 别在目录树上雕花，把精力放在 `03 Atlas (MOC)/` 的入口页上。

---

## 三个亮点

### 1. 🎮 首页 = 游戏大厅

`03 Atlas (MOC)/首页.md` 用 Dataview 把未完成任务、逾期任务、最近新增聚合成一张仪表盘：

````markdown
```dataview
TASK
FROM "01 Notes" OR "02 Projects"
WHERE !completed
SORT file.ctime DESC
```
````

### 2. 🌳 技能树自动算进度

`技能树.md` 里直接写 `- [ ]` / `- [x]`，首页的 `dataviewjs` 块会读取该文件、按 `##` 标题分组统计勾选率，渲染成进度条：

```js
const cb = line.match(/^\s*-\s*\[([ xX])\]/)
if (cb && current) {
  skills[current].total++
  if (cb[1].toLowerCase() === "x") skills[current].done++
}
```

配 `.obsidian/snippets/game-progress.css` 出视觉效果。**每天打勾，进度条就是你的成长曲线。**

### 3. 📊 `md-stats.mjs` 笔记统计

零依赖的 Node 脚本，递归统计 `.md` 文件的数量、字符数（按 Unicode 码点，中文/emoji 各算 1）、字节数与 Top 10：

```bash
node md-stats.mjs              # 统计当前目录
node md-stats.mjs "01 Notes"   # 统计指定目录
node md-stats.mjs --json       # 输出 JSON，方便别的程序接着用
```

细节处理得比较认真：跳过符号链接（防无限递归）、去 BOM、统一 `\r\n`（防 Windows 虚增字符数）、单目录读取失败不会让整次遍历崩掉。

---

## 快速开始

```bash
git clone https://github.com/garyfly/knowledge-base.git
```

1. 用 Obsidian 打开该文件夹（**Open folder as vault**）。
2. 按下面清单安装社区插件（本仓库**不包含** `.obsidian` 目录）。
3. 把 `03 Atlas (MOC)/首页.md` 设为 Homepage 插件的启动页。
4. 在 `03 Atlas (MOC)/技能树.md` 里打勾，回首页看进度条。

### 需要的社区插件

| 插件 | 用途 | 优先级 |
|---|---|---|
| **Dataview** | 把笔记变成清单/表格/进度条，本库的「数据库引擎」 | 必需 |
| **Templater** / **QuickAdd** | 一键生成带结构的笔记 | 必需 |
| **Homepage** | 打开软件直接进「游戏大厅」首页 | 必需 |
| **Obsidian Git** | 自动 commit + 同步，知识库当代码库管 | 推荐 |
| **Obsidian Tasks** | 任务加截止日期、重复、进度 | 推荐 |
| **Excalidraw** | 画架构图、流程图、思维导图 | 可选 |
| **Calendar** / Habit Tracker | 打卡与连续记录 | 可选 |

安装入口：**设置 → 第三方插件 → 社区插件**。

---

## 笔记工作流（每天 10 分钟）

```
【抓】遇到好文章 / 报错 / 想法  →  一键抓进 00 Inbox，别分类
【处】每天或每周统一处理        →  拆成原子笔记，写一句"这解决了什么"
【链】加双链 [[...]]           →  挂到对应 MOC / 主题下
【做】能复现的 Debug           →  存成模板 / 速查表，标注踩坑
【复习】Dataview 翻出来         →  把没复习过的重新过一遍
```

三个让「知识变成资产」的习惯：

1. **每篇笔记都写 Frontmatter**（`tags`、`date`、`type`），Dataview 全靠它。
2. **Debug 记录模板化**：`问题描述 → 复现 → 根因 → 解决 → 教训`——这是程序员最值钱的知识。
3. **先搜自己的库**：遇到报错先搜库里有没有，比搜 Google 快。

---

## 🔒 安全约定

本仓库是公开的，因此**任何含真实凭据的笔记都必须留在本地**。`.gitignore` 中已硬性排除：

```gitignore
00 Inbox/字节订阅密钥.md    # 含真实 API 密钥，永不入库
.obsidian/                   # 插件打包文件，约 15MB
path-backup/                 # 本机 PATH 备份与二进制
graphflow-out/               # 图谱缓存（含 sqlite）
.graphflow-cache/
```

> [!warning] 如果你 fork 后要往里加内容
> 提交前先自查一遍。下面这条命令能扫出常见密钥格式：
>
> ```bash
> git diff --cached | grep -nE 'ark-[0-9a-f]{8}-|sk-[A-Za-z0-9]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}'
> ```
>
> 一旦密钥被推上公开仓库，即使立刻删除，也可能已被爬虫抓取并留存在 fork 中——**唯一的补救办法是去服务商后台吊销密钥**。

---

## 许可

[MIT](./LICENSE) © guanchunfei

笔记内容以「尽量准确」为目标，但不保证没有过时或错误的结论，请自行判断后再用于生产环境。
