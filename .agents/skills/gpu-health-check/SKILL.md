---
name: gpu-health-check
description: Use BEFORE launching any framework server or running any benchmark. Checks GPU status, VRAM availability, and cleans up stale processes.
---

# GPU Health Check

## Overview

Verify GPU is ready for benchmarking. Check VRAM is clear, no stale processes remain, and the environment is clean before launching a framework server.

**Announce at start:** "Running GPU health check before proceeding."

## Environment

- **GPU**: NVIDIA A100-SXM4-80GB (80 GB VRAM)
- **Driver**: 570.86.10
- **CUDA**: 12.8

## The Process

### Step 1: Check GPU Status

```bash
nvidia-smi --query-gpu=name,memory.used,memory.total,memory.free,utilization.gpu,temperature.gpu --format=csv,noheader
```

**Pass criteria:** Memory used < 1000 MiB AND GPU utilization = 0%

### Step 2: Check for Stale Processes

Check for leftover framework processes from previous runs:

```bash
# SGLang processes
pgrep -fa 'sglang' 2>/dev/null || echo "No SGLang processes"

# vLLM processes
pgrep -fa 'vllm' 2>/dev/null || echo "No vLLM processes"

# Ollama processes
pgrep -fa 'ollama' 2>/dev/null || echo "No Ollama processes"

# Any python process using GPU
nvidia-smi --query-compute-apps=pid,name,used_memory --format=csv,noheader 2>/dev/null || echo "No GPU compute processes"
```

### Step 3: Cleanup (if needed)

If stale processes found, offer cleanup:

1. **Gentle cleanup** - Kill framework processes:
   ```bash
   bash /home/work/serving_framework/sglang/scripts/killall_sglang.sh
   pkill -f 'vllm.entrypoints' || true
   pkill -f 'ollama serve' || true
   ```

2. **Wait and verify** - Wait 10 seconds, re-check with nvidia-smi

3. **Aggressive cleanup** (if gentle fails):
   ```bash
   nvidia-smi --query-compute-apps=pid --format=csv,noheader | xargs -r kill -9
   sleep 5
   ```

### Step 4: Report

Report final status in this format:

```
GPU Health Check Results:
- GPU: NVIDIA A100-SXM4-80GB
- VRAM: [used]/81920 MiB ([percentage]%)
- GPU Utilization: [value]%
- Temperature: [value]C
- Stale Processes: [None / Cleaned up]
- Status: READY / NOT READY
```

## When to Use

- Before launching any framework server (SGLang, vLLM, Ollama)
- Before running any benchmark
- When a benchmark fails unexpectedly (check if OOM)
- When switching between frameworks

## Key Principles

- **Always check before launch** - Never assume VRAM is clear
- **Kill gracefully first** - Avoid force-kill unless necessary
- **Report clearly** - User must know exact VRAM state
- **Block on failure** - Do NOT proceed if VRAM is not clear
