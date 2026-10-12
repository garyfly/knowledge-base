---
title: S0 Node 后端热身
type: stage
week: W1
status: pending
tags:
  - Node.js
  - 学习计划
---

# S0 · Node 后端热身（1 周）

> 📌 **每天照这份执行 → [[S0 逐日任务清单]]**（本文件是知识点与验收标准，逐日清单是可勾选的任务）
>
> 目标：把"前端视角的 JS"切换成"后端视角的 JS"。不写 API，只补地基。
> 前端的 JS 活在浏览器里（有 DOM、有 window、单次执行到页面关闭）；后端的 JS 活在进程里（没有页面、会长期运行、会有并发请求、会崩、要吃 CPU 和内存）。这一周就是补这个差。

## 实战需求

**需求 A：写一个 CLI 小工具 `nb`（node-box），能对本地文件做统计与批量操作。**

具体验收：

1. `nb count <目录>` —— 递归统计目录下 `.md` 文件数量、总字数、每个文件字数 Top10
2. `nb rename <目录> --pattern "*.md" --prefix "note-"` —— 批量重命名，且支持 `--dry-run` 只打印不执行
3. `nb watch <目录>` —— 监听目录变化，实时打印"新增/修改/删除"
4. 支持 `--json` 输出机器可读格式，支持 `--help`，出错时退出码非 0

**需求 B：手写一个"并发控制器"**，能限制同时执行的任务数（这题是后面所有后端代码的基础）：

```ts
await runWithConcurrency(tasks, 4); // 最多 4 个同时跑，返回结果数组，保持顺序
```

## 知识点与前端对照

| 知识点 | 前端你可能这么理解 | 后端真实含义 | 要能回答 |
| --- | --- | --- | --- |
| 模块系统 | import/export 就行 | ESM vs CJS、`type: module`、`exports` 字段、条件导出 | 为什么 Node 里 `.js` 有时不能直接 import？ |
| 事件循环 | 微任务宏任务面试题 | Node 有 6 个阶段（timers/poll/check/close...），`setImmediate` vs `setTimeout(0)` | libuv 的 poll 阶段会阻塞吗？ |
| 异步模型 | fetch/await | 回调 → Promise → async；**CPU 密集任务会阻塞整个进程** | 为什么后端不能在大循环里做同步计算？ |
| 缓冲区 | ArrayBuffer 陌生 | `Buffer`、流（Stream）、背压 | 上传 1GB 文件为什么不能 `readFile`？ |
| 进程与线程 | 单线程 | `process`、`child_process`、`worker_threads`、`cluster` | 什么时候用 worker，什么时候用多进程？ |
| 文件与路径 | 少用 | `node:fs/promises`、`path`、`os` | 为什么必须用 `path.join` 而不是字符串拼接？ |
| 环境与配置 | `.env` 是后端的事 | `process.env`、`--env-file`、启动参数解析 | 密钥为什么不能写进代码？ |
| 错误 | try/catch 就完事 | 未捕获异常会让进程退出；退出码约定 | 生产环境进程挂了谁来重启？ |

## 任务清单（按天）

- [ ] D1 环境与脚手架：Node 22 装好、`pnpm init`、TS + tsx + tsconfig（`strict: true`、`NodeNext`）、`node --version` 记录
- [ ] D2 模块与文件：`node:path` / `node:fs/promises` 把 `nb count` 写出来（递归用 `fs.readdir({withFileTypes:true})`）
- [ ] D3 命令行解析：自己手写 `process.argv` 解析（不要一上来用 commander），实现 `--help` 与 `--dry-run`
- [ ] D4 异步并发：实现 `runWithConcurrency`，用假任务测出"确实同时最多 4 个"；再对比 `Promise.all` 的差别
- [ ] D5 流与 Buffer：给 `nb count` 加"大文件用流读取"，打印内存占用对比（`process.memoryUsage()`）
- [ ] D6 进程与监听：`nb watch` 用 `fs.watch` 实现，观察事件重复触发问题并处理
- [ ] D7 复盘：写本周笔记，回答上表"要能回答"那一列的全部问题（不许查 AI，先自己写）

## 验收标准

- [ ] `nb count ./某目录 --json` 输出合法 JSON，`jq` 能解析
- [ ] `--dry-run` 下文件确实没被改动（用 `git status` 验证）
- [ ] `runWithConcurrency` 有测试证明并发上限，且结果顺序正确
- [ ] 能口头解释：为什么 CPU 密集任务要放 worker_threads 而不是 `await`
- [ ] 能画出：一个 Node 进程从启动到处理一个异步任务的事件循环流转图

## 常见坑

1. **tsconfig 报错一堆**：`module`/`moduleResolution` 用 `NodeNext`，`package.json` 加 `"type": "module"`，相对导入必须写 `.js` 后缀（TS 里也写 `.js`）。
2. **`fs.watch` 事件触发两次**：编辑器保存会触发 rename+change，这是正常的，需要节流合并。
3. **`Promise.all` 不是并发控制**：它只是并发等待，任务在一开始就全部启动了。
4. **退出码**：`process.exit(1)` 才是失败；报错后进程仍挂着是新手最常见的"卡住"。
5. **不要在这一周学任何框架**。这周的目标是"看懂没有框架时发生了什么"。

## AI 协作提示词

**让 AI 出题（推荐每天用一次）：**
```text
我是前端，刚开始学 Node 后端。今天学了 Node 的事件循环阶段、Buffer/Stream、child_process 和 worker_threads。
不要给我教程，直接出 5 道场景判断题（每个都带一段有 bug 或性能问题的代码），
一次问一道，我答完再给下一道，答错时先给提示不要给答案。
```

**让 AI 审查并发控制：**
```text
下面是我实现的 runWithConcurrency（贴代码）。
请只做审查，不要重写：指出 3 个可能的边界问题（空数组、任务抛错、并发数大于任务数），
并给出对应的测试用例名。不要给完整实现。
```

**术语翻译：**
```text
用"前端已经熟悉的概念"类比解释：背压（backpressure）、阻塞、worker_threads、退出码。
每个给一句类比 + 一句"在 Node 里具体指什么"。
```

## 复盘（自己写，写完再对照 AI）

### 本周踩的坑
-

### 三个我真正搞懂的概念
-

### 还模糊、下周要继续验证的问题
-
