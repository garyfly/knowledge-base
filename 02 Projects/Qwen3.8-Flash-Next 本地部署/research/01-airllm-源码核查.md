# airllm × Qwen/Qwen3.8-Flash-Next 源码核查（Windows / RTX 3060 Laptop 6GB / 32GB RAM）

核查对象：`https://github.com/lyogavin/airllm`，git clone HEAD `d9f0025`（2026-11-08 06:12 UTC）；
`air_llm/setup.py:18` 版本 `4.0.0`；PyPI 上 airllm 最新正式版也是 `4.0.0`（2026-09-05 发布）。
本机环境：Windows 11 26200 / i7-11800H / 32GB / Python 3.11.3（`D:\Dayuse\python\python3.11\python.exe`）/ torch 2.8.0+cpu / 无 CUDA。

标注约定：**【证实】**=读了源码或在本机跑出结果；**【推测】**=由代码/config 推算、未在真实权重上验证。

---

## 0. 结论速览（先给结论）

| 问题 | 结论 | 依据 |
|---|---|---|
| 支持的类 | `Qwen4ExpForConditionalGeneration` → `AirLLMQwen4Exp`；都走 `AutoModel.from_pretrained` 自动分派 | 【证实】`auto_model.py:17-27,52-60`；`airllm/__init__.py:36` |
| 流式粒度 | **整层流式（whole decoder layer）**，512 个 experts 一起进显存；**没有** per-expert 流式 | 【证实】`airllm_qwen4_exp.py:50-62` 无 `expert_prefix`；`airllm_base.py:795-797` |
| 每 token 磁盘读 | ≈ 48 层 × 4.8GiB ≈ **230GiB/token**（不含 PLE 的少量随机 gather） | 【证实：层大小按 config 计算；流式逻辑代码证实】 |
| 磁盘峰值 | 切层产物 **≈329GiB（≈354GB）**；`delete_original=True` 峰值 **≈430GiB（≈462GB）**；默认（不删原件）**≈665GiB（≈714GB）** | 【证实】代码 + 真实 index/API 尺寸 |
| delete_original | 边切边删（逐 shard），但 **Windows 上必崩** `FileNotFoundError` | 【本机复现】`utils.py:507-513,737-741` |
| 51B PLE 表 | `torch.UntypedStorage.from_file` 文件 mmap（非常驻 RAM）；代码里**没有**任何内存硬检查 | 【证实】`utils.py:312-322,325-343`；注释见 `airllm_base.py:717`、`utils.py:352` |
| 5.95GB VRAM | 单层权重 ≈4.8GiB + CUDA context/激活 ≈0.9GB；KV cache ~13MB、PLE 注入 ~3MB，可忽略 | 【推测：按 config 反推，与 README 实测吻合】 |
| compression | 通用代码会执行，但 **PLE 永远不压缩**；且必须 bitsandbytes+CUDA（`.cuda()`），本机 CPU torch 完全不可用；6GB 卡切层时就会 OOM | 【证实】`utils.py:486-505,702-706,491,498`；`airllm_base.py:131-133` |
| transformers | 必须 **>=5.16.0** 的正式版（5.15.1 无、5.16.1 有 `models/qwen4_exp/`）；README 的"必须 git 版"已过时 | 【本机实测 wheel 内容】 |
| 仓库内实测速度 | **没有任何 tok/s / 耗时数字**；只有 VRAM 宣传值 | 【证实】README/docs/tests/py 全文 grep |
| 本机能否跑 | **不能**：磁盘（354GB > 单盘最大 188.6GB）、显存（5.95GB > 6GB 卡可用值）、速度（分钟级/token）三重否决 | 综合 |

---

## 1. 做法与装包情况

- `D:\Dayuse\python\python3.11\python.exe -m venv .tmp-airllm\venv` 成功（pip 22.3.1）。
- **pip 装 airllm 失败**：`pip download/install` 连不上（本机 git 全局配了 `http.proxy=http://127.0.0.1:7897`，该代理已死；pip 请求同样被卡住，长时间无输出后我终止）。`git clone` 加 `-c http.proxy= -c https.proxy=` 绕过代理后成功（见 `.tmp-airllm/airllm-src`）。
- 因此**没有 `pip show airllm` 的运行时版本号**；版本以源码为准：`air_llm/setup.py:18` = `4.0.0`，PyPI JSON 最新 = `4.0.0`。
- 依赖 wheel 全部从 `files.pythonhosted.org` 直连下载后解包到 `.tmp-airllm/deps`（transformers 5.16.1 / accelerate 1.15.0 / huggingface_hub 1.9.2 / tokenizers 0.23.3 / safetensors 0.8.0），不污染全局环境。
- 模型 config/index 从 hf-mirror 取（`hf-mirror.com/Qwen/Qwen3.8-Flash-Next/{config.json,model.safetensors.index.json}`，另取 HF API `?blobs=true` 拿每个 shard 的精确字节数）。**没有下载任何权重**。

---

## 2. (a) 走哪个类 / 怎么切层 / 每层多大 / 存哪

### 2.1 分派链【证实】
1. `AutoModel.get_architecture()` 读 `AutoConfig.architectures[0]`（`auto_model.py:42-50`）。该模型 config 的 `architectures` = `["Qwen4ExpForConditionalGeneration"]`（config.json 第 2-4 行）。
2. `ARCH_OVERRIDES["Qwen4ExpForConditionalGeneration"] = "AirLLMQwen4Exp"`（`auto_model.py:17-27`），`get_module_class` 返回它（`auto_model.py:52-60`）。
3. `airllm/__init__.py:36` 导出 `AirLLMQwen4Exp`；实现文件 `air_llm/airllm/airllm_qwen4_exp.py:17`。
4. 因为 architecture 名里含 `ConditionalGeneration`，建空模型时会先试 `AutoModelForImageTextToText`（`airllm_base.py:275-285`）；transformers 5.22 的 auto 映射里 `qwen4_exp → Qwen4ExpForConditionalGeneration`（`transformers/models/auto/modeling_auto.py:1225`）。

### 2.2 模块布局【证实】
`airllm_qwen4_exp.py:48-62` 的 `layer_names_dict`：

```
embed  = model.language_model.embed_tokens
layer_prefix = model.language_model.layers        # 48 层
norm   = model.language_model.hyper_connection_mixer   # 没有最终 RMSNorm
lm_head= lm_head
resident = ['model.visual']                        # 视觉塔常驻（<1GB）
cpu_resident_marker = 'ple.ple_embedding.ngram_embedding'
```

真实 index.json 验证：131 个 safetensors 分片、1658 个张量、PLE 实际路径为 `model.language_model.layers.1.ple.ple_embedding.ngram_embedding`（config `ple_layer_ids:[2]`，代码按 `layer_idx+1` 判定，见 transformers `modeling_qwen4_exp.py:1262-1263`）。

### 2.3 切层器怎么切 / 存哪【证实】
- 入口 `find_or_create_local_splitted_path`（`utils.py:809-886`）：先只下非权重文件（`ignore_patterns=['*.safetensors','*.bin']`，`utils.py:851-853`），再**逐 shard 按需下载**（`utils.py:748-751,767-770`），在 checkpoint 目录下建 `splitted_model/`（`utils.py:557-560`；可用 `layer_shards_saving_path` 改位置）。
- 每个模块写一个文件 `<module>.safetensors`（`utils.py:787-791`，`persist/safetensor_model_persister.py`）。
- 一个 checkpoint shard 若"整片只装一个模块"，则**硬链接**过去而不复制（`utils.py:654-672,715`，`link_or_copy_file` `utils.py:517-541`）。真实布局里 131 个 shard 只有 `lm_head`（1.18GiB）满足，其余 129 个都是多模块共享 → **必须复制**。

### 2.4 每层多大【计算，与总量自洽】
config（hf-mirror config.json）：48 层、hidden 2560、512 experts、`num_experts_per_tok`=10、`moe_intermediate_size`=640、`shared_expert_intermediate_size`=640、24 heads × head_dim 256、KV heads 2、`ple_embed_dim`=2560。

- 每层 MoE：512 × (2×640×2560 + 640×2560) = **2,516,582,400** 参数 + shared expert 4.9M + 注意力/DeltaNet/hyper-connection 约 40~50M ⇒ **≈2.57B 参数/层**。
- bf16 ⇒ **≈4.79GiB（≈5.14GB）/层**。
- 全模型：48×2.57B + PLE 51.2B + embed 0.636B + lm_head 0.636B + mtp(~2.57B) + vision(~0.4B) ≈ **179B 参数**，与 index 的 `total_size` 359,999,963,128 B（=335.28GiB，bf16 ⇒ 179.8B 参数）一致，误差 <1%。**尺寸自洽，可信。**

### 2.5 流式粒度：整层，不是 per-expert【证实，关键】
- `AirLLMQwen4Exp.layer_names_dict` 里**没有 `expert_prefix`**（`airllm_qwen4_exp.py:50-62`）。
- `_setup_expert_streaming` 只有在 `layer_names_dict.get('expert_prefix')` 存在时才工作，否则直接 return（`airllm_base.py:791-797`）。
- 实现注释也明确写了："Packed MoE experts are 3D tensors on a single module, not a `ModuleList`, so Kimi-style per-expert module hooks do not apply. **A whole MoE layer is a few GB of bf16; that is what streams today.**"（`airllm_qwen4_exp.py:39-41`）
- 流式发生在每个 decoder layer 的 forward pre-hook：`_pre_hook` 把整层权重搬上 GPU，`_post_hook` 再 `to('meta')`（`airllm_base.py:889-919`）；prefetch 只是把"下一层"提前读到 CPU（`airllm_base.py:900-904`）。

**推论【推测，但幅度很硬】**：每生成 1 token 要过全部 48 层，每层都重新从磁盘搬 ≈4.79GiB ⇒ **≈230GiB 磁盘读 / token**；没有 MoE 的 10/512 稀疏性收益。这会直接决定速度量级（见 §7）。

---

## 3. (b) 磁盘峰值到底几倍

### 3.1 真实原件尺寸【证实】
- `model.safetensors.index.json` 的 `metadata.total_size` = **359,999,963,128 B = 360.00 GB = 335.28 GiB**。
- HF API（`?blobs=true`）实测 131 个 shard 合计 360,000,192,888 B；单 shard 约 3.13GiB；**PLE 表由 128 个 `shard_N.weight` 组成（每个 745MiB），分布在 shard 00005~00037**。

### 3.2 切层产物尺寸【证实 + 计算】
- PLE 表：`320,001,536 × 160 × 2B` = **95.37GiB（102.4GB）**（config 推算，且与代码注释 "~102GB of bf16" 一致，`airllm_qwen4_exp.py:33`、`airllm_base.py:717`）。
- 切层时 PLE 的 128 个 shard 被**流式写成新文件** `<...>.mmap`（`utils.py:239-306`，create 逻辑 `utils.py:700-706`），**不写 safetensors**，且不再属于父层（父层载入时被过滤：`utils.py:757-759,775-777`）。
- `mtp.*` 被丢弃（`utils.py:612` 之后 `layer_owner` 不认领 + 测试 `tests/test_qwen38_flash_next_split.py:229-235` 断言）。
- 其余模块：129/131 shard 需复制（`lm_head` 硬链接省 1.18GiB）。
- ⇒ **最终切层目录 ≈ 335.28 − mtp(~4.8) ≈ 330.4GiB，扣掉硬链接的 1.18 ⇒ 新占 ≈329GiB ≈ 353.5GB。**

### 3.3 peak 时机【证实】
`delete_original=True` 是**每前进一个 shard 就删上一个**（`utils.py:735-742`，`shard != 0` 才删；单文件模型在最后删 `utils.py:800-805`）。但 **PLE 的 mmap 必须在原 shard 还在时写出**（`persist_ngram_mmap` 从原 shard 读，`utils.py:239-306`，且此分支 `continue` 不推进 shard 游标）。所以 mmap 落盘那一刻：

```
剩余原件(≈326GiB) + 已切产物(≈10GiB) + 新 mmap(95.4GiB) ≈ 430GiB ≈ 462GB
```

切完后：`330GiB` 左右（只留切层副本是可以的，但原件的删除会因 §3.4 在 Windows 上崩）。

`delete_original=False` 时：先过 `check_space`，它要求 `free + 已有切层 ≥ 原件大小`（`utils.py:463-484`，4bit 分支还有公式方向错误 `total/0.2813`，`utils.py:473-474`），峰值 ≈ **335.28 + 329 ≈ 665GiB ≈ 713GB**。

### 3.4 Windows 致命坑：`delete_original=True` 必崩【本机复现】
`remove_real_and_linked_file`（`utils.py:507-513`）：

```python
if (os.path.realpath(to_delete) != to_delete):   # Path vs str 恒不等
    targetpath = os.path.realpath(to_delete)
os.remove(to_delete)     # 删掉普通文件/符号链接
if (targetpath): os.remove(targetpath)   # 若 targetpath 就是同一个真实文件 → FileNotFoundError
```

只有当原件是 **symlink**（HF 缓存正常时 snapshot 里是 symlink → realpath 指向 blob）才不炸。本机 HF 缓存**不支持 symlink**（冒烟测试里 huggingface_hub 明确警告：*"your machine does not support them ... Caching files will still work but in a degraded version"*），文件是真副本 → `realpath == path` → 第二次 `os.remove` 抛 `FileNotFoundError`。

我在本机用仓库自带假 checkpoint 直接复现了：

```
deleting original file: ...\model-00001-of-00003.safetensors
FileNotFoundError: [WinError 2] ...: '...\model-00001-of-00003.safetensors'
  at utils.py:513 (called from utils.py:741)
```

⇒ **在这台 Windows 上，`delete_original=True` 会在切第一个可删 shard 时中断**；要么开 Windows 开发者模式/管理员让 HF 建 symlink，要么放弃自动删原件（那就变成 2× 峰值）。**README 说 "`delete_original=True` reclaims the originals after the split" 在这里不成立。**

---

## 4. (c) 51B n-gram embedding（PLE）怎么处理

- 表结构：`nn.Embedding(320,001,536, 160)`，bf16 = 95.37GiB（`utils.py:352` 注释写 "~191GB of empty fp32"，即 fp32 建表时 204.8GB）。
- **构建期**：transformers/accelerate 正常建模型会在 CPU 先 alloc 191GB fp32 → 64GB 机器直接 OOM；airllm 用 `_force_meta_embeddings()` 把 `nn.Embedding.__init__` 临时改成 `device='meta'`（`utils.py:346-367`，`airllm_base.py:305` 使用），之后再用 `MmapEmbedding` 替换。**这是"64GB 依据"的第一层含义**。
- **运行时**：`open_ngram_mmap_table` 用 `torch.UntypedStorage.from_file(path, shared=True, nbytes=...)` + `tensor.set_(storage,...)` 建 2D bf16 视图（`utils.py:312-322`）；`MmapEmbedding` 把 `.weight` 换成 **0 大小 Parameter**，forward 直接 `nn.functional.embedding(input, self._table)`（`utils.py:325-343`）。表**不是** Parameter/buffer，所以父层 `to('meta')` 不会把它赶走（注释 `utils.py:328-331`；`_post_hook` 也因此走逐参数驱逐分支 `airllm_base.py:906-917`）。
- transformers 侧配合：`_no_placement_params = ["ple.ple_embedding.ngram_embedding.weight"]`（transformers 5.22.2 `modeling_qwen4_exp.py:1324`）；gather 在表所在 device（=CPU）做，结果 `.to(ngram_ids.device)` 上 GPU（同文件 `:1172-1174`）⇒ **VRAM 只占几 MB**。
- **代码里没有任何硬性内存检查/阈值**（无 psutil、无 available-memory 判断）。"64GB 够"只出现在注释：
  - `airllm_base.py:717`："Flash-Next's n-gram table is ~102GB bf16. We mmap it from disk so a 64GB host can still run"；
  - `utils.py:352`："…~191GB of empty fp32 -- which OOMs a 64GB host…"；
  - `airllm_qwen4_exp.py:33`："file-mmaps it on the host, so ~102GB of bf16 never lands in GPU VRAM or anonymous RAM"。
- **风险路径（非默认，但要防）**：如果 split 目录里的 `.mmap`/`.mmap.json` 不存在（旧版本切的层、或手工删过），`_load_cpu_resident_modules` 会退化成 `load_merged_ngram_embedding` = **95GiB 匿名内存**（`airllm_base.py:723-743`，`utils.py:174-211`）→ 32GB 必 OOM。所以必须用**同一版本** airllm 做切层。
- 本机 32GB 结论：mmap 是文件页（可回收），**不会因 PLE 本身 OOM**；但每 token 的 CPU gather 会命中 95GiB 文件的随机页 → 大量缺页/磁盘随机读。

---

## 5. (d) 5.95GB 显存由什么组成 / 能否压低

【推测：由 config 与代码路径反推，与 README 的 4090 实测 5.95GB 吻合】

| 组成 | 估算 | 依据 |
|---|---|---|
| 当前 decoder layer 全部权重（512 experts + shared + attn/hc） | **≈4.79GiB ≈ 5.14GB** | §2.4；`airllm_base.py:889-898` 整层上卡 |
| CUDA context / cuBLAS workspace / 碎片 | ≈0.5–1GB | 常规经验 |
| 激活（seq 512、hidden 2560、10 experts×640） | ≈0.05–0.2GB | 推算 |
| KV cache（12 个 full-attention 层，2 KV heads ×256，512 上下文） | **≈13MB** | 12×2×2×256×512×2B |
| PLE 注入（batch×seq×16 heads×160） | **≈3MB** | `modeling_qwen4_exp.py:1172-1174` |
| 视觉塔常驻（`model.visual`，`resident`） | ≈0.1–0.2GB | `airllm_qwen4_exp.py:55-57`、`airllm_base.py:673-687` |

**能压的**：`max_new_tokens` 只影响 KV（这里本来就只有 ~13MB，压了没用）；`compression='4bit'` 理论上把 5.14GB 权重压到 ≈1.4GB，但见 §6；`fp8` **不是 airllm 的 compression 选项**（只接受 `'4bit'/'8bit'`，`airllm_base.py:106-107`），只能靠预量化 checkpoint（本仓库只有 Kimi K3 走这条）。
⇒ **在 6GB 卡上没有任何现实手段把"单层 5.14GB + context"压进 6GB**（Windows 显示器/合成器还要占 0.3–1GB，3060 Laptop 实际可用通常 5.2–5.6GB）。**大概率直接 OOM 或掉进 WDDM shared memory 导致假死。**

---

## 6. (e) compression='4bit'/'8bit' 对该架构是否生效

- **没有架构级跳过**：`compress_layer_state_dict`（`utils.py:486-505`）/`uncompress_layer_state_dict`（`utils.py:104-132`）是通用路径，`split_and_save_layers` 对所有层调用（`utils.py:785`），读层时统一解压（`utils.py:444-459`）。
- **但对 PLE 完全无效**：split 循环遇到 `cpu_resident_marker` 直接 `continue`（`utils.py:700-706`）→ PLE 永远是 bf16 95.37GiB 的 `.mmap`，4bit/8bit 压不到它。
- **必须 bitsandbytes + CUDA**：`utils.py:491,498` 直接 `v.cuda()` 再 quantize；`airllm_base.py:131-133` 缺 bnb 直接 raise。本机 torch 是 **+cpu**，`compression` 一行都跑不了。
- **即便有 CUDA，6GB 卡切层就会 OOM**：切层时要把单个 packed-expert 张量（≈5.03GB）整体 `.cuda()` 再量化，还要 +nf4 输出（≈1.3GB） ⇒ 峰值 >6GB。
- **压缩后磁盘估算**：4bit ≈ 95.37 + 0.2813×(330.4−95.37) ≈ **161.5GiB（≈173GB）**；8bit ≈ **213GiB（≈229GB）**。（`utils.py:473-476` 的 4bit `check_space` 公式方向写反成 `total/0.2813`，实际会要求 3.55× 空闲，属 bug。）
- **压缩后显存**：单层 ≈1.4GB，理论上 6GB 能放——但前提（CUDA torch + bnb + 切层不 OOM + 磁盘 173GB 放得下）本机**全部不满足**。

---

## 7. (f) transformers 版本要求 / Windows 前置条件

### 7.1 transformers【本机实测 wheel 内容】
- 我把 PyPI 的 wheel 下下来逐个查 `transformers/models/qwen4_exp/__init__.py`：
  - 5.8.0 / 5.8.1 / 5.9.0 / 5.10.0 / 5.15.0 / 5.15.1：**没有** qwen4_exp；
  - **5.16.1 / 5.17.0 / 5.18.0 / 5.19.0 / 5.20.0 / 5.22.2：有**；auto 映射到 `Qwen4ExpForConditionalGeneration`（`modeling_auto.py:1225`）。
- 模型 config.json 写的是 `"transformers_version": "5.8.0.dev0"` —— 这是模型卡生成时的 dev 版本，**架构进入正式 wheel 是 5.16.x**。
- ⇒ **要求 `transformers>=5.16`**（我按 5.15.1/5.16.1 夹逼，建议装最新 5.22.x 并显式 pin）。README（2026/08）"today 要 `pip install git+https://github.com/huggingface/transformers.git`" **已过时**。
- ⚠️ airllm 自己的 `setup.py:33` 只写 `transformers>=4.49,<6`，`pip install airllm` **可能装到没有 qwen4_exp 的版本**，必须自己 pin `>=5.16`。transformers 5.16+ 同时要求 `huggingface_hub>=1.5`（新 API）、`tokenizers>=0.22`、`regex>=2025.10.22`，pip 会自动升级——Windows 上这步体积不小。

### 7.2 不需要的东西（重要，少踩坑）
- **不需要 flash-attn**：`Qwen4ExpPreTrainedModel` 写死 `_supports_flash_attn = False`、`_supports_sdpa = True`（transformers 5.22.2 `modeling_qwen4_exp.py:1314-1315`），airllm 也优先要 sdpa（`airllm_base.py:336-345`）。PyPI `flash-attn` 最新 2.8.3.post2 **没有任何 Windows wheel**，但这里用不到。
- **不需要 fla / causal-conv1d**：Gated DeltaNet 有纯 torch 回退；`causal_conv1d_fn/update` 用 `@use_kernel_func_from_hub_with_fallback`（`modeling_qwen4_exp.py:202-223`），缺包就走 torch。
- 视觉塔：`model.visual` 常驻加载（`airllm_base.py:673-687`），任何图片输入路径都可能触发；纯文本也应能跑。

### 7.3 Windows 硬坑（按严重度）
1. **CUDA torch 必须重装**：本机 torch 2.8.0+cpu，`torch.cuda.is_available()=False`。RTX 3060 Laptop 是 sm_86，要装 cu12x 的 Windows wheel（≈2.5–3GB 下载）。不装 GPU 版的话 airllm 会 `default_device()=cpu`（`utils.py:88-101`），能跑但慢一倍以上（我们的 0.5B 冒烟就是 CPU 跑的）。
2. **`delete_original=True` 在无 symlink 权限的 Windows 上必崩**（§3.4，本机已复现）。
3. **bitsandbytes**：PyPI 有 `bitsandbytes-0.50.2-py3-none-win_amd64.whl`，但需要 CUDA torch；且见 §6 的 6GB 卡限制。
4. **pagefile 只有 C: 20GB**：切层时进程要同时持有 1~2 个 ≈3.1GiB shard + 当前层 dict + mmap 写缓冲，提交量可能到 10–15GB；32GB RAM + 20GB pagefile 够用但没余量（mmap 95GiB 是文件页，不计匿名提交）。
5. **mmap/hardlink 本身没问题**：本机实测 `torch.UntypedStorage.from_file(shared=True)` + bf16 2D 视图 OK；`os.link`（NTFS 同卷）OK；仓库自带的 `test_qwen38_flash_next_split.py` **16 个测试全过**（8.1s，含 mmap 生成、PLE 剥离、硬链接/复制判定）。
6. **长路径/中文路径**：splitted 目录名含 `model.language_model.layers.1.ple.ple_embedding.ngram_embedding` 这种 60+ 字符，Windows 260 字符限制在深层 HF cache 下要留意（未实测）。

---

## 8. (g) 仓库里的实测速度数据

**没有。** 对 README.md、docs、`air_llm/**/*.py`、tests 全文 grep `tok/s|tokens/s|throughput|耗时|minute|second` 均无实测吞吐；只有 VRAM 宣传值：

- README.md:34 "…runs in **5.95GB** of VRAM, measured end to end on one RTX 4090"；
- README.md:9/112/294 同类表述（125B / 5.95GB）；27B 3.33GB（README.md:36）；Kimi K3 3.72GB（README.md:38）；
- 唯一"提速"表述是 compression "up to 3x"（README.md:149），且没有测试条件。

README 的 5.95/3.33/3.72 都是"单卡实测 VRAM"，**没有任何时间/吞吐数字**，也没有给出测速脚本。

---

## 9. 本机 Windows 实测（三个实验）

### 9.1 仓库自带 qwen38-Flash-Next 切层测试【通过】
```
python airllm-src\air_llm\tests\test_qwen38_flash_next_split.py
Ran 16 tests in 8.147s -- OK
```
覆盖：架构映射、PLE 128 个 shard 合并成 mmap、PLE 从父层剥离、packed experts 留在层内、MTP 丢弃、vision 单独 shard、硬链接/复制判定。

### 9.2 端到端冒烟：Qwen2.5-0.5B-Instruct（CPU）
环境：torch 2.8.0+cpu / transformers 5.16.1 / accelerate 1.15.0 / hf-mirror / airllm git HEAD。**没有下载任何 >2GB 权重。**
```
import airllm ok, 14.9s
using generic AirLLM streaming model for architecture: Qwen2ForCausalLM
Fetching 1 files ... 103s (≈1GB, hf-mirror ~10MB/s)
[切层] saved as ...\splitted_model\model.embed_tokens.safetensors ... model.layers.0..23 ... model.norm.safetensors
built empty Qwen2ForCausalLM via AutoModelForCausalLM (attn=sdpa)
load/split ok, 123.8s, device=cpu, dtype=torch.bfloat16, class=AirLLMBaseModel, layers=27
generate ok, 13.54s for 4 tokens (3.38s/token)
OUTPUT: What is the capital of France? The capital of France
```
⇒ **Windows 上 airllm 的"下载→切层→加载→generate"整条链路是通的**（CPU、bf16、sdpa 回退、逐层流式都正常）。与 Flash-Next 无关的部分（AutoModel 分派、safetensors 切层、hook 流式、生成）在本机已验证。

速度锚点：0.5B 模型 ≈1GB 权重/token，3.38s/token ⇒ 本机（CPU + C: 盘）有效吞吐 ≈ **0.3GB/s**。
外推【推测】Flash-Next 若走同样路径：230GiB/token ÷ 0.3GB/s ≈ **13 分钟/token**；就算换 NVMe 3GB/s 也 ≈ **80 秒/token**。即 **0.001–0.02 tok/s**，1 句话（20 token）要 1.5–4 小时。**这不是"慢"，是不可用。**

### 9.3 `delete_original=True` 复现失败【本机】
见 §3.4：假 checkpoint、真实文件、`split_and_save_layers(..., delete_original=True)` → `FileNotFoundError` at `utils.py:513`。

---

## 10. 对这台机器的判定（结论）

按代码证据，三个独立否决点，任一都足以拦住：

1. **磁盘（最硬）**：单盘最大空闲 F: 188.6GB，而切层产物本身就要 **≈353GB**（即使原件全删）。默认 `delete_original=False` 峰值 ≈713GB。**不可能。**
2. **显存（很硬）**：单层 bf16 ≈5.14GB + CUDA context/激活 ≈0.9GB ≈ README 的 5.95GB；6GB Laptop 卡在 Windows 上实际可用 ~5.2–5.6GB ⇒ **OOM / shared memory 假死**。
3. **速度（致命体验）**：整层流式 ⇒ 每 token 读 ≈230GiB；本机实测有效带宽 0.3GB/s ⇒ 分钟级/token。**交互不可用。**
4. 附加：`delete_original=True` 在本机（HF 缓存无 symlink 权限）会崩；compression 需要 CUDA torch + bitsandbytes，本机 CPU torch 完全不可用，且有 6GB 切层 OOM 风险。

**若仍想验证/前进**：优先用更小的同架构替代（例如先跑 Qwen3-30B-A3B 级别，单层 ~1.2GB、总盘 ~60GB、有 per-expert streaming 路径），或者等 airllm 给 qwen4_exp 补上 `expert_prefix`（MoE 稀疏流式）后再评估——那时代码路径会变成"每 token 只读 10/512 experts"，量级能降 1~2 个数量级。

---

## 11. 未证实/需要真实权重才能定的

- README 的 **5.95GB** 与 **64GB 内存够** 两个数字：我只有代码与 config 推算，**没有真权重实测**（本机也跑不动）；推算与 5.95GB 自洽（4.79GiB 层 + ~0.9GB context），但"4090 实测"无法复核。
- 实际 tok/s：**仓库无任何数据**，§9.2 的外推基于 0.5B + CPU，SSD/GPU 下会不同（乐观 1–2 分钟/token），但量级结论不变。
- Windows 上 95GiB 单文件 mmap 的长期稳定性（页回收、1024 页粒度、NTFS 大文件）未在真权重上验证；只验证了小文件 mmap API 可用。
- `hf-mirror` 是否能完整镜像 128 个 PLE shard 的 360GB（只验证了 config/index/API 可访问，未下权重）。
- transformers 5.16.x 是否能完整跑通 qwen4_exp 前向（本机只有 CPU torch，且无权重）；本报告只验证了"wheel 里包含该模块 + auto 映射存在"。


