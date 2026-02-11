# CLAUDE.md

Claude Code (claude.ai/code) 가이드 문서.

## 프로젝트 개요

LLM serving framework 비교 프로젝트. vLLM, SGLang, Ollama 3개 프레임워크를 동일 조건에서 벤치마크하고, 성능·특성·장단점을 비교하는 기술 블로그를 작성한다.

## 벤치마크 서버 환경 (A100)

| 항목 | 스펙 |
|------|------|
| OS | Ubuntu 22.04.3 LTS |
| GPU | NVIDIA A100-SXM4-80GB (80 GB VRAM, NVLink) |
| CPU | Intel Xeon Platinum 8468, 2 Socket, 96 Core / 192 Thread |
| RAM | ~1 TiB |
| NVIDIA Driver | 570.86.10 |
| CUDA (nvcc) | 12.1 |

## 디렉토리 구조

```
/home/work/serving_framework/
    sglang/          # 소스 클론 (v0.5.6.post2)
    vllm/            # 소스 클론 (v0.16.0rc1)
    ollama/          # 소스 클론 (v0.15.6)
    blog/            # 블로그 작성
    docs/            # 문서·계획
    results/         # 벤치마크 결과 (sglang/, vllm/, ollama/, summary/)
    CLAUDE.md
```

## 초기 세팅

### 1. uv 설치

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. 소스 클론

```bash
git clone https://github.com/sgl-project/sglang.git
git -C sglang checkout v0.5.6.post2

git clone https://github.com/vllm-project/vllm.git
git -C vllm checkout v0.16.0rc1

git clone https://github.com/ollama/ollama.git
git -C ollama checkout v0.15.6
```

### 3. 프레임워크별 venv 생성 및 패키지 설치

소스 빌드가 아닌 **pip pre-built wheels**로 설치한다 (소스 빌드 시 이슈 발생).
프레임워크별 독립 가상환경을 사용한다. Python 3.12 기준.

```bash
# SGLang
uv venv sglang/sglang_env --python 3.12
source sglang/sglang_env/bin/activate
uv pip install "sglang[all]==0.5.6.post2"
deactivate

# vLLM
uv venv vllm/vllm_env --python 3.12
source vllm/vllm_env/bin/activate
uv pip install vllm
deactivate

# Ollama (Go 바이너리 — 별도 설치)
# https://ollama.com/download/linux
curl -fsSL https://ollama.com/install.sh | sh
```

### 설치 현황

| Framework | 가상환경 | pip 설치 버전 | 상태 |
|-----------|---------|--------------|------|
| SGLang | `sglang/sglang_env/` | 0.5.6.post2 | 설치 완료 |
| vLLM | `vllm/vllm_env/` | — | venv 생성됨, pip 패키지 미설치 |
| Ollama | (Go 바이너리) | — | 미설치 |

```bash
# SGLang 환경 활성화
source sglang/sglang_env/bin/activate

# vLLM 환경 활성화
source vllm/vllm_env/bin/activate
```

## 벤치마크 대상 모델

| 모델 | 용도 | TP |
|------|------|----|
| `openai/gpt-oss-20b` | 기본 벤치마크 모델 | 1 |

## 비교 원칙

- **동일 모델**: 모든 프레임워크에서 `openai/gpt-oss-20b` 사용
- **동일 입력**: 동일한 프롬프트/데이터셋
- **동일 메트릭**: throughput, latency 등 동일 지표 측정
- **동일 양자화**: FP8, INT4 등 테스트 시 동일 방식 적용
- **동일 조건**: batch size, concurrency 등 통제

## 프레임워크별 서버 실행

### SGLang
```bash
source sglang/sglang_env/bin/activate
python3 -m sglang.launch_server \
  --model-path openai/gpt-oss-20b \
  --tp 1
```

### vLLM
```bash
source vllm/vllm_env/bin/activate
vllm serve openai/gpt-oss-20b --host 0.0.0.0 --port 8000
```

### Ollama
```bash
ollama serve
# 별도 터미널에서 모델 로드
ollama run gpt-oss:20b
```

## 소스코드 접근 정책

각 프레임워크(`sglang/`, `vllm/`, `ollama/`) 소스코드는 **사용자가 명시적으로 분석을 요청한 경우에만** 접근한다. 벤치마크·서버 실행 등 운영 작업 시에는 이 문서의 명령어를 참고한다.
