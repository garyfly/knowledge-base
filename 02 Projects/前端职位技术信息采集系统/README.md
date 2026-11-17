# BOSS直聘 前端岗位采集（深圳）— 方案与实现

> 目标：采集 BOSS直聘 深圳地区「前端」相关岗位，落成结构化表格（薪资、公司、技能标签、JD 正文），用于岗位技能分析。
>
> **两条结论**：① Firecrawl 没有桌面端，也不适合抓 BOSS；② **Playwright 会被 BOSS 的 CDP 检测识别并白屏**，最稳的做法是把采集逻辑做成浏览器用户脚本，跑在你自己的 Chrome 里。

---

## 1. Firecrawl 有没有桌面端？

**没有官方桌面客户端。** Firecrawl 的产品形态只有这几种：

| 形态 | 说明 |
|---|---|
| 云端 API / Playground | 官网注册拿 Key，调 `scrape` / `crawl` / `map` / `search` |
| 自托管 | GitHub 开源版（AGPL-3.0），Docker 起服务 |
| CLI | 命令行工具，本质是 API 的壳 |
| MCP Server | 挂进 Claude / Cursor 等客户端当工具 |
| SDK | Python / Node / Go 等 |

[官方文档](https://docs.firecrawl.dev/introduction) 里的「Claude Desktop / Cowork」是**把 Firecrawl 当 MCP 工具接进 Claude 桌面版**，不是 Firecrawl 自己的桌面软件。官网没有 `.exe` / `.dmg` 下载页是正常的。

## 2. 为什么 Firecrawl 不适合 BOSS直聘

| 障碍 | 具体表现 |
|---|---|
| 登录态 | 搜索接口要带登录 cookie（含 `__zp_stoken__`），云端无法携带你的账号会话 |
| 风控 | 云服务出口是机房 IP，BOSS 基本直接弹安全验证 / 返回空 |
| 交互式反爬 | 页面会主动重定向到 `about:blank`，需要真实浏览器上下文连续操作 |
| 字体加密 | 列表页工资用 `@font-face` 私有区字符混淆（U+E000~U+F8FF），DOM 取到乱码 |
| 成本 | 云端按页计费，几百页比本地跑脚本贵得多 |

Firecrawl 的强项是「公开静态站 → 干净 Markdown 喂大模型」，BOSS 这种「登录后动态接口 + 强风控」在它的能力边界之外。

## 3. BOSS直聘 的数据在哪

```
https://www.zhipin.com/web/geek/job?query=前端&city=101280600   ← 页面（Vue SPA，HTML 里没数据）
        ↓ 页面自己发 XHR
GET /wapi/zpgeek/search/joblist.json?scene=1&query=前端&city=101280600&page=1&pageSize=30
        ↓ 返回 JSON
zpData.jobList[] → jobName / salaryDesc / brandName / skills / bossName / encryptJobId ...
```

- `salaryDesc` 是**真实可读**的 `"18-22K"`，比解析 DOM 靠谱得多；
- 详情接口：`GET /wapi/zpgeek/job/detail.json?securityId=xxx`（用列表里的 `securityId`，不是 `encryptJobId`），能拿 JD 正文、详细地址、公司规模；
- 城市 code 用官方接口查：[city/site.json](https://www.zhipin.com/wapi/zpgeek/common/data/city/site.json) → **深圳 = `101280600`**（`101280100` 是广州，`101280200` 是韶关，网上不少教程写错）。

## 4. 为什么会白屏：Playwright 被识别了

现象：自动化浏览器打开 zhipin.com，页面正常显示 1~2 秒后变成 `about:blank` 白屏；手动用 Chrome 打开完全正常。

原因不是 IP、不是账号，而是**浏览器被 CDP 接管后留下的指纹**。BOSS 的检测点主要有三个：

| 检测点 | 自动化浏览器的暴露方式 |
|---|---|
| `navigator.webdriver` | Playwright/Selenium 默认启动参数里带 `--enable-automation`，该属性为 `true` |
| `Runtime.enable` 泄漏 | Playwright 执行 JS 必须开 CDP 的 `Runtime.enable`，页面可以用 `Error.stack` / `console` 的 getter 反查出来 |
| 启动参数 / 指纹 | `--disable-blink-features`、`--disable-component-update` 等组合本身就是特征；再加上无头 UA、缺失插件、WebGL 渲染器等 |

也就是说，只加 `--disable-blink-features=AutomationControlled` 是**不够的**——那只解决 `navigator.webdriver` 一项，`Runtime.enable` 这条最硬的泄漏还在，所以照样白屏。

`/wapi/` 接口本身对「正常浏览器」是放行的（这也是为什么手动翻页一切正常），它卡的是**浏览器**，不是请求。

### 三条可行路线

| 路线 | 是否被检测 | 成本 | 适用 |
|---|---|---|---|
| **A. 用户脚本（Tampermonkey）跑在普通 Chrome 里** | ❌ 完全没有 CDP 痕迹 | 最低，装个脚本就行 | **推荐**，本职场景就是个人求职分析 |
| B. patchright（Playwright 反检测补丁版） | 大概率绕过 | 中，装包即可 | 需要保存登录态、批量无人值守时 |
| C. 手动 DevTools 抓 HAR / 一页页复制 | ❌ | 高（人工） | 只要几十条数据时最快的办法 |

---

## 5. 方案 A（推荐）：Tampermonkey 用户脚本

**原理**：脚本注入到你自己 Chrome 的 zhipin.com 页面里，用页面自己的 `fetch` 调 `/wapi/zpgeek/search/joblist.json`。没有 CDP、没有 webdriver 标志、没有额外进程，风控视角下和你在页面上手动翻页没有区别。

### 安装使用

1. Chrome 装 **Tampermonkey** 扩展；
2. Tampermonkey → 添加新脚本 → 粘贴 [boss_zhipin_collect.user.js](boss_zhipin_collect.user.js) 全文 → 保存（Ctrl+S）；
3. 打开 `https://www.zhipin.com/web/geek/job?query=前端&city=101280600`，确认右上有登录头像；
4. 右下角出现「BOSS 职位采集」面板 → 点 **开始采集** → 跑完点 **导出 CSV**。

面板会自动从 URL 读 `query` / `city`，也可以手改；设置存在 localStorage，下次不用重填。

### 特性

- 逐页请求，每页间隔 **2.5~4.5 秒**随机，不并发；
- 按 `encryptJobId` 去重，多关键词重复岗位只留一条；
- 返回 `code != 0` / 非 JSON 会自动停并提示（触发风控的信号）；
- 导出 CSV（UTF-8 BOM，Excel 直接打开）和 JSON；
- 面板可折叠，不影响页面操作。

### 想采多个关键词

改面板里的关键词跑一轮 → 导出 CSV 一次，换关键词再跑。或者装好后在控制台里没有更好的办法——保持手动换词，反而最安全（不同关键词之间天然有间隔）。

---

## 6. 方案 B（备选）：patchright 自动化

如果确实需要「无人值守 + 复用登录态」，把 Playwright 换成 [patchright](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright)——它是打过补丁的 Playwright 驱动，专门处理上面三个检测点（避开 `Runtime.enable`、移除 `--enable-automation`、补 `--disable-blink-features=AutomationControlled`），API 完全一样。

```bash
pip install patchright
python boss_zhipin_jobs.py --login        # 会打印「引擎=patchright」
python boss_zhipin_jobs.py --keywords 前端,前端开发,web前端 --pages 10
```

`boss_zhipin_jobs.py` 会自动优先加载 patchright（`ENGINE` 常量），没装才退回原版 Playwright 并给出警告。

> 注意：patchright 官方标注只支持 Chromium 系；它也不是「绝对不被检测」，BOSS 若升级风控仍可能失效。**稳定性排序：用户脚本 > patchright > 原版 Playwright（必白屏）。**

### 关键脚本参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `--keywords` | 前端 | 逗号分隔多关键词 |
| `--city` | 深圳 | 城市名或 code |
| `--pages` | 10 | 单关键词最多翻几页 |
| `--page-size` | 30 | 每页条数 |
| `--detail` | 关 | 额外抓 JD 正文 |
| `--headless` | 关 | 无头更容易被识别，别开 |
| `--profile` | `.browser_profile` | 登录态目录，别提交 git |

---

## 7. 字段

| 字段 | 含义 |
|---|---|
| `query` | 命中的搜索关键词 |
| `job_name` / `salary` | 岗位名 / 薪资原文（`18-22K·13薪`） |
| `salary_min_k` / `salary_max_k` | 解析后的月薪区间（K），面议为空 |
| `company` / `industry` / `company_scale` / `company_stage` | 公司名 / 行业 / 规模 / 融资阶段 |
| `city` / `district` / `business_area` | 深圳 / 南山区 / 科技园 |
| `experience` / `degree` | 经验、学历要求 |
| `skills` / `labels` / `welfare` | 技能标签、职位标签、福利 |
| `boss_name` / `boss_title` / `boss_online` | 招聘者（个人信息，仅自用） |
| `job_id` / `security_id` / `url` | 去重键 / 详情接口键 / 原始链接 |
| `description` / `address` | JD 正文、详细地址（仅 `--detail` 时） |

## 8. 避坑与限流

1. **单关键词最多约 10 页**。想覆盖更多岗位就换关键词（`前端`、`web前端`、`React`、`Vue`、`H5`）和筛选条件，别死磕翻页。
2. **`code != 0` 或被跳 `about:blank` = 触发风控**，立刻停，隔 30 分钟以上再来。
3. **不要并发、不要高频**。默认 2.5~4.5 秒间隔已经偏保守，别再压缩。
4. 登录态会过期，采到空就刷新页面重新登录；`.browser_profile/` 含 cookie，别提交 git。
5. **DOM 工资是乱码**，别去解析 `.job-salary` 的 `textContent`，那是字体混淆后的私有区字符。

## 9. 合规边界

- 仅采集**公开招聘信息**，用于个人求职 / 技能趋势分析，不转售、不二次发布；
- 不采集、不存储招聘者私人联系方式（手机号、微信号），`boss_name` 只用于自己联系 HR；
- 不绕过账号权限、不破解验证码、不高频压站；
- BOSS直聘《用户协议》对自动化抓取有限制条款，个人低频使用风险较低，商业用途请走官方合作；
- 若要公开分析结论，建议只发布**聚合统计**（技能词频、薪资中位数），不发布原始职位数据。

## 10. 后续可以做什么

- 技能词频与共现分析（React / Vue / TS / 小程序 的占比与组合）
- 薪资 × 经验 × 公司规模 分组统计
- 每周增量采集（按 `job_id` 去重），观察岗位池变化
- 用 Obsidian Bases 把导出的 CSV 做成看板
