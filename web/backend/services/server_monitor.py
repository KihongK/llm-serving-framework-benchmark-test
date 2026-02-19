"""GPU polling and framework health check service."""

import subprocess

import aiohttp

from bench.config import FRAMEWORK_CONFIG

from ..config import FRAMEWORK_LABELS


def get_gpu_stats() -> dict:
    """Query GPU memory and utilization via nvidia-smi."""
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


async def check_server_health(framework: str) -> dict:
    """Check if a framework server is healthy."""
    config = FRAMEWORK_CONFIG.get(framework)
    if not config:
        return {
            "framework": framework,
            "label": framework,
            "healthy": False,
            "base_url": "",
        }

    base_url = config["base_url"]
    health_paths = ["/health", "/v1/models", "/api/tags"]
    healthy = False

    async with aiohttp.ClientSession() as session:
        for path in health_paths:
            try:
                async with session.get(
                    f"{base_url}{path}",
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as resp:
                    if resp.status == 200:
                        healthy = True
                        break
            except Exception:
                continue

    return {
        "framework": framework,
        "label": FRAMEWORK_LABELS.get(framework, framework),
        "healthy": healthy,
        "base_url": base_url,
    }


async def check_all_health() -> list[dict]:
    """Check health for all 3 frameworks."""
    results = []
    for fw in ["sglang", "vllm", "ollama"]:
        results.append(await check_server_health(fw))
    return results
