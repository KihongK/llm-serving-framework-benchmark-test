---
name: framework-setup
description: Use when setting up, launching, or verifying a serving framework (SGLang, vLLM, Ollama). Handles installation, server launch, and health verification.
---

# Framework Setup

## Overview

Set up and launch LLM serving framework servers with correct configurations for benchmarking. Ensures each framework is properly installed, running, and healthy before benchmarks begin.

**Announce at start:** "Setting up [framework_name] for benchmarking."

**PREREQUISITE:** Run `gpu-health-check` skill first to ensure VRAM is clear.

## Project Layout

```
/home/work/serving_framework/
    sglang/          # v0.5.6.post2 (cloned)
    vllm/            # Cloned
    ollama/          # Planned
```

## Unified Configuration

All frameworks MUST use these consistent settings for fair comparison:

- **Model**: meta-llama/Llama-3.1-8B-Instruct (or as specified by user)
- **Host**: 0.0.0.0
- **Quantization**: Same across all (none/FP8/INT4 as specified)
- **Max model length**: Same across all
- **GPU memory utilization**: Default per framework (document the value)

## Framework-Specific Setup

### SGLang

**Launch:**
```bash
python3 -m sglang.launch_server \
    --model-path meta-llama/Llama-3.1-8B-Instruct \
    --host 0.0.0.0 \
    --port 30000
```

**Health check:**
```bash
curl -s http://localhost:30000/health | python3 -m json.tool
# Or
curl -s http://localhost:30000/v1/models
```

**Shutdown:**
```bash
bash /home/work/serving_framework/sglang/scripts/killall_sglang.sh
```

### vLLM

**Launch:**
```bash
python3 -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-3.1-8B-Instruct \
    --host 0.0.0.0 \
    --port 30000
```

**Health check:**
```bash
curl -s http://localhost:30000/health
curl -s http://localhost:30000/v1/models
```

**Shutdown:**
```bash
pkill -f 'vllm.entrypoints' || true
```

### Ollama

**Launch:**
```bash
OLLAMA_HOST=0.0.0.0:30000 ollama serve &
ollama pull llama3.1:8b-instruct-fp16
```

**Health check:**
```bash
curl -s http://localhost:30000/api/tags
```

**Shutdown:**
```bash
pkill -f 'ollama serve' || true
```

## Verification Procedure

After launching any framework, verify with a quick inference test:

```bash
curl -s http://localhost:30000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "meta-llama/Llama-3.1-8B-Instruct",
        "messages": [{"role": "user", "content": "Say hello in one word."}],
        "max_tokens": 10
    }' | python3 -m json.tool
```

**Pass criteria:**
- HTTP 200 response
- Valid JSON with generated text
- Response within 5 seconds

## Report Format

```
Framework Setup Report:
- Framework: [name] [version]
- Model: [model_name]
- Port: [port]
- VRAM Usage: [used]/81920 MiB
- Health Check: PASS / FAIL
- Inference Test: PASS / FAIL
- Status: READY FOR BENCHMARK / FAILED
```

## Key Principles

- **gpu-health-check first** - Always verify VRAM before launching
- **One framework at a time** - Never run two servers simultaneously
- **Same port** - All frameworks use port 30000 for benchmark consistency
- **Document versions** - Record exact versions of each framework
- **Verify before benchmark** - Always run health + inference test
