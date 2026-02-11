---
name: results-analyzer
description: Use after benchmarks complete to analyze, compare, and visualize results across frameworks. Generates comparison tables and charts.
---

# Results Analyzer

## Overview

Analyze benchmark results from multiple frameworks, generate comparison tables, statistical summaries, and visualization-ready data for the technical blog post.

**Announce at start:** "Analyzing benchmark results across frameworks."

## Input

Results stored in:
```
/home/work/serving_framework/results/
    [framework]/[profile]-[timestamp].txt
```

## Analysis Pipeline

### Step 1: Parse Raw Results

Extract metrics from each benchmark output file:
- Total throughput (req/s)
- Output token throughput (tokens/s)
- Input token throughput (tokens/s)
- TTFT (mean, median, p99)
- TPOT (mean, median, p99)
- ITL (mean, median, p99)
- Total duration
- VRAM usage

### Step 2: Generate Comparison Table

Create a markdown comparison table:

```markdown
| Metric | SGLang | vLLM | Ollama | Winner |
|--------|--------|------|--------|--------|
| Throughput (req/s) | X | Y | Z | [best] |
| Output Tokens/s | X | Y | Z | [best] |
| Mean TTFT (ms) | X | Y | Z | [best] |
| P99 TTFT (ms) | X | Y | Z | [best] |
| Mean TPOT (ms) | X | Y | Z | [best] |
| P99 TPOT (ms) | X | Y | Z | [best] |
| VRAM Usage (MiB) | X | Y | Z | [best] |
```

Mark the winner with percentage difference from second place.

### Step 3: Generate Relative Performance

Normalize all metrics relative to the best performer (100%):

```markdown
| Metric | SGLang | vLLM | Ollama |
|--------|--------|------|--------|
| Throughput | 100% | 87% | 45% |
| Latency (TTFT) | 95% | 100% | 40% |
| ...
```

### Step 4: Generate Python Visualization Script

Create a Python script at `results/summary/generate_charts.py` that produces:

1. **Bar chart** - Throughput comparison across frameworks
2. **Latency distribution** - TTFT/TPOT box plots per framework
3. **Radar chart** - Multi-dimensional comparison (throughput, latency, VRAM efficiency)
4. **Profile comparison** - Performance across different workload profiles

Use matplotlib/seaborn. Save charts as PNG to `results/summary/charts/`.

### Step 5: Generate Summary JSON

Save structured results to `results/summary/comparison-[timestamp].json`:

```json
{
    "timestamp": "2026-02-11T00:00:00Z",
    "environment": {
        "gpu": "NVIDIA A100-SXM4-80GB",
        "driver": "570.86.10",
        "cuda": "12.8"
    },
    "model": "meta-llama/Llama-3.1-8B-Instruct",
    "frameworks": {
        "sglang": {"version": "...", "results": {}},
        "vllm": {"version": "...", "results": {}},
        "ollama": {"version": "...", "results": {}}
    },
    "winner_summary": {}
}
```

## Output Files

```
results/summary/
    comparison-[timestamp].json     # Structured data
    comparison-table.md             # Markdown table for blog
    relative-performance.md         # Normalized comparison
    generate_charts.py              # Visualization script
    charts/
        throughput-comparison.png
        latency-distribution.png
        radar-comparison.png
        profile-comparison.png
```

## Key Principles

- **Fair comparison** - Same conditions must have been used (verify from metadata)
- **Show raw numbers** - Don't just show percentages, include absolute values
- **Statistical rigor** - If multiple runs exist, show mean + std deviation
- **Highlight trade-offs** - A framework might win on throughput but lose on latency
- **Blog-ready output** - Tables and charts should be directly embeddable
