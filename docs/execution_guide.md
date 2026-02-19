# LLM 서빙 프레임워크 벤치마크 실행 가이드

> SGLang v0.5.8.post1 | vLLM v0.15.1 | Ollama v0.16.2
> 대상 GPU: NVIDIA A100-SXM4-80GB | 모델: openai/gpt-oss-20b (20B)
> 작성일: 2026-02-19

이 문서는 LLM 서빙 프레임워크(vLLM, SGLang, Ollama) 벤치마크를 처음부터 끝까지 실행하기 위한 단계별 가이드이다.
모든 명령어는 프로젝트 루트 `/home/work/llm-serving-framework-benchmark-test/` 기준이다.

---

## 1. 사전 점검 체크리스트

벤치마크를 시작하기 전에 아래 항목을 반드시 확인한다.

### 1-1. GPU 상태 확인

```bash
nvidia-smi
```

확인 사항:
- GPU가 정상 인식되는지 (NVIDIA A100-SXM4-80GB)
- Driver Version, CUDA Version 출력 여부
- GPU 온도가 비정상적으로 높지 않은지 (80도 이상이면 냉각 확인)

### 1-2. GPU 독점 사용 확인

벤치마크 중에는 다른 프로세스가 GPU를 사용하면 안 된다. 현재 GPU를 사용 중인 프로세스를 확인한다.

```bash
nvidia-smi

# 또는 더 상세하게 확인
fuser -v /dev/nvidia*
```

다른 프로세스가 GPU를 사용 중이면 해당 프로세스를 종료한 후 진행한다.

### 1-3. 디스크 용량 확인

모델 캐시 및 결과 파일을 위한 충분한 디스크 공간이 필요하다.

```bash
df -h /home/work
```

- 모델 캐시(`~/.cache/huggingface/`): 20B 모델 기준 약 40GB 이상 필요
- 벤치마크 결과(`results/`): 수십 MB 수준
- 최소 50GB 이상의 여유 공간을 확보한다.

### 1-4. 네트워크 확인

모델을 처음 실행하는 경우 HuggingFace에서 모델 다운로드가 필요하다.

```bash
# HuggingFace 접근 가능 여부 확인
curl -s -o /dev/null -w "%{http_code}" https://huggingface.co
```

### 1-5. tmux 설치 확인

서버를 백그라운드에서 실행하기 위해 tmux를 사용한다.

```bash
which tmux
# 설치되어 있지 않으면:
sudo apt-get install -y tmux
```

### 1-6. 가상환경 존재 확인

```bash
# SGLang 가상환경
ls sglang/sglang_env/bin/activate

# vLLM 가상환경
ls vllm/vllm_env/bin/activate

# Ollama 바이너리
which ollama
```

가상환경이 없으면 `CLAUDE.md`의 초기 세팅 절차를 먼저 수행한다.

---

## 2. 프레임워크별 서버 실행

각 프레임워크는 독립적인 서버 프로세스로 실행된다. **한 번에 하나의 프레임워크만 실행**하여 GPU 리소스를 독점적으로 사용해야 한다.

### 2-1. SGLang 서버

#### 서버 시작

```bash
tmux new-session -d -s sglang
tmux send-keys -t sglang 'cd /home/work/llm-serving-framework-benchmark-test && source sglang/sglang_env/bin/activate && python3 -m sglang.launch_server --model-path openai/gpt-oss-20b --tp 1 --port 30000 --host 0.0.0.0 --mem-fraction-static 0.85' Enter
```

#### 주요 옵션 설명

| 옵션 | 설명 |
|------|------|
| `--model-path` | HuggingFace 모델 ID 또는 로컬 경로 |
| `--tp 1` | Tensor Parallel 수. A100 1장이므로 1로 설정 |
| `--port 30000` | API 서버 포트. SGLang 기본값은 30000 |
| `--host 0.0.0.0` | 모든 네트워크 인터페이스에서 접근 허용 |
| `--mem-fraction-static 0.85` | GPU 메모리의 85%를 KV 캐시에 할당. 나머지 15%는 모델 가중치 및 임시 버퍼용 |

#### 서버 준비 확인

모델 로딩에 수 분이 걸릴 수 있다. 로그를 확인하거나 health check로 준비 상태를 확인한다.

```bash
# 로그 확인 (tmux 세션에 접속)
tmux attach -t sglang
# 빠져나오기: Ctrl+B, D

# health check (준비될 때까지 반복)
curl http://localhost:30000/health
# 정상 응답: 200 OK
```

자동으로 준비 대기하려면:

```bash
while ! curl -s http://localhost:30000/health > /dev/null 2>&1; do
  echo "SGLang 서버 대기 중..."
  sleep 5
done
echo "SGLang 서버 준비 완료"
```

#### 서버 종료

```bash
# tmux 세션 종료 (서버 프로세스 함께 종료)
tmux kill-session -t sglang

# GPU 메모리 해제 확인
nvidia-smi
```

---

### 2-2. vLLM 서버

#### 서버 시작

```bash
tmux new-session -d -s vllm
tmux send-keys -t vllm 'cd /home/work/llm-serving-framework-benchmark-test && source vllm/vllm_env/bin/activate && vllm serve openai/gpt-oss-20b --host 0.0.0.0 --port 8000 --tensor-parallel-size 1 --gpu-memory-utilization 0.85 --enable-prefix-caching' Enter
```

#### 주요 옵션 설명

| 옵션 | 설명 |
|------|------|
| `openai/gpt-oss-20b` | 서빙할 모델 ID |
| `--host 0.0.0.0` | 모든 네트워크 인터페이스에서 접근 허용 |
| `--port 8000` | API 서버 포트. vLLM 기본값은 8000 |
| `--tensor-parallel-size 1` | Tensor Parallel 수. A100 1장이므로 1 |
| `--gpu-memory-utilization 0.85` | GPU 메모리의 85%를 모델+KV 캐시에 활용 |
| `--enable-prefix-caching` | Prefix Caching 활성화. 시나리오 4(접두사 캐시 테스트)에서 중요 |

#### 서버 준비 확인

```bash
# 로그 확인
tmux attach -t vllm
# 빠져나오기: Ctrl+B, D

# health check
curl http://localhost:8000/health
# 정상 응답: 200 OK
```

자동으로 준비 대기하려면:

```bash
while ! curl -s http://localhost:8000/health > /dev/null 2>&1; do
  echo "vLLM 서버 대기 중..."
  sleep 5
done
echo "vLLM 서버 준비 완료"
```

#### 서버 종료

```bash
tmux kill-session -t vllm

# GPU 메모리 해제 확인
nvidia-smi
```

---

### 2-3. Ollama 서버

#### 서버 시작

```bash
tmux new-session -d -s ollama
tmux send-keys -t ollama 'OLLAMA_HOST=0.0.0.0:11434 ollama serve' Enter
```

서버가 시작된 후, 모델을 미리 다운로드(pull)한다:

```bash
# 서버가 준비될 때까지 잠시 대기
sleep 5

# 모델 다운로드 (최초 1회만 필요)
ollama pull gpt-oss:20b
```

#### 주요 환경 변수 설명

| 환경 변수 | 설명 |
|-----------|------|
| `OLLAMA_HOST` | 바인드할 주소:포트. 기본값 `127.0.0.1:11434` |
| `OLLAMA_NUM_PARALLEL` | 동시 요청 처리 수. 기본값 1 (벤치마크에서는 기본값 사용) |
| `OLLAMA_GPU_OVERHEAD` | GPU 메모리 오버헤드 예약량 |

#### 서버 준비 확인

```bash
# health check
curl http://localhost:11434/api/tags
# 정상 응답: JSON 형태의 모델 목록

# 모델이 로드되었는지 확인
curl http://localhost:11434/api/tags | python3 -m json.tool
```

자동으로 준비 대기하려면:

```bash
while ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
  echo "Ollama 서버 대기 중..."
  sleep 3
done
echo "Ollama 서버 준비 완료"
```

#### 서버 종료

```bash
tmux kill-session -t ollama

# GPU 메모리 해제 확인
nvidia-smi
```

---

## 3. 벤치마크 실행

벤치마크를 실행하기 전에 **대상 프레임워크의 서버가 정상적으로 실행 중**인지 반드시 확인한다.

### 3-1. run_all.sh 사용 (권장)

`bench/run_all.sh`는 가상환경 생성, health check, 벤치마크 실행, 결과 저장을 자동으로 처리한다.

#### 전체 프레임워크 실행

```bash
cd /home/work/llm-serving-framework-benchmark-test
bash bench/run_all.sh
```

> **주의**: 전체 실행 시 3개 프레임워크 서버가 모두 실행 중이어야 한다.
> 실제 운용에서는 아래처럼 프레임워크별로 개별 실행을 권장한다.

#### 단일 프레임워크 실행

```bash
# SGLang만 실행 (모든 시나리오)
bash bench/run_all.sh sglang

# vLLM만 실행 (모든 시나리오)
bash bench/run_all.sh vllm

# Ollama만 실행 (모든 시나리오)
bash bench/run_all.sh ollama
```

#### 특정 시나리오만 실행

```bash
# SGLang의 concurrent 시나리오만
bash bench/run_all.sh sglang concurrent

# vLLM의 single 시나리오만
bash bench/run_all.sh vllm single

# Ollama의 prefix_cache 시나리오만
bash bench/run_all.sh ollama prefix_cache
```

#### 다른 모델로 실행

```bash
# SGLang + Llama 3.1 8B 모델
bash bench/run_all.sh sglang all llama3.1-8b
```

#### 반복 실행 (Trial) — 결과 신뢰도 향상

환경변수 `BENCH_TRIALS`를 설정하면 각 시나리오를 N회 반복 실행하여 mean±std를 계산한다.

```bash
# 3회 반복 실행
BENCH_TRIALS=3 bash bench/run_all.sh sglang

# 5회 반복 (더 높은 신뢰도)
BENCH_TRIALS=5 bash bench/run_all.sh vllm concurrent
```

#### run_all.sh 사용 형식 정리

```
bash bench/run_all.sh [framework] [scenario] [model]
```

| 인자 | 기본값 | 가능한 값 |
|------|--------|----------|
| `framework` | `all` | `sglang`, `vllm`, `ollama`, `all` |
| `scenario` | `all` | `single`, `concurrent`, `long_context`, `prefix_cache`, `korean`, `all` |
| `model` | `gpt-oss-20b` | `gpt-oss-20b`, `llama3.1-8b` |

---

### 3-2. 직접 실행 (python -m bench)

더 세밀한 제어가 필요할 때 Python 모듈을 직접 실행한다.

#### 벤치마크 환경 활성화

```bash
# bench_env가 없으면 먼저 생성
if [ ! -d bench/bench_env ]; then
  uv venv bench/bench_env --python 3.12
  source bench/bench_env/bin/activate
  uv pip install aiohttp numpy tqdm matplotlib
  deactivate
fi

# 환경 활성화
source bench/bench_env/bin/activate
```

#### 실행 예시

```bash
# SGLang - 모든 시나리오
python -m bench --framework sglang --scenario all --model gpt-oss-20b

# vLLM - 특정 시나리오 조합 (쉼표로 구분)
python -m bench --framework vllm --scenario single,concurrent

# Ollama - 결과 저장 경로 지정
python -m bench --framework ollama --scenario all --output-dir results/ollama

# 한국어 시나리오만 실행
python -m bench --framework sglang --scenario korean

# 3회 반복 실행 (mean±std 계산)
python -m bench --framework sglang --scenario all --trials 3
```

#### CLI 옵션 설명

| 옵션 | 필수 | 설명 | 기본값 |
|------|------|------|--------|
| `--framework` | O | 벤치마크 대상 프레임워크 | - |
| `--scenario` | X | 실행할 시나리오 (쉼표 구분 가능) | `all` |
| `--model` | X | 모델 프리셋 이름 | `gpt-oss-20b` |
| `--output-dir` | X | 결과 JSON 저장 경로 | `results/<framework>/` |
| `--trials` | X | 시나리오 반복 실행 횟수 (mean±std 계산) | `1` |

#### 가능한 시나리오 이름

| 시나리오 이름 | 설명 |
|-------------|------|
| `single` | 단일 요청 기본 성능 (입력 128/512/1024 토큰) |
| `concurrent` | 동시 요청 부하 테스트 (동시성 1/8/16/32/64) |
| `long_context` | 긴 입력 처리 (2048/4096 토큰) |
| `prefix_cache` | 접두사 캐시 효율성 (공유 시스템 프롬프트 50개 요청) |
| `korean` | 한국어/영어 대조 성능 비교 |
| `all` | 위 5개 시나리오 전부 실행 |

---

## 4. 결과 확인 및 분석

### 4-1. 결과 파일 위치

벤치마크 완료 후 결과 JSON 파일이 다음 경로에 저장된다:

```
results/
  sglang/
    sglang_gpt-oss-20b_results.json
  vllm/
    vllm_gpt-oss-20b_results.json
  ollama/
    ollama_gpt-oss-20b_results.json
  summary/
    all_results.json          # 전체 통합 결과
    comparison.md             # 프레임워크 비교 표
    analysis_report.md        # 가설 검증 포함 분석 보고서
    charts/                   # 시각화 차트 이미지 (PNG)
```

### 4-2. 결과 JSON 구조

각 프레임워크의 결과 JSON은 다음과 같은 구조이다:

```json
{
  "framework": "sglang",
  "model_preset": "gpt-oss-20b",
  "model": "openai/gpt-oss-20b",
  "timestamp": "2026-02-19 14:30:00",
  "server_config": {
    "base_url": "http://localhost:30000",
    "model": "openai/gpt-oss-20b",
    "chat_endpoint": "/v1/chat/completions"
  },
  "gpu_info": {
    "memory_used_mb": 45000.0,
    "memory_total_mb": 81920.0,
    "gpu_utilization_pct": 85.0
  },
  "results": [
    {
      "scenario": "single_request",
      "framework": "sglang",
      "concurrency": 1,
      "input_tokens": 128,
      "output_tokens": 256,
      "num_requests": 10,
      "avg_ttft_ms": 45.23,
      "p50_ttft_ms": 43.10,
      "p95_ttft_ms": 52.80,
      "p99_ttft_ms": 55.10,
      "avg_latency_ms": 1230.50,
      "p50_latency_ms": 1220.00,
      "p95_latency_ms": 1280.00,
      "p99_latency_ms": 1295.00,
      "total_token_throughput": 208.50,
      "request_throughput": 0.81,
      "success_rate": 100.0,
      "total_time_sec": 12.35,
      "gpu_memory_mb": 45000.0,
      "gpu_utilization_pct": 85.0
    }
  ]
}
```

#### 주요 메트릭 해석

| 메트릭 | 의미 | 좋은 방향 |
|--------|------|----------|
| `avg_ttft_ms` | 평균 첫 토큰 도달 시간 (ms) | 낮을수록 좋음 |
| `p99_latency_ms` | 99번째 백분위 응답 시간 (ms) | 낮을수록 좋음 |
| `total_token_throughput` | 초당 총 생성 토큰 수 (tok/s) | 높을수록 좋음 |
| `request_throughput` | 초당 완료 요청 수 (req/s) | 높을수록 좋음 |
| `success_rate` | 성공률 (%) | 100%에 가까울수록 좋음 |
| `gpu_memory_mb` | GPU 메모리 사용량 (MB) | 참고용 (효율성 판단) |

### 4-3. 비교 분석 생성

`run_all.sh`에서 전체 프레임워크를 실행한 경우, 자동으로 `results/summary/` 에 비교 요약이 생성된다.

개별 실행 후 수동으로 요약을 생성하려면:

```bash
source bench/bench_env/bin/activate
python -m bench.analyze
```

### 4-4. 결과 확인 명령어

```bash
# 특정 프레임워크 결과 빠르게 확인
python3 -c "
import json
with open('results/sglang/sglang_gpt-oss-20b_results.json') as f:
    data = json.load(f)
for r in data['results']:
    print(f\"[{r['scenario']}] conc={r['concurrency']} | TTFT={r['avg_ttft_ms']}ms | throughput={r['total_token_throughput']}tok/s | p99={r['p99_latency_ms']}ms | success={r['success_rate']}%\")
"

# 비교 표 확인
cat results/summary/comparison.md
```

---

## 5. 트러블슈팅

### 5-1. 서버가 응답하지 않음

**증상**: `curl http://localhost:<PORT>/health` 에서 "Connection refused" 또는 무응답

**해결 방법**:

```bash
# 1. tmux 세션이 살아있는지 확인
tmux ls

# 2. 해당 세션의 로그 확인
tmux attach -t sglang   # 또는 vllm, ollama

# 3. 포트가 열려있는지 확인
ss -tlnp | grep <PORT>

# 4. 프로세스 확인
ps aux | grep sglang    # 또는 vllm, ollama
```

주요 원인:
- 모델 로딩이 아직 완료되지 않음 (특히 최초 실행 시 다운로드 필요)
- 가상환경 활성화 실패
- 이전 서버 프로세스가 포트를 점유 중

### 5-2. OOM (Out of Memory) 오류

**증상**: `CUDA out of memory`, `RuntimeError: CUDA error`

**해결 방법**:

```bash
# 1. 현재 GPU 메모리 사용량 확인
nvidia-smi

# 2. 다른 GPU 프로세스가 있으면 종료
# (PID를 확인하고 kill)

# 3. 메모리 사용률 낮추기
# SGLang: --mem-fraction-static 값을 0.80 이하로 조정
python3 -m sglang.launch_server --model-path openai/gpt-oss-20b --tp 1 --port 30000 --mem-fraction-static 0.80

# vLLM: --gpu-memory-utilization 값을 0.80 이하로 조정
vllm serve openai/gpt-oss-20b --port 8000 --gpu-memory-utilization 0.80
```

### 5-3. 요청 타임아웃

**증상**: 벤치마크 실행 중 `Timeout` 오류 다수 발생

**해결 방법**:

```bash
# 1. 서버 로그에서 오류 확인
tmux attach -t <framework>

# 2. 타임아웃 값 조정 (기본 300초)
# bench/config.py 의 REQUEST_TIMEOUT 값을 늘린다
# 예: 600초로 변경
```

`bench/config.py` 파일에서:

```python
REQUEST_TIMEOUT = 600  # 기본값 300 -> 600으로 변경
```

### 5-4. 모델을 찾을 수 없음

**증상**: `Model not found`, `FileNotFoundError`

**해결 방법**:

```bash
# SGLang/vLLM: HuggingFace 모델 ID 확인
# 모델명이 정확한지 확인: openai/gpt-oss-20b
python3 -c "from huggingface_hub import model_info; print(model_info('openai/gpt-oss-20b'))"

# HuggingFace 로그인이 필요한 모델인 경우
huggingface-cli login

# Ollama: 모델이 다운로드되었는지 확인
ollama list
# 없으면 다운로드
ollama pull gpt-oss:20b
```

### 5-5. 벤치마크가 멈춤 (hang)

**증상**: 벤치마크 진행률이 멈추고 더 이상 진행되지 않음

**해결 방법**:

```bash
# 1. 서버 로그 확인 (tmux 세션 접속)
tmux attach -t <framework>

# 2. 작은 시나리오부터 테스트
python -m bench --framework sglang --scenario single

# 3. 단일 curl 요청으로 서버 응답 확인
curl -X POST http://localhost:30000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-oss-20b",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 10,
    "stream": false
  }'
```

### 5-6. 가상환경 활성화 실패

**증상**: `source: not found`, `No such file or directory`

**해결 방법**:

```bash
# 가상환경 경로 확인
ls -la sglang/sglang_env/bin/activate
ls -la vllm/vllm_env/bin/activate

# 가상환경이 없으면 재생성
uv venv sglang/sglang_env --python 3.12
source sglang/sglang_env/bin/activate
uv pip install "sglang[all]==0.5.6.post2"
deactivate
```

### 5-7. CUDA 버전 불일치

**증상**: `CUDA driver version is insufficient for CUDA runtime version`

**해결 방법**:

```bash
# 설치된 CUDA 버전 확인
nvcc --version
nvidia-smi  # Driver Version / CUDA Version 확인

# PyTorch CUDA 버전 확인
python3 -c "import torch; print(torch.version.cuda)"
```

CUDA 12.1 환경 기준으로 pip 패키지가 설치되어 있어야 한다. 버전이 다르면 가상환경을 재생성하고 올바른 CUDA 버전에 맞는 패키지를 설치한다.

### 5-8. 포트 충돌

**증상**: `Address already in use`, `bind: address already in use`

**해결 방법**:

```bash
# 포트를 사용 중인 프로세스 확인
lsof -i :30000   # SGLang
lsof -i :8000    # vLLM
lsof -i :11434   # Ollama

# 해당 프로세스 종료
kill <PID>

# 또는 강제 종료
kill -9 <PID>
```

---

## 6. 예상 소요 시간

A100-SXM4-80GB + openai/gpt-oss-20b 모델 기준 예상 소요 시간이다. 실제 시간은 모델 응답 속도 및 서버 상태에 따라 달라질 수 있다.

### 6-1. 시나리오별 소요 시간

| 시나리오 | 프레임워크당 예상 시간 | 설명 |
|---------|-------------------|------|
| `single` | 약 5분 | 입력 3종 x 10회 = 30개 요청 + 워밍업 |
| `concurrent` | 약 15~20분 | 동시성 5단계 x 100개 요청 = 500개 요청 |
| `long_context` | 약 5분 | 입력 2종 x 동시성 2종 x 5회 = 20개 요청 |
| `prefix_cache` | 약 10분 | 순차 50개 요청 (캐시 효과 측정) |
| `korean` | 약 15분 | 한국어/영어 대조 프롬프트 다수 |
| **합계 (all)** | **약 50~60분** | 프레임워크 1개 기준 |

### 6-2. 전체 벤치마크 총 소요 시간

| 구간 | 예상 시간 |
|------|----------|
| SGLang 서버 시작 + 모델 로딩 | 약 3~5분 |
| SGLang 벤치마크 (all) | 약 50~60분 |
| SGLang 서버 종료 + GPU 메모리 해제 대기 | 약 1~2분 |
| vLLM 서버 시작 + 모델 로딩 | 약 3~5분 |
| vLLM 벤치마크 (all) | 약 50~60분 |
| vLLM 서버 종료 + GPU 메모리 해제 대기 | 약 1~2분 |
| Ollama 서버 시작 + 모델 로딩 | 약 3~5분 |
| Ollama 벤치마크 (all) | 약 50~60분 |
| Ollama 서버 종료 | 약 1분 |
| **총 합계** | **약 2.5~3시간** |

> 특정 시나리오만 실행하면 시간을 크게 줄일 수 있다.
> 예: `single` 시나리오만 3개 프레임워크 실행 시 약 20~30분

---

## 7. 빠른 참조 체크리스트 (Runbook)

아래는 전체 벤치마크를 순서대로 실행하기 위한 축약된 체크리스트이다. 각 단계의 명령어를 순서대로 복사하여 실행한다.

```
프로젝트 루트: /home/work/llm-serving-framework-benchmark-test
```

### Step 1. 사전 점검

```bash
cd /home/work/llm-serving-framework-benchmark-test
nvidia-smi                          # GPU 상태 확인
df -h /home/work                    # 디스크 용량 확인
which tmux                          # tmux 설치 확인
```

### Step 2. SGLang 벤치마크

```bash
# 서버 시작
tmux new-session -d -s sglang
tmux send-keys -t sglang 'cd /home/work/llm-serving-framework-benchmark-test && source sglang/sglang_env/bin/activate && python3 -m sglang.launch_server --model-path openai/gpt-oss-20b --tp 1 --port 30000 --host 0.0.0.0 --mem-fraction-static 0.85' Enter

# 서버 준비 대기
while ! curl -s http://localhost:30000/health > /dev/null 2>&1; do sleep 5; done
echo "SGLang 준비 완료"

# 벤치마크 실행
bash bench/run_all.sh sglang

# 서버 종료
tmux kill-session -t sglang
sleep 10  # GPU 메모리 해제 대기
nvidia-smi  # 메모리 해제 확인
```

### Step 3. vLLM 벤치마크

```bash
# 서버 시작
tmux new-session -d -s vllm
tmux send-keys -t vllm 'cd /home/work/llm-serving-framework-benchmark-test && source vllm/vllm_env/bin/activate && vllm serve openai/gpt-oss-20b --host 0.0.0.0 --port 8000 --tensor-parallel-size 1 --gpu-memory-utilization 0.85 --enable-prefix-caching' Enter

# 서버 준비 대기
while ! curl -s http://localhost:8000/health > /dev/null 2>&1; do sleep 5; done
echo "vLLM 준비 완료"

# 벤치마크 실행
bash bench/run_all.sh vllm

# 서버 종료
tmux kill-session -t vllm
sleep 10
nvidia-smi
```

### Step 4. Ollama 벤치마크

```bash
# 서버 시작
tmux new-session -d -s ollama
tmux send-keys -t ollama 'OLLAMA_HOST=0.0.0.0:11434 ollama serve' Enter
sleep 5

# 모델 다운로드 (최초 1회)
ollama pull gpt-oss:20b

# 서버 준비 대기
while ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do sleep 3; done
echo "Ollama 준비 완료"

# 벤치마크 실행
bash bench/run_all.sh ollama

# 서버 종료
tmux kill-session -t ollama
sleep 5
nvidia-smi
```

### Step 5. 결과 분석

```bash
# 결과 파일 존재 확인
ls -la results/sglang/
ls -la results/vllm/
ls -la results/ollama/

# 비교 분석 생성
source bench/bench_env/bin/activate
python -m bench.analyze
deactivate

# 결과 확인
cat results/summary/comparison.md
ls results/summary/charts/
```

### Step 6. 정리

```bash
# 남아있는 tmux 세션 확인 및 정리
tmux ls
# (세션이 남아있으면)
tmux kill-server

# GPU 상태 최종 확인
nvidia-smi
```

---

> 이 가이드에 대한 질문이나 문제가 발생하면 `docs/benchmark_design.md`에서 벤치마크 설계 세부사항을, `CLAUDE.md`에서 프로젝트 전체 설정 정보를 참고한다.
