"""CLI 엔트리포인트 — python -m bench."""

import argparse
import asyncio
import json
import os
import time

from .client import ScenarioResult, TrialSummary, get_gpu_stats
from .config import FRAMEWORK_CONFIG, MODEL_PRESETS
from .scenarios import SCENARIOS


async def run_benchmark(
    framework: str,
    scenarios: list[str],
    output_dir: str,
    model_preset: str = "gpt-oss-20b",
    trials: int = 1,
):
    """벤치마크 실행."""
    from .client import check_server_health

    # 서버 상태 확인
    config = FRAMEWORK_CONFIG[framework]
    print(f"\nChecking {framework} server at {config['base_url']}...")
    healthy = await check_server_health(config["base_url"])
    if not healthy:
        print(f"ERROR: {framework} server is not responding at {config['base_url']}")
        print("Please start the server first. See docs/benchmark_design.md for instructions.")
        return

    print(f"Server is healthy. Starting benchmark...")
    print(f"Model: {config['model']}")
    if trials > 1:
        print(f"Trials: {trials}")

    all_results = []
    trial_summaries = []

    for scenario_name in scenarios:
        if scenario_name not in SCENARIOS:
            print(f"Unknown scenario: {scenario_name}. Skipping.")
            continue
        scenario_func = SCENARIOS[scenario_name]

        if trials == 1:
            results = await scenario_func(framework)
            all_results.extend(results)
        else:
            # 여러 trial 실행: 동일 시나리오/설정별로 그룹화하여 mean±std 계산
            trial_results_by_key: dict[str, list[ScenarioResult]] = {}
            for trial_idx in range(trials):
                print(f"\n{'#'*60}")
                print(f"  Trial {trial_idx + 1}/{trials} — {scenario_name}")
                print(f"{'#'*60}")
                results = await scenario_func(framework)
                for r in results:
                    key = f"{r.scenario}|{r.concurrency}|{r.input_tokens}"
                    trial_results_by_key.setdefault(key, []).append(r)

            # 각 그룹의 마지막 trial 결과를 대표값으로 사용
            for key, group in trial_results_by_key.items():
                all_results.append(group[-1])
                if len(group) > 1:
                    ts = TrialSummary.from_results(group)
                    trial_summaries.append(ts)

    # 결과 저장 (모델명을 파일명에 포함하여 다른 모델 결과와 구분)
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{framework}_{model_preset}_results.json")
    output_data = {
        "framework": framework,
        "model_preset": model_preset,
        "model": config["model"],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "server_config": config,
        "gpu_info": get_gpu_stats(),
        "trials": trials,
        "results": [r.to_dict() for r in all_results],
    }

    if trial_summaries:
        output_data["trial_summary"] = [ts.to_dict() for ts in trial_summaries]

    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"Results saved to: {output_file}")
    print(f"{'='*60}")

    # 요약 출력
    print(f"\n{'='*60}")
    print(f"SUMMARY - {framework} ({config['model']})")
    print(f"{'='*60}")
    for r in all_results:
        print(
            f"  [{r.scenario}] conc={r.concurrency} in={r.input_tokens} "
            f"| TTFT={r.avg_ttft_ms}ms | throughput={r.total_token_throughput}tok/s "
            f"| p99={r.p99_latency_ms}ms | success={r.success_rate}%"
        )

    if trial_summaries:
        print(f"\n{'='*60}")
        print(f"TRIAL SUMMARY (mean ± std, {trials} trials)")
        print(f"{'='*60}")
        for ts in trial_summaries:
            print(
                f"  [{ts.scenario}] "
                f"TTFT={ts.mean_ttft_ms}±{ts.std_ttft_ms}ms "
                f"| throughput={ts.mean_throughput}±{ts.std_throughput}tok/s "
                f"| p99={ts.mean_p99_latency_ms}±{ts.std_p99_latency_ms}ms "
                f"| success={ts.mean_success_rate}%"
            )


def main():
    parser = argparse.ArgumentParser(description="LLM Serving Framework Benchmark")
    parser.add_argument(
        "--framework",
        required=True,
        choices=["sglang", "vllm", "ollama"],
        help="Target framework to benchmark",
    )
    parser.add_argument(
        "--scenario",
        default="all",
        help="Comma-separated scenario names: single,concurrent,long_context,prefix_cache,korean,all",
    )
    parser.add_argument(
        "--model",
        default="gpt-oss-20b",
        choices=list(MODEL_PRESETS.keys()),
        help="Model preset to use (default: gpt-oss-20b)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory (default: results/<framework>/)",
    )
    parser.add_argument(
        "--trials",
        type=int,
        default=1,
        help="Number of trial runs per scenario (default: 1). Use >1 for mean±std.",
    )
    args = parser.parse_args()

    # 모델 프리셋 적용
    if args.model in MODEL_PRESETS:
        preset = MODEL_PRESETS[args.model]
        FRAMEWORK_CONFIG[args.framework]["model"] = preset[args.framework]

    if args.scenario == "all":
        scenarios = list(SCENARIOS.keys())
    else:
        scenarios = [s.strip() for s in args.scenario.split(",")]

    # 프로젝트 루트 기준으로 results/<framework>/
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = args.output_dir or os.path.join(project_dir, "results", args.framework)

    print(f"Framework: {args.framework}")
    print(f"Model: {FRAMEWORK_CONFIG[args.framework]['model']}")
    print(f"Scenarios: {', '.join(scenarios)}")
    print(f"Trials: {args.trials}")
    print(f"Output: {output_dir}")

    asyncio.run(run_benchmark(args.framework, scenarios, output_dir, args.model, args.trials))


if __name__ == "__main__":
    main()
