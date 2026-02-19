"""Analysis service — wraps bench.analyze for structured hypothesis verification."""

from .result_loader import load_all_results


def _get_scenario_results(data: dict, scenario: str) -> dict[str, list[dict]]:
    out = {}
    for fw, fw_data in data.items():
        results = [r for r in fw_data.get("results", []) if r["scenario"] == scenario]
        if results:
            out[fw] = results
    return out


FW_LABELS = {"sglang": "SGLang", "vllm": "vLLM", "ollama": "Ollama"}


def verify_hypotheses_structured(data: dict | None = None) -> list[dict]:
    """Return H1-H5 as structured dicts instead of markdown."""
    if data is None:
        data = load_all_results()
    if not data:
        return [
            {
                "id": f"H{i}",
                "title": t,
                "description": d,
                "verdict": "NO DATA",
                "evidence": ["벤치마크를 먼저 실행하세요."],
            }
            for i, (t, d) in enumerate(
                [
                    ("Prefix Cache", "SGLang의 prefix caching이 vLLM보다 효율적"),
                    ("Concurrent Throughput", "SGLang/vLLM이 동시 요청에서 Ollama보다 월등히 빠름"),
                    ("Single Request", "Ollama가 단일 요청에서 경쟁력 있음"),
                    ("Degradation Pattern", "프레임워크별 성능 저하 패턴이 다름"),
                    ("Korean Efficiency", "한국어/영어 토큰 효율성 차이"),
                ],
                1,
            )
        ]

    hypotheses = []

    # H1: SGLang > vLLM in prefix caching
    h1 = {
        "id": "H1",
        "title": "Prefix Cache Efficiency",
        "description": "SGLang의 prefix caching이 vLLM보다 효율적",
        "verdict": "NO DATA",
        "evidence": [],
    }
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
            h1["verdict"] = "SUPPORTED" if ratio > 1.1 else ("INCONCLUSIVE" if ratio > 0.9 else "NOT SUPPORTED")
            h1["evidence"] = [
                f"SGLang cached TTFT: {sg_later:.1f}ms (speedup: {sg_speedup:.2f}x)",
                f"vLLM cached TTFT: {vl_later:.1f}ms (speedup: {vl_speedup:.2f}x)",
                f"vLLM/SGLang ratio: {ratio:.2f}x",
            ]
    hypotheses.append(h1)

    # H2: SGLang/vLLM >> Ollama in concurrent
    h2 = {
        "id": "H2",
        "title": "Concurrent Throughput",
        "description": "SGLang/vLLM이 동시 요청에서 Ollama보다 월등히 빠름",
        "verdict": "NO DATA",
        "evidence": [],
    }
    cl = _get_scenario_results(data, "concurrent_load")
    if cl:
        target_conc = 32
        thrpts = {}
        for fw in ["sglang", "vllm", "ollama"]:
            if fw in cl:
                match = [r for r in cl[fw] if r["concurrency"] == target_conc]
                if match:
                    thrpts[fw] = match[0]["total_token_throughput"]

        if "ollama" in thrpts and thrpts["ollama"] > 0:
            evidence = []
            for fw in ["sglang", "vllm"]:
                if fw in thrpts:
                    r = thrpts[fw] / thrpts["ollama"]
                    evidence.append(f"{FW_LABELS[fw]}/Ollama throughput ratio (c={target_conc}): {r:.1f}x")
            h2["evidence"] = evidence
            h2["verdict"] = (
                "SUPPORTED"
                if any(thrpts.get(fw, 0) / thrpts["ollama"] > 3 for fw in ["sglang", "vllm"])
                else "INCONCLUSIVE"
            )
        elif thrpts:
            h2["evidence"] = [f"Available frameworks: {', '.join(thrpts.keys())}"]
            h2["verdict"] = "INCONCLUSIVE"
    hypotheses.append(h2)

    # H3: Ollama competitive in single request
    h3 = {
        "id": "H3",
        "title": "Single Request Competitiveness",
        "description": "Ollama가 단일 요청에서 경쟁력 있음 (TTFT 2x 이내)",
        "verdict": "NO DATA",
        "evidence": [],
    }
    sr = _get_scenario_results(data, "single_request")
    if sr:
        ttfts = {}
        for fw in ["sglang", "vllm", "ollama"]:
            if fw in sr:
                match = [r for r in sr[fw] if r["input_tokens"] == 512]
                if match:
                    ttfts[fw] = match[0]["avg_ttft_ms"]
        if "ollama" in ttfts and len(ttfts) >= 2:
            best_other = min(v for k, v in ttfts.items() if k != "ollama")
            ratio = ttfts["ollama"] / best_other if best_other > 0 else float("inf")
            h3["evidence"] = [f"{FW_LABELS[fw]} TTFT (512 tokens): {v:.1f}ms" for fw, v in ttfts.items()]
            h3["evidence"].append(f"Ollama/best-other ratio: {ratio:.2f}x")
            h3["verdict"] = "SUPPORTED" if ratio < 2.0 else "NOT SUPPORTED"
    hypotheses.append(h3)

    # H4: Different degradation patterns
    h4 = {
        "id": "H4",
        "title": "Degradation Patterns",
        "description": "프레임워크별 성능 저하 패턴이 다름",
        "verdict": "NO DATA",
        "evidence": [],
    }
    if cl and len(cl) >= 2:
        evidence = []
        for fw in ["sglang", "vllm", "ollama"]:
            if fw not in cl:
                continue
            results = sorted(cl[fw], key=lambda r: r["concurrency"])
            if len(results) >= 2:
                low = results[0]
                high = results[-1]
                if low["p99_latency_ms"] > 0:
                    deg = high["p99_latency_ms"] / low["p99_latency_ms"]
                    evidence.append(
                        f"{FW_LABELS[fw]}: c={low['concurrency']} -> c={high['concurrency']}, "
                        f"p99 {low['p99_latency_ms']:.0f}ms -> {high['p99_latency_ms']:.0f}ms ({deg:.1f}x)"
                    )
        h4["evidence"] = evidence
        h4["verdict"] = "SUPPORTED" if evidence else "INCONCLUSIVE"
    hypotheses.append(h4)

    # H5: Korean vs English token efficiency
    h5 = {
        "id": "H5",
        "title": "Korean vs English Efficiency",
        "description": "한국어/영어 토큰 효율성 차이",
        "verdict": "NO DATA",
        "evidence": [],
    }
    evidence = []
    for fw in ["sglang", "vllm", "ollama"]:
        if fw not in data:
            continue
        results = data[fw].get("results", [])
        ko_thrpts = [
            r["total_token_throughput"]
            for r in results
            if r["scenario"].startswith("korean_korean_") and r["concurrency"] == 1 and r["total_token_throughput"] > 0
        ]
        en_thrpts = [
            r["total_token_throughput"]
            for r in results
            if r["scenario"].startswith("korean_english_") and r["concurrency"] == 1 and r["total_token_throughput"] > 0
        ]
        if ko_thrpts and en_thrpts:
            ko_avg = sum(ko_thrpts) / len(ko_thrpts)
            en_avg = sum(en_thrpts) / len(en_thrpts)
            ratio = ko_avg / en_avg if en_avg > 0 else 0
            evidence.append(f"{FW_LABELS[fw]}: Korean={ko_avg:.1f} tok/s, English={en_avg:.1f} tok/s (ratio: {ratio:.2f}x)")
    if evidence:
        h5["evidence"] = evidence
        h5["verdict"] = "SUPPORTED"
    hypotheses.append(h5)

    return hypotheses


def get_comparison_data(data: dict | None = None) -> dict:
    """Return structured comparison data for the frontend."""
    if data is None:
        data = load_all_results()
    if not data:
        return {"frameworks": [], "scenarios": {}}

    frameworks = list(data.keys())
    scenarios: dict[str, dict] = {}

    for scenario_name in ["single_request", "concurrent_load", "long_context", "prefix_cache"]:
        by_fw = _get_scenario_results(data, scenario_name)
        if by_fw:
            scenarios[scenario_name] = by_fw

    # Korean scenarios
    ko_data: dict[str, list] = {}
    for fw, fw_data in data.items():
        ko = [r for r in fw_data.get("results", []) if r["scenario"].startswith("korean_")]
        if ko:
            ko_data[fw] = ko
    if ko_data:
        scenarios["korean"] = ko_data

    return {"frameworks": frameworks, "scenarios": scenarios}
