---
title: S1 手写 HTTP 服务器
type: stage
week: W2
status: pending
tags:
  - Node.js
  - HTTP
  - 学习计划
---

# S1 · 手写 HTTP 服务器（1 周）

> 目标：**不装 Express，用 `node:http` 从零实现一个能用的服务器。**
> 这一周的意义只有一个：以后你用框架时，知道框架替你做了什么。跳过这周的人，后面永远在"框架魔法"里打转。

## 实战需求

写一个 `mini-server`，支持：

1. **静态文件服务**：把 `./public` 目录通过 HTTP 暴露，正确处理 MIME 类型、`index.html` 默认页、404
2. **JSON API**：`GET /api/time` 返回当前时间；`POST /api/echo` 回显请求体；`GET /api/users/:id` 路由参数
3. **手写路由表**：不用正则库，支持 `GET /api/users/:id` 这种动态段，能匹配、能提取参数
4. **中间件管道**：实现自己的 `use(fn)`，让日志、鉴权、错误处理可以像 Express 一样串联
5. **正确的 HTTP 语义**：状态码（200/201/204/400/404/405/500）、`Content-Type`、`Content-Length`、CORS 头
6. **请求日志**：方法、路径、状态码、耗时

最终产出：一个 `server.ts` + 一份"Express 帮我做了什么"的对照表。

## 知识点与前端对照

| 知识点 | 前端视角 | 后端视角（本周要掌握） |
| --- | --- | --- |
| HTTP 报文 | 只看见 fetch 的入参出参 | 请求行/头/体；响应头决定浏览器行为 |
| 状态码 | 404 就是没找到 | 语义契约：201 创建、204 无体、401 vs 403、405 方法不允许 |
| MIME | 浏览器自己认 | 你要自己查扩展名返回 `Content-Type`，错一个字符图片就不显示 |
| 路由 | 前端路由（history/hash） | 服务端路由：方法 + 路径模式 → 处理器 |
| 中间件 | axios 拦截器 | 请求在管道中流动，`next()` 决定是否继续 |
| 请求体 | JSON 自带 | `req` 是流：要自己收集 chunk、拼 buffer、按 `Content-Length` 判断、JSON.parse |
| CORS | 报错就找后端加头 | 预检请求（OPTIONS）、简单请求与复杂请求、`Access-Control-Allow-Origin` 不能乱给 `*` |
| 连接 | 无所谓 | keep-alive、超时、`server.close()` 优雅关闭 |

## 任务清单（按天）

- [ ] D1 最小服务器：`http.createServer` 返回 "hello"，理解 `req`/`res` 是什么；用 `curl -v` 看原始报文
- [ ] D2 路由表：实现 `addRoute(method, pattern, handler)`，支持 `:id`，手写 `matchPath` + 测试
- [ ] D3 请求体与响应封装：`readJson(req)`（处理流、限制大小、非法 JSON 返回 400）、`sendJson(res, code, data)`
- [ ] D4 静态文件：`fs.createReadStream` 管道给 `res`，MIME 表、防目录穿越（`../`）、304 缓存（可选加分）
- [ ] D5 中间件管道：实现 `use()` 与 `next()`，串联 `logger → cors → router → errorHandler`
- [ ] D6 CORS 与错误处理：手写 OPTIONS 预检响应；统一错误结构 `{ code, message, traceId }`；用真实浏览器跨域验证
- [ ] D7 收尾与对照表：写"Express 帮我做了什么"（至少 8 条）+ 用 `ab` 或 `autocannon` 打一次 QPS 留档

## 验收标准

- [ ] 浏览器直接访问 `http://localhost:3000/index.html` 能渲染页面，CSS/JS/图片都正常
- [ ] `curl -X OPTIONS -H "Origin: http://localhost:5173" -v` 返回正确的预检响应
- [ ] `POST /api/echo` 传非法 JSON 返回 400 而不是崩进程
- [ ] 访问 `/../../etc/passwd`（URL 编码变体）被拒绝
- [ ] 未捕获的 handler 异常不会杀死进程，返回 500 且有日志
- [ ] 能画出一次请求从 TCP 到响应的完整流程图（含中间件顺序）
- [ ] 对照表里能指出：哪些是 Express 帮你做的，哪些是 HTTP 协议本身要求的

## 常见坑

1. **忘记 `res.end()`** —— 请求永远挂起，浏览器一直转圈，这是本周最经典的坑。
2. **`Content-Length` 写错** —— 中文按 Buffer 字节算，不是字符串长度（`Buffer.byteLength`）。
3. **响应头必须在写 body 之前设置** —— 先 `write` 再 `setHeader` 会抛 `ERR_HTTP_HEADERS_SENT`。
4. **路由顺序**：`/api/users/me` 会被 `/api/users/:id` 抢先匹配，真实框架里有优先级规则。
5. **async handler 抛错**：在 `node:http` 里 promise rejection 不会被自动捕获，要 `.catch(next)`。
6. **CORS 的 `*` 与 `credentials` 不能共存**，前端带 cookie 时后端必须回具体 Origin。

## AI 协作提示词

**让 AI 当"协议检察官"：**
```text
这是我用 node:http 手写的服务器（贴代码）。
请扮演 HTTP 协议检察官：逐条指出我违反 RFC 的地方（状态码、头字段、缓存、安全），
按严重程度排序，每条给"会出什么线上问题"，不要重写代码。
```

**对比学习：**
```text
我用 node:http 实现了路由、中间件、静态文件、CORS（贴我的实现思路）。
请对比 Express 5 的实现方式，只用表格列出差异（我的做法 / Express 的做法 / 差异带来的后果），
不要给 Express 的完整代码。
```

**故障注入：**
```text
假设我的服务器上线后出现这三种现象：① 部分请求永远不返回 ② 高并发下内存持续上涨 ③ 图片偶发损坏。
基于我这份代码（贴代码），分别给出最可能的原因和验证方法（给命令）。
```

## 复盘（自己写）

### "Express 帮我做了什么" —— 我的 8 条
1.
2.
3.

### 本周踩的坑
-

### 我还不确定的 HTTP 细节
-
