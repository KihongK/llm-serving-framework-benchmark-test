"""Web server configuration."""

import os

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RESULTS_DIR = os.path.join(PROJECT_DIR, "results")
BENCH_ENV = os.path.join(PROJECT_DIR, "bench", "bench_env")
BENCH_PYTHON = os.path.join(BENCH_ENV, "bin", "python")

WEB_HOST = "0.0.0.0"
WEB_PORT = 8080

FRAMEWORKS = ["sglang", "vllm", "ollama"]
FRAMEWORK_LABELS = {"sglang": "SGLang", "vllm": "vLLM", "ollama": "Ollama"}
FRAMEWORK_COLORS = {"sglang": "#2196F3", "vllm": "#FF9800", "ollama": "#4CAF50"}

# Framework environment paths and ports for server management
FRAMEWORK_ENVS = {
    "sglang": {
        "python": os.path.join(PROJECT_DIR, "sglang", "sglang_env", "bin", "python"),
        "port": 30000,
    },
    "vllm": {
        "vllm_bin": os.path.join(PROJECT_DIR, "vllm", "vllm_env", "bin", "vllm"),
        "port": 8000,
    },
    "ollama": {
        "binary": "/usr/local/bin/ollama",
        "port": 11434,
    },
}

SERVER_START_TIMEOUT = 120  # seconds to wait for health check
SERVER_STOP_TIMEOUT = 10    # seconds before SIGKILL fallback
