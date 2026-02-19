"""Benchmark execution via subprocess + log queue."""

import asyncio
import uuid
from dataclasses import dataclass, field

from ..config import BENCH_PYTHON, PROJECT_DIR


@dataclass
class BenchmarkJob:
    job_id: str
    framework: str
    scenarios: list[str]
    model: str
    trials: int
    status: str = "pending"
    process: asyncio.subprocess.Process | None = None
    log_lines: list[str] = field(default_factory=list)
    subscribers: list[asyncio.Queue] = field(default_factory=list)

    def add_log(self, line: str):
        self.log_lines.append(line)
        for q in self.subscribers:
            q.put_nowait(line)


class BenchmarkRunner:
    def __init__(self):
        self.jobs: dict[str, BenchmarkJob] = {}

    def create_job(
        self,
        framework: str,
        scenarios: list[str],
        model: str = "gpt-oss-20b",
        trials: int = 1,
    ) -> BenchmarkJob:
        job_id = str(uuid.uuid4())[:8]
        job = BenchmarkJob(
            job_id=job_id,
            framework=framework,
            scenarios=scenarios,
            model=model,
            trials=trials,
        )
        self.jobs[job_id] = job
        return job

    async def run_job(self, job: BenchmarkJob):
        """Execute benchmark as subprocess and stream output."""
        job.status = "running"
        scenario_str = ",".join(job.scenarios)

        cmd = [
            BENCH_PYTHON, "-m", "bench",
            "--framework", job.framework,
            "--scenario", scenario_str,
            "--model", job.model,
            "--trials", str(job.trials),
        ]

        job.add_log(f"$ {' '.join(cmd)}\n")

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=PROJECT_DIR,
            )
            job.process = proc

            async for line in proc.stdout:
                decoded = line.decode("utf-8", errors="replace")
                job.add_log(decoded)

            await proc.wait()

            if proc.returncode == 0:
                job.status = "completed"
                job.add_log("\n[Benchmark completed successfully]\n")
            else:
                job.status = "failed"
                job.add_log(f"\n[Benchmark failed with exit code {proc.returncode}]\n")

        except asyncio.CancelledError:
            job.status = "cancelled"
            job.add_log("\n[Benchmark cancelled]\n")
            if job.process:
                job.process.terminate()
        except Exception as e:
            job.status = "failed"
            job.add_log(f"\n[Error: {e}]\n")
        finally:
            job.process = None
            # Signal subscribers that stream is done
            for q in job.subscribers:
                q.put_nowait(None)

    async def cancel_job(self, job_id: str) -> bool:
        job = self.jobs.get(job_id)
        if not job or job.status != "running":
            return False
        if job.process:
            job.process.terminate()
            job.status = "cancelled"
            job.add_log("\n[Benchmark cancelled by user]\n")
            for q in job.subscribers:
                q.put_nowait(None)
            return True
        return False

    async def cancel_all(self):
        for job_id, job in self.jobs.items():
            if job.status == "running":
                await self.cancel_job(job_id)

    def subscribe(self, job_id: str) -> asyncio.Queue | None:
        job = self.jobs.get(job_id)
        if not job:
            return None
        q: asyncio.Queue = asyncio.Queue()
        # Send existing log lines
        for line in job.log_lines:
            q.put_nowait(line)
        if job.status not in ("pending", "running"):
            q.put_nowait(None)  # already done
        else:
            job.subscribers.append(q)
        return q


runner = BenchmarkRunner()
