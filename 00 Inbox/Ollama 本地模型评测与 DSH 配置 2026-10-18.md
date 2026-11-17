# Ollama 本地模型评测与 DSH 配置（2026-10-18）

> 实测机器：RTX 3060 Laptop（6GB 显存）+ i7-11800H（8 核 16 线程）+ 32GB DDR4，Ollama 0.35.1。
> 测试时间：2026-10-17 深夜 ~ 2026-10-18 凌晨。原始数据：`.tmp-ollama-eval/results*.json`。

## 一句话结论

本机（6GB 显存）真正好用的是两个 **MoE** 模型：**LFM2.5 8B-A1B**（快、工具调用好，日常首选）和 **Qwen3.6 35B-A3B Coding**（质量最高，代码/复杂任务用，但要留足内存）。
新下载的 **Laguna XS 2.1** 模型本身很强，但 33B/20GB 超出本机舒适区，实测只有 ~8 tok/s 且加载要 37 秒，不适合日常交互。
老的 **Qwen3.5 9B**（fast / fast-long / fast-64k / qwen3.5:9b）因为 9B 稠密模型装不进 6GB 显存，只有 ~12.6 tok/s，已被 LFM2.5 全面超越。

---

## 一、你下载的模型（14 个 tag，其实只有 5 个基座）

| 基座模型 | 对应 tag | 参数 / 量化 | 说明 |
|---|---|---|---|
| Qwen3.5 9.7B 稠密 | `fast`, `fast-64k`, `fast-long`, `qwen3.5:9b-q4_K_M` | 9.7B / Q4_K_M / 6.6GB | 同一权重，只是 num_ctx 和采样参数不同 |
| Qwen3.6 35.5B-A3B MoE | `qwen3.6-coding-32k`, `qwen3.6-coding-64k`, `coder`, `coder-long`, `coder-cpu`, `qwen3.6:35b-a3b-coding` | 35.5B 总参 / 3B 激活 / Q4_K_M / 22GB | 同一权重，只是上下文与 GPU 层数不同；`coder-cpu` 是纯 CPU 版 |
| LFM2.5 8.5B-A1B MoE | `lfm2.5:8b-a1b-q4_K_M` | 8.5B 总参 / 1B 激活 / Q4_K_M / 5.2GB | Liquid AI 端侧模型，128K 上下文，推理型（自带 CoT） |
| Laguna XS 2.1 33.4B-A3B MoE | `laguna-xs-2.1:q4_K_M` | 33.4B 总参 / 3B 激活 / Q4_K_M / 20GB | Poolside 的 agentic coding 模型，SWE-bench Multilingual 63.1% |
| nomic-embed-text 137M | `nomic-embed-text` | F16 / 274MB | 向量模型，给知识库/RAG 用，不参与聊天 |

重复 tag 占用大量磁盘（20~22GB 一个），建议每个基座只留 1~2 个设置版本。

---

## 二、速度实测（同一提示词，生成 256 token，warm）

| 模型 | 上下文 | 加载耗时 | 解码速度 | 首 token 前处理 | 备注 |
|---|---|---|---|---|---|
| **LFM2.5 8B-A1B** | 4K | 14.1s | **77.4 tok/s** | 1098 tok/s | 6GB 显存基本装得下，全程 GPU |
| **LFM2.5 8B-A1B** | 16K | 12.8s | **53.6 tok/s** | — | 16K 上下文版（新做的） |
| **Qwen3.6 35B-A3B Coding** | 8K | 40.6s | **26.4 tok/s**（二次 30.6） | — | 22GB，需 ~20GB 空闲内存 |
| **Laguna XS 2.1** | 16K | 37.5s | 8.16 tok/s（上下文变长后 5.9~6.2，长输出时 3.6） | — | 20GB 权重，大部分算在 CPU 上 |
| Qwen3.5 9B（fast-64k） | 4K | 11.5s | 12.65 tok/s | 165 tok/s | 9B 稠密 > 6GB 显存，一半在 CPU |

> 结论：`fast` 系列的命名已经过时——9B 稠密模型在 6GB 显卡上只有 12.6 tok/s，比 8.5B/1B 激活的 MoE 慢 6 倍。
> Laguna 每次冷启动要 30~40 秒，生成 500 token 要 1~2 分钟，交互体验不可接受。

---

## 三、质量实测（5 个中文任务 + 工具调用）

评分：✅ 正确且符合要求；⚠️ 部分正确/格式有小问题；❌ 没完成。

| 任务 | LFM2.5 8B-A1B | Qwen3.6 35B-A3B | Laguna XS 2.1 | Qwen3.5 9B (fast) |
|---|---|---|---|---|
| 概率题（3红2蓝取2红） | ✅ 3/10，两种解法 | ✅ 3/10（需给足 token） | ⚠️ 思路正确，500 token 内没写完 | ✅ 3/10 但非常啰嗦 |
| Python 括号校验 O(n) | ✅ 栈实现正确 | ✅（思考正确，输出被截断） | ⚠️ 思路正确，被截断 | ✅ 正确 |
| 小学生解释蓝天（≤150字） | ⚠️ 内容对，但有一次用英文回答 | ✅ 中文，约 90 字，很好 | ⚠️ 被截断 | ✅ 正确 |
| JSON 抽取（只输出JSON） | ✅ 完全正确、只输出 JSON | ⚠️ 正确但包了 ```json 代码块 | ⚠️ 输出到一半（400 token 时还在想） | ✅ 正确 |
| 工具调用 get_weather(北京) | ✅ `{"city":"Beijing"}` | ✅ `{"city":"北京"}` | ✅ `{"city":"北京"}` | 未测 |
| 思考过程 | 推理写在正文里（`<think>` 标签），会污染回答 | 思考过程独立（`thinking` 字段），但很长，吃 token | 思考很长，慢 | 无 thinking |

模型公开评测（供参考）：
- **LFM2.5-8B-A1B**：IFEval 91.84、IFBench 56.47、BFCLv3 64.36、Tau² Telecom 88.07、MATH500 88.76、AIME25 42.53；主打低幻觉、指令跟随、工具链。
- **Laguna XS 2.1**：SWE-bench Multilingual 63.1%，与 Qwen3.6 35B-A3B、gpt-oss-120b 等对比的 agentic coding 模型。
- **Qwen3.6 35B-A3B Coding**：SWE 类代码任务本地最强；本机实测质量也最好。

---

## 四、推荐怎么用

1. **日常聊天 / 轻量任务 / 工具调用：`LFM2.5 8B-A1B 16K`**
   - 最快（54~77 tok/s），工具调用正确，指令跟随好，5.2GB 显存友好。
   - 缺点：知识量有限；会把推理过程写在正文里；偶尔不按语言回答（中文提问回英文）。
2. **本地代码 / 复杂推理：`Qwen3.6 35B-A3B Coding 32K`**
   - 本机质量最高的本地模型，实测 26~30 tok/s；工具调用正确。
   - 前置条件：需要 ~20GB 空闲内存（DSH 常驻后本机大约剩 12~16GB，最好关掉浏览器/其他大程序）；thinking 很啰嗦，`maxTokens` 给到 4K~8K 才够。
3. **Laguna XS 2.1：不建议在本机日常用**
   - 模型本身没问题，但 6GB 显存 + 32GB 内存带 33B/20GB 模型太勉强：~8 tok/s、加载 37s、长一点就掉到 4~6 tok/s。
   - 建议：换 24GB 显存机器、或云端跑；本机只在“不赶时间”的离线任务里用。
4. **Qwen3.5 9B（fast / fast-64k / fast-long / qwen3.5:9b）：建议淘汰**
   - 6.6GB 装不进 6GB 显存，速度只有 12.6 tok/s，质量也不如 LFM2.5。
   - 最多留一个 `fast-long` 备用，其余可删。
5. **`coder-cpu`（纯 CPU 版 35B）：建议删除**，速度极慢。
6. **`nomic-embed-text`：保留**，知识库/笔记向量检索用。

清理建议（按基座保留）：
- Qwen3.6：留 `qwen3.6-coding-32k` + `qwen3.6-coding-64k`，删 `coder`、`coder-long`、`coder-cpu`、`qwen3.6:35b-a3b-coding`（可省约 66GB）。
- Qwen3.5：留一个（建议 `fast-long` 或 `qwen3.5:9b`），删其余（每个 6.6GB）。
- Laguna / LFM2.5：各留原有 + 16K 变体（16K 变体只多一个 manifest，不额外占磁盘）。

---

## 五、DSH（DeepSeek Harness）里的配置

### 已完成的配置

1. 在 DSH 的 desktop profile 里注册了 Ollama provider（OpenAI 兼容接口）：
   - 文件：`C:\Users\guan\.dsh\profiles\desktop\cordis.patch.yml`
   - provider：`Ollama 本地`，`baseURL: http://127.0.0.1:11434/v1`
   - 模型：
     - `lfm2.5:8b-a1b-16k` — LFM2.5 8B-A1B · 本地快（16K 上下文）
     - `laguna-xs-2.1:16k` — Laguna XS 2.1 33B-A3B · 本地（16K 上下文）
     - `qwen3.6-coding-32k` — Qwen3.6 35B-A3B Coding 32K · 本地
     - `qwen3.6-coding-64k` — Qwen3.6 35B-A3B Coding 64K · 本地
2. 新建了两个 16K 上下文变体（原模型默认只有 4096 上下文，DSH 的系统提示 + 工具定义约 10K token，会被截断）：
   - `ollama create laguna-xs-2.1:16k`
   - `ollama create lfm2.5:8b-a1b-16k`
3. 修复了 profile 目录：`profiles/desktop` 里缺少 `package.json`（DSH 0.2.1 已把设置从 settings.yaml 迁到 profile patch；缺 manifest 时设置页无法保存）。补回 `package.json` 后，GUI 的设置已经可以正常写入 patch（patch 里已出现 `ui-theme`、`ui-chat` 等行）。
4. 已验证：用 DSH 自带的 `--dump-config` 组合 profile 时，`llm-pi-ai` 行被正确覆盖为 Ollama provider 配置（无 patch 报错），说明配置格式和 id 都对得上。

### 怎么在界面里用

1. 确认 Ollama 正在运行（`ollama list` 能出结果）。
2. 打开 DSH → 模型选择器 → 选 **“Ollama 本地”** → 选 `LFM2.5 8B-A1B · 本地快` 等模型。
3. 第一次调用会加载模型（LFM2.5 约 13 秒，Qwen3.6 约 40 秒，Laguna 约 37 秒），后续保持 5 分钟内免加载。
4. 如果模型选择器里没看到 “Ollama 本地”：重启 DSH 应用（配置在启动时重新读取），并确认 Ollama 在 11434 端口运行。

### 注意事项

- 16K 上下文对 DSH agent 偏小（系统+工具就占约 10K），长对话会频繁压缩；要长任务建议选 `qwen3.6-coding-32k`。
- 本机 32GB 内存，DSH 常驻后空闲约 12~16GB；跑 35B（22GB）模型前最好关掉浏览器等大内存程序。
- 本地模型不会自动下载/更新，`ollama pull` 新模型后需要按照上面的格式在 patch 里追加模型 id，或在 GUI 的“设置 → 模型”里添加。
- 本机所有测试都在 `num_ctx` 受限（4K/8K/16K）下完成；更高上下文会进一步增加内存占用并降低速度。

### 2026-10-25 修复：切到本地模型报 `No API key for provider: ollama`

- **现象**：在模型选择器里切到「Ollama 本地 → LFM2.5 8B-A1B · 本地快」后，第一轮请求立刻失败，DSH 轨迹里是 `assistant/attempt` → `finish(kind=error)`，报 `No API key for provider: ollama`（`PI_AI_ERROR`）。
- **根因**：Ollama 本身没问题（直连 `/v1/chat/completions` 返回 200）。DSH 的 `llm-pi-ai` 底层是 pi-ai 的 OpenAI 兼容实现，**即使目标是本地路由，也要求请求带一个 apiKey 或 Authorization 头**，否则在发出请求前就抛这个错。而 patch 里的 `ollama` provider 只写了 `baseURL` / `models`，没有 `apiKeyEnv`，等于没有凭据引用 → 必然报错。
- **修复**：在 `C:\Users\guan\.dsh\profiles\desktop\cordis.patch.yml` 的 `ollama` provider 下补一行：

  ```yaml
  apiKeyEnv: OLLAMA_API_KEY
  ```

  `OLLAMA_API_KEY` 已经在 `C:\Users\guan\.dsh\.credentials.yaml` 里存了一个占位值；Ollama 不校验 key，值是什么都行。
- **生效方式**：DSH 的 HMR 默认监听 profile patch 文件（`dsh-base` 里的 `hmr` 行），改完会自动重载配置；如果切模型后仍报同样的错，重启一次 DSH 即可。
- **已实测**：用 DSH 0.2.1-rc.2 自带的 CLI 起了一次 headless 会话，喂同一份 provider 配置 + `OLLAMA_API_KEY`，`lfm2.5:8b-a1b-16k` 正常返回（约 27 秒，含模型自己的思考过程）。
- 备注：LFM2.5 会把思考过程写进正文（`<think>` 标签），回答看起来啰嗦是模型行为，不是 DSH 的问题；长任务还是建议 `qwen3.6-coding-32k`。

### 2026-10-25 复测：这台 6GB 显存的机器上到底怎么选

环境：RTX 3060 Laptop **6GB**、i7-11800H、32GB DDR4、Ollama **0.40.8**（换了 runner，MoE 模型速度和 10-18 那次差别很大）、`OLLAMA_KV_CACHE_TYPE=q8_0`、`OLLAMA_FLASH_ATTENTION=1`、`OLLAMA_NUM_PARALLEL=1`、`OLLAMA_KEEP_ALIVE=30m`。

关键前提：**DSH 一轮请求的输入约 10,800 token**（系统提示 + 工具定义 + 用户消息，从会话 `usage.inputTokens` 读出），所以体感主要取决于「预填充速度（首字延迟）」而不是只看 tok/s。

实测（约 8.5K token 提示词 + 128 token 输出，冷/热各一次；下表为热态）：

| 模型 | 权重/显存驻留 | 加载 | 预填充 | 首字（冷 / 热） | 解码 | 上下文 |
|---|---|---|---|---|---|---|
| **LFM2.5 8B-A1B 32K** | 5.41GB / 4.0GB | 8.5s | 2620 tok/s | 11.9s / **3.3s** | **83 tok/s** | 32K |
| Laguna XS 2.1 33B-A3B 16K | 19.27GB / 3.68GB | 31.1s | 331 tok/s | 56.4s / 25.4s | 28.8 tok/s | 16K |
| Qwen3.6 35B-A3B Coding 32K | 21.24GB / 2.74GB | 40.1s | 273 tok/s | 71.8s / 31.7s | 29.1 tok/s | 32K |
| Qwen3.5 9B（fast-64k） | 6.34GB | 11.7s | 103.7 tok/s* | — | 12.1 tok/s | 64K |

> *fast 系列只有短提示词下的数字，实际长提示词更慢，已可淘汰。20GB 级模型有 85%~90% 的层跑在 CPU/内存上，所以加载和预填充都慢一个数量级。

结论：

1. **最快、最适合日常：LFM2.5 8B-A1B（32K 变体）**。权重基本进显存，首字 3 秒级、解码 80+ tok/s。缺点：思考过程写在正文里（`<think>`），而且 `maxTokens=4096` 经常被思考吃光、还没给出最终答案就截断（22:45 那次「你好啊」36 秒就是这种情况）。想看到干净结论可以把该模型的 `maxTokens` 调到 8192（代价是一轮 1~2 分钟），或者只拿它做短问答。
2. **质量最高：Qwen3.6 35B-A3B Coding 32K**。代码/推理明显强于另外两个，思考走独立字段（`reasoning`），正文干净；但首字 30 秒上下、一轮 1~2 分钟，且要占用 ~21GB 内存（32GB 机器上最好关掉浏览器）。适合不赶时间的硬任务。
3. **Laguna XS 2.1**：Ollama 0.40.8 下从原来的 8 tok/s 提升到 ~29 tok/s，但 16K 上下文对 DSH 太小（10.8K 提示词+输出基本贴边），加载还要 31 秒，不建议当默认。
4. **淘汰**：`fast` / `fast-long` / `fast-64k` / `qwen3.5:9b`（12 tok/s，稠密 9B 装不进 6GB 显存）；`coder` / `coder-long` / `coder-cpu` / `qwen3.6:35b-a3b-coding` 与 `qwen3.6-coding-*` 是同一权重，删 tag 也省不了磁盘（**blobs 共享，整个模型库实际只有 51.1GB**，不是标称加起来的上百 GB）。
5. **想真正升级**：换「同显存装更多参数」的模型，而不是更大的模型。2026-10 新出的 `bonsai-2:9b`（三元 9B，约 3.2GB，能全进显存）和 `qwen3.5:4b`（约 3GB）值得试，Ollama 仓库 tag 已核实存在，但**本机还没实测**，装完要再跑一遍 DSH 工具调用回归。

本次实测脚本与原始数据：`.tmp-local-eval/`（`results-load-final.json`、`quality-final.json`）。

DSH 侧改动：新建了 `lfm2.5:8b-a1b-32k`（`ollama create`，`num_ctx 32768`），并已加进 `cordis.patch.yml` 的模型列表；`agent-default-model` 目前仍是 `laguna-xs-2.1:16k`，建议改成 `lfm2.5:8b-a1b-32k`。

---

## 附：测试方法

- 速度：`/api/generate`，同一中文提示词，`num_predict=256`，`temperature=0.2`，`seed=42`，记录 `load_duration`、`eval_count/eval_duration`。
- 质量：5 个任务（概率题、括号校验、中文解释、JSON 抽取、高原煮饭），`num_predict` 400~2500，人工核对正确性与格式。
- 工具：`/api/chat` 传入 `get_weather` 工具定义，检查是否返回 `tool_calls`。
- 原始结果：`.tmp-ollama-eval/results.json`（LFM2.5 / fast-64k）、`results3.json`（16K 变体 + qwen3.6）、`results4.json`（qwen3.6 质量）。
