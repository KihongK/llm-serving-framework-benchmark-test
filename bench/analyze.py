"""벤치마크 결과 분석 — 비교 테이블 + 가설 검증 + 차트 생성.

사용법:
    python -m bench.analyze                      # 기본 경로
    python -m bench.analyze --results-dir /path   # 커스텀 경로
"""

import argparse
import json
import os
import time

from .visualize import generate_all_charts, load_all_results

FW_LABELS = {"sglang": "SGLang", "vllm": "vLLM", "ollama": "Ollama"}


def _get_scenario_results(data: dict, scenario: str) -> dict[str, list[dict]]:
    """프레임워크별 특정 시나리오 결과."""
    out = {}
    for fw, fw_data in data.items():
        results = [r for r in fw_data.get("results", []) if r["scenario"] == scenario]
        if results:
            out[fw] = results
    return out


def _fmt(val, unit: str = "") -> str:
    """숫자 포맷팅."""
    if val is None or val == 0:
        return "N/A"
    if isinstance(val, float):
        return f"{val:,.2f}{unit}"
    return f"{val}{unit}"


def generate_comparison_tables(data: dict) -> str:
    """시나리오별 비교 Markdown 테이블 생성."""
    lines = []

    # --- 시나리오 1: Single Request ---
    sr = _get_scenario_results(data, "single_request")
    if sr:
        lines.append("## 1. Single Request Baseline\n")
        lines.append("| Framework | Input Tokens | TTFT (ms) | Throughput (tok/s) | p50 Latency | p95 Latency | p99 Latency | Success |")
        lines.append("|-----------|-------------|-----------|-------------------|-------------|-------------|-------------|---------|")
        for fw in ["sglang", "vllm", "ollama"]:
            if fw not in sr:
                continue
            for r in sorted(sr[fw], key=lambda x: x["input_tokens"]):
                lines.append(
                    f"| {FW_LABELS[fw]} | {r['input_tokens']} | {_fmt(r['avg_ttft_ms'])} | "
                    f"{_fmt(r['total_token_throughput'])} | {_fmt(r['p50_latency_ms'])}ms | "
                    f"{_fmt(r['p95_latency_ms'])}ms | {_fmt(r['p99_latency_ms'])}ms | {_fmt(r['success_rate'])}% |"
                )
        lines.append("")

    # --- 시나리오 2: Concurrent Load ---
    cl = _get_scenario_results(data, "concurrent_load")
    if cl:
        lines.append("## 2. Concurrent Load Test\n")
        lines.append("| Framework | Concurrency | Req Throughput (req/s) | Token Throughput (tok/s) | TTFT p50 | TTFT p95 | p99 Latency | Success |")
        lines.append("|-----------|------------|----------------------|------------------------|----------|----------|-------------|---------|")
        for fw in ["sglang", "vllm", "ollama"]:
            if fw not in cl:
                continue
            for r in sorted(cl[fw], key=lambda x: x["concurrency"]):
                lines.append(
                    f"| {FW_LABELS[fw]} | {r['concurrency']} | {_fmt(r['request_throughput'])} | "
                    f"{_fmt(r['total_token_throughput'])} | {_fmt(r['p50_ttft_ms'])}ms | "
                    f"{_fmt(r['p95_ttft_ms'])}ms | {_fmt(r['p99_latency_ms'])}ms | {_fmt(r['success_rate'])}% |"
                )
        lines.append("")

    # --- 시나리오 3: Long Context ---
    lc = _get_scenario_results(data, "long_context")
    if lc:
        lines.append("## 3. Long Context Test\n")
        lines.append("| Framework | Input Tokens | Concurrency | TTFT (ms) | Throughput (tok/s) | p99 Latency | GPU Mem (MB) | Success |")
        lines.append("|-----------|-------------|------------|-----------|-------------------|-------------|-------------|---------|")
        for fw in ["sglang", "vllm", "ollama"]:
            if fw not in lc:
                continue
            for r in sorted(lc[fw], key=lambda x: (x["input_tokens"], x["concurrency"])):
                mem = r.get("peak_memory_mb", 0) or r.get("gpu_memory_mb", 0)
                lines.append(
                    f"| {FW_LABELS[fw]} | {r['input_tokens']} | {r['concurrency']} | "
                    f"{_fmt(r['avg_ttft_ms'])} | {_fmt(r['total_token_throughput'])} | "
                    f"{_fmt(r['p99_latency_ms'])}ms | {_fmt(mem)} | {_fmt(r['success_rate'])}% |"
                )
        lines.append("")

    # --- 시나리오 4: Prefix Cache ---
    pc = _get_scenario_results(data, "prefix_cache")
    if pc:
        lines.append("## 4. Prefix Cache Efficiency\n")
        lines.append("| Framework | First 5 TTFT (ms) | Later TTFT (ms) | Speedup | Throughput (tok/s) | p99 Latency | Success |")
        lines.append("|-----------|------------------|----------------|---------|-------------------|-------------|---------|")
        for fw in ["sglang", "vllm", "ollama"]:
            if fw not in pc:
                continue
            r = pc[fw][0]
            first5 = _fmt(r.get("first_5_avg_ttft_ms", 0))
            later = _fmt(r.get("later_avg_ttft_ms", 0))
            speedup = _fmt(r.get("cache_speedup_ratio", 0), "x")
            lines.append(
                f"| {FW_LABELS[fw]} | {first5} | {later} | {speedup} | "
                f"{_fmt(r['total_token_throughput'])} | "
                f"{_fmt(r['p99_latency_ms'])}ms | {_fmt(r['success_rate'])}% |"
            )
        lines.append("")

    # --- 시나리오 5: Korean ---
    ko_results = {}
    for fw, fw_data in data.items():
        ko = [r for r in fw_data.get("results", []) if r["scenario"].startswith("korean_")]
        if ko:
            ko_results[fw] = ko

    if ko_results:
        lines.append("## 5. Korean Language Performance\n")
        lines.append("| Framework | Scenario | Concurrency | TTFT (ms) | Throughput (tok/s) | p99 Latency | Success |")
        lines.append("|-----------|----------|------------|-----------|-------------------|-------------|---------|")
        for fw in ["sglang", "vllm", "ollama"]:
            if fw not in ko_results:
                continue
            for r in ko_results[fw]:
                lines.append(
                    f"| {FW_LABELS[fw]} | {r['scenario']} | {r['concurrency']} | "
                    f"{_fmt(r['avg_ttft_ms'])} | {_fmt(r['total_token_throughput'])} | "
                    f"{_fmt(r['p99_latency_ms'])}ms | {_fmt(r['success_rate'])}% |"
                )
        lines.append("")

    # --- GPU 리소스 요약 ---
    lines.append("## 6. GPU Resource Usage\n")
    lines.append("| Framework | Peak Memory (MB) | Avg Memory (MB) | Avg GPU Util (%) |")
    lines.append("|-----------|-----------------|----------------|-----------------|")
    for fw in ["sglang", "vllm", "ollama"]:
        if fw not in data:
            continue
        results = data[fw].get("results", [])
        peaks = [r.get("peak_memory_mb", 0) or r.get("gpu_memory_mb", 0) for r in results]
        avgs = [r.get("avg_memory_mb", 0) for r in results if r.get("avg_memory_mb", 0) > 0]
        utils = [r.get("avg_gpu_util_pct", 0) for r in results if r.get("avg_gpu_util_pct", 0) > 0]
        lines.append(
            f"| {FW_LABELS[fw]} | {_fmt(max(peaks) if peaks else 0)} | "
            f"{_fmt(sum(avgs) / len(avgs) if avgs else 0)} | "
            f"{_fmt(sum(utils) / len(utils) if utils else 0)}% |"
        )
    lines.append("")

    return "\n".join(lines)


def verify_hypotheses(data: dict) -> str:
    """가설 H1~H5 자동 검증."""
    lines = ["## 7. 가설 검증 결과\n"]

    fws = set(data.keys())

    # H1: SGLang > vLLM in prefix caching (캐시 적용 후 later TTFT 비교)
    lines.append("### H1: SGLang의 prefix caching이 vLLM보다 효율적")
    pc = _get_scenario_results(data, "prefix_cache")
    if "sglang" in pc and "vllm" in pc:
        sg = pc["sglang"][0]
        vl = pc["vllm"][0]
        sg_later = sg.get("later_avg_ttft_ms", 0) or sg["avg_ttft_ms"]
        vl_later = vl.get("later_avg_ttft_ms", 0) or vl["avg_ttft_ms"]
        sg_speedup = sg.get("cache_speedup_ratio", 0)
        vl_speedup = vl.get("cache_speedup_ratio", 0)
        if sg_later > 0 and vl_later > 0:
            ratio = vl_later / sg_later
            verdict = "SUPPORTED" if ratio > 1.1 else ("INCONCLUSIVE" if ratio > 0.9 else "NOT SUPPORTED")
            lines.append(f"- SGLang cached TTFT: {sg_later}ms (speedup: {sg_speedup}x)")
            lines.append(f"- vLLM cached TTFT: {vl_later}ms (speedup: {vl_speedup}x)")
            lines.append(f"- vLLM/SGLang ratio: {ratio:.2f}x")
            lines.append(f"- **결과: {verdict}**")
        else:
            lines.append("- 데이터 부족으로 판정 불가")
    else:
        lines.append("- 데이터 부족: SGLang 또는 vLLM prefix_cache 결과 없음")
    lines.append("")

    # H2: SGLang/vLLM >> Ollama in concurrent requests
    lines.append("### H2: SGLang/vLLM이 동시 요청에서 Ollama보다 월등히 빠름")
    cl = _get_scenario_results(data, "concurrent_load")
    if cl:
        # concurrency=32 기준 비교
        target_conc = 32
        thrpts = {}
        for fw in ["sglang", "vllm", "ollama"]:
            if fw in cl:
                match = [r for r in cl[fw] if r["concurrency"] == target_conc]
                if match:
                    thrpts[fw] = match[0]["total_token_throughput"]

        if "ollama" in thrpts and thrpts["ollama"] > 0:
            for fw in ["sglang", "vllm"]:
                if fw in thrpts:
                    ratio = thrpts[fw] / thrpts["ollama"]
                    lines.append(f"- {FW_LABELS[fw]} / Ollama throughput ratio (c={target_conc}): {ratio:.1f}x")
            verdict = "SUPPORTED" if any(thrpts.get(fw, 0) / thrpts["ollama"] > 3 for fw in ["sglang", "vllm"]) else "INCONCLUSIVE"
            lines.append(f"- **결과: {verdict}**")
        elif thrpts:
            lines.append(f"- Ollama concurrency={target_conc} 데이터 없음. 사용 가능한 프레임워크: {', '.join(thrpts.keys())}")
        else:
            lines.append("- 데이터 부족")
    else:
        lines.append("- concurrent_load 결과 없음")
    lines.append("")

    # H3: Ollama competitive in single request
    lines.append("### H3: Ollama가 단일 요청에서 경쟁력 있음")
    sr = _get_scenario_results(data, "single_request")
    if sr:
        # input=512 기준
        ttfts = {}
        for fw in ["sglang", "vllm", "ollama"]:
            if fw in sr:
                match = [r for r in sr[fw] if r["input_tokens"] == 512]
                if match:
                    ttfts[fw] = match[0]["avg_ttft_ms"]

        if "ollama" in ttfts and len(ttfts) >= 2:
            best_other = min(v for k, v in ttfts.items() if k != "ollama")
            ratio = ttfts["ollama"] / best_other if best_other > 0 else float("inf")
            for fw, val in ttfts.items():
                lines.append(f"- {FW_LABELS[fw]} TTFT (512 tokens): {val}ms")
            verdict = "SUPPORTED" if ratio < 2.0 else "NOT SUPPORTED"
            lines.append(f"- Ollama / best-other ratio: {ratio:.2f}x")
            lines.append(f"- **결과: {verdict}** (2x 이내면 경쟁력 있음으로 판정)")
        else:
            lines.append("- 데이터 부족")
    else:
        lines.append("- single_request 결과 없음")
    lines.append("")

    # H4: Different performance degradation patterns
    lines.append("### H4: 프레임워크별 성능 저하 패턴이 다름")
    if cl and len(cl) >= 2:
        lines.append("- 동시성 증가에 따른 p99 latency 변화:")
        for fw in ["sglang", "vllm", "ollama"]:
            if fw not in cl:
                continue
            results = sorted(cl[fw], key=lambda r: r["concurrency"])
            if len(results) >= 2:
                low = results[0]
                high = results[-1]
                if low["p99_latency_ms"] > 0:
                    degradation = high["p99_latency_ms"] / low["p99_latency_ms"]
                    lines.append(
                        f"  - {FW_LABELS[fw]}: c={low['concurrency']} → c={high['concurrency']}, "
                        f"p99 {low['p99_latency_ms']}ms → {high['p99_latency_ms']}ms ({degradation:.1f}x)"
                    )
        lines.append("- **결과: 위 데이터에서 패턴 차이 확인 필요**")
    else:
        lines.append("- 데이터 부족 (최소 2개 프레임워크 필요)")
    lines.append("")

    # H5: Korean vs English token efficiency differences
    lines.append("### H5: 한국어/영어 토큰 효율성 차이")
    ko_found = False
    for fw in ["sglang", "vllm", "ollama"]:
        if fw not in data:
            continue
        results = data[fw].get("results", [])
        ko_thrpts = [r["total_token_throughput"] for r in results
                     if r["scenario"].startswith("korean_korean_") and r["concurrency"] == 1 and r["total_token_throughput"] > 0]
        en_thrpts = [r["total_token_throughput"] for r in results
                     if r["scenario"].startswith("korean_english_") and r["concurrency"] == 1 and r["total_token_throughput"] > 0]
        if ko_thrpts and en_thrpts:
            ko_found = True
            ko_avg = sum(ko_thrpts) / len(ko_thrpts)
            en_avg = sum(en_thrpts) / len(en_thrpts)
            ratio = ko_avg / en_avg if en_avg > 0 else 0
            lines.append(f"- {FW_LABELS[fw]}: Korean avg={ko_avg:.1f} tok/s, English avg={en_avg:.1f} tok/s (ratio: {ratio:.2f}x)")

    if ko_found:
        lines.append("- **결과: 위 비율에서 차이 확인 필요 (1.0에서 벗어날수록 효율 차이 큼)**")
    else:
        lines.append("- korean 시나리오 결과 없음")
    lines.append("")

    return "\n".join(lines)


def generate_report(results_dir: str, output_dir: str | None = None):
    """전체 분석 보고서 생성."""
    if output_dir is None:
        output_dir = os.path.join(results_dir, "summary")
    os.makedirs(output_dir, exist_ok=True)

    data = load_all_results(results_dir)
    if not data:
        print("No result files found. Run benchmarks first.")
        return

    print(f"Analyzing results for: {', '.join(FW_LABELS.get(fw, fw) for fw in data)}")

    # 보고서 생성
    report_lines = [
        "# LLM Serving Framework Benchmark — 분석 보고서\n",
        f"생성 시각: {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
        f"프레임워크: {', '.join(FW_LABELS.get(fw, fw) for fw in data)}\n",
    ]

    # 모델/환경 정보
    for fw, fw_data in data.items():
        model = fw_data.get("model", "N/A")
        gpu = fw_data.get("gpu_info", {})
        trials = fw_data.get("trials", 1)
        report_lines.append(f"- **{FW_LABELS.get(fw, fw)}**: model={model}, trials={trials}")
        if gpu.get("memory_total_mb"):
            report_lines.append(f"  - GPU: {gpu['memory_total_mb']:.0f} MB total")
    report_lines.append("\n---\n")

    # 비교 테이블
    report_lines.append(generate_comparison_tables(data))

    # 가설 검증
    report_lines.append("---\n")
    report_lines.append(verify_hypotheses(data))

    # Trial 요약 (있는 경우)
    has_trials = False
    for fw_data in data.values():
        if fw_data.get("trial_summary"):
            has_trials = True
            break

    if has_trials:
        report_lines.append("---\n")
        report_lines.append("## 8. Trial Summary (mean ± std)\n")
        report_lines.append("| Framework | Scenario | Trials | TTFT (ms) | Throughput (tok/s) | p99 Latency (ms) | Success (%) |")
        report_lines.append("|-----------|----------|--------|-----------|-------------------|-------------------|-------------|")
        for fw in ["sglang", "vllm", "ollama"]:
            if fw not in data:
                continue
            for ts in data[fw].get("trial_summary", []):
                lines_str = (
                    f"| {FW_LABELS[fw]} | {ts['scenario']} | {ts['num_trials']} | "
                    f"{ts['mean_ttft_ms']}±{ts['std_ttft_ms']} | "
                    f"{ts['mean_throughput']}±{ts['std_throughput']} | "
                    f"{ts['mean_p99_latency_ms']}±{ts['std_p99_latency_ms']} | "
                    f"{ts['mean_success_rate']} |"
                )
                report_lines.append(lines_str)
        report_lines.append("")

    # 보고서 저장
    report_path = os.path.join(output_dir, "analysis_report.md")
    with open(report_path, "w") as f:
        f.write("\n".join(report_lines))
    print(f"\nAnalysis report saved to: {report_path}")

    # 차트 생성
    print("\nGenerating charts...")
    generate_all_charts(results_dir, os.path.join(output_dir, "charts"))

    print(f"\nAnalysis complete. See {output_dir}/")


def main():
    parser = argparse.ArgumentParser(description="Analyze benchmark results and generate report")
    parser.add_argument(
        "--results-dir",
        default=None,
        help="Results directory (default: <project>/results/)",
    )
    args = parser.parse_args()

    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    results_dir = args.results_dir or os.path.join(project_dir, "results")
    generate_report(results_dir)


if __name__ == "__main__":
    main()
