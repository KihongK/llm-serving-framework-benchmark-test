"""5개 시나리오 함수."""

import statistics
import time

import aiohttp
from tqdm import tqdm

from .client import (
    ScenarioResult,
    get_gpu_stats,
    run_concurrent_requests,
    send_request,
)
from .config import FRAMEWORK_CONFIG
from .prompts import (
    ENGLISH_CONTRAST_PROMPTS,
    KOREAN_PROMPTS,
    SYSTEM_PROMPT_LONG,
    generate_prompt,
)


async def scenario_single_request(framework: str, warmup: int = 3) -> list[ScenarioResult]:
    """시나리오 1: 단일 요청 기본 성능."""
    print(f"\n{'='*60}")
    print(f"[Scenario 1] Single Request Baseline - {framework}")
    print(f"{'='*60}")

    input_lengths = [128, 512, 1024]
    output_tokens = 256
    num_requests = 10
    all_results = []

    for input_len in input_lengths:
        print(f"\n--- Input: {input_len} tokens, Output: {output_tokens} tokens ---")
        prompt = generate_prompt(input_len)
        messages = [
            {"role": "user", "content": prompt + f"\nPlease write a detailed response about AI technology trends."}
        ]
        messages_list = [messages] * (warmup + num_requests)

        results, elapsed = await run_concurrent_requests(
            framework, messages_list, output_tokens, concurrency=1
        )

        # 워밍업 제외
        results = results[warmup:]

        sr = ScenarioResult(
            scenario="single_request",
            framework=framework,
            concurrency=1,
            input_tokens=input_len,
            output_tokens=output_tokens,
            num_requests=num_requests,
            results=results,
            total_time_sec=round(elapsed, 2),
        )

        gpu = get_gpu_stats()
        sr.gpu_memory_mb = gpu["memory_used_mb"]
        sr.gpu_utilization_pct = gpu["gpu_utilization_pct"]
        sr.compute_aggregates()
        all_results.append(sr)

        print(f"  TTFT (avg): {sr.avg_ttft_ms} ms")
        print(f"  Throughput: {sr.total_token_throughput} tok/s")
        print(f"  Latency p50/p95/p99: {sr.p50_latency_ms}/{sr.p95_latency_ms}/{sr.p99_latency_ms} ms")
        print(f"  Success rate: {sr.success_rate}%")

    return all_results


async def scenario_concurrent_load(framework: str) -> list[ScenarioResult]:
    """시나리오 2: 동시 요청 부하 테스트."""
    print(f"\n{'='*60}")
    print(f"[Scenario 2] Concurrent Load Test - {framework}")
    print(f"{'='*60}")

    concurrency_levels = [1, 8, 16, 32, 64]
    input_tokens = 512
    output_tokens = 256
    total_requests = 100
    all_results = []

    prompt = generate_prompt(input_tokens)
    messages = [
        {"role": "user", "content": prompt + "\nSummarize the key points about modern AI systems."}
    ]

    for conc in concurrency_levels:
        print(f"\n--- Concurrency: {conc}, Total Requests: {total_requests} ---")
        messages_list = [messages] * total_requests

        results, elapsed = await run_concurrent_requests(
            framework, messages_list, output_tokens, concurrency=conc
        )

        sr = ScenarioResult(
            scenario="concurrent_load",
            framework=framework,
            concurrency=conc,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            num_requests=total_requests,
            results=results,
            total_time_sec=round(elapsed, 2),
        )

        gpu = get_gpu_stats()
        sr.gpu_memory_mb = gpu["memory_used_mb"]
        sr.gpu_utilization_pct = gpu["gpu_utilization_pct"]
        sr.compute_aggregates()
        all_results.append(sr)

        print(f"  Request throughput: {sr.request_throughput} req/s")
        print(f"  Token throughput: {sr.total_token_throughput} tok/s")
        print(f"  TTFT p50/p95: {sr.p50_ttft_ms}/{sr.p95_ttft_ms} ms")
        print(f"  Latency p50/p95/p99: {sr.p50_latency_ms}/{sr.p95_latency_ms}/{sr.p99_latency_ms} ms")
        print(f"  Success rate: {sr.success_rate}%")

    return all_results


async def scenario_long_context(framework: str) -> list[ScenarioResult]:
    """시나리오 3: 긴 입력 처리 테스트."""
    print(f"\n{'='*60}")
    print(f"[Scenario 3] Long Context Test - {framework}")
    print(f"{'='*60}")

    input_lengths = [2048, 4096]
    concurrency_levels = [1, 8]
    output_tokens = 256
    num_requests = 5
    all_results = []

    for input_len in input_lengths:
        prompt = generate_prompt(input_len)
        messages = [
            {"role": "user", "content": prompt + "\nProvide a comprehensive analysis of the above content."}
        ]

        for conc in concurrency_levels:
            print(f"\n--- Input: {input_len} tokens, Concurrency: {conc} ---")
            messages_list = [messages] * num_requests

            results, elapsed = await run_concurrent_requests(
                framework, messages_list, output_tokens, concurrency=conc
            )

            sr = ScenarioResult(
                scenario="long_context",
                framework=framework,
                concurrency=conc,
                input_tokens=input_len,
                output_tokens=output_tokens,
                num_requests=num_requests,
                results=results,
                total_time_sec=round(elapsed, 2),
            )

            gpu = get_gpu_stats()
            sr.gpu_memory_mb = gpu["memory_used_mb"]
            sr.gpu_utilization_pct = gpu["gpu_utilization_pct"]
            sr.compute_aggregates()
            all_results.append(sr)

            print(f"  TTFT (avg): {sr.avg_ttft_ms} ms")
            print(f"  Throughput: {sr.total_token_throughput} tok/s")
            print(f"  Latency p50/p95/p99: {sr.p50_latency_ms}/{sr.p95_latency_ms}/{sr.p99_latency_ms} ms")
            print(f"  GPU Memory: {sr.gpu_memory_mb} MB")

    return all_results


async def scenario_prefix_cache(framework: str) -> list[ScenarioResult]:
    """시나리오 4: 접두사 캐시 효율성 테스트."""
    print(f"\n{'='*60}")
    print(f"[Scenario 4] Prefix Cache Efficiency Test - {framework}")
    print(f"{'='*60}")

    output_tokens = 256
    num_requests = 50

    # 공통 시스템 프롬프트 + 다른 사용자 질문
    user_questions = [
        f"Question {i}: Explain the concept of {topic} in detail."
        for i, topic in enumerate([
            "neural networks", "gradient descent", "attention mechanism",
            "transformer architecture", "tokenization", "embedding layers",
            "backpropagation", "loss functions", "regularization",
            "batch normalization", "dropout", "learning rate scheduling",
            "convolutional networks", "recurrent networks", "generative models",
            "reinforcement learning", "transfer learning", "fine-tuning",
            "prompt engineering", "few-shot learning", "chain of thought",
            "model quantization", "knowledge distillation", "model pruning",
            "distributed training", "tensor parallelism", "pipeline parallelism",
            "data parallelism", "mixed precision training", "gradient accumulation",
            "beam search", "nucleus sampling", "temperature scaling",
            "top-k sampling", "repetition penalty", "length penalty",
            "KV cache", "flash attention", "multi-head attention",
            "positional encoding", "rotary embeddings", "layer normalization",
            "residual connections", "feed-forward networks", "softmax function",
            "cross-entropy loss", "perplexity", "BLEU score",
            "model serving", "inference optimization",
        ], start=1)
    ]

    messages_list = [
        [
            {"role": "system", "content": SYSTEM_PROMPT_LONG},
            {"role": "user", "content": q},
        ]
        for q in user_questions[:num_requests]
    ]

    print(f"\n--- Shared System Prompt (~2048 tokens) + {num_requests} different questions ---")
    print(f"--- Concurrency: 1 (sequential, to measure cache effect) ---")

    # 순차 실행으로 캐시 효과 측정
    config = FRAMEWORK_CONFIG[framework]
    url = f"{config['base_url']}{config['chat_endpoint']}"

    all_request_results = []
    start = time.perf_counter()

    connector = aiohttp.TCPConnector(limit=5)
    async with aiohttp.ClientSession(connector=connector) as session:
        for i, messages in enumerate(tqdm(messages_list, desc=f"{framework} prefix-cache", ncols=80)):
            payload = {
                "model": config["model"],
                "messages": messages,
                "max_tokens": output_tokens,
                "temperature": 0,
                "stream": True,
            }
            result = await send_request(session, url, payload)
            all_request_results.append(result)

    elapsed = time.perf_counter() - start

    sr = ScenarioResult(
        scenario="prefix_cache",
        framework=framework,
        concurrency=1,
        input_tokens=2048,
        output_tokens=output_tokens,
        num_requests=num_requests,
        results=all_request_results,
        total_time_sec=round(elapsed, 2),
    )

    gpu = get_gpu_stats()
    sr.gpu_memory_mb = gpu["memory_used_mb"]
    sr.gpu_utilization_pct = gpu["gpu_utilization_pct"]
    sr.compute_aggregates()

    # 첫 5개 vs 나머지 TTFT 비교
    first_ttfts = [r.ttft_ms for r in all_request_results[:5] if r.success and r.ttft_ms > 0]
    later_ttfts = [r.ttft_ms for r in all_request_results[5:] if r.success and r.ttft_ms > 0]

    print(f"\n  Overall TTFT (avg): {sr.avg_ttft_ms} ms")
    if first_ttfts:
        print(f"  First 5 requests TTFT (avg): {round(statistics.mean(first_ttfts), 2)} ms")
    if later_ttfts:
        print(f"  Remaining requests TTFT (avg): {round(statistics.mean(later_ttfts), 2)} ms")
    if first_ttfts and later_ttfts:
        speedup = statistics.mean(first_ttfts) / statistics.mean(later_ttfts)
        print(f"  Cache speedup (first/later TTFT): {round(speedup, 2)}x")
    print(f"  Token throughput: {sr.total_token_throughput} tok/s")
    print(f"  Success rate: {sr.success_rate}%")

    return [sr]


async def scenario_korean(framework: str, warmup: int = 3) -> list[ScenarioResult]:
    """시나리오 5: 한국어 성능 테스트.

    한국어/영어 대조 프롬프트로 토큰 효율성과 처리량을 비교한다.
    """
    print(f"\n{'='*60}")
    print(f"[Scenario 5] Korean Language Performance Test - {framework}")
    print(f"{'='*60}")

    output_tokens = 256
    num_requests = 10
    concurrency_levels = [1, 8]
    all_results = []

    prompt_pairs = [
        ("short_question", KOREAN_PROMPTS["short_question"], ENGLISH_CONTRAST_PROMPTS["short_question"]),
        ("essay", KOREAN_PROMPTS["essay"], ENGLISH_CONTRAST_PROMPTS["essay"]),
        ("technical", KOREAN_PROMPTS["technical"], ENGLISH_CONTRAST_PROMPTS["technical"]),
        ("long_summarize_ko", KOREAN_PROMPTS["summarize_prefix"] + generate_prompt(512, lang="ko"), None),
        ("long_summarize_en", ENGLISH_CONTRAST_PROMPTS["summarize_prefix"] + generate_prompt(512, lang="en"), None),
    ]

    for conc in concurrency_levels:
        for prompt_name, prompt_text, contrast_text in prompt_pairs:
            lang = "ko" if "ko" in prompt_name or prompt_name in ("short_question", "essay", "technical") else "en"
            # 한국어 프롬프트 테스트
            if prompt_text:
                label = f"korean_{prompt_name}" if lang == "ko" else f"english_{prompt_name}"
                print(f"\n--- {label}, Concurrency: {conc} ---")

                messages = [{"role": "user", "content": prompt_text}]
                messages_list = [messages] * (warmup + num_requests) if conc == 1 else [messages] * num_requests

                results, elapsed = await run_concurrent_requests(
                    framework, messages_list, output_tokens, concurrency=conc
                )

                if conc == 1:
                    results = results[warmup:]

                sr = ScenarioResult(
                    scenario=f"korean_{label}",
                    framework=framework,
                    concurrency=conc,
                    input_tokens=0,  # 실제 토큰 수는 모델마다 다름
                    output_tokens=output_tokens,
                    num_requests=num_requests,
                    results=results,
                    total_time_sec=round(elapsed, 2),
                )

                gpu = get_gpu_stats()
                sr.gpu_memory_mb = gpu["memory_used_mb"]
                sr.gpu_utilization_pct = gpu["gpu_utilization_pct"]
                sr.compute_aggregates()
                all_results.append(sr)

                print(f"  TTFT (avg): {sr.avg_ttft_ms} ms")
                print(f"  Throughput: {sr.total_token_throughput} tok/s")
                print(f"  Latency p50/p95/p99: {sr.p50_latency_ms}/{sr.p95_latency_ms}/{sr.p99_latency_ms} ms")
                print(f"  Avg tokens generated: {sum(r.tokens_generated for r in results if r.success) / max(len([r for r in results if r.success]), 1):.0f}")
                print(f"  Success rate: {sr.success_rate}%")

            # 영어 대조 프롬프트 테스트 (contrast_text가 있을 때만)
            if contrast_text and conc == 1:
                label_en = f"english_contrast_{prompt_name}"
                print(f"\n--- {label_en}, Concurrency: {conc} ---")

                messages_en = [{"role": "user", "content": contrast_text}]
                messages_list_en = [messages_en] * (warmup + num_requests)

                results_en, elapsed_en = await run_concurrent_requests(
                    framework, messages_list_en, output_tokens, concurrency=1
                )
                results_en = results_en[warmup:]

                sr_en = ScenarioResult(
                    scenario=f"korean_{label_en}",
                    framework=framework,
                    concurrency=1,
                    input_tokens=0,
                    output_tokens=output_tokens,
                    num_requests=num_requests,
                    results=results_en,
                    total_time_sec=round(elapsed_en, 2),
                )

                gpu_en = get_gpu_stats()
                sr_en.gpu_memory_mb = gpu_en["memory_used_mb"]
                sr_en.gpu_utilization_pct = gpu_en["gpu_utilization_pct"]
                sr_en.compute_aggregates()
                all_results.append(sr_en)

                print(f"  TTFT (avg): {sr_en.avg_ttft_ms} ms")
                print(f"  Throughput: {sr_en.total_token_throughput} tok/s")
                print(f"  Avg tokens generated: {sum(r.tokens_generated for r in results_en if r.success) / max(len([r for r in results_en if r.success]), 1):.0f}")

    # 한국어 vs 영어 요약 비교
    print(f"\n{'='*60}")
    print(f"Korean vs English Comparison Summary")
    print(f"{'='*60}")
    for sr in all_results:
        print(
            f"  [{sr.scenario}] conc={sr.concurrency} "
            f"| TTFT={sr.avg_ttft_ms}ms | throughput={sr.total_token_throughput}tok/s "
            f"| p99={sr.p99_latency_ms}ms | success={sr.success_rate}%"
        )

    return all_results


SCENARIOS = {
    "single": scenario_single_request,
    "concurrent": scenario_concurrent_load,
    "long_context": scenario_long_context,
    "prefix_cache": scenario_prefix_cache,
    "korean": scenario_korean,
}
