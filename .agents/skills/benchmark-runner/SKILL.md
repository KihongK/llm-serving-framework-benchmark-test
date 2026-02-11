---
name: benchmark-runner
description: Use when running benchmarks against a serving framework. Ensures unified test conditions, captures results, and saves structured output.
---

# Benchmark Runner

## Overview

Run benchmarks against LLM serving frameworks under unified, controlled conditions. Uses SGLang's `bench_serving.py` as the primary tool, which supports multiple backends.

**Announce at start:** "Running benchmark against [framework] with [parameters]."

**PREREQUISITES:**
1. Run `gpu-health-check` skill - VRAM must be clear
2. Run `framework-setup` skill - Server must be running and verified

## Primary Benchmark Tool

SGLang's bench_serving.py located at:
```
/home/work/serving_framework/sglang/python/sglang/bench_serving.py
```

## Standard Benchmark Profiles

### Profile 1: Random Workload (Primary)
```bash
python3 -m sglang.bench_serving \
    --backend [sglang|vllm|openai] \
    --host 127.0.0.1 \
    --port 30000 \
    --num-prompts 3000 \
    --dataset-name random \
    --random-input 1024 \
    --random-output 1024 \
    --random-range-ratio 0.5
```

### Profile 2: Short Input/Output
```bash
python3 -m sglang.bench_serving \
    --backend [sglang|vllm|openai] \
    --host 127.0.0.1 \
    --port 30000 \
    --num-prompts 3000 \
    --dataset-name random \
    --random-input 256 \
    --random-output 256 \
    --random-range-ratio 0.5
```

### Profile 3: Long Context
```bash
python3 -m sglang.bench_serving \
    --backend [sglang|vllm|openai] \
    --host 127.0.0.1 \
    --port 30000 \
    --num-prompts 1000 \
    --dataset-name random \
    --random-input 4096 \
    --random-output 1024 \
    --random-range-ratio 0.5
```

## Backend Mapping

| Framework | --backend value | Notes |
|-----------|----------------|-------|
| SGLang | `sglang` | Native support |
| vLLM | `vllm` | Native support |
| Ollama | `openai` | OpenAI-compatible API |
| Other | `openai` | Any OpenAI-compatible server |

## Execution Protocol

### Before Each Run
1. Confirm server is healthy: `curl -s http://localhost:30000/health`
2. Record VRAM usage: `nvidia-smi --query-gpu=memory.used --format=csv,noheader`
3. Record timestamp: `date -u +%Y-%m-%dT%H:%M:%SZ`

### During Run
- Monitor for errors in benchmark output
- If benchmark hangs > 10 minutes with no output, investigate
- Do NOT interrupt a running benchmark unless asked

### After Each Run
1. Save raw output to: `results/[framework]/[profile]-[timestamp].txt`
2. Record VRAM peak: `nvidia-smi --query-gpu=memory.used --format=csv,noheader`
3. Extract key metrics (see below)

## Key Metrics to Capture

From bench_serving.py output, extract:

| Metric | Unit | Description |
|--------|------|-------------|
| Total throughput | requests/s | Overall request throughput |
| Output token throughput | tokens/s | Token generation speed |
| Input token throughput | tokens/s | Prompt processing speed |
| Mean TTFT | ms | Time to first token |
| Median TTFT | ms | Time to first token (p50) |
| P99 TTFT | ms | Time to first token (p99) |
| Mean TPOT | ms | Time per output token |
| Median TPOT | ms | Time per output token (p50) |
| P99 TPOT | ms | Time per output token (p99) |
| Mean ITL | ms | Inter-token latency |
| Median ITL | ms | Inter-token latency (p50) |
| P99 ITL | ms | Inter-token latency (p99) |

## Results Directory Structure

```
/home/work/serving_framework/results/
    sglang/
        random-1024-1024-[timestamp].txt
        random-256-256-[timestamp].txt
        random-4096-1024-[timestamp].txt
    vllm/
        random-1024-1024-[timestamp].txt
        ...
    ollama/
        random-1024-1024-[timestamp].txt
        ...
    summary/
        comparison-[timestamp].json
```

## Report Format

After each benchmark run:

```
Benchmark Results:
- Framework: [name]
- Profile: [profile_name]
- Model: [model]
- Num Prompts: [count]
- Duration: [seconds]s
- Throughput: [value] req/s
- Output Token Throughput: [value] tokens/s
- Mean TTFT: [value] ms
- Median TTFT: [value] ms
- P99 TTFT: [value] ms
- Mean TPOT: [value] ms
- VRAM Peak: [value] MiB
```

## Key Principles

- **Same conditions** - Every framework gets identical parameters
- **Save everything** - Raw output, not just summaries
- **Multiple runs** - Run at least 2-3 times for consistency (if user requests)
- **Sequential** - One framework at a time, never parallel
- **Document anomalies** - Note any errors, retries, or unusual behavior
