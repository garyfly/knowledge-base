---
title: OpenCode 内置免费模型对比
date: 2026-08-13
tags:
  - opencode
  - ai
  - 模型对比
  - 免费模型
type: note
related: "[[Obsidian Copilot + opencode 配置]]"
source:
  - https://opencode.ai/docs/zen/
  - https://opencode.ai/go
  - https://kilo.ai/landing/free-models
  - https://openrouter.ai/stealth/ox-alpha
---

# OpenCode 内置免费模型对比

> [!important] 一句话结论
> **编码能力最强：`Ox Alpha Free`**（但限时免费、来历未认领）。
> **最稳妥日常：`Hy3 Free`**（开源、不偏科、不会突然消失）。

## 对比表

| 模型                         | 出品方         | 类型      | 上下文       | 特点                                   |
| -------------------------- | ----------- | ------- | --------- | ------------------------------------ |
| **Ox Alpha**               | 匿名（疑智谱 GLM） | 推理      | **100 万** | **编码/agentic 最强**，多模态，唯一「Unlimited」档 |
| **Nemotron 3.5 Lightning** | NVIDIA      | **快模型** | 长         | 主打低延迟、快速响应                           |
| **Muse Spark 1.2**         | Meta        | 多模态推理   | 长         | 视觉/图表推理强，但需配 Muse Code 才发挥编码         |
| **Hy3**                    | 腾讯混元        | 通用+推理   | **256K**  | **开源、代码/长文/Agent 三向不偏科、最稳**          |
| **Nemotron 3 Ultra**       | NVIDIA      | 推理+代理   | 1M 量级     | 英伟达最强开源，适合长 agentic 任务               |
| **MiMo V2.5**              | 小米          | 推理/通用旗舰 | 长         | agentic + 多模态/语音强                    |
| **Big Pickle**             | ❓未确认        | ❓       | ❓         | **查证不到权威信息，别当主力**                    |

## 推荐

### 🥇 首选：Ox Alpha Free
- 理由：编码/agentic 能力公认最强（DeepSWE 跑分碾压），唯一「无限制」档，百万上下文+多模态，最适合高难编码任务。
- ⚠️ 三个坑：
  - **限时免费**（约一周），随时可能下线或转收费
  - **来历未认领**（匿名模型），存在偶发拒答/身份泄露
  - 只适合临时/探索性项目，**别做生产依赖**

### 🥈 稳妥日常：Hy3 Free
- 理由：腾讯混元开源、256K 上下文、约 295B MoE，代码/长文/Agent 三方面都不偏科，最稳、可自托管、不会突然消失。

### 建议组合用法
> 日常 agentic 编码用 **Ox Alpha**（上限最高）→ 不稳定/被限流时切 **Hy3** 兜底 → 长上下文纯推理用 **Nemotron 3 Ultra** / **MiMo V2.5**。

## 各模型一句话定位

- **Ox Alpha**：匿名推理模型，编码最强也最「神秘」。
- **Nemotron 3.5 Lightning**：英伟达「快思考」版，低延迟，适合轻量频繁编码。
- **Muse Spark 1.2**：Meta 多模态推理，视觉/图表强，编码需配 Muse Code。
- **Hy3**：腾讯混元，通用+推理混合，代码/长文/Agent 全才。
- **Nemotron 3 Ultra**：英伟达最强开源，代理式长任务、多模态。
- **MiMo V2.5**：小米旗舰，agentic 工作负载、多模态+语音。
- **Big Pickle**：无法查证，社区别名/占位可能性大，勿依赖。

## ⚠️ 必须知道的坑

1. **Ox Alpha 限时免费 + 神秘身份**：官方未认领来源（疑智谱），有敏感拒答/身份泄露问题，生产环境谨慎。
2. **「Unlimited」≠ 真正无限**：Zen 免费层 token 预算和并发通常仍有限制，被限流要切模型。
3. **免费模型普遍不稳定**：促销/轮换性质，延迟、可用性、上下文截断随负载波动。
4. **Big Pickle 无法查证**：无权威信息，别当主力。
5. **Muse Spark 单独用可能不达预期**：需配 Muse Code 才发挥编码能力。

## 相关说明

- 这组免费模型属于 **OpenCode Zen 免费层**（官方针对编程代理测试过的精选模型），构成会**动态轮换**。
- OpenCode 还有 **Go** 入口（低成本编码模型），Ox Alpha 限时也在 Go 上架。

## 参考链接

- [OpenCode Zen 官方文档](https://opencode.ai/docs/zen/)
- [OpenCode Go](https://opencode.ai/go)
- [Ox Alpha OpenRouter 入口](https://openrouter.ai/stealth/ox-alpha)
- [Ox Alpha 指南（Developers Digest）](https://www.developersdigest.tech/blog/ox-alpha-opencode-guide)
- [Kilo 编码模型排行榜](https://kilo.ai/leaderboard)
- [腾讯混元 Hy3 官方](https://hy.tencent.com/research/hy3)
- [小米 MiMo](https://mimo.xiaomi.com/)
