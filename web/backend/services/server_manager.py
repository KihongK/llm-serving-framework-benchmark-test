"""Framework server lifecycle management — start, stop, log streaming."""

import asyncio
import os
import signal
import time
from dataclasses import dataclass, field

import aiohttp

from bench.config import MODEL_PRESETS
from ..config import FRAMEWORK_ENVS, SERVER_START_TIMEOUT, SERVER_STOP_TIMEOUT, PROJECT_DIR


@dataclass
class ManagedServer:
    framework: str
    model: str
    status: str = "starting"  # starting, running, stopping, stopped, failed
    process: asyncio.subprocess.Process | None = None
    log_lines: list[str] = field(default_factory=list)
    subscribers: list[asyncio.Queue] = field(default_factory=list)
    started_at: float | None = None
    pid: int | None = None
    managed: bool = True  # True=GUI started, False=externally detected

    def add_log(self, line: str):
        self.log_lines.append(line)
        for q in self.subscribers:
            q.put_nowait(line)


class ServerManager:
    def __init__(self):
        self.server: ManagedServer | None = None
        self._health_task: asyncio.Task | None = None
        self._stream_task: asyncio.Task | None = None
        self._pull_task: asyncio.Task | None = None

    def _resolve_model(self, framework: str, model_preset: str) -> str:
        """Resolve model preset name to framework-specific model path."""
        presets = MODEL_PRESETS.get(model_preset)
        if presets and framework in presets:
            return presets[framework]
        return model_preset

    def _build_command(self, framework: str, model: str) -> list[str]:
        """Build the server launch command for a given framework."""
        env = FRAMEWORK_ENVS[framework]
        resolved = self._resolve_model(framework, model)

        if framework == "sglang":
            return [
                env["python"], "-m", "sglang.launch_server",
                "--model-path", resolved,
                "--tp", "1",
                "--port", str(env["port"]),
                "--mem-fraction-static", "0.85",
            ]
        elif framework == "vllm":
            return [
                env["vllm_bin"], "serve", resolved,
                "--host", "0.0.0.0",
                "--port", str(env["port"]),
                "--gpu-memory-utilization", "0.85",
                "--enable-prefix-caching",
            ]
        elif framework == "ollama":
            return [env["binary"], "serve"]
        else:
            raise ValueError(f"Unknown framework: {framework}")

    def _get_health_url(self, framework: str) -> str:
        port = FRAMEWORK_ENVS[framework]["port"]
        if framework == "ollama":
            return f"http://localhost:{port}/api/tags"
        return f"http://localhost:{port}/health"

    async def _check_health(self, framework: str) -> bool:
        """Check if the server is healthy via HTTP."""
        url = self._get_health_url(framework)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    return resp.status == 200
        except Exception:
            return False

    async def _poll_health(self, server: ManagedServer):
        """Poll health endpoint until server is ready or timeout."""
        deadline = time.monotonic() + SERVER_START_TIMEOUT
        while time.monotonic() < deadline:
            if server.status not in ("starting",):
                return
            if await self._check_health(server.framework):
                server.status = "running"
                server.started_at = time.time()
                server.add_log(f"\n[Server is ready — {server.framework} running on port {FRAMEWORK_ENVS[server.framework]['port']}]\n")
                return
            await asyncio.sleep(2)

        # Timeout
        if server.status == "starting":
            server.status = "failed"
            server.add_log(f"\n[Server failed to start within {SERVER_START_TIMEOUT}s]\n")

    async def _stream_output(self, server: ManagedServer):
        """Read process stdout/stderr and push to log + subscribers."""
        proc = server.process
        if not proc or not proc.stdout:
            return
        try:
            async for line in proc.stdout:
                decoded = line.decode("utf-8", errors="replace")
                server.add_log(decoded)
                # Detect common failures
                if "Address already in use" in decoded:
                    server.status = "failed"
                    server.add_log("\n[Error: Port already in use]\n")
                elif "OutOfMemoryError" in decoded or "CUDA out of memory" in decoded:
                    server.status = "failed"
                    server.add_log("\n[Error: GPU out of memory]\n")

            # Process ended — check if expected
            await proc.wait()
            if server.status in ("starting", "running"):
                server.status = "failed"
                server.add_log(f"\n[Server process exited unexpectedly with code {proc.returncode}]\n")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            server.add_log(f"\n[Stream error: {e}]\n")

    async def _pull_ollama_model(self, server: ManagedServer, model_preset: str):
        """After ollama serve is healthy, pull the model."""
        resolved = self._resolve_model("ollama", model_preset)
        binary = FRAMEWORK_ENVS["ollama"]["binary"]
        server.add_log(f"\n[Pulling model: {resolved}]\n")
        try:
            proc = await asyncio.create_subprocess_exec(
                binary, "pull", resolved,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env={**os.environ, "OLLAMA_HOST": f"0.0.0.0:{FRAMEWORK_ENVS['ollama']['port']}"},
            )
            if proc.stdout:
                async for line in proc.stdout:
                    server.add_log(line.decode("utf-8", errors="replace"))
            await proc.wait()
            if proc.returncode != 0:
                server.add_log(f"\n[Model pull failed with code {proc.returncode}]\n")
            else:
                server.add_log(f"\n[Model {resolved} ready]\n")
        except Exception as e:
            server.add_log(f"\n[Model pull error: {e}]\n")

    async def start_server(self, framework: str, model: str = "gpt-oss-20b"):
        """Start a framework server. Stops any currently running server first."""
        if framework not in FRAMEWORK_ENVS:
            raise ValueError(f"Unknown framework: {framework}")

        # Stop existing server if running
        if self.server and self.server.status in ("starting", "running"):
            await self.stop_server(force=True)

        server = ManagedServer(framework=framework, model=model, managed=True)
        self.server = server

        cmd = self._build_command(framework, model)
        server.add_log(f"$ {' '.join(cmd)}\n")

        try:
            env = {**os.environ}
            if framework == "ollama":
                env["OLLAMA_HOST"] = f"0.0.0.0:{FRAMEWORK_ENVS['ollama']['port']}"

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=PROJECT_DIR,
                env=env,
            )
            server.process = proc
            server.pid = proc.pid

            # Start background tasks
            self._stream_task = asyncio.create_task(self._stream_output(server))
            self._health_task = asyncio.create_task(self._poll_health(server))

            # For ollama, pull model after server is healthy
            if framework == "ollama":
                async def _wait_and_pull():
                    if self._health_task:
                        await self._health_task
                    if server.status == "running":
                        await self._pull_ollama_model(server, model)
                self._pull_task = asyncio.create_task(_wait_and_pull())

        except Exception as e:
            server.status = "failed"
            server.add_log(f"\n[Failed to start: {e}]\n")
            raise

    async def stop_server(self, force: bool = False):
        """Stop the currently managed server."""
        server = self.server
        if not server or server.status in ("stopped", "stopping"):
            return

        # Check if benchmark is running (unless force)
        if not force:
            from .benchmark_runner import runner
            for job in runner.jobs.values():
                if job.status == "running":
                    raise RuntimeError("BENCHMARK_RUNNING")

        server.status = "stopping"
        server.add_log("\n[Stopping server...]\n")

        # Cancel background tasks
        for task in (self._health_task, self._pull_task):
            if task and not task.done():
                task.cancel()

        proc = server.process
        if proc and proc.returncode is None:
            try:
                proc.terminate()
                try:
                    await asyncio.wait_for(proc.wait(), timeout=SERVER_STOP_TIMEOUT)
                except asyncio.TimeoutError:
                    proc.kill()
                    await proc.wait()
                    server.add_log("[Force killed after timeout]\n")
            except ProcessLookupError:
                pass

        # For ollama, also kill any lingering serve processes
        if server.framework == "ollama":
            try:
                kill_proc = await asyncio.create_subprocess_exec(
                    "pkill", "-f", "ollama serve",
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await kill_proc.wait()
            except Exception:
                pass

        # Cancel stream task after process is dead
        if self._stream_task and not self._stream_task.done():
            self._stream_task.cancel()
            try:
                await self._stream_task
            except asyncio.CancelledError:
                pass

        server.status = "stopped"
        server.process = None
        server.add_log("[Server stopped]\n")

        # Signal subscribers that stream is done
        for q in server.subscribers:
            q.put_nowait(None)

    async def detect_external_servers(self):
        """Check if any framework server is already running (started outside GUI)."""
        # Run health checks concurrently to avoid blocking startup
        checks = {fw: self._check_health(fw) for fw in FRAMEWORK_ENVS}
        results = dict(zip(checks.keys(), await asyncio.gather(*checks.values())))
        for fw, healthy in results.items():
            if healthy:
                server = ManagedServer(
                    framework=fw,
                    model="unknown",
                    status="running",
                    managed=False,
                    started_at=time.time(),
                )
                self.server = server
                server.add_log(f"[Detected externally running {fw} server]\n")
                return

    def get_status(self) -> dict:
        """Return current managed server status as a dict."""
        server = self.server
        if not server or server.status == "stopped":
            return {
                "framework": None,
                "model": None,
                "status": "stopped",
                "managed": True,
                "pid": None,
                "uptime_sec": None,
                "log_lines": 0,
            }
        uptime = None
        if server.started_at and server.status == "running":
            uptime = round(time.time() - server.started_at, 1)
        return {
            "framework": server.framework,
            "model": server.model,
            "status": server.status,
            "managed": server.managed,
            "pid": server.pid,
            "uptime_sec": uptime,
            "log_lines": len(server.log_lines),
        }

    def subscribe(self) -> asyncio.Queue | None:
        """Subscribe to server log stream. Returns None if no server."""
        server = self.server
        if not server:
            return None
        q: asyncio.Queue = asyncio.Queue()
        # Send existing log lines
        for line in server.log_lines:
            q.put_nowait(line)
        if server.status in ("stopped", "failed"):
            q.put_nowait(None)
        else:
            server.subscribers.append(q)
        return q


server_manager = ServerManager()
