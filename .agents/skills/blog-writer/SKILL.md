---
name: blog-writer
description: Use when writing the technical comparison blog post after all benchmarks are complete and results are analyzed.
---

# Blog Writer - LLM Serving Framework Comparison

## Overview

Write a comprehensive technical blog post comparing LLM serving frameworks based on benchmark results. The blog should be data-driven, fair, and practically useful for engineers choosing a framework.

**Announce at start:** "Writing the technical comparison blog post."

**PREREQUISITES:**
1. All framework benchmarks completed
2. `results-analyzer` skill has generated comparison data
3. Results available in `results/summary/`

## Blog Structure

### 1. Introduction
- Why framework choice matters for LLM deployment
- What frameworks are being compared and why these were chosen
- Brief description of test environment (A100 specs)
- Link to methodology section for reproducibility

### 2. Framework Overviews
For each framework (SGLang, vLLM, Ollama):
- What it is and its design philosophy
- Key architectural decisions
- Target use case / audience
- Version tested
- Installation complexity (1-5 rating with justification)

### 3. Test Methodology
- Hardware specifications (from CLAUDE.md)
- Model used and why
- Benchmark tool (SGLang bench_serving.py)
- Test profiles (random workloads with different input/output lengths)
- What metrics are measured and why they matter
- How fairness was ensured (same port, same parameters, same model)

### 4. Results
- Embed comparison tables from `results/summary/comparison-table.md`
- Embed charts from `results/summary/charts/`
- Walk through each metric with analysis
- Highlight surprising findings
- Explain performance differences (architectural reasons)

### 5. Framework Characteristics (Beyond Benchmarks)
- Ease of setup and deployment
- Documentation quality
- API compatibility (OpenAI API support)
- Supported model formats
- Quantization support
- Multi-GPU / distributed inference
- Community and ecosystem
- Production readiness

### 6. Recommendations
- **Best for throughput**: [framework] - when you need maximum tokens/s
- **Best for latency**: [framework] - when you need lowest TTFT
- **Best for ease of use**: [framework] - when you want simplest setup
- **Best for production**: [framework] - when you need reliability
- Decision matrix table

### 7. Conclusion
- Summary of key findings
- Future directions (what to test next)
- Acknowledgments

## Writing Guidelines

- **Data first** - Every claim must be backed by benchmark data
- **Fair and balanced** - Acknowledge strengths AND weaknesses of each
- **Practical** - Focus on what matters for real deployments
- **Reproducible** - Include exact commands to reproduce results
- **Visual** - Use charts and tables, not walls of text
- **Audience** - ML engineers evaluating frameworks for production

## Output

Save blog post to: `blog/llm-serving-comparison.md`

Include:
- Embedded images referencing `results/summary/charts/`
- Code blocks with exact benchmark commands
- Comparison tables
- Framework version information

## Integration with Other Skills

- Use `doc-coauthoring` for collaborative refinement
- Use `copy-editing` for final polish
- Use `results-analyzer` output as data source

## Key Principles

- **No favoritism** - Present results objectively
- **Explain WHY** - Don't just show numbers, explain architectural reasons
- **Actionable** - Reader should be able to choose a framework after reading
- **Honest about limitations** - Single GPU, single model, synthetic workload caveats
