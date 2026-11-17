#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
airllm 跑 Qwen/Qwen3.8-Flash-Next（125B 主模型 + 51B n-gram embedding，BF16 共 360GB）。

== 先看清代价（2026-11 复核，数字都来自 airllm README + 官方权重清单）==
  * 权重：335.3 GiB / 360 GB，131 个 safetensors 分片
  * 显存：airllm 自称 5.95GB 峰值（RTX 4090 端到端跑过一句；仓库里没有任何 tok/s）
  * 内存：README 说 64GB 机器够（51B n-gram 表 mmap，代码里没有硬性内存检查）
  * 磁盘（源码核对 utils.py）：切完的分片目录就有 ≈329GiB(354GB) —— 这是硬地板，压不掉；
          delete_original=True 峰值 ≈430GiB(462GB)，不开则 ≈665GiB(714GB)
  * 速度（源码核对 airllm_qwen4_exp.py：整层流式，**没有 per-expert 流式**）：
          每 token 要把 48 层各读一遍 ≈ 230GiB；按本机实测有效带宽 0.3GB/s ≈ 13 分钟/token，
          按 7GB/s 的理想 NVMe 也要 33 s/token。第三方 Windows 实测 3B 模型 10~29 s/token。

== 本机（6GB 显存 / 32GB 内存 / 单盘最大 188.6GB）实际结论 ==
  ① 磁盘：切层硬地板 354GB > 188.6GB —— 连下载都完成不了；
  ② 显存：单层 4.79GiB + CUDA/激活 ≈ 5.95GB，Windows WDDM 还要占 0.3~1GB → 大概率 OOM；
  ③ 速度：设计上就是 30 秒~十几分钟/token，不可交互。
  另外：delete_original=True 在本机（无符号链接权限的 Windows）已复现必崩 FileNotFoundError。
  这个脚本默认只做「预检 + 打印方案」，需要显式 --i-know 才会真的开始下载。

用法:
  # 只看预检（默认）
  python airllm_flash_next.py --root F:\\airllm

  # 外接了 >=512GB SSD、并把页面文件调到 64GB+ 之后：
  python airllm_flash_next.py --root X:\\airllm --i-know --max-new-tokens 16
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
import time

MODEL_ID = "Qwen/Qwen3.8-Flash-Next"
BF16_GB = 360.0        # 335.3 GiB，官方清单求和
SHARD_DIR_GB = 354.0   # 切完的分片目录≈329GiB（硬地板），只有 lm_head 能硬链接
PEAK_DELETE_ON = 462   # delete_original=True 的峰值（PLE 新 mmap 95.37GiB 那一瞬间）
PEAK_DELETE_OFF = 714  # 不开 delete_original：原件 + 分片副本
RAM_WANTED_GB = 64.0
TOKENS_GIB_PER_TOKEN = 230.0  # 48 层 × 4.79GiB；整层流式，无 per-expert 稀疏收益


def human(n: float) -> str:
    return f"{n:.1f} GB"


def preflight(root: str) -> bool:
    ok = True
    os.makedirs(root, exist_ok=True)

    free = shutil.disk_usage(root).free / 2**30
    print(f"[磁盘] {root} 空闲 {human(free)}")
    print(f"       切层后目录就有 {human(SHARD_DIR_GB)}（硬地板）；"
          f"峰值：开 delete_original ≈{human(PEAK_DELETE_ON)}，不开 ≈{human(PEAK_DELETE_OFF)}")
    if free < SHARD_DIR_GB:
        ok = False
        print(f"       ✗ 连硬地板都不到，差 {human(SHARD_DIR_GB - free)}")
    else:
        print("       ✓")

    try:
        import psutil
        vm = psutil.virtual_memory()
        ram_total = vm.total / 2**30
        print(f"[内存] 共 {human(ram_total)}，可用 {human(vm.available / 2**30)}；airllm 建议 {RAM_WANTED_GB:.0f}GB")
        if ram_total < RAM_WANTED_GB:
            ok = False
            print(f"       ✗ 差 {human(RAM_WANTED_GB - ram_total)}（n-gram 表 100GB 会反复换页）")
        else:
            print("       ✓")
    except ImportError:
        print("[内存] 没装 psutil，跳过（pip install psutil 可看）")

    try:
        import torch
        print(f"[torch] {torch.__version__} cuda={torch.cuda.is_available()}")
        if not torch.cuda.is_available():
            print("       ✗ CPU 版 torch：先按 setup 脚本装 CUDA 轮子")
            ok = False
        else:
            free_vram, total_vram = torch.cuda.mem_get_info()
            print(f"[显存] {torch.cuda.get_device_name(0)} 空闲 {free_vram/2**30:.2f}GiB / 共 {total_vram/2**30:.2f}GiB；"
                  f"airllm 称需要 5.95GB")
            if free_vram / 2**30 < 6.0:
                print("       ⚠ 每层约 5.0GB（512 专家 × 3 × 2560 × 640 × 2B），"
                      "Windows 桌面本身占 1.0~1.5GB，很可能 OOM")
    except ImportError:
        print("[torch] 未安装：先跑 setup_airllm_windows.ps1")

    # 速度预算
    print("\n[速度预算]（源码确认：qwen4_exp 走整层流式，没有 per-expert 流式）")
    print(f"       每 token 读 48 层 × 4.79GiB ≈ {TOKENS_GIB_PER_TOKEN:.0f}GiB")
    print(f"       本机实测有效带宽 ≈0.3GB/s => {TOKENS_GIB_PER_TOKEN / 0.3 / 60:.0f} 分钟/token")
    print(f"       理想 7GB/s NVMe => {TOKENS_GIB_PER_TOKEN / 7:.0f} s/token（仍然不可交互）")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=r"F:\airllm", help="权重/切层缓存目录（放大容量盘）")
    ap.add_argument("--max-new-tokens", type=int, default=16)
    ap.add_argument("--compression", default=None, choices=[None, "4bit", "8bit"],
                    help="airllm 块量化；对 qwen4_exp 是否生效需先源码确认，默认不开")
    ap.add_argument("--i-know", action="store_true", help="预检不通过也继续（会下载 360GB）")
    args = ap.parse_args()

    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
    os.environ.setdefault("HF_HOME", os.path.join(args.root, "hf-cache"))
    os.environ.setdefault("PYTHONUTF8", "1")

    print(f"目标模型: {MODEL_ID}（BF16 {BF16_GB:.0f}GB）")
    ok = preflight(args.root)
    if not ok and not args.i_know:
        print("\n预检未通过。外面加 --i-know 可以强行继续，但按上面的数字，本机大概率是"
              "\n「下载一天 + 每 token 等几分钟」，不建议。")
        return 2

    from airllm import AutoModel

    shards = os.path.join(args.root, "shards", "qwen3.8-flash-next-bf16")
    os.makedirs(shards, exist_ok=True)

    print(f"\n[1/3] 下载 + 切层（首次会跑很久；watch 磁盘剩余空间）-> {shards}")
    t0 = time.time()
    model = AutoModel.from_pretrained(
        MODEL_ID,
        layer_shards_saving_path=shards,
        compression=args.compression,
        delete_original=False,   # 已知删崩风险；磁盘不够就先别开
        profiling_mode=True,
    )
    print(f"      完成，用时 {(time.time() - t0) / 60:.1f} 分钟")

    print("[2/3] 推理")
    text = ["用一句话说明你和 Qwen3.8-Flash 的区别。"]
    ids = model.tokenizer(text, return_tensors="pt", return_attention_mask=False,
                          truncation=True, max_length=128, padding=False)
    t0 = time.time()
    out = model.generate(ids["input_ids"].to(model.device),
                         max_new_tokens=args.max_new_tokens,
                         use_cache=True, return_dict_in_generate=True)
    dt = time.time() - t0
    n = out.sequences.shape[1] - ids["input_ids"].shape[1]
    print("[3/3] 输出:", model.tokenizer.decode(out.sequences[0]))
    print(f"      {n} token / {dt:.1f}s => {n / dt:.4f} tok/s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
