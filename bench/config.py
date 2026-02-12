"""프레임워크 설정, 모델 프리셋, 상수."""

FRAMEWORK_CONFIG = {
    "sglang": {
        "base_url": "http://localhost:30000",
        "model": "openai/gpt-oss-20b",
        "chat_endpoint": "/v1/chat/completions",
    },
    "vllm": {
        "base_url": "http://localhost:8000",
        "model": "openai/gpt-oss-20b",
        "chat_endpoint": "/v1/chat/completions",
    },
    "ollama": {
        "base_url": "http://localhost:11434",
        "model": "gpt-oss:20b",
        "chat_endpoint": "/v1/chat/completions",
    },
}

# 모델 프리셋: --model 인자로 선택 가능
MODEL_PRESETS = {
    "gpt-oss-20b": {
        "sglang": "openai/gpt-oss-20b",
        "vllm": "openai/gpt-oss-20b",
        "ollama": "gpt-oss:20b",
    },
    "llama3.1-8b": {
        "sglang": "meta-llama/Llama-3.1-8B-Instruct",
        "vllm": "meta-llama/Llama-3.1-8B-Instruct",
        "ollama": "llama3.1:8b",
    },
}

REQUEST_TIMEOUT = 300  # seconds
