<#
.SYNOPSIS
  在 Windows 上准备 airllm 运行环境（CUDA 版 torch + git 版 transformers + airllm）。

.DESCRIPTION
  只做“装环境”，不下载模型权重。装完先跑 Qwen/Qwen2.5-0.5B-Instruct 冒烟测试，
  确认 Windows 上切层 + generate 能跑通，再考虑要不要碰 125B 的 Flash-Next。

  背景数字（2026-11 复核）：
    Qwen3.8-Flash-Next BF16 权重 = 335.3 GiB / 360 GB，131 个分片
    airllm 自称 5.95GB 显存可跑，但同时要求 ~360GB 磁盘 + 64GB 内存
    本机（6GB 显存 / 32GB 内存 / 单盘最大空闲 188.6GB）不满足后两条。

.EXAMPLE
  # 默认装到 F:\airllm（F 盘空闲最多）
  .\setup_airllm_windows.ps1

.EXAMPLE
  .\setup_airllm_windows.ps1 -Root 'F:\airllm' -CudaWheel cu128
#>
param(
  [string]$Root = 'F:\airllm',
  [string]$Python = 'D:\Dayuse\python\python3.11\python.exe',
  # RTX 3060 Laptop 是 sm_86，cu128/cu126/cu121 的轮子都支持；按装得动的选。
  [string]$CudaWheel = 'cu128',
  [string]$HfEndpoint = 'https://hf-mirror.com',
  # 走国内镜像时 hf_transfer 可能不生效，默认关。
  [switch]$UseHfTransfer
)

$ErrorActionPreference = 'Stop'
function Step($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }

# ---------- 0. 前置检查 ----------
Step '0/6 前置检查'
if (-not (Test-Path $Python)) { throw "找不到 Python：$Python" }
$pyVer = & $Python --version 2>&1
Write-Host "Python: $pyVer ($Python)"
$gpu = (& nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv,noheader 2>$null)
if ($LASTEXITCODE -eq 0) { Write-Host "GPU: $gpu" } else { Write-Warning 'nvidia-smi 不可用：本机没有可用的 NVIDIA 驱动，airllm 会退化成 CPU 推理（极慢）' }

if (-not (Test-Path $Root)) { New-Item -ItemType Directory -Force -Path $Root | Out-Null }
$drive = (Get-Item $Root).PSDrive
$freeGB = [math]::Round($drive.Free / 1GB, 1)
Write-Host "根目录 $Root 所在盘 $($drive.Name): 空闲 $freeGB GB"
if ($freeGB -lt 400) {
  Write-Warning "Flash-Next BF16 需要 ~360GB 权重 + 切层副本，建议该盘空闲 >= 400GB；当前只有 $freeGB GB。冒烟测试（0.5B 模型）不受影响。"
}

# ---------- 1. venv ----------
Step '1/6 创建虚拟环境'
$venv = Join-Path $Root 'venv'
if (-not (Test-Path $venv)) {
  & $Python -m venv $venv
  if ($LASTEXITCODE -ne 0) { throw 'venv 创建失败' }
}
$vpy = Join-Path $venv 'Scripts\python.exe'
Write-Host "venv: $venv"

Step '2/6 升级 pip'
& $vpy -m pip install -U pip wheel setuptools --quiet
if ($LASTEXITCODE -ne 0) { throw 'pip 升级失败' }

# ---------- 2. torch（CUDA 版）----------
Step "3/6 安装 CUDA 版 torch（索引 $CudaWheel）"
# 说明：默认 PyPI 的 torch 是 CPU 版（本机全局就是 2.8.0+cpu）。GPU 推理必须装 CUDA 轮子。
& $vpy -m pip install -U torch --index-url "https://download.pytorch.org/whl/$CudaWheel"
if ($LASTEXITCODE -ne 0) {
  Write-Warning "CUDA $CudaWheel 安装失败，尝试 cu126 / cu121 ..."
  foreach ($alt in @('cu126','cu121')) {
    & $vpy -m pip install -U torch --index-url "https://download.pytorch.org/whl/$alt"
    if ($LASTEXITCODE -eq 0) { Write-Host "已用 $alt 装好 torch" -ForegroundColor Green; break }
  }
}
& $vpy -c "import torch; print('torch', torch.__version__, 'cuda_available=', torch.cuda.is_available(), 'cuda=', torch.version.cuda)"
if ($LASTEXITCODE -ne 0) { throw 'torch 安装后无法导入' }

# ---------- 3. airllm ----------
Step '4/6 安装 airllm'
& $vpy -m pip install -U airllm
if ($LASTEXITCODE -ne 0) { throw 'airllm 安装失败（检查网络/镜像）' }

# ---------- 4. transformers（带 qwen4_exp）----------
Step '5/6 安装带 qwen4_exp 的 transformers'
# 2026-11 源码核查结论：qwen4_exp 从 transformers **5.16.0** 起才在 pip 正式版里（5.15.1 及以下没有），
# auto 映射也在（modeling_auto.py:1225）。README 里「pip install git+...transformers.git」的写法已过时，
# 装 >=5.16 的正式版即可。注意 airllm 自己的 setup.py 只写 transformers>=4.49,<6，不会帮你 pin 对。
& $vpy -m pip install -U "transformers>=5.16"
if ($LASTEXITCODE -ne 0) {
  Write-Warning 'pip 版失败，退回 git 主分支（需要能访问 GitHub）...'
  & $vpy -m pip install -U "transformers @ git+https://github.com/huggingface/transformers.git"
}
& $vpy -c "import transformers; from transformers.models.qwen4_exp import configuration; print('transformers', transformers.__version__, 'qwen4_exp OK')"
if ($LASTEXITCODE -ne 0) { throw 'qwen4_exp 导入失败：Flash-Next 必须用 >=5.8 的 transformers' }

# 注意：qwen4_exp 的 modeling 里 _supports_flash_attn=False、_supports_sdpa=True，
# causal_conv1d / Gated DeltaNet 都有纯 torch 回退 —— Windows 上不需要 flash-attn，也不需要编译 CUDA 扩展。

# 可选：4bit 块量化（airllm 的 compression='4bit'）需要 bitsandbytes
Step '6/6 可选依赖：bitsandbytes / accelerate'
& $vpy -m pip install -U bitsandbytes accelerate --quiet
if ($LASTEXITCODE -ne 0) { Write-Warning 'bitsandbytes 在 Windows 上可能没有可用轮子；不影响 FP16 逐层推理，只影响 compression=4bit' }

# ---------- 5. 环境变量 ----------
Step '写入环境变量（仅当前会话提示，永久生效见下方）'
Write-Host @"
请在你自己的 shell 里先设这些（或写进系统环境变量）：
  `$env:HF_ENDPOINT = '$HfEndpoint'        # huggingface.co 直连超时，走镜像
  `$env:HF_HOME     = '$Root\hf-cache'     # 权重缓存放到大容量盘
  `$env:PYTHONUTF8  = '1'
$(if ($UseHfTransfer) { "  `$env:HF_HUB_ENABLE_HF_TRANSFER = '1'" })

冒烟测试（0.5B 小模型，约 1GB 下载）：
  & '$vpy' '$PSScriptRoot\airllm_smoke_test.py'

正式跑 Flash-Next（需要 >=400GB 空闲盘 + >=64GB 内存，本机需外接 SSD / 加内存）：
  & '$vpy' '$PSScriptRoot\airllm_flash_next.py' --root '$Root'
"@ -ForegroundColor Yellow

Write-Host "`n环境就绪：$venv" -ForegroundColor Green
