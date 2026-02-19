# LLM Serving Framework Benchmark

vLLM, SGLang, Ollama 3개 LLM serving 프레임워크를 동일 조건에서 벤치마크하고 성능을 비교하는 프로젝트.

## 주요 기능

- **5가지 벤치마크 시나리오**: single request, concurrent, long context, prefix cache, Korean
- **웹 대시보드**: 서버 관리, GPU 모니터링, 벤치마크 실행, 결과 시각화
- **가설 검증**: 5개 가설(H1~H5)에 대한 데이터 기반 검증
- **CLI 도구**: 스크립트 기반 벤치마크 실행 및 분석

## 환경

| 항목 | 스펙 |
|------|------|
| GPU | NVIDIA A100-SXM4-80GB |
| Framework | SGLang 0.5.8 / vLLM 0.15.1 / Ollama 0.16.2 |
| Model | `openai/gpt-oss-20b` (TP=1) |

## 빠른 시작

### 1. 사전 준비

```bash
# uv 설치
curl -LsSf https://astral.sh/uv/install.sh | sh

# 시스템 의존성
sudo apt install libnuma-dev
```

### 2. 프레임워크 설치

```bash
# SGLang
uv venv sglang/sglang_env --python 3.12
source sglang/sglang_env/bin/activate
uv pip install "sglang[all]"
deactivate

# vLLM
uv venv vllm/vllm_env --python 3.12
source vllm/vllm_env/bin/activate
uv pip install vllm
deactivate

# Ollama
curl -fsSL https://ollama.com/install.sh | sh
```

### 3. 벤치마크 실행 (CLI)

```bash
# 서버 시작 (예: vLLM)
source vllm/vllm_env/bin/activate
vllm serve openai/gpt-oss-20b --host 0.0.0.0 --port 8000 \
  --gpu-memory-utilization 0.85 --enable-prefix-caching

# 벤치마크 실행
source bench/bench_env/bin/activate
python -m bench --framework vllm --scenario all

# 또는 run_all.sh로 간편 실행
bash bench/run_all.sh vllm
```

### 4. 웹 대시보드

```bash
# 프론트엔드 빌드
cd web/frontend && npm install && npm run build && cd ../..

# 서버 시작
source bench/bench_env/bin/activate
uvicorn web.backend.app:app --host 0.0.0.0 --port 8080
```

브라우저에서 `http://localhost:8080` 접속.

대시보드에서 서버 Start/Stop, 벤치마크 실행, 결과 비교를 모두 할 수 있다.

## 프로젝트 구조

```
bench/               # 벤치마크 CLI (python -m bench)
web/
├── backend/         # FastAPI 백엔드 (REST API + WebSocket)
└── frontend/        # React + TypeScript 프론트엔드
docs/                # 설계 문서, 분석 보고서, 가이드
results/             # 벤치마크 결과 JSON + 차트 (gitignore)
```

## 벤치마크 시나리오

| 시나리오 | 설명 |
|----------|------|
| `single` | 단일 요청 지연시간 (baseline) |
| `concurrent` | 동시 요청 처리량 (1/4/16/64 동시성) |
| `long_context` | 긴 입력 컨텍스트 처리 성능 |
| `prefix_cache` | 접두사 캐싱 효과 측정 |
| `korean` | 한국어 토큰화 성능 |

## 측정 메트릭

- **TTFT** (Time to First Token): 첫 토큰 생성까지 지연시간
- **Throughput**: 초당 토큰 처리량 (tok/s)
- **Latency**: 요청별 전체 응답 시간 (p50, p95, p99)
- **GPU Memory**: 피크/평균 GPU 메모리 사용량
- **Success Rate**: 요청 성공률

## 문서

| 문서 | 내용 |
|------|------|
| [벤치마크 설계](docs/benchmark_design.md) | 가설 H1~H5, 시나리오, 메트릭 정의 |
| [기술 분석](docs/research_report.md) | 프레임워크 아키텍처 비교 |
| [메트릭 가이드](docs/metric_guide.md) | 메트릭 해석 가이드 (한국어) |
| [실행 가이드](docs/execution_guide.md) | 단계별 실행 매뉴얼 |
