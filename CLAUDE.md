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
| CUDA (nvcc) | 12.1 (V12.1.105) |
| Python (system) | 3.10.12 |
| uv | 0.10.4 |

### A100 소프트웨어 버전 (실제 설치)

| 패키지 | SGLang 환경 | vLLM 환경 | 비고 |
|--------|------------|----------|------|
| **Framework** | SGLang 0.5.8.post1 | vLLM 0.15.1 | pip wheels |
| **PyTorch** | 2.3.0 | 2.3.0 | |
| **Triton** | 2.3.0 | 2.3.0 | |
| **Flash Attention** | 2.5.9.post1 | 2.5.9.post1 | |
| **xformers** | 0.0.26.post1 | 0.0.26.post1 | |
| **Transformers** | 4.42.3 | 4.42.3 | |
| **NumPy** | 1.26.4 | 1.26.4 | |
| **CUDA (pip)** | 12.1.105 | 12.1.105 | nvidia-cuda-runtime-cu12 |
| **Ollama** | — | — | 0.16.2 (Go 바이너리) |

## 디렉토리 구조

```
/home/work/llm-serving-framework-benchmark-test/
├── sglang/                  # sglang_env/ (venv만 존재, 소스 클론 안 함)
├── vllm/                    # vllm_env/ (venv만 존재, 소스 클론 안 함)
├── ollama/                  # (미생성 — Go 바이너리로 시스템 설치)
├── bench/                   # 벤치마크 소스코드 (python -m bench)
│   ├── __main__.py          # CLI 엔트리포인트 (--framework, --scenario, --trials 등)
│   ├── client.py            # RequestResult, ScenarioResult, GpuMonitor, TrialSummary, HTTP 클라이언트
│   ├── scenarios.py         # 5개 시나리오 (single, concurrent, long_context, prefix_cache, korean)
│   ├── config.py            # 프레임워크 설정, 모델 프리셋, 상수
│   ├── prompts.py           # 영어/한국어 프롬프트, 필러 텍스트
│   ├── visualize.py         # matplotlib 차트 6종 생성 (python -m bench.visualize)
│   ├── analyze.py           # 결과 분석 + 가설 검증 + 보고서 (python -m bench.analyze)
│   ├── run_all.sh           # 전체 실행 스크립트 (bash bench/run_all.sh)
│   └── bench_env/           # 벤치마크 + 웹 서버 전용 venv
├── web/                     # 웹 GUI (FastAPI + React)
│   ├── backend/
│   │   ├── app.py           # FastAPI 앱 (CORS, 라우터, lifespan)
│   │   ├── config.py        # 서버 설정, FRAMEWORK_ENVS, 타임아웃 상수
│   │   ├── models/
│   │   │   └── schemas.py   # Pydantic 모델 (BenchmarkRequest, ManagedServerStatus 등)
│   │   ├── routers/
│   │   │   ├── server.py    # /api/v1/server/* (health, gpu, start, stop, managed)
│   │   │   ├── benchmark.py # /api/v1/benchmark/* (run, status, cancel)
│   │   │   ├── results.py   # /api/v1/results/* (프레임워크별 결과 JSON)
│   │   │   └── analysis.py  # /api/v1/analysis/* (가설 검증, 비교 리포트)
│   │   ├── services/
│   │   │   ├── server_manager.py   # 프레임워크 서버 시작/종료/로그 관리
│   │   │   ├── server_monitor.py   # GPU 폴링, 프레임워크 헬스 체크
│   │   │   ├── benchmark_runner.py # 벤치마크 서브프로세스 실행 + 로그 큐
│   │   │   ├── result_loader.py    # results/ JSON 로딩
│   │   │   └── analysis_service.py # 가설 검증 로직
│   │   └── ws/
│   │       ├── benchmark_ws.py  # /ws/benchmark/{job_id} (벤치마크 로그 스트리밍)
│   │       ├── monitor_ws.py    # /ws/gpu (GPU 모니터링 2초 폴링)
│   │       └── server_ws.py     # /ws/server/logs (서버 시작/런타임 로그)
│   └── frontend/
│       ├── src/
│       │   ├── api/
│       │   │   ├── types.ts      # 타입 정의 (GPUStats, ServerHealth, ManagedServerStatus 등)
│       │   │   ├── client.ts     # REST API 클라이언트 (api.startServer, api.stopServer 등)
│       │   │   └── websocket.ts  # WebSocket 연결 (벤치마크, GPU, 서버 로그)
│       │   ├── hooks/
│       │   │   ├── useGPUMonitor.ts    # GPU WebSocket 실시간 모니터링
│       │   │   ├── useServerManager.ts # 서버 상태 폴링 + 시작/종료 + 로그
│       │   │   ├── useResults.ts       # 결과 데이터 로딩
│       │   │   └── useWebSocket.ts     # 범용 WebSocket 훅
│       │   ├── components/
│       │   │   ├── monitoring/    # ServerStatusCard, ServerLogModal, GPUGauge
│       │   │   ├── benchmark/     # BenchmarkForm, LogViewer
│       │   │   ├── results/       # ComparisonTable, ScenarioSelector
│       │   │   ├── charts/        # Recharts 기반 차트 컴포넌트
│       │   │   ├── hypothesis/    # 가설 검증 카드
│       │   │   └── layout/        # Sidebar, Layout
│       │   └── pages/
│       │       ├── DashboardPage.tsx   # 서버 상태 + GPU + 최근 결과
│       │       ├── BenchmarkPage.tsx   # 벤치마크 실행 + 로그
│       │       ├── ResultsPage.tsx     # 결과 비교 테이블 + 차트
│       │       └── HypothesisPage.tsx  # 가설 검증 결과
│       ├── package.json
│       └── vite.config.ts
├── docs/                    # 문서
│   ├── benchmark_design.md  # 벤치마크 설계 명세 (가설 H1~H5, 시나리오, 메트릭)
│   ├── research_report.md   # 프레임워크 기술 분석 보고서
│   ├── metric_guide.md      # 메트릭 해석 가이드 (초보자용, 한국어)
│   └── execution_guide.md   # 벤치마크 실행 가이드 (단계별, 한국어)
├── results/                 # 벤치마크 결과 (생성 파일, gitignore)
│   ├── sglang/              # SGLang 결과 JSON
│   ├── vllm/                # vLLM 결과 JSON
│   ├── ollama/              # Ollama 결과 JSON
│   └── summary/             # 통합 결과 (charts/, analysis_report.md 등)
├── blog/                    # 블로그 작성
├── CLAUDE.md
└── README.md
```

## 초기 세팅

### 1. 시스템 의존성

```bash
sudo apt install libnuma-dev  # SGLang sgl_kernel 런타임 필요
```

### 2. uv 설치

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. 프레임워크별 venv 생성 및 패키지 설치

소스 클론 없이 **pip pre-built wheels**로 설치한다 (소스 빌드 시 이슈 발생).
프레임워크별 독립 가상환경을 사용한다. Python 3.12 기준.

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

# Ollama (Go 바이너리 — 별도 설치)
curl -fsSL https://ollama.com/install.sh | sh
```

### 설치 현황

| Framework | 가상환경 | 설치 버전 | 상태 |
|-----------|---------|----------|------|
| SGLang | `sglang/sglang_env/` | 0.5.8.post1 | 설치 완료 |
| vLLM | `vllm/vllm_env/` | 0.15.1 | 설치 완료 |
| Ollama | (Go 바이너리) | 0.16.2 | 설치 완료 |

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

### CLI에서 직접 실행

```bash
# SGLang
source sglang/sglang_env/bin/activate
python3 -m sglang.launch_server \
  --model-path openai/gpt-oss-20b \
  --tp 1 --port 30000 --mem-fraction-static 0.85

# vLLM
source vllm/vllm_env/bin/activate
vllm serve openai/gpt-oss-20b \
  --host 0.0.0.0 --port 8000 \
  --gpu-memory-utilization 0.85 --enable-prefix-caching

# Ollama
OLLAMA_HOST=0.0.0.0:11434 ollama serve
ollama pull gpt-oss:20b   # 별도 터미널
```

### 웹 GUI에서 실행

대시보드의 서버 카드에서 Start/Stop 버튼으로 서버를 관리할 수 있다. GPU 메모리를 공유하므로 **한 번에 하나의 프레임워크만 실행 가능**하다. 다른 프레임워크를 시작하면 기존 서버가 자동 종료된다.

## 벤치마크 실행

### 빠른 실행

```bash
# 단일 프레임워크 (권장)
bash bench/run_all.sh sglang
bash bench/run_all.sh vllm
bash bench/run_all.sh ollama

# 전체 실행 (3개 프레임워크 순차)
bash bench/run_all.sh

# 반복 실행 (mean±std)
BENCH_TRIALS=3 bash bench/run_all.sh sglang
```

### 직접 실행

```bash
source bench/bench_env/bin/activate
python -m bench --framework sglang --scenario all --model gpt-oss-20b
python -m bench --framework vllm --scenario single,concurrent --trials 3
```

### CLI 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--framework` | `sglang`, `vllm`, `ollama` | (필수) |
| `--scenario` | `single`, `concurrent`, `long_context`, `prefix_cache`, `korean`, `all` | `all` |
| `--model` | `gpt-oss-20b`, `llama3.1-8b` | `gpt-oss-20b` |
| `--trials` | 반복 실행 횟수 (mean±std 계산) | `1` |
| `--output-dir` | 결과 저장 경로 | `results/<framework>/` |

### 결과 분석

```bash
source bench/bench_env/bin/activate
python -m bench.analyze          # 비교 테이블 + 가설 검증 + 차트 생성
python -m bench.visualize        # 차트만 생성
```

출력: `results/summary/analysis_report.md`, `results/summary/charts/*.png`

## 웹 GUI

### 실행

```bash
source bench/bench_env/bin/activate

# 개발 모드 (백엔드 + 프론트엔드 핫리로드)
uvicorn web.backend.app:app --host 0.0.0.0 --port 8080 &
cd web/frontend && npm run dev   # http://localhost:5173

# 프로덕션 모드 (빌드 후 단일 서버)
cd web/frontend && npm run build
uvicorn web.backend.app:app --host 0.0.0.0 --port 8080
# http://localhost:8080
```

### 주요 기능

| 페이지 | 기능 |
|--------|------|
| Dashboard | 서버 상태 (Start/Stop), GPU 모니터링, 최근 결과 |
| Benchmark | 프레임워크·시나리오 선택, 실행, 실시간 로그 |
| Results | 프레임워크 간 성능 비교 테이블 + 차트 |
| Hypothesis | 가설 검증 결과 (H1~H5) |

### API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| `GET` | `/api/v1/server/health` | 프레임워크 서버 헬스 체크 |
| `GET` | `/api/v1/server/gpu` | GPU 메모리·사용률 |
| `GET` | `/api/v1/server/managed` | 관리 중인 서버 상태 |
| `POST` | `/api/v1/server/start` | 서버 시작 (`{framework, model}`) |
| `POST` | `/api/v1/server/stop` | 서버 종료 (`{force: bool}`) |
| `POST` | `/api/v1/benchmark/run` | 벤치마크 실행 |
| `GET` | `/api/v1/benchmark/status/{id}` | 벤치마크 상태 |
| `POST` | `/api/v1/benchmark/cancel/{id}` | 벤치마크 취소 |
| `GET` | `/api/v1/results/all` | 전체 결과 |
| `GET` | `/api/v1/analysis/hypotheses` | 가설 검증 결과 |
| `WS` | `/ws/benchmark/{id}` | 벤치마크 로그 스트리밍 |
| `WS` | `/ws/gpu` | GPU 모니터링 (2초 간격) |
| `WS` | `/ws/server/logs` | 서버 시작/런타임 로그 |

## 문서 참조

| 문서 | 내용 |
|------|------|
| `docs/benchmark_design.md` | 벤치마크 설계 명세 (가설 H1~H5, 시나리오, 메트릭 정의) |
| `docs/research_report.md` | 프레임워크 기술 분석 (아키텍처, 기능, 성능 비교) |
| `docs/metric_guide.md` | 메트릭 해석 가이드 (초보자용, 한국어) |
| `docs/execution_guide.md` | 벤치마크 실행 가이드 (단계별 매뉴얼, 트러블슈팅) |

## 참고 사항

- 프레임워크 소스코드는 클론하지 않았다. `sglang/`, `vllm/` 디렉토리에는 venv만 존재한다.
- 웹 GUI의 `bench_env/`는 벤치마크 CLI와 웹 백엔드가 공유하는 venv이다.
- GPU 메모리를 공유하므로 한 번에 하나의 프레임워크 서버만 실행해야 한다.
- 벤치마크·서버 실행 등 운영 작업 시에는 이 문서의 명령어를 참고한다.
