"""벤치마크 결과 시각화 — matplotlib 기반 6개 차트 생성.

사용법:
    python -m bench.visualize              # 기본 경로에서 결과 로드
    python -m bench.visualize --results-dir /path/to/results
"""

import argparse
import json
import os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")  # 비대화형 백엔드
import matplotlib.pyplot as plt
import numpy as np

# 프레임워크별 색상 및 스타일
FW_COLORS = {"sglang": "#2196F3", "vllm": "#FF9800", "ollama": "#4CAF50"}
FW_LABELS = {"sglang": "SGLang", "vllm": "vLLM", "ollama": "Ollama"}
DPI = 150


def load_all_results(results_dir: str) -> dict[str, dict]:
    """모든 프레임워크의 결과 JSON을 로드."""
    data = {}
    for fw in ["sglang", "vllm", "ollama"]:
        fw_dir = os.path.join(results_dir, fw)
        if not os.path.isdir(fw_dir):
            continue
        for fname in sorted(os.listdir(fw_dir)):
            if fname.endswith("_results.json"):
                fpath = os.path.join(fw_dir, fname)
                with open(fpath) as f:
                    data[fw] = json.load(f)
                break  # 프레임워크당 첫 번째 결과 파일만
    return data


def _get_results_by_scenario(data: dict, scenario: str) -> dict[str, list[dict]]:
    """프레임워크별로 특정 시나리오의 결과 리스트 반환."""
    out = {}
    for fw, fw_data in data.items():
        results = [r for r in fw_data.get("results", []) if r["scenario"] == scenario]
        if results:
            out[fw] = results
    return out


def chart_single_request(data: dict, output_dir: str):
    """차트 1: 단일 요청 — 입력 길이별 TTFT/Throughput 바 차트."""
    by_fw = _get_results_by_scenario(data, "single_request")
    if not by_fw:
        return

    input_lengths = sorted({r["input_tokens"] for results in by_fw.values() for r in results})
    frameworks = [fw for fw in ["sglang", "vllm", "ollama"] if fw in by_fw]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    x = np.arange(len(input_lengths))
    width = 0.25

    for i, fw in enumerate(frameworks):
        fw_results = {r["input_tokens"]: r for r in by_fw[fw]}
        ttfts = [fw_results.get(il, {}).get("avg_ttft_ms", 0) for il in input_lengths]
        thrpts = [fw_results.get(il, {}).get("total_token_throughput", 0) for il in input_lengths]

        ax1.bar(x + i * width, ttfts, width, label=FW_LABELS[fw], color=FW_COLORS[fw])
        ax2.bar(x + i * width, thrpts, width, label=FW_LABELS[fw], color=FW_COLORS[fw])

    ax1.set_xlabel("Input Tokens")
    ax1.set_ylabel("TTFT (ms)")
    ax1.set_title("Single Request — TTFT by Input Length")
    ax1.set_xticks(x + width)
    ax1.set_xticklabels([str(il) for il in input_lengths])
    ax1.legend()
    ax1.grid(axis="y", alpha=0.3)

    ax2.set_xlabel("Input Tokens")
    ax2.set_ylabel("Throughput (tok/s)")
    ax2.set_title("Single Request — Throughput by Input Length")
    ax2.set_xticks(x + width)
    ax2.set_xticklabels([str(il) for il in input_lengths])
    ax2.legend()
    ax2.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "01_single_request.png"), dpi=DPI)
    plt.close(fig)
    print("  [1/6] Single Request chart saved.")


def chart_throughput_vs_concurrency(data: dict, output_dir: str):
    """차트 2: 동시성 증가에 따른 Token Throughput 라인 차트."""
    by_fw = _get_results_by_scenario(data, "concurrent_load")
    if not by_fw:
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    for fw in ["sglang", "vllm", "ollama"]:
        if fw not in by_fw:
            continue
        results = sorted(by_fw[fw], key=lambda r: r["concurrency"])
        concs = [r["concurrency"] for r in results]
        thrpts = [r["total_token_throughput"] for r in results]
        ax.plot(concs, thrpts, "o-", label=FW_LABELS[fw], color=FW_COLORS[fw], linewidth=2, markersize=8)

    ax.set_xlabel("Concurrency")
    ax.set_ylabel("Token Throughput (tok/s)")
    ax.set_title("Throughput vs Concurrency")
    ax.legend()
    ax.grid(alpha=0.3)
    ax.set_xticks(sorted({r["concurrency"] for results in by_fw.values() for r in results}))

    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "02_throughput_vs_concurrency.png"), dpi=DPI)
    plt.close(fig)
    print("  [2/6] Throughput vs Concurrency chart saved.")


def chart_latency_vs_concurrency(data: dict, output_dir: str):
    """차트 3: 동시성 증가에 따른 p99 Latency 라인 차트."""
    by_fw = _get_results_by_scenario(data, "concurrent_load")
    if not by_fw:
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    for fw in ["sglang", "vllm", "ollama"]:
        if fw not in by_fw:
            continue
        results = sorted(by_fw[fw], key=lambda r: r["concurrency"])
        concs = [r["concurrency"] for r in results]
        p99s = [r["p99_latency_ms"] for r in results]
        ax.plot(concs, p99s, "s--", label=FW_LABELS[fw], color=FW_COLORS[fw], linewidth=2, markersize=8)

    ax.set_xlabel("Concurrency")
    ax.set_ylabel("p99 Latency (ms)")
    ax.set_title("p99 Latency vs Concurrency")
    ax.legend()
    ax.grid(alpha=0.3)
    ax.set_xticks(sorted({r["concurrency"] for results in by_fw.values() for r in results}))

    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "03_latency_vs_concurrency.png"), dpi=DPI)
    plt.close(fig)
    print("  [3/6] Latency vs Concurrency chart saved.")


def chart_prefix_cache(data: dict, output_dir: str):
    """차트 4: Prefix Cache — 첫 5개 vs 나머지 TTFT 비교."""
    by_fw = _get_results_by_scenario(data, "prefix_cache")
    if not by_fw:
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    frameworks = [fw for fw in ["sglang", "vllm", "ollama"] if fw in by_fw]
    x = np.arange(len(frameworks))
    width = 0.35

    first5_vals = []
    later_vals = []

    for fw in frameworks:
        r = by_fw[fw][0]
        first5 = r.get("first_5_avg_ttft_ms", 0) or r.get("avg_ttft_ms", 0)
        later = r.get("later_avg_ttft_ms", 0) or r.get("avg_ttft_ms", 0)
        first5_vals.append(first5)
        later_vals.append(later)

    ax.bar(x - width / 2, first5_vals, width, label="First 5 Requests (Cold)", color="#EF5350")
    ax.bar(x + width / 2, later_vals, width, label="Remaining Requests (Cached)", color="#66BB6A")

    ax.set_xlabel("Framework")
    ax.set_ylabel("Avg TTFT (ms)")
    ax.set_title("Prefix Cache — TTFT Comparison (Cold vs Cached)")
    ax.set_xticks(x)
    ax.set_xticklabels([FW_LABELS[fw] for fw in frameworks])
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "04_prefix_cache.png"), dpi=DPI)
    plt.close(fig)
    print("  [4/6] Prefix Cache chart saved.")


def chart_korean_vs_english(data: dict, output_dir: str):
    """차트 5: 한국어 vs 영어 처리량 비교."""
    ko_scenarios = set()
    en_scenarios = set()
    for fw_data in data.values():
        for r in fw_data.get("results", []):
            s = r["scenario"]
            if s.startswith("korean_korean_"):
                ko_scenarios.add(s)
            elif s.startswith("korean_english_"):
                en_scenarios.add(s)

    if not ko_scenarios and not en_scenarios:
        return

    fig, ax = plt.subplots(figsize=(12, 6))
    frameworks = [fw for fw in ["sglang", "vllm", "ollama"] if fw in data]

    # 한국어/영어 각각의 평균 throughput
    x = np.arange(len(frameworks))
    width = 0.35

    ko_thrpts = []
    en_thrpts = []

    for fw in frameworks:
        fw_results = data[fw].get("results", [])
        ko_vals = [r["total_token_throughput"] for r in fw_results
                   if r["scenario"].startswith("korean_korean_") and r["concurrency"] == 1]
        en_vals = [r["total_token_throughput"] for r in fw_results
                   if r["scenario"].startswith("korean_english_") and r["concurrency"] == 1]
        ko_thrpts.append(sum(ko_vals) / len(ko_vals) if ko_vals else 0)
        en_thrpts.append(sum(en_vals) / len(en_vals) if en_vals else 0)

    ax.bar(x - width / 2, ko_thrpts, width, label="Korean", color="#E91E63")
    ax.bar(x + width / 2, en_thrpts, width, label="English", color="#3F51B5")

    ax.set_xlabel("Framework")
    ax.set_ylabel("Token Throughput (tok/s)")
    ax.set_title("Korean vs English — Single Request Throughput")
    ax.set_xticks(x)
    ax.set_xticklabels([FW_LABELS[fw] for fw in frameworks])
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "05_korean_vs_english.png"), dpi=DPI)
    plt.close(fig)
    print("  [5/6] Korean vs English chart saved.")


def chart_gpu_memory(data: dict, output_dir: str):
    """차트 6: 프레임워크별 피크 GPU 메모리 사용량."""
    frameworks = [fw for fw in ["sglang", "vllm", "ollama"] if fw in data]
    if not frameworks:
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    peak_mems = []
    for fw in frameworks:
        results = data[fw].get("results", [])
        # peak_memory_mb가 있으면 사용, 없으면 gpu_memory_mb 폴백
        peaks = [r.get("peak_memory_mb", 0) or r.get("gpu_memory_mb", 0) for r in results]
        peak_mems.append(max(peaks) if peaks else 0)

    bars = ax.bar(
        [FW_LABELS[fw] for fw in frameworks],
        peak_mems,
        color=[FW_COLORS[fw] for fw in frameworks],
        width=0.5,
    )

    # 바 위에 값 표시
    for bar, val in zip(bars, peak_mems):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 200,
                    f"{val:.0f} MB", ha="center", va="bottom", fontweight="bold")

    ax.set_ylabel("Peak GPU Memory (MB)")
    ax.set_title("Peak GPU Memory Usage by Framework")
    ax.grid(axis="y", alpha=0.3)

    # A100 80GB 참조선
    ax.axhline(y=81920, color="red", linestyle="--", alpha=0.5, label="A100 80GB Total")
    ax.legend()

    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "06_gpu_memory.png"), dpi=DPI)
    plt.close(fig)
    print("  [6/6] GPU Memory chart saved.")


def generate_all_charts(results_dir: str, output_dir: str | None = None):
    """모든 차트를 생성.

    Args:
        results_dir: results/ 디렉토리 경로
        output_dir: 차트 출력 디렉토리 (기본: results/summary/charts/)
    """
    if output_dir is None:
        output_dir = os.path.join(results_dir, "summary", "charts")
    os.makedirs(output_dir, exist_ok=True)

    print(f"\nLoading results from {results_dir}...")
    data = load_all_results(results_dir)
    if not data:
        print("No result files found. Run benchmarks first.")
        return

    print(f"Found results for: {', '.join(FW_LABELS.get(fw, fw) for fw in data)}")
    print(f"Generating charts to {output_dir}...\n")

    chart_single_request(data, output_dir)
    chart_throughput_vs_concurrency(data, output_dir)
    chart_latency_vs_concurrency(data, output_dir)
    chart_prefix_cache(data, output_dir)
    chart_korean_vs_english(data, output_dir)
    chart_gpu_memory(data, output_dir)

    print(f"\nAll charts saved to {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Generate benchmark visualization charts")
    parser.add_argument(
        "--results-dir",
        default=None,
        help="Results directory (default: <project>/results/)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Chart output directory (default: results/summary/charts/)",
    )
    args = parser.parse_args()

    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    results_dir = args.results_dir or os.path.join(project_dir, "results")
    generate_all_charts(results_dir, args.output_dir)


if __name__ == "__main__":
    main()
