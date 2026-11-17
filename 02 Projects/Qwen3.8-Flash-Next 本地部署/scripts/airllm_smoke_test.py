#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
airllm 冒烟测试：用一个 0.5B 小模型验证 Windows 上「切层 + 逐层推理」这条链路能不能跑通。

为什么要先跑这个：
  airllm 在 Windows 上没有任何官方支持声明，GitHub issue #364 / #396 里 Windows 用户的实测是
  3B 模型 10~29 秒/token。先花 1GB 流量确认链路通不通，再决定要不要碰 360GB 的 Flash-Next。

用法:
  set HF_ENDPOINT=https://hf-mirror.com
  <venv>\Scripts\python.exe airllm_smoke_test.py
"""
import os
import sys
import time

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")  # huggingface.co 直连常超时
os.environ.setdefault("PYTHONUTF8", "1")

MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"
SHARDS = os.path.join(
    os.environ.get("AIRLLM_ROOT", r"F:\airllm"), "shards", "smoke-qwen2.5-0.5b"
)


def main() -> int:
    import torch

    print("torch:", torch.__version__, "| cuda_available:", torch.cuda.is_available())
    if torch.cuda.is_available():
        free, total = torch.cuda.mem_get_info()
        print(f"GPU: {torch.cuda.get_device_name(0)} | free {free/2**30:.2f}GiB / total {total/2**30:.2f}GiB")

    from airllm import AutoModel

    os.makedirs(SHARDS, exist_ok=True)
    print(f"\n[1/3] 加载并切层 {MODEL_ID} -> {SHARDS}")
    t0 = time.time()
    model = AutoModel.from_pretrained(
        MODEL_ID,
        layer_shards_saving_path=SHARDS,
        delete_original=False,   # 已知 delete_original 有删崩问题（issue #297/#337），先别开
        profiling_mode=True,
    )
    print(f"      加载/切层完成，用时 {time.time() - t0:.1f}s")

    print("[2/3] 推理")
    text = ["用一句话解释什么是磁盘换显存。"]
    ids = model.tokenizer(
        text, return_tensors="pt", return_attention_mask=False,
        truncation=True, max_length=128, padding=False,
    )
    t0 = time.time()
    out = model.generate(
        ids["input_ids"].to(model.device),
        max_new_tokens=16,
        use_cache=True,
        return_dict_in_generate=True,
    )
    dt = time.time() - t0
    n_new = out.sequences.shape[1] - ids["input_ids"].shape[1]
    print("      输出:", model.tokenizer.decode(out.sequences[0]))
    print(f"[3/3] 生成 {n_new} token 用时 {dt:.1f}s => {n_new / dt:.2f} tok/s")

    print("\n结论：链路可以跑通。" if dt < 600 else "\n结论：能跑但慢到不可用。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
