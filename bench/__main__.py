"""CLI 엔트리포인트 — python -m bench."""

import argparse
import asyncio
import json
import os
import time

from .client import ScenarioResult, get_gpu_stats
from .config import FRAMEWORK_CONFIG, MODEL_PRESETS
from .scenarios import SCENARIOS


async def run_benchmark(framework: str, scenarios: list[str], output_dir: str, model_preset: str = "gpt-oss-20b"):
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

    all_results = []
    for scenario_name in scenarios:
        if scenario_name not in SCENARIOS:
            print(f"Unknown scenario: {scenario_name}. Skipping.")
            continue
        scenario_func = SCENARIOS[scenario_name]
        results = await scenario_func(framework)
        all_results.extend(results)

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
        "results": [r.to_dict() for r in all_results],
    }

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
        help="Comma-separated scenario names: single,concurrent,long_context,prefix_cache,all",
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
    print(f"Output: {output_dir}")

    asyncio.run(run_benchmark(args.framework, scenarios, output_dir, args.model))


if __name__ == "__main__":
    main()
