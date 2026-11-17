---
title: Qwen3.8-Flash-Next 在 6GB 笔记本上的部署评估
type: report
date: 2026-11-08
tags:
  - LLM
  - 本地部署
  - airllm
  - Qwen
  - 显存
---

# Qwen3.8-Flash-Next 在 6GB 笔记本上的部署评估

> 评估对象：[lyogavin/airllm](https://github.com/lyogavin/airllm) × [Qwen/Qwen3.8-Flash-Next](https://huggingface.co/Qwen/Qwen3.8-Flash-Next)
> 本机：RTX 3060 Laptop **6GB** / i7-11800H / **32GB** DDR4 / Win11 / Python 3.11 / 单盘最大空闲 **188.6GB**
> 方法：读完 airllm 4.0.0 源码 + 官方权重清单 + 第三方实测，再逐项对照本机实测

---

## 0. 结论先行

**airllm 的「6GB 能跑」只说了显存，没说另外两项：~360GB 磁盘、64GB 内存。** 这两项你这台机器都不满足，而且源码核对后发现：

| 硬门槛 | airllm 要求 | 本机实际 | 判定 |
|---|---|---|---|
| 磁盘（切层后硬地板） | **354 GB**（源码 `utils.py`） | 单盘最大 188.6 GB | ❌ 差 165GB |
| 磁盘（切层峰值） | 462 GB（开 delete_original）/ 714 GB（不开） | 同上 | ❌ |
| 显存 | 5.95 GB（4090 实测，非 6GB 卡） | 空闲 **4.65 GB**（桌面已占 1.34GB） | ❌ 大概率 OOM |
| 内存 | 64 GB | 31.7 GB | ⚠️ 不是硬 OOM 点，但会放大慢 |
| 速度（设计上限） | 整层流式，每 token 读 **~230 GiB** | 实测有效带宽 ~0.3 GB/s | ❌ **≈13 分钟/token** |

**一句话：这台机器上不能按 airllm 的方式跑 Flash-Next。** 想本地跑，唯一有机会出字的是 **llama.cpp / Strata + Q2_0 量化（下载 66~76GB，预计 1~5 tok/s）**；想用好 Flash-Next，走**云 API（$0.16/$0.47 每百万 token）**比本地折腾便宜得多。

---

## 1. airllm 到底怎么「用 6GB 跑 125B」

它没有变魔术，做的是**磁盘换显存**：

1. 把模型按层切开存到磁盘；
2. 推理时**每次只把一层搬上 GPU**，算完就丢掉；
3. 所以 **显存 ≈ 最大单层**，而不是整个模型。

代公式：

```
显存需求  ≈ 单层最大字节数
速度上限  ≈ 每秒磁盘读取字节数 / 每 token 需要读的字节数
```

对这个模型：

- 每层 MoE：512 专家 × 3 矩阵 × 2560 × 640 × 2B ≈ **5.14 GB（4.79 GiB）**（每层约 2.57B 参数）
- 48 层 → 每 token 要过 **230 GiB** 的层数据（不含 51B n-gram 表的少量随机查表）
- 所以 5.95GB 显存 ≈ 一层 4.79GiB + CUDA context/激活 ≈0.9GB —— **不是** 留了余量给 6GB 卡的桌面占用
  （KV cache 只有 ~13MB、PLE 注入 ~3MB、视觉塔 0.1~0.2GB，都压不出多少空间）

关键：源码里 `qwen4_exp` **没有实现 per-expert 流式**（`airllm_qwen4_exp.py` 没有 `expert_prefix`，512 个专家是打包的 3D 张量，注释明说 Kimi 式 per-expert hook 不适用）。也就是说**本来只用到 10/512 个专家（≈4.7GB/token），但它会把整层读进来**。

> 参考量级：airllm 自己的 Windows 实测（issue [#364](https://github.com/lyogavin/airllm/issues/364)、[#396](https://github.com/lyogavin/airllm/issues/396)）里，**3B 模型**是 10.9~28.6 秒/token；3090 上跑 20B 一次查询约 30 分钟（[#374](https://github.com/lyogavin/airllm/issues/374)）。仓库里**没有任何 Flash-Next 的 tok/s 数据**。

---

## 2. 本机体检（实测）

| 项目 | 实测值 | 备注 |
|---|---|---|
| GPU | RTX 3060 Laptop **6144 MiB** | `nvidia-smi` |
| 桌面已占显存 | **1342 MiB**（空闲 4653 MiB） | 2560×1440 屏 + 浏览器等；WDDM 不会全吐出来 |
| 内存 | 31.7 GB，当时可用 14.3 GB，提交上限 51.7 GB | 页面文件只在 C 盘 20GB |
| 磁盘空闲 | C 58.8 / D 63.3 / E 77.5 / **F 188.6** GB | 两块 NVMe（477GB + 466GB） |
| 盘速（F:） | 顺序写 **916 MB/s**，读 ~2.6 GB/s（含缓存，冷读约 1.5~2） | 顺序写是 airllm 切层时的真实约束 |
| Python/torch | 3.11.3 / **torch 2.8.0+cpu** | 全局 torch 是 CPU 版，GPU 推理得重装 CUDA 轮子 |
| 网络 | huggingface.co 直连超时；**hf-mirror.com / ModelScope 可用** | 权重清单从 hf-mirror API 拉取 |

---

## 3. 三道门槛逐项对照（源码级）

### ① 磁盘：354GB 是硬地板，不是 360GB「大概」

airllm 切层后的产物：每个模块一个文件。**已经 Source 核对**（`air_llm/airllm/utils.py`）：

- 131 个原始 shard 里只有 `lm_head` 能硬链接，其余 129 个都要真复制；
- 51B n-gram 表（PLE）会被剥出来重写成 **95.37GiB** 的 `.mmap` 文件 —— 等于再复制一份；
- 切完的分片目录 ≈ **329 GiB / 354 GB**（只省掉 5GB 的 MTP）；
- `delete_original=True` 边切边删，但写 PLE mmap 那一刻峰值 ≈ **430 GiB / 462 GB**；不开则 ≈ **665 GiB / 714 GB**。

→ 本机 F 盘整块才 316GB，**即使全清空也放不下 354GB 的分片**。这一步就结束了。

> 另外：`delete_original=True` 在**没有符号链接权限的 Windows 上必崩**（`utils.py:513` 先删 `path` 再删 `realpath`，本机 HF 缓存是真副本，两次路径相同 → `FileNotFoundError`）。团队已在任务机上用假 checkpoint 复现。

### ② 显存：5.95GB 是 4090 上的数字，6GB 卡是另一回事

- 单层 4.79GiB + CUDA context/激活 ≈ 5.95GB；
- Windows 桌面本身占 1.0~1.5GB（本机实测 1.34GB），6GB 卡实际可用约 5.2~5.6GB；
- 结果：**要么 OOM，要么掉进 shared memory 卡死**（就是 issue #396 里长 prompt 显存 O(n²) 到 10.66GiB 的那种）。
- 用 `compression='4bit'` 也救不了：量化时要把整层 5GB `.cuda()` 再压，6GB 卡在切层阶段就炸；而且 **PLE 表永远 bf16 95.37GiB，压不掉**。

### ③ 速度：设计上就是「分钟级/token」

| 场景 | 每 token 读盘 | 本机实测有效带宽 0.3GB/s | 理想 7GB/s NVMe |
|---|---:|---:|---:|
| airllm 整层流式（现状） | 230 GiB | **≈13 分钟/token** | ≈33 s/token |
| 如果实现了 per-expert 流式 | ≈4.7 GiB | ≈16 s/token | ≈0.7 s/token |

第二行是「本来可以」的世界，但这个架构在 airllm 里没实现。对比本机现有基线：**LFM2.5 8B-A1B 83 tok/s、Qwen3.6 35B-A3B 29 tok/s**（`00 Inbox/Ollama 本地模型评测与 DSH 配置 2026-10-18.md` 实测）。

---

## 4. 三条可选路线（按推荐度）

| 路线 | 磁盘 | 内存 | 显存 | 预期速度 | 推荐 |
|---|---|---|---|---|---|
| **云 API**：Qwen3.8-Flash（= 本模型生产版） | 0 | 0 | 0 | 网络 | ★★★★★ |
| 维持 Ollama 基线（LFM2.5 / Qwen3.6） | 现成 | 现成 | 现成 | 83 / 29 tok/s（实测） | ★★★★ |
| Strata / llama.cpp + **Q2_0** 量化（本地 Flash-Next 唯一机会） | 下载 66~76GB ✅ | 34GB 专家 → 建议 44GB+ ⚠️ | 6GB 未验证 ⚠️ | 1~5 tok/s【推算】 | ★★ |
| airllm + BF16 | 354GB 起 / 峰值 462~714 ❌ | 64GB ❌ | 5.95GB ❌ | 13 分钟/token ❌ | ✗ |

### 为什么 Strata 比 airllm 靠谱

airllm 是「整层搬」，Strata/llama.cpp 是**专家级缓存**：只把当前 token 路由到的 10/512 专家读进来，其余常驻 RAM 或 SSD。模型同样是 125B+51B，但每 token 的 I/O 从 230GiB 降到 ~0.7GB。代价是需要显卡和内存兜住专家表（Strata 官方门槛：32GB PC 需 24GB 显卡；12~16GB 显卡只跑 Coder 版），**6GB 卡不在任何已发布验证范围**。

实测参照（Strata 官方社区跑分，Windows）：RTX 3060 **12GB** + 64GB RAM，Q2_0 → 45 tok/s（128 ctx）/ 37 tok/s（260K ctx）；RTX 4070 12GB + 32GB → 48 tok/s。→ **12GB 是当前本地跑 Flash-Next 的实际门槛。**

### 云 API 价格（真·兜底）

- 阿里云百炼 / Qwen Cloud：**输入 $0.16 / 输出 $0.47 每百万 token**，默认 100 万上下文（[官方 blog 转载](https://developer.aliyun.com/article/1759085)）
- OpenRouter：`qwen/qwen3.8-flash` **$0.15 / $0.47**，1M 上下文
- 换算：本地 29 tok/s 跑 100 万输出 token 要 9.6 小时；云端约 **$0.47（≈3.4 元）**

---

## 5. 如果还是想亲手试

### 路线 A：airllm（需要先解决硬件，`scripts/` 里有现成脚本）

前置条件（缺一不可）：
1. **外接 ≥1TB SSD**（切层峰值 462GB，留余量）——本机内置盘怎么清都不够；
2. 页面文件挪到大盘并设到 **64~96GB**（现在是 C 盘 20GB）；
3. 装 **CUDA 版 torch**（现在是 2.8.0+cpu）——脚本会自动装。

另外两个已经踩过的坑，脚本里都规避了：
- `transformers` 必须 **≥5.16**（`qwen4_exp` 从 5.16 起才进 pip 正式版；README 里「必须 git 版」的说法已过时，5.15.1 及以下没有这个模块）；
- `delete_original=True` 在无符号链接权限的 Windows 上会崩，脚本默认关掉。

然后：

```powershell
.\scripts\setup_airllm_windows.ps1 -Root 'X:\airllm'      # 装环境（约 3GB 下载）
# 先冒烟：0.5B 小模型，确认 Windows 上切层+推理链能跑
& 'X:\airllm\venv\Scripts\python.exe' .\scripts\airllm_smoke_test.py
# 再上大的（会下载 360GB；脚本默认只做预检，--i-know 才真跑）
& 'X:\airllm\venv\Scripts\python.exe' .\scripts\airllm_flash_next.py --root 'X:\airllm' --i-know
```

预期：下载数小时 + 切层 1~2 小时，然后 **33 秒 ~ 13 分钟/token**（取决于盘）。适合「我就想看它出字」，不适合用。

### 路线 B：Strata + Q2_0（本机唯一可能出字且能忍的本地路线）

```powershell
# 1) 装 Strata（MIT，Windows 安装包）：https://github.com/Niko1221/Strata/releases/latest
# 2) 先看计划（不下载、不改盘；型号名以这里列出的为准）：
strata launch --family qwen --model q2_0 --plan
# 3) 按计划执行（会下 66~76GB + 6GB MTP 草稿层）
strata launch --family qwen --model q2_0 --yes --no-tui
```

选型：内存只有 32GB，**别选 IQ3_S（专家 50GB）**，从 **Q2_0（专家 34GB）** 或 **IQ2_XS（35.5GB）** 开始；它会自动进 low-RAM 模式，专家从 SSD 读。
预期：1~5 tok/s【推算，6GB 卡无任何实测】，加载/首字要几十秒到几分钟。

### 路线 C：把 Qwen3.8-Flash 接进 DSH（最省事）

百炼 / OpenRouter 拿 key → 在 `C:\Users\guan\.dsh\profiles\desktop\cordis.patch.yml` 加一个 OpenAI 兼容 provider（参考现有 `ollama` 那段，`baseURL` 换掉、`apiKeyEnv` 指向新 key）→ 设置里选 `qwen3.8-flash` 即可。参考同目录 `Ollama 本地模型评测与 DSH 配置` 笔记里 provider 的写法。

---

## 6. 我在这台机器上实际验证了什么（不是纸面推演）

| 验证项 | 结果 |
|---|---|
| airllm 仓库自带 `tests/test_qwen38_flash_next_split.py` | **Windows 上 16/16 通过**（8.1s，含 PLE 分离、mmap、硬链接判定）→ 切层代码本身没坏 |
| 端到端冒烟：Qwen2.5-0.5B-Instruct（CPU torch） | 切层 + generate **跑通**，27 个层模块，下载 103s、加载 124s，生成 4 token 用 13.5s = **3.38 s/token**（CPU），输出正确 |
| 由冒烟外推有效带宽 | ≈0.3GB/s（0.5B 每秒要读约 1GB）⇒ 230GiB/token 约 **13 分钟/token**；哪怕盘真跑到 2GB/s 也要 ~2 分钟/token |
| `torch.UntypedStorage.from_file(shared=True)` + bf16 视图 | 本机 OK（PLE mmap 依赖它） |
| `os.link` 硬链接 | NTFS 同盘 OK |
| `delete_original=True` | **本机复现必崩** `FileNotFoundError`（无 symlink 权限时 HF 缓存是真副本） |
| 磁盘/显存/内存/盘速 | 全部实测（见第 2 节） |

没做的：**没有下载 360GB 权重**（磁盘物理上放不下），所以没有 Flash-Next 的真实 tok/s —— 但由上面 0.3GB/s 的实测带宽和 230GiB/token 的读量，速度结论已经不需要再测了。

---

## 7. 这次核查里值得记住的几条

1. **宣传语里没写的门槛才是真门槛**：airllm 说 6GB 显存，但同一段里写着 64GB 内存 + 360GB 盘；后面两项才是决定成败的。
2. **「能跑」≠「能用」**：airllm 能把 671B 塞进 12GB，代价是每 token 把模型从磁盘读一遍；对 6B 激活的 MoE，专家级缓存（llama.cpp/Strata）比整层流式快两个数量级。
3. **量化救不了所有东西**：Flash-Next 的 51B n-gram 表（95GiB）在 airllm 里永远 bf16，而且 `compression=4bit` 在 6GB 卡上连切层都过不去。
4. **Windows 显存更紧**：WDDM 桌面常驻 1~1.5GB，标称 6GB 的卡实际能给模型 5.2~5.6GB；「5.95GB 峰值」这种数字在 6GB 笔记本上等于不可用。
5. **airllm 在 Windows 没有官方支持声明**，社区实测全是 10~30 s/token（3B 模型）。

---

## 8. 参考

- airllm 仓库：https://github.com/lyogavin/airllm （源码核对于 4.0.0，HEAD `d9f0025`：`auto_model.py`、`airllm_qwen4_exp.py`、`utils.py`）
- airllm Windows 实测 issue：[#364](https://github.com/lyogavin/airllm/issues/364) / [#396](https://github.com/lyogavin/airllm/issues/396) / [#374](https://github.com/lyogavin/airllm/issues/374) / [#309](https://github.com/lyogavin/airllm/issues/309)
- 模型卡与权重清单：https://huggingface.co/Qwen/Qwen3.8-Flash-Next （144 文件 / 335.3 GiB / 131 分片）
- vLLM 部署 recipe（官方口径的硬件要求）：https://recipes.vllm.ai/Qwen/Qwen3.8-Flash-Next
- Qwen3.8-Flash 发布与价格：https://developer.aliyun.com/article/1759085
- Strata（本地跑 Flash-Next 的现实方案）：https://github.com/Niko1221/Strata ｜ [硬件选型表](https://github.com/Niko1221/Strata/blob/main/docs/MODELS.md)
- GGUF 量化（Q2_0 61.9GiB）：https://huggingface.co/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF
- 本机复现脚本：`scripts/setup_airllm_windows.ps1`、`scripts/airllm_flash_next.py`、`scripts/airllm_smoke_test.py`

---

> [!note] 数据来源与时效
> 显存/内存/磁盘/盘速为本机实测（2026-11-08）；模型体积取自 hf-mirror API 实际求和；airllm 行为取自 4.0.0 源码；
> 第三方速度标注了【实测】或【推算】。标【推算】的数字没有对应硬件上的直接测量，别当承诺用。
