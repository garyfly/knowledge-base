# 02 · 云订阅与 API 定价调研（2026 年 11 月）

> 目标：为"每天使用大模型、用一年"建立可复核的云端成本模型，用于和"约 1 万元买本地机器跑开源模型"对比。
>
> **查询日期：2026-11-10**（数据取自当日可访问的页面；不同页面自身标注的更新日期在各表"来源"列中注明）
> **汇率口径：1 USD ≈ 7.20 CNY**（与 GPU 比价站 rentgpu.link 当日折算口径一致；实际换汇/代充会有 1–5% 偏差）
> **一年按 365 天计**，未计税费、网络代理/代充溢价、以及各平台的"限时活动价"。

**本文件的可信度分级**（每张表都会标注）：

| 标记 | 含义 |
|---|---|
| ✅ 官网 | 厂商官方定价页/官方文档直接读到 |
| 🟡 二手 | 第三方文章/比价站转述官方价，附查询日期 |
| ⚠️ 待核实 | 只找到第三方整理或页面被 JS/导航截断，**下单前必须自己复核** |
| ❌ 未查到 | 明确没查到，不猜 |

---

## 0. 一页结论（先看这里）

| 使用强度 | 最便宜的"订阅"路线（年费） | 纯 API 年费区间（同样用量） | 订阅+API 混合（真实年费） |
|---|---|---|---|
| 轻度<br>20 轮/天，3 万输入 + 1 万输出/天 | **¥0**（Gemini 免费层 / GLM-4.7-Flash 免费）<br>付费最低：千问 App 高级 ¥200/年 | **¥4 – ¥2,300**<br>中位 ≈ ¥150（DeepSeek Flash ¥33、GPT-6 Luna ¥23、GLM-5.3-Flash ¥19） | **≈ ¥233/年**（千问 App 高级 ¥200 + DeepSeek Flash 兜底 ¥33） |
| 中度<br>100 轮/天，15 万输入 + 4 万输出/天 | 千问 App 精英 ¥568/年<br>或 豆包标准 ¥816/年 | **¥17 – ¥10,184**<br>中位 ≈ ¥700（DeepSeek Flash ¥147、GPT-6 Luna ¥102、GLM-5.3-Flash ¥85） | **≈ ¥347/年**（千问 App 高级 ¥200 + DeepSeek Flash ¥147）；用 GPT-6 Luna 纯 API 只要 ¥102 |
| 重度<br>写代码 + Agent，300 万输入 + 30 万输出/天，90% 缓存 | 国内：GLM Coding Pro（价 ⚠️）+ 兜底 ≈ ¥3,000 级<br>海外：Claude Max ¥8,640/年 | **¥737 – ¥56,371**<br>· DeepSeek Flash **¥737**（90% 缓存）/ ¥1,993（无缓存）<br>· Qwen3.8-Max ¥6,734<br>· Sonnet 5.5 / GPT-6.1 Sol ¥10,565<br>· Opus 5.5 ¥21,129<br>· GPT-6 Astra ¥56,371 | **≈ ¥4,900 – ¥12,200/年**（见 §C.5） |

**三句话印象**：
1. 轻度、中度用**国内订阅或免费层**几乎不要钱；纯 API 也只要一两百元/年。
2. 重度是分水岭：**订阅必然被限流**，真实成本由"订阅年费 + 超额 API"决定，落在 **¥4,900 – ¥12,200/年**。
3. 对照"1 万元本地机器"：本地机年化约 ¥4,400（折旧 3 年 + 电费），但只能跑 27B–70B 量化模型；**同价位的云方案能用到 Opus/Sol 级模型，且不用自己运维** —— 见 §C.6。

---

## A. 订阅类（人民币/年）

### A.1 海外订阅

| 订阅 | 美元价 | 人民币/年 | 额度与限制（关键） | 明确禁止/限制的自动化用法 | 来源 |
|---|---|---|---|---|---|
| **ChatGPT Plus** | $20/月 | **¥1,728**（$240/年） | 有 5 小时窗口。每 5 小时本地消息估算：GPT-6 Astra **5–45** 条、GPT-6.1 Sol **15–160** 条、GPT-6 Luna **350–3,000** 条。Work 与 Codex 共用额度 | 订阅**不含 API 额度**；订阅与 API 分开计费。自动化/程序化调用只能走 API 另付 | 🟡 [卡码笔记 2026-10-30 更新](https://notes.kamacoder.com/ai/chatgpt/plus-pro-compare.html)（其引用官方 learn.chatgpt.com/docs/pricing，本机抓取被 403） |
| **ChatGPT Pro 100** | $100/月 | **¥8,640** | 约 5× Plus 用量；**当前无 5 小时限制**（仍有套餐总额度，用完可等恢复或买 credits） | 同上 | 🟡 同上 |
| **ChatGPT Pro 200** | $200/月 | **¥17,280** | 恢复后的"原 20x 档"，当前额度约为 Plus 的 **10×**（不是旧 20×）；无 5 小时限制 | 同上 | 🟡 同上 |
| **ChatGPT Pro 500** | $500/月 | **¥43,200** | 专属 GPT-6 Astra Ultrafast（Ultrafast 对套餐内用量按 8× 消耗、额外 credits 按 6×）；无 5 小时限制 | 同上 | 🟡 同上 |
| **Claude Pro** | $20/月（年付 $17/月） | **¥1,728**（年付 **¥1,469**） | 5 小时会话额度 + 每周额度（全模型）；Claude.ai / Claude Code / Desktop **共用同一份额度** | 订阅**不含** API credits（Pro 不在赠送名单内）；用量超限可买 usage credits | ✅ [claude.com/pricing](https://claude.com/pricing)（2026-11-10）／✅ [帮助中心](https://support.claude.com/en/articles/11647753-how-do-usage-and-length-limits-work) |
| **Claude Max**（原 Max 5x） | $100/月 | **¥8,640** | 5 小时 = 5× Pro，每周 = 5× Pro；**含每月 $100 Claude API credits**（仅限 API / Agent SDK / Managed Agents，**不含**交互式 Claude Code）；只能月付 | credits 不能用于交互式 Claude Code；API 侧仍受速率与消费上限约束 | ✅ [claude.com/platform/api](https://claude.com/platform/api)／✅ [Max 方案](https://support.claude.com/en/articles/11049741-what-is-the-max-plan)／🟡 [apidog 2026-11-02](https://apidog.com/blog/claude-ultra-plan/) |
| **Claude Ultra**（原 Max 20x） | $200/月 | **¥17,280** | 已**验证账户无 5 小时限制**；每周额度 = **10× Pro**；Fable 另有独立周额度；**含每月 $200 API credits**；只能月付 | 同上；未验证账户仍临时保留 5 小时限制 | ✅ 同上 |
| **Gemini AI Plus** | $7.99/月 | **¥691** | 入门档 | — | 🟡 [Mashable 2026-05-19（I/O 2026）](https://mashable.com/article/google-io-2026-gemini-ultra-ai-subscription-tiers) |
| **Gemini AI Pro** | $19.99/月 | **¥1,727** | 2026 年起额度**按算力计量**（不按条数），每 5 小时刷新；撞顶后自动**降级到更轻的模型**而不是断供；可买 Antigravity / Flow 的按量 credits | 订阅不含 Gemini API 额度（API 有独立免费层，见 §B.3） | 🟡 同上 |
| **Gemini AI Ultra** | 起 $99.99/月（顶档 $200/月，原 $250 降价） | **¥8,639**（$99.99 档） | 5× Pro 额度；Gemini Spark 等独占；含 20TB 存储 + YouTube Premium 等捆绑 | 同上 | 🟡 同上（2026-11 未见更新的官方价目页，⚠️ 建议下单前复核） |
| **GitHub Copilot Pro / Pro+** | ❌ 未查到 2026-11 官方价目 | ❌ | 官方博客已确认 **转向用量计费（AI credits + 按模型计价）**；旧版 Pro $10 / Pro+ $39 的价目不再适用 | — | ❌ [github.com/pricing](https://github.com/pricing)、[features/copilot/plans](https://github.com/features/copilot/plans)、[docs plans](https://docs.github.com/en/copilot/get-started/plans) 三个页面均被导航/JS 截断，取不到正文价格；[GitHub Blog](https://github.blog/news-insights/company-news/github-copilot-is-moving-to-usage-based-billing/) 只确认计费模式变更 |
| **Cursor Pro**（legacy） | $20/月 | **¥1,728** | 旧版计划：两个**月度**池（Cursor Models 池 + Other Models 池）；超出可开 on-demand 按 API 价后付 | 第三方模型从 Other Models 池按 API list price 扣；不允许把订阅额度当 API 用 | ✅ [Legacy 计划文档](https://cursor.com/docs/account/pricing/legacy-cursor-plans)（2026-11-10） |
| **Cursor Pro+**（legacy） | $60/月 | **¥5,184** | 同上，额度更高 | 同上 | ✅ 同上 |
| **Cursor Ultra**（legacy） | $200/月 | **¥17,280** | 同上，额度最高 | 同上 | ✅ 同上 |
| **Cursor 新"X 订阅"**（新客默认） | Plus $8 / Premium $30 / Super $100 / Ultra $200 | ¥691 / ¥2,592 / ¥8,640 / ¥17,280（年付 $80/$300/$1,000/$2,000） | 单一**每周**池，Cursor 模型与 Grok 共享；**第三方模型不含在内**，Premium 以上按 API list price 从预付 credit 扣 | 第三方模型不再"含在订阅里"，等于变相按量计费 | ✅ [cursor.com/docs/models-and-pricing](https://cursor.com/docs/models-and-pricing) |

> 海外订阅的通则：**订阅 = 交互式使用；API = 另一套计费**。唯一例外是 Claude Max/Ultra 和 Team 计划带 API credits，而 credits 也明确**不能**用于交互式 Claude Code。

### A.2 国内订阅

| 订阅 | 价格 | 折人民币/年 | 额度与限制 | 是否含 API / 是否禁自动化 | 来源 |
|---|---|---|---|---|---|
| **豆包专业版 · 标准** | ¥68/月（连续包月） | **¥816** | 专家模式、办公任务模式额度 = 免费版的 **5 倍以上**；学生认证 ¥38/月 | 是 App 订阅，**不含**火山方舟 API；API 另按 §B 计费 | ✅ [澎湃新闻 2026-06-24](https://m.thepaper.cn/newsDetail_forward_33441793) |
| **豆包专业版 · 加强** | ¥200/月 | **¥2,400** | = 标准套餐的 4 倍额度 | 同上 | ✅ 同上 |
| **豆包专业版 · 高级** | ¥500/月，年付 **¥5,088** | **¥5,088**（年付）／¥6,000（月付） | = 标准套餐的 10 倍额度 | 同上 | ✅ 同上 |
| **豆包 Coding Plan 个人版 · Lite** | ¥40/月（季付 ¥120） | **¥480** | 供 Claude Code / Codex / OpenCode 等工具接入方舟模型 | 仅限指定工具；按量超额走标准 API | ✅ [火山方舟官方价格页 2026-11-05](https://ark.volcengine.com/region:cn-beijing/docs/model-pricing.md) |
| **豆包 Coding Plan 个人版 · Pro** | ¥200/月（季付 ¥600） | **¥2,400** | 同上，额度更高 | 同上 | ✅ 同上 |
| **豆包 Agent Plan 个人版** | Small ¥40 / Medium ¥200 / Large ¥500 / Max ¥1,000 每月 | ¥480 / ¥2,400 / ¥6,000 / ¥12,000 | 面向 Agent/Computer-Use 场景 | 同上 | ✅ 同上 |
| **Kimi · Go** | 年付折月 ¥39 | **¥468** | Agent 额度 = 4× speed 队列；定时任务 6 个 | API 是**另一套按量计费**（官方文档明确"不提供订阅制方案，与 Kimi 会员、Kimi Code 区分"） | 🟡 [Kimi 官方资源页 2026-10-24](https://www.kimi.com/resources/kimi-k3-1-pro-pricing) |
| **Kimi · Plus** | 年付折月 ¥79 | **¥948** | Agent 额度 2×（相对免费），含 Kimi Code | 同上 | 🟡 同上 |
| **Kimi · Pro** | 年付折月 ¥159 | **¥1,908** | Agent 额度 4×；含 K3.1 Pro Highspeed + Kimi Code | 同上 | 🟡 同上 |
| **Kimi · Max** | 年付折月 ¥559 | **¥6,708** | Agent 额度 14×；K3 超长对话（1M） | 同上 | 🟡 同上 |
| **Kimi · Ultra** | 年付折月 ¥1,119 | **¥13,428** | Agent 额度 28× | 同上 | 🟡 同上 |
| **智谱 GLM Coding Plan · Lite** | ⚠️ 价格未在官方文档给出（第三方 2026-04 整理 ¥49/月） | ⚠️ 约 ¥588（待核实） | **每 5 小时 2,000 积分 / 每周 10,000 积分** | **仅限官方指定工具**（Claude Code、Codex、OpenCode、WorkBuddy 等）；直连 API 不享套餐额度；禁止共享/中转/倒卖，违者可限流、封号 | ✅ 额度与规则见 [套餐概览](https://docs.bigmodel.cn/cn/coding-plan/overview.md)、[使用须知](https://docs.bigmodel.cn/cn/coding-plan/usage-notes.md)；⚠️ 价格 |
| **智谱 GLM Coding Plan · Pro** | ⚠️ 未查到官方价 | ⚠️ | **5 小时 12,000 / 每周 60,000 积分** | 同上 | ✅ 额度同上 |
| **智谱 GLM Coding Plan · Max** | ⚠️ 未查到官方价 | ⚠️ | **5 小时 28,000 / 每周 140,000 积分** | 同上 | ✅ 额度同上 |
| **通义千问 App · 高级** | ¥19/月，年付 ¥200 | **¥200** | 额度提升至 **2 倍** | App 订阅不含 API；API 走百炼/千问 AI 平台 | 🟡 [PChome 2026-08-11](https://article.pchome.net/news/15475.html) |
| **通义千问 App · 精英** | ¥49/月，年付 ¥568 | **¥568** | 5 倍额度 | 同上 | 🟡 同上 |
| **通义千问 App · 旗舰** | ¥128/月，年付 ¥1,499 | **¥1,499** | 20 倍额度 | 同上 | 🟡 同上 |
| **千问 AI 平台 Token Plan · Lite** | ¥39/月 | **¥468** | 20,000 credits/周期 | 面向 API/编码工具，但 credits 制、非纯 token 价 | ✅ [官方 CHANGELOG 2026-11-09](https://platform.qianwenai.com/docs/changelog/token-plan-credits-1109) |
| **Token Plan · Essential** | ¥79/月 | **¥948** | 45,000 credits | 同上 | ✅ 同上 |
| **Token Plan · Standard** | ¥139/月 | **¥1,668** | 80,000 credits | 同上 | ✅ 同上 |
| **Token Plan · Pro** | **¥312/月**（原 ¥499，降 37%） | **¥3,744** | 200,000 credits | 同上 | ✅ 同上 |
| **腾讯元宝** | 目前主打**免费**（2026-07 报道"豆包收费、元宝免费"） | ¥0 | 未见公开会员价目 | — | 🟡 [21 世纪经济报道 2026-07](https://m.21jingji.com/article/20260708/herald/68598f1da803b389fb4a851ba8fda07d.html) |
| **百度文心** | ⚠️ 第三方 2026-04 整理 ¥59.9/月 | ⚠️ 约 ¥719（待核实） | 未查到官方额度说明 | — | ⚠️ 二手整理，官网价目页未取到 |
| **MiniMax M Plan** | ❌ 三档（Go / Explore 3× / Build 12×）价格未查到 | ❌ | 文本仅 M3.1 Flash；Explore/Build 才含 H3 视频 | 订阅 Key 与普通 API Key **不可混用**，混用会扣账户余额 | ✅ 档位见 [M Plan 概览](https://platform.minimax.cn/docs/m-plan/intro)；❌ 价格 |
| **讯飞 AStudio · 标准** | ¥16.8/月 | **¥202** | 每月基础 2,000 积分（+限时赠送） | 积分制，套餐积分与赠送积分 1 个月有效 | ✅ [AStudio 价格页](https://agent.xfyun.cn/studio-price/) |
| **讯飞 AStudio · 高级** | ¥56.8/月 | **¥682** | 每月 6,000 积分，高峰期资源优先 | 同上 | ✅ 同上 |
| **讯飞星火 MaaS「无忧版」** | ⚠️ 第三方 2026-04：¥3.9 首月 / ¥19 续费 | ⚠️ 约 ¥228（按 ¥19 续费） | 宣称**请求次数不限量、无 5 小时限制** | ⚠️ 该类"不限量"套餐通常有并发/公平使用限制 | ⚠️ [腾讯云社区 2026-07-20 转载](https://cloud.tencent.cn/developer/article/2712091) |

### A.3 各订阅"够不够每天用 / 够不够重度用"

| 订阅 | 轻度（20 轮/天） | 中度（100 轮/天） | 重度（Agent 300 万输入/天） | 依据 |
|---|---|---|---|---|
| ChatGPT Plus | ✅ 够 | ⚠️ 接近上限（Sol 15–160 条/5h） | ❌ 远不够，Codex 与 Work 抢同一份额度 | 官方 5 小时消息估算 |
| ChatGPT Pro 100 / 200 | ✅ 宽裕 | ✅ 够 | ⚠️ Pro 200（≈10× Plus）大多数情况够，极端并发仍会撞；可叠加 credits | 同上 |
| Claude Pro | ✅ 够 | ⚠️ Claude Code 一天下来可能见底 | ❌ 不够（5h + 周额度双重） | 官方帮助中心 |
| Claude Max | ✅ 宽裕 | ✅ 够 | ⚠️ 5× Pro 周额度，长任务密集时会撞；含 $100/月 API credits 可溢出到 API | 官方帮助中心 + apidog |
| Claude Ultra | ✅ | ✅ | ✅ 验证账户无 5h 窗口、周额度 10× Pro、含 $200/月 credits | 同上 |
| Gemini AI Pro | ✅ | ⚠️ 按算力计量，复杂任务消耗快 | ⚠️ 撞顶不切断，但会**降级到轻模型**（体验损失） | Mashable/I-O 2026 |
| Gemini AI Ultra | ✅ | ✅ | ⚠️ 5× Pro 额度，重度靠降级兜底 | 同上 |
| 豆包 标准/加强/高级 | ✅ / ✅ / ✅ | ⚠️ / ✅ / ✅ | ❌ / ⚠️ / ✅（高级 = 标准 10 倍） | 澎湃（官方口径） |
| Kimi Go / Pro / Max / Ultra | ✅ | ⚠️ / ✅ / ✅ / ✅ | ❌ / ⚠️ / ✅ / ✅（Agent 额度 4×/14×/28×） | Kimi 官方资源页 |
| GLM Coding Lite / Pro / Max | ✅ | ✅ / ✅ / ✅ | ⚠️ / ✅ / ✅ —— **算过**：重度 300 万输入+30 万输出/天，90% 缓存命中时 ≈ **1,386 积分/天 ≈ 9,702 积分/周**，Pro（60,000/周）绰绰有余，**Lite（10,000/周）刚好卡线**；若缓存 0%，则 19,530/周，Pro 仍够、Lite 不够 | 按官方积分公式 `(输入×6.9 + 缓存×1.7 + 输出×24)/10000` 复算 |
| 千问 App 高级/精英/旗舰 | ✅ | ⚠️ / ✅ / ✅ | 2×/5×/20× 免费额度（免费基线未公开，无法精确换算） | PChome |
| 讯飞 AStudio 标准/高级 | ✅ | ⚠️ / ✅ | 积分制（2,000 / 6,000 分/月） | 官方价格页 |

**结论**：没有任何一个"20 美元级"订阅能撑住重度 Agent 编码；**订阅被限流后叠加 API 是常态而非例外**（§C.5 给真实年费）。

---

## B. API 按量计费（元/百万 tokens）

> 单位：元/百万 tokens；输入/输出分开；"缓存" 指命中缓存的输入价。
> 美元价按 7.2 折算，表内直接给人民币，括号内保留美元原价。

### B.1 国内厂商（✅ 官网为主）

| 模型 | 输入 | 输出 | 缓存命中 | 备注 | 来源 |
|---|---:|---:|---:|---|---|
| **deepseek-flash**（空闲时段） | ¥1 | ¥4 | ¥0.02 | 半价档 | ✅ [DeepSeek 官方定价](https://api-docs.deepseek.com/zh-cn/quick_start/pricing)（2026-11-10） |
| **deepseek-flash**（高峰时段） | ¥2 | ¥8 | ¥0.04 | 高峰 = 北京时周一至周五 9:00–12:00、14:00–18:00（不含法定节假日） | ✅ 同上 |
| **deepseek-v4-pro**（空闲） | ¥4.5 | ¥13.5 | ¥0.15 | | ✅ 同上 |
| **deepseek-v4-pro**（高峰） | ¥9 | ¥27 | ¥0.30 | | ✅ 同上 |
| **qwen3.8-max**（百炼·华北2） | ¥12 | ¥36 | ¥1.5 | 显式缓存创建 ¥15；Batch ¥6/¥18 | ✅ 阿里云百炼（经 [开发者社区 2026-10-24](https://developer.aliyun.com/article/1774616) 转载的官方价目） |
| **qwen3.7-plus**（新加坡） | $0.40 ≈ ¥2.88 | $1.60 ≈ ¥11.52 | 未公布（缓存约输入价 12.5%） | 超 256K 后 $1.20/$4.80 | 🟡 [Morph 2026-09-07 读自 Model Studio](https://www.morphllm.com/qwen-api) |
| **qwen3.8-flash**（新加坡） | $0.15 ≈ ¥1.08 | $0.47 ≈ ¥3.38 | — | 最便宜档 | 🟡 同上 |
| **qwen3-coder-plus** | $1.00 ≈ ¥7.2 | $5.00 ≈ ¥36 | — | **超 256K 后 $6/$60（陷阱）** | 🟡 同上 |
| **kimi-k3.1-pro** | ¥13 | ¥68 | ¥1.30 | 缓存写入 ¥13（5min）/ ¥26（1h） | ✅ [Kimi 官方资源页 2026-10-24](https://www.kimi.com/resources/kimi-k3-1-pro-pricing) |
| **kimi-k3** | ¥20 | ¥100 | ¥2.00 | K2 系列 2026-12 底全部下线 | ✅ 同上 |
| **kimi-k3.1-pro-highspeed** | ¥26 | ¥136 | ¥1.30 | | ✅ 同上 |
| **GLM-5.3** | ¥8 | ¥28 | ¥2 | Batch 五折；缓存存储限时免费 | ✅ [智谱 API 定价](https://docs.bigmodel.cn/cn/guide/start/pricing.md) |
| **GLM-5.3-Flash** | ¥0.8 | ¥2.8 | ¥0.23 | 多模态 | ✅ 同上 |
| **GLM-5.3-FlashX** | ¥2 | ¥7 | ¥0.57 | | ✅ 同上 |
| **GLM-4.7-Flash** | **免费** | **免费** | 免费 | 免费模型 | ✅ 同上 |
| **doubao-seed-2.1-pro** | ¥6 | ¥30 | ¥1.2 | 输入 ≤1024K | ✅ [火山方舟价格页 2026-11-05](https://ark.volcengine.com/region:cn-beijing/docs/model-pricing.md) |
| **doubao-seed-2.0-pro**（≤32K） | ¥3.2 | ¥16 | ¥0.64 | 分段计费；32–128K 为 ¥4.8/¥24 | ✅ 同上 |
| **doubao-seed-2.0-lite**（≤32K） | ¥0.6 | ¥3.6 | ¥0.12 | | ✅ 同上 |
| **doubao-seed-2.0-mini**（≤32K） | ¥0.2 | ¥2.0 | ¥0.04 | 最便宜豆包 | ✅ 同上 |
| **MiniMax-M3.1-Flash** | ¥1 | ¥4 | ¥0.10 | | ✅ [MiniMax 官方定价](https://platform.minimax.cn/docs/pricing/overview) |

### B.2 海外厂商（含缓存价）

| 模型 | 输入 | 输出 | 缓存读 | 缓存写 | 人民币（输入/输出） | 来源 |
|---|---:|---:|---:|---:|---|---|
| **Claude Sonnet 5.5** | $2 | $10 | $0.10 | $2.50 | ¥14.4 / ¥72 | ✅ [claude.com/platform/api](https://claude.com/platform/api) |
| **Claude Opus 5.5** | $4 | $20 | $0.20 | $5 | ¥28.8 / ¥144 | ✅ 同上 |
| **Claude Fable 5.2** | $8 | $40 | $0.20 | $10 | ¥57.6 / ¥288 | ✅ 同上 |
| **Claude Haiku 5.5** | ❌ | ❌ | ❌ | ❌ | ❌ | 页面在该行被截断 |
| **GPT-6.1 Sol** | $2 | $10 | $0.10 | $2.50 | ¥14.4 / ¥72 | 🟡 [Magora 2026-10-13（读自官方价目）](https://magora-systems.com/openai-api-pricing/)；Batch 五折 $1/$5；长上下文 $4/$15；Fast 模式 $4/$20 |
| **GPT-6 Luna** | $0.10 | $0.50 | $0.01 | $0.125 | ¥0.72 / ¥3.6 | 🟡 同上 |
| **GPT-6 Astra** | $10 | $50 | $1.00 | $12.50 | ¥72 / ¥360 | 🟡 同上 |
| **Gemini 4 Argon** | $2（12/1 起 $4） | $10（12/1 起 $20） | $0.10 | — | ¥14.4 / ¥72（12 月后翻倍） | 🟡 [Morph 2026-10-25 读自 ai.google.dev](https://www.morphllm.com/gemini-api-pricing) |
| **Gemini 3.8 Flash** | $0.75 | $3.75 | $0.075 | — | ¥5.4 / ¥27（2027-01-01 翻倍） | 🟡 同上 |
| **Gemini 3.1 Pro** | $2（≤200K） | $12 | $0.20 | — | ¥14.4 / ¥86.4 | 🟡 同上 |
| **Gemini 2.5 Flash** | $0.30 | $2.50 | $0.03 | — | ¥2.16 / ¥18 | 🟡 同上 |
| **Gemini 2.5 Flash-Lite** | $0.10 | $0.40 | $0.01 | — | ¥0.72 / ¥2.88 | 🟡 同上 |

### B.3 免费额度 / 免费模型 / 折扣档（这是省钱关键）

| 项目 | 内容 | 来源 |
|---|---|---|
| **DeepSeek 夜间（空闲）折扣** | 空闲时段 = 高峰价的 **50%**：deepseek-flash 输入 ¥1 vs ¥2、输出 ¥4 vs ¥8。北京时间周一至周五 9–12、14–18 为高峰，其余（含周末、法定节假日）= 空闲 | ✅ [DeepSeek 定价页](https://api-docs.deepseek.com/zh-cn/quick_start/pricing) |
| **智谱免费模型** | GLM-4.7-Flash、GLM-4-Flash-250414、GLM-Z1-Flash、GLM-4.6V-Flash、GLM-4V-Flash 等**输入输出全免费** | ✅ [智谱定价](https://docs.bigmodel.cn/cn/guide/start/pricing.md) |
| **Gemini API 免费层** | gemini-3.8-flash / 3.6-flash / 3.5-flash-lite / 3.1-flash-lite / 3-flash / 2.5-pro / 2.5-flash / 2.5-flash-lite **免费**；**Argon 与 3.1 Pro 无免费层**。免费层内容会被用于改进产品，限额更低 | 🟡 [Morph 2026-10-25](https://www.morphllm.com/gemini-api-pricing) |
| **通义免费额度** | 每个专有模型 **100 万 tokens / 90 天**（新加坡区；Batch/缓存/精调不抵扣） | 🟡 [Morph 2026-09](https://www.morphllm.com/qwen-api) |
| **豆包免费额度** | 火山方舟新用户免费推理额度 + "安心体验模式"（仅耗 50w 免费 token）；联网内容插件每月 2 万次免费 | ✅ [Ark 价格页/免费额度文档](https://ark.volcengine.com/region:cn-beijing/docs/model-pricing.md) |
| **OpenRouter 免费模型** | 2026-10-04 时点 **22 个免费模型**（Google Lyria、NVIDIA Nemotron 3、Qwen、Cohere 等，上下文 256K–1M） | 🟡 [Overfeed 2026-10-04](https://overfeed.news/reports/2026-10-04-api-prices) |
| **OpenRouter 便宜开源模型** | DeepSeek Flash Latest 输入 **$0.003/M**（≈¥0.022）；gpt-oss-20b $0.018/$0.09（≈¥0.13/¥0.65）；Mistral Nemo $0.019/$0.03；GLM-5.3 $0.22/$3.39；Kimi K3 输入 $0.499；Qwen3.8-27b $0.15/$2.00 | 🟡 同上 + Morph Qwen 页 |
| **Batch/低优先级折扣** | OpenAI Batch 五折；Gemini Batch/Flex 五折；智谱 Batch 五折；通义 Batch ¥6/¥18；MiniMax/豆包 低优推理约五折 | 各官方页 |

---

## C. 一年成本模型（核心）

### C.1 三档使用强度定义（token 量）

| 档位 | 每天对话轮数 | 输入 tokens/天 | 输出 tokens/天 | 全年输入 | 全年输出 | 缓存假设 |
|---|---:|---:|---:|---:|---:|---|
| 轻度 | 20 | 30,000 | 10,000 | 10.95 M | 3.65 M | 忽略（0%） |
| 中度 | 100 | 150,000 | 40,000 | 54.75 M | 14.60 M | 忽略（0%） |
| 重度（Agent/编码） | — | 1,000,000 – 3,000,000 | 300,000 | 365 M – 1,095 M | 109.5 M | **主场景取 300 万/天、90% 缓存命中**；另给 0% 缓存的悲观值 |

**算式（可复核）**：

```
年费 = 全年输入×(1−缓存命中率)×输入单价/1e6
     + 全年输入×缓存命中率×缓存命中单价/1e6
     + 全年输出×输出单价/1e6
```

- 重度"90% 缓存"依据：Agent 循环每步重发同一段上下文，Claude Code / Codex 类工作流缓存命中率通常在 85–95%。
- 有"缓存写入"费的模型（Claude、GPT）：把未命中的那部分输入按**写入价**计（更保守），未命中比例 10%。

### C.2 ① 纯订阅方案年费（人民币）

海外：

| 订阅 | 月费 | 年费 | 备注 |
|---|---:|---:|---|
| ChatGPT Plus | $20 | **¥1,728** | 轻度够用 |
| ChatGPT Pro 100 | $100 | **¥8,640** | ≈5× Plus |
| ChatGPT Pro 200 | $200 | **¥17,280** | ≈10× Plus |
| ChatGPT Pro 500 | $500 | **¥43,200** | Ultrafast 专属 |
| Claude Pro | $20 | **¥1,728**（年付 **¥1,469**） | |
| Claude Max | $100 | **¥8,640** | 含 $100/月 API credits |
| Claude Ultra | $200 | **¥17,280** | 含 $200/月 API credits |
| Gemini AI Plus | $7.99 | **¥691** | |
| Gemini AI Pro | $19.99 | **¥1,727** | |
| Gemini AI Ultra | $99.99 | **¥8,639** | |
| Cursor Pro / Pro+ / Ultra（legacy） | $20 / $60 / $200 | **¥1,728 / ¥5,184 / ¥17,280** | |
| Cursor（新 X 订阅）Premium / Super / Ultra | $30 / $100 / $200 | **¥2,592 / ¥8,640 / ¥17,280** | |
| GitHub Copilot | ❌ | ❌ | 未查到 2026-11 价目 |

国内：

| 订阅 | 年费 | 备注 |
|---|---:|---|
| 豆包 标准 / 加强 / 高级 | **¥816 / ¥2,400 / ¥5,088** | 高级年付 5,088（月付 6,000） |
| 豆包 Coding Plan Lite / Pro | **¥480 / ¥2,400** | 编码工具专用 |
| 豆包 Agent Plan Small / Medium / Large / Max | **¥480 / ¥2,400 / ¥6,000 / ¥12,000** | |
| Kimi Go / Plus / Pro / Max / Ultra | **¥468 / ¥948 / ¥1,908 / ¥6,708 / ¥13,428** | 年付折算 |
| 智谱 GLM Coding Lite / Pro / Max | ⚠️ 未查到官方价 | 仅积分配额已知 |
| 千问 App 高级 / 精英 / 旗舰 | **¥200 / ¥568 / ¥1,499** | 年付价 |
| 千问 Token Plan Lite / Essential / Standard / Pro | **¥468 / ¥948 / ¥1,668 / ¥3,744** | 2026-11-09 新价 |
| MiniMax M Plan | ❌ 未查到 | Go/Explore/Build 三档 |
| 腾讯元宝 | ¥0 | 主打免费 |
| 百度文心 | ⚠️ ≈¥719 | ¥59.9/月，二手 |
| 讯飞 AStudio 标准 / 高级 | **¥202 / ¥682** | |
| 讯飞星火 MaaS 无忧版 | ⚠️ ≈¥228 | ¥19/月续费，二手 |

### C.3 ② 纯 API 方案年费（同样用量，人民币）

| 模型 | 轻度 ¥/年 | 中度 ¥/年 | 重度 ¥/年（90% 缓存） | 重度 ¥/年（0% 缓存） |
|---|---:|---:|---:|---:|
| **DeepSeek Flash**（70% 空闲价混合） | **33** | **147** | **737** | **1,993** |
| DeepSeek V4-Pro（70% 空闲价混合） | 128 | 577 | 2,754 | 8,327 |
| **GLM-5.3-Flash** | 19 | 85 | 621 | 1,183 |
| GLM-5.3 | 190 | 847 | 5,913 | 11,826 |
| **MiniMax M3.1-Flash** | 26 | 113 | 646 | 1,533 |
| Doubao-Seed-2.1-Pro | 175 | 766 | 5,125 | 9,855 |
| Qwen3.7-Plus | 74 | 326 | 1,932 | 4,415 |
| **Qwen3.8-Max** | 263 | 1,183 | **6,734** | 17,082 |
| Kimi K3.1 Pro | 391 | 1,705 | 10,151 | 21,681 |
| **Claude Sonnet 5.5** | 460 | 2,037 | **10,565** | 27,594 |
| Claude Opus 5.5 | 920 | 4,073 | **21,129** | 55,188 |
| Claude Fable 5.2 | 1,840 | 8,147 | 40,839 | 110,376 |
| **GPT-6.1 Sol** | 460 | 2,037 | **10,565** | 27,594 |
| GPT-6 Luna | **23** | **102** | 564 | 1,380 |
| GPT-6 Astra | 2,300 | 10,184 | 56,371 | 137,970 |
| Gemini 4 Argon（11/30 前价） | 420 | 1,840 | 10,170 | 23,652 |
| **Gemini 3.8 Flash** | 158 | 690 | 4,080 | 8,870 |
| Gemini 2.5 Flash-Lite | 18 | 81 | 465 | 1,104 |
| OpenRouter gpt-oss-20b | **4** | **17** | 213 | 213 |

**样例算式（重度 · Claude Sonnet 5.5，主场景 300 万输入/天，90% 缓存）**：

```
全年输入 = 3,000,000 × 365 = 1,095 M；全年输出 = 300,000 × 365 = 109.5 M
未命中输入 1,095M×10% = 109.5M × ¥18（缓存写入价 $2.50×7.2）  = ¥1,971
缓存命中   1,095M×90% = 985.5M × ¥0.72（$0.10×7.2）            = ¥710
输出       109.5M × ¥72（$10×7.2）                             = ¥7,884
合计                                                          ≈ ¥10,565  ✅ 与表中一致
```

**样例算式（重度 · DeepSeek Flash，90% 缓存）**：

```
未命中输入 109.5M × ¥1.3（70%空闲混合价）  = ¥142.4
缓存命中   985.5M × ¥0.026                = ¥25.6
输出       109.5M × ¥5.2                  = ¥569.4
合计                                      ≈ ¥737  ✅ 与表中一致
```

> 若按"100 万输入/天"的轻量重度（全年输入 365 M），上表数值约为 **1/3**：Sonnet ≈ ¥3,520、DeepSeek Flash ≈ ¥246。表中取 300 万/天的保守上限。

**读法**：同样的重度用量，**DeepSeek Flash 与 GPT-6 Astra 相差 76 倍**。选模型比选套餐重要得多。

### C.4 ③ 订阅 + API 混合（按档位给最优组合）

| 档位 | 推荐组合 | 订阅年费 | API 年费（兜底/超额） | 合计 |
|---|---|---:|---:|---:|
| 轻度 | 千问 App 高级（¥200/年）+ DeepSeek Flash 兜底 | 200 | 33 | **¥233** |
| 轻度 | 免费路线：Gemini 免费层 + GLM-4.7-Flash | 0 | 0 | **¥0**（有限速） |
| 轻度 | Kimi Go ¥468 + DeepSeek Flash | 468 | 33 | ¥501 |
| 中度 | 千问 App 高级 + DeepSeek Flash | 200 | 147 | **¥347** |
| 中度 | 豆包 标准 ¥816 + DeepSeek Flash 兜底 | 816 | 147 | ¥963 |
| 中度 | 纯 API（GPT-6 Luna） | 0 | 102 | **¥102**（最便宜） |
| 重度 | **Claude Max**（¥8,640，含 $1,200/年 API credits ≈ ¥8,640 API 额度） | 8,640 | 0（credits 内） | **¥8,640** |
| 重度 | Claude Max + 超额买 $500 credits | 8,640 | 3,600 | **¥12,240** |
| 重度 | **ChatGPT Plus + Codex 超额走 GPT-6.1 Sol API**（约 30% 用量溢出） | 1,728 | 3,169 | **¥4,897** |
| 重度 | GLM Coding Pro（价 ⚠️）+ DeepSeek Flash 兜底 | ⚠️ | 737 | ⚠️ 估算 ¥3,100 级 |
| 重度 | 千问 Token Plan Pro ¥3,744 + DeepSeek Flash 兜底 | 3,744 | 737 | **¥4,481** |
| 重度 | 纯 API：DeepSeek Flash | 0 | 737 | **¥737**（最便宜，但要自己搭工具链） |

**Claude Max 的关键算术**：重度 Sonnet 5.5 纯 API 一年 ≈ ¥10,565；而 Max 一年 ¥8,640 **已经含 $1,200 = ¥8,640 的 API credits**，等于"订阅额度基本白送"。这就是为什么海外重度用户常选 Max 而不是纯 API。

### C.5 重度用户的真实年成本："先被限流，再叠加 API"

这是大多数人实际发生的路径，也是本题最重要的一张表：

| 组合 | 订阅 | 溢出部分怎么算 | 真实年成本 |
|---|---|---|---:|
| ChatGPT Plus → 撞 Codex 额度 → 用 GPT-6.1 Sol API 补 30% 用量 | ¥1,728 | 30% 重度用量：328.5M 输入（90% 缓存）+ 32.85M 输出 = ¥3,169 | **≈ ¥4,897** |
| ChatGPT Plus → 直接升 Pro 200 | ¥17,280 | 不用 API | **¥17,280**（比补 API 贵 3.5 倍） |
| Claude Pro → 撞 5h/周额度 → 升 Max | ¥8,640 | 含 $1,200 credits | **¥8,640** |
| Claude Pro → 撞额度 → 继续买 usage credits（不升级） | ¥1,728 | 视溢出量，重度按 ¥10,565 级 API 计 | **≈ ¥12,300**（不划算） |
| Claude Ultra（重度 + 长任务密集） | ¥17,280 | 含 $200/月 credits | **¥17,280**，若 credits 也不够再 +$2,400 → ¥34,560 |
| 豆包 高级（¥5,088/年）→ 撞额度 → 火山方舟 API 补 | ¥5,088 | DeepSeek-V4-Pro 在方舟 ¥9/¥27 | ≈ ¥8,000–12,000 |
| Kimi Pro（¥1,908）→ 撞额度 → Kimi K3.1 Pro API 补 | ¥1,908 | 重度溢出 30% ≈ ¥3,045 | ≈ ¥4,953 |
| GLM Coding Pro → 撞额度 → 智谱标准 API | ⚠️ | GLM-5.3 重度 ¥5,913（若全走 API） | ⚠️ 估算 ¥6,000–8,400 |
| 纯 API（DeepSeek Flash，90% 缓存） | 0 | — | **¥737** |

**结论**：
- "订阅 + 补 API"在重度档普遍落在 **¥4,900 – ¥12,200/年**；
- 最省的重度方案不是"买更贵的订阅"，而是**国内 Coding Plan / 纯 API + 一个便宜订阅**；
- 反过来，**只升订阅不补 API**（Pro 200 / Ultra）是 ¥17,000–43,000 档，对个人用户很不划算。

### C.6 对照"1 万元本地机器"

| 项目 | 云端 | 本地（1 万元机器） |
|---|---|---|
| 首年支出 | 轻度 ¥0–233；中度 ¥100–960；重度 ¥4,900–12,200 | 机器 ¥10,000 + 电费 ≈ ¥1,000（600W×8h×365×¥0.6）→ **首年 ¥11,000** |
| 年化（3 年折旧） | 同上（可随时停） | ≈ ¥3,333 + ¥1,000 电费 = **¥4,433/年** |
| 能力上限 | Opus 5.5 / GPT-6 Astra / Gemini 4 Argon / Fable 5.2 | 约 27B–70B 量化（Qwen3.8-27B 级），旗舰能力差 1–2 档 |
| 缓存/长上下文 | 1M 上下文、缓存命中 5–10 折 | 受显存限制（24GB 跑 27B FP8 已吃紧） |
| 运维 | 无 | 驱动/量化/推理框架自管，故障自修 |
| 边际成本 | 用多少付多少 | 24h 空转也耗电 |

**判断**：如果重度且长期用，**本地机的年化 ¥4,400 与"云端 ¥4,900 订阅+API 混合"几乎同价**，但云端模型能力强 1–2 档；本地机的价值在隐私、离线、无限调用。轻度/中度用户买本地机在 3 年内**不可能回本**（云端年费 < ¥1,000）。

---

## D. 云 GPU 租用（偶尔跑本地模型）

> 数据源：rentgpu.link（31 家平台比价，2026-11-10 06:45 更新，CC BY 4.0）+ gpus.io（RunPod/Vast.ai 对比，2026-11-09）+ 平台官方页。
> 年成本 = 小时价 × 12 个月 × 月租小时数。**不含**存储、带宽、镜像/系统盘费用；竞价实例可能被中断。

### D.1 每小时单价

| 卡型 | 平台 | 单价 | 说明 | 来源 |
|---|---|---:|---|---|
| **RTX 4090 24G** | Salad（美）竞价 | **¥1.15/h** | 当前全网最低（$0.160 折算） | 🟡 [rentgpu 4090 比价](https://rentgpu.link/gpu/rtx-4090) |
| RTX 4090 | PPIO 派欧云（国内 Spot） | ¥1.16/h | 竞价，1 小时保护期 | 🟡 同上 |
| RTX 4090 | 算家云（国内） | ¥1.24/h | 官网标价（原 ¥2.08） | 🟡 同上 |
| RTX 4090 | 晨涧云 | ¥1.38/h | 包日折算 | 🟡 同上 |
| RTX 4090 | 智星云 | ¥1.65/h | 低价专区 | 🟡 同上 |
| **RTX 4090** | **恒源云（国内）** | **¥1.88/h** | 按量实时价（原价 ¥4.00） | 🟡 同上 |
| **RTX 4090** | **AutoDL（国内）** | **¥2.08/h** | 官网市场按量最低价 | 🟡 同上 |
| RTX 4090 | 矩池云 | ¥2.20/h | 按分钟计费 | 🟡 同上 |
| RTX 4090 | RunPod（社区云） | $0.34/h ≈ ¥2.45 | Secure Cloud $0.89/h ≈ ¥6.41 | 🟡 同上 + [gpus.io](https://gpus.io/en/providers/compare/runpod-vs-vast-ai) |
| RTX 4090 | Vast.ai | $0.40/h ≈ ¥2.88 | 竞价；rentgpu 折算 ¥2.46 | 🟡 同上 |
| **RTX 3090 24G** | Vast.ai | **$0.12/h ≈ ¥0.86** | 全网地板价 | 🟡 gpus.io 2026-11-09 |
| RTX 3090 | RunPod | $0.50/h ≈ ¥3.60 | | 🟡 同上 |
| RTX 3090 | 国内最低 | ¥0.63/h | rentgpu 标注"Vast.ai（美国）竞价"；**国内 3090 单价未查到** | 🟡 rentgpu 2026-11-10 |
| **A100 80G** | Vast.ai | **$0.40/h ≈ ¥2.88** | | 🟡 gpus.io 2026-11-09 |
| A100 80G | RunPod | $1.79/h ≈ ¥12.89 | on-demand | 🟡 同上 |
| A100 80G | 蓝耘（国内，A100-SXM4-80G） | ¥9.70/h | 人工复核 2026-11-01 | 🟡 rentgpu 4090 页备注 |
| **L40S 48G** | Vast.ai | **$0.47/h ≈ ¥3.38** | | 🟡 gpus.io 2026-11-09 |
| L40S 48G | RunPod | $1.09/h ≈ ¥7.85 | | 🟡 同上 |
| RTX 5090 32G | Vast.ai / RunPod | $0.21 / $1.19 per h | 参考 | 🟡 同上 |

### D.2 年成本（每月 10 小时 / 50 小时）

| 卡型 · 平台 | 单价 | 10h/月 → 120h/年 | 50h/月 → 600h/年 |
|---|---:|---:|---:|
| 3090 · Vast.ai 竞价 | ¥0.86 | **¥104** | **¥518** |
| 4090 · Salad 竞价 | ¥1.15 | ¥138 | ¥690 |
| 4090 · 算家云 | ¥1.24 | ¥149 | ¥744 |
| 4090 · 恒源云 | ¥1.88 | ¥226 | ¥1,128 |
| 4090 · AutoDL | ¥2.08 | **¥250** | **¥1,248** |
| 4090 · Vast.ai | ¥2.88 | ¥346 | ¥1,728 |
| 4090 · RunPod（社区） | ¥2.45 | ¥294 | ¥1,469 |
| 4090 · RunPod（Secure） | ¥6.41 | ¥769 | ¥3,845 |
| A100 80G · Vast.ai | ¥2.88 | ¥346 | ¥1,728 |
| A100 80G · 蓝耘（国内） | ¥9.70 | ¥1,164 | ¥5,820 |
| A100 80G · RunPod | ¥12.89 | **¥1,547** | **¥7,733** |
| L40S · Vast.ai | ¥3.38 | ¥406 | ¥2,030 |
| L40S · RunPod | ¥7.85 | ¥942 | ¥4,709 |

**对本题的意义**：每月只跑 10 小时本地模型，**年成本 ¥100–1,550**，远低于买 1 万元机器；即使每月 50 小时，4090 级也只要 ¥690–1,248/年。**"偶尔跑本地"用云 GPU 远比买机器划算**，"每天跑 8 小时"才轮到买机器（约 3 年回本）。

### D.3 GPU 部分的注意事项

- 竞价/Spot 实例**随时可能被回收**，长任务必须能 checkpoint；不能中断的任务用 on-demand（价格通常 2–4 倍）。
- 上述价格**不含**系统盘/数据盘、公网带宽、镜像费；实际月账单通常比纯算力高 10–20%。
- AutoDL / 恒源云常有"包月/包周"价，比按量便宜 20–40%，长任务应对比包月。
- 国内 3090 / L40S 的按量单价本次**未查到**（平台页面为纯前端渲染，比价站也未收录），不做推测。

---

## E. 明确"未查到"的清单（不虚构，下单前务必复核）

| 项目 | 状态 | 建议复核入口 |
|---|---|---|
| GitHub Copilot 2026-11 官方价目（Pro/Pro+/Business 与 AI credits 单价） | ❌ 未查到（3 个页面均被导航/JS 截断，仅确认已转用量计费） | https://github.com/features/copilot/plans ；https://docs.github.com/en/copilot/get-started/plans |
| 智谱 GLM Coding Plan 三档**价格**（积分额度已查到） | ❌ 官方文档只有积分规则 | https://docs.bigmodel.cn/cn/coding-plan/overview.md ；https://www.bigmodel.cn/glm-coding |
| MiniMax M Plan 三档价格 | ❌ | https://platform.minimax.cn/docs/m-plan/intro |
| 腾讯元宝会员价 | ❌（目前主打免费） | https://yuanbao.tencent.com |
| 百度文心会员价（第三方 ¥59.9/月） | ⚠️ 待核实 | 百度 AI 官网价目页 |
| 讯飞星火 MaaS「无忧版」现价（第三方 ¥3.9 首月/¥19 续） | ⚠️ 待核实 | https://maas.xfyun.cn/packageSubscription |
| Claude Haiku 5.5 API 价 | ❌ 页面截断 | https://claude.com/platform/api |
| 通义 qwen3.8-flash 的**人民币**价（只取到新加坡美元价） | ⚠️ 部分 | https://help.aliyun.com/zh/model-studio/models |
| 国内 3090 / L40S 按量单价 | ❌ | https://www.autodl.com/market/list ；https://www.gpushare.com |

**抓取技巧（下次复核用）**：
- 火山方舟、智谱、千问、MiniMax 的文档站支持 **URL 后加 `.md`** 直接拿 Markdown（例：`https://ark.volcengine.com/region:cn-beijing/docs/model-pricing.md`），能绕开 JS 渲染。
- 智谱有文档索引 `https://docs.bigmodel.cn/llms.txt`；火山方舟有 `https://ark.volcengine.com/llms.txt`。
- `bigmodel.cn`、`autodl.com`、`gpushare.com`、`ai.google.dev` 的**定价页正文是前端渲染**，直接抓只能拿到导航；这类页面改用第三方比价站（rentgpu.link / gpus.io）或官方 `.md`。

---

## 附：本文件所有关键数字的一行速查

- 汇率 $1 = ¥7.2；全年按 365 天。
- 轻度年 token：10.95M 输入 + 3.65M 输出。
- 中度：54.75M + 14.6M。
- 重度：365M–1,095M 输入 + 109.5M 输出（**主场景用 1,095M + 109.5M，90% 缓存**）。
- 最便宜重度纯 API：**DeepSeek Flash ¥737/年**（90% 缓存）。
- 最贵重度纯 API：**GPT-6 Astra ¥56,371/年**。
- 重度"订阅+补 API"真实区间：**¥4,897 – ¥12,240/年**。
- 云 GPU 偶尔跑：**¥104 – ¥1,547/年**（10h/月）。
- 1 万元本地机年化：**≈ ¥4,433/年**（3 年折旧 + 电费）。
