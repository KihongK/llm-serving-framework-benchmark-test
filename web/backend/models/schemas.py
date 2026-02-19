"""Pydantic request/response models."""

from pydantic import BaseModel


class BenchmarkRequest(BaseModel):
    framework: str
    scenarios: list[str] = ["all"]
    model: str = "gpt-oss-20b"
    trials: int = 1


class BenchmarkJob(BaseModel):
    job_id: str
    framework: str
    scenarios: list[str]
    model: str
    trials: int
    status: str = "pending"  # pending, running, completed, failed, cancelled


class BenchmarkStatus(BaseModel):
    job_id: str
    status: str
    framework: str
    progress: str = ""


class GPUStats(BaseModel):
    memory_used_mb: float = 0.0
    memory_total_mb: float = 0.0
    gpu_utilization_pct: float = 0.0


class ServerHealth(BaseModel):
    framework: str
    label: str
    healthy: bool
    base_url: str


class HypothesisResult(BaseModel):
    id: str
    title: str
    description: str
    verdict: str  # SUPPORTED, NOT SUPPORTED, INCONCLUSIVE, NO DATA
    evidence: list[str]


class ServerStartRequest(BaseModel):
    framework: str  # "sglang" | "vllm" | "ollama"
    model: str = "gpt-oss-20b"


class ServerStopRequest(BaseModel):
    force: bool = False


class ManagedServerStatus(BaseModel):
    framework: str | None = None
    model: str | None = None
    status: str = "stopped"  # starting, running, stopping, stopped, failed
    managed: bool = True  # True=GUI started, False=externally detected
    pid: int | None = None
    uptime_sec: float | None = None
    log_lines: int = 0
