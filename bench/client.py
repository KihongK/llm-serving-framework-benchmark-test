"""RequestResult, ScenarioResult, HTTP 요청, GPU 조회."""

import asyncio
import json
import statistics
import subprocess
import time
from dataclasses import asdict, dataclass, field

import aiohttp
import numpy as np
from tqdm import tqdm

from .config import FRAMEWORK_CONFIG, REQUEST_TIMEOUT


@dataclass
class RequestResult:
    """단일 요청의 결과."""
    success: bool
    ttft_ms: float = 0.0          # Time to First Token (ms)
    total_latency_ms: float = 0.0  # 총 레이턴시 (ms)
    tokens_generated: int = 0      # 생성된 토큰 수
    token_throughput: float = 0.0  # tokens/sec (이 요청 기준)
    error: str = ""


@dataclass
class ScenarioResult:
    """시나리오 실행 결과."""
    scenario: str
    framework: str
    concurrency: int
    input_tokens: int
    output_tokens: int
    num_requests: int
    results: list = field(default_factory=list)

    # 집계 메트릭
    avg_ttft_ms: float = 0.0
    p50_ttft_ms: float = 0.0
    p95_ttft_ms: float = 0.0
    p99_ttft_ms: float = 0.0
    avg_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    total_token_throughput: float = 0.0
    request_throughput: float = 0.0
    success_rate: float = 0.0
    total_time_sec: float = 0.0
    gpu_memory_mb: float = 0.0
    gpu_utilization_pct: float = 0.0

    def compute_aggregates(self):
        """개별 결과로부터 집계 메트릭 계산."""
        successful = [r for r in self.results if r.success]
        if not successful:
            return

        self.success_rate = len(successful) / len(self.results) * 100

        ttfts = [r.ttft_ms for r in successful if r.ttft_ms > 0]
        latencies = [r.total_latency_ms for r in successful]
        throughputs = [r.token_throughput for r in successful]
        total_tokens = sum(r.tokens_generated for r in successful)

        if ttfts:
            self.avg_ttft_ms = round(statistics.mean(ttfts), 2)
            self.p50_ttft_ms = round(np.percentile(ttfts, 50), 2)
            self.p95_ttft_ms = round(np.percentile(ttfts, 95), 2)
            self.p99_ttft_ms = round(np.percentile(ttfts, 99), 2)

        if latencies:
            self.avg_latency_ms = round(statistics.mean(latencies), 2)
            self.p50_latency_ms = round(np.percentile(latencies, 50), 2)
            self.p95_latency_ms = round(np.percentile(latencies, 95), 2)
            self.p99_latency_ms = round(np.percentile(latencies, 99), 2)

        if self.total_time_sec > 0:
            self.total_token_throughput = round(total_tokens / self.total_time_sec, 2)
            self.request_throughput = round(len(successful) / self.total_time_sec, 2)

    def to_dict(self):
        d = asdict(self)
        d.pop("results", None)
        return d


def get_gpu_stats() -> dict:
    """nvidia-smi로 GPU 메모리 및 활용률 조회."""
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=memory.used,memory.total,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split(",")
            if len(parts) >= 3:
                return {
                    "memory_used_mb": float(parts[0].strip()),
                    "memory_total_mb": float(parts[1].strip()),
                    "gpu_utilization_pct": float(parts[2].strip()),
                }
    except Exception:
        pass
    return {"memory_used_mb": 0, "memory_total_mb": 0, "gpu_utilization_pct": 0}


async def check_server_health(base_url: str) -> bool:
    """서버 health 체크."""
    health_paths = ["/health", "/v1/models", "/api/tags"]
    async with aiohttp.ClientSession() as session:
        for path in health_paths:
            try:
                async with session.get(
                    f"{base_url}{path}", timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        return True
            except Exception:
                continue
    return False


async def send_request(
    session: aiohttp.ClientSession,
    url: str,
    payload: dict,
) -> RequestResult:
    """단일 스트리밍 요청을 보내고 TTFT, 총 레이턴시, 생성 토큰 수를 측정."""
    start_time = time.perf_counter()
    first_token_time = None
    tokens_generated = 0

    try:
        async with session.post(
            url,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
        ) as resp:
            if resp.status != 200:
                body = await resp.text()
                return RequestResult(success=False, error=f"HTTP {resp.status}: {body[:200]}")

            async for line in resp.content:
                decoded = line.decode("utf-8").strip()
                if not decoded or not decoded.startswith("data:"):
                    continue
                data_str = decoded[5:].strip()
                if data_str == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                    choices = data.get("choices", [])
                    if choices:
                        delta = choices[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            if first_token_time is None:
                                first_token_time = time.perf_counter()
                            # Approximate token count by splitting on spaces
                            # More accurate: count SSE chunks with content
                            tokens_generated += 1
                except json.JSONDecodeError:
                    continue

    except asyncio.TimeoutError:
        return RequestResult(
            success=False,
            total_latency_ms=(time.perf_counter() - start_time) * 1000,
            error="Timeout",
        )
    except Exception as e:
        return RequestResult(
            success=False,
            total_latency_ms=(time.perf_counter() - start_time) * 1000,
            error=str(e),
        )

    end_time = time.perf_counter()
    total_latency = (end_time - start_time) * 1000  # ms
    ttft = (first_token_time - start_time) * 1000 if first_token_time else 0.0

    # 생성 시간 (첫 토큰 이후) 기반 throughput
    generation_time = (end_time - first_token_time) if first_token_time else (end_time - start_time)
    tok_throughput = tokens_generated / generation_time if generation_time > 0 else 0.0

    return RequestResult(
        success=True,
        ttft_ms=round(ttft, 2),
        total_latency_ms=round(total_latency, 2),
        tokens_generated=tokens_generated,
        token_throughput=round(tok_throughput, 2),
    )


async def run_concurrent_requests(
    framework: str,
    messages_list: list[list[dict]],
    max_tokens: int,
    concurrency: int,
) -> tuple[list[RequestResult], float]:
    """동시 요청을 실행하고 결과 리스트와 총 소요 시간을 반환."""
    config = FRAMEWORK_CONFIG[framework]
    url = f"{config['base_url']}{config['chat_endpoint']}"

    semaphore = asyncio.Semaphore(concurrency)
    results = []

    async def bounded_request(session, messages):
        async with semaphore:
            payload = {
                "model": config["model"],
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0,
                "stream": True,
            }
            return await send_request(session, url, payload)

    connector = aiohttp.TCPConnector(limit=concurrency + 10)
    async with aiohttp.ClientSession(connector=connector) as session:
        start = time.perf_counter()
        tasks = [bounded_request(session, msgs) for msgs in messages_list]

        with tqdm(total=len(tasks), desc=f"{framework} (c={concurrency})", ncols=80) as pbar:
            for coro in asyncio.as_completed(tasks):
                result = await coro
                results.append(result)
                pbar.update(1)

        elapsed = time.perf_counter() - start

    return results, elapsed
