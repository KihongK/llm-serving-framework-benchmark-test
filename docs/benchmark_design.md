# LLM 서빙 프레임워크 벤치마크 설계서

> SGLang v0.5.6.post2 | vLLM v0.15.1 | Ollama v0.15.6
> 작성일: 2026-02-12

---

## 1. 벤치마크 목적

리서치 보고서에서 확인된 세 프레임워크의 핵심 아키텍처 차이가 **실제 성능에 어떤 영향**을 미치는지 정량적으로 검증한다.

### 검증 대상 핵심 가설

| # | 가설 | 관련 기술 차이 |
|---|------|--------------|
| H1 | SGLang이 공유 접두사 시나리오에서 vLLM보다 높은 처리량을 보인다 | RadixAttention(자동) vs PagedAttention(수동 Prefix Caching) |
| H2 | SGLang/vLLM이 Ollama보다 동시 요청 처리에서 압도적으로 우수하다 | 연속 배칭 vs 순차 처리 |
| H3 | Ollama가 단일 요청 레이턴시에서 경쟁력을 보인다 | llama.cpp C/C++ 최적화, GGUF 양자화 |
| H4 | 동시 요청 수 증가에 따른 성능 저하 패턴이 프레임워크마다 다르다 | 스케줄러 아키텍처 차이 |
| H5 | 한국어 입력/출력 시 영어 대비 토큰 효율성과 처리량이 프레임워크마다 다르다 | 토크나이저 차이, 바이트-레벨 인코딩 오버헤드 |

---

## 2. 테스트 환경

### 2.1 A100 벤치마크 서버 (주 테스트)

| 항목 | 스펙 |
|------|------|
| OS | Ubuntu 22.04.3 LTS |
| GPU | NVIDIA A100-SXM4-80GB (80 GB VRAM, NVLink) |
| CPU | Intel Xeon Platinum 8468, 2 Socket, 96 Core / 192 Thread |
| RAM | ~1 TiB |
| NVIDIA Driver | 570.86.10 |
| CUDA (nvcc) | 12.1 |

### 2.2 RTX 5090 실서빙 서버 (보조 테스트)

| 항목 | 스펙 |
|------|------|
| OS | Ubuntu 24.04 |
| GPU | RTX 5090 |
| CPU | AMD 7800X3D |
| RAM | 32GB |
| NVIDIA Driver | TBD |
| CUDA | TBD |

### 2.3 소프트웨어 버전

| Framework | 버전 | 가상환경 |
|-----------|------|---------|
| SGLang | 0.5.6.post2 | `sglang/sglang_env/` |
| vLLM | 0.15.1 | `vllm/vllm_env/` |
| Ollama | 0.15.6 | (Go 바이너리) |

---

## 3. 테스트 모델

| 모델 | HuggingFace ID | Ollama ID | 파라미터 | 용도 |
|------|---------------|-----------|---------|------|
| GPT-OSS 20B | `openai/gpt-oss-20b` | `gpt-oss:20b` | 20B | 기본 벤치마크 모델 (CLAUDE.md 지정) |
| Llama 3.1 8B | `meta-llama/Llama-3.1-8B-Instruct` | `llama3.1:8b` | 8B | 7B급 소형 모델 비교 |

> **모델 선정 근거**:
> - **GPT-OSS 20B**: CLAUDE.md에서 지정된 기본 벤치마크 모델. A100 80GB VRAM에서 TP=1으로 FP16 로드 가능 (20B x 2bytes = ~40GB). Ollama에서는 GGUF 포맷(`gpt-oss:20b`)을 사용.
> - **Llama 3.1 8B**: 7B급 소형 모델. 세 프레임워크 모두 Llama 3 계열을 지원. FP16 기준 ~16GB VRAM으로 A100에서 여유롭게 로드 가능. 모델 크기에 따른 프레임워크 오버헤드 차이를 비교하기 위해 포함.

### 프레임워크별 모델 실행 명령어

#### GPT-OSS 20B (기본 모델)

| Framework | 명령어 |
|-----------|--------|
| SGLang | `python3 -m sglang.launch_server --model-path openai/gpt-oss-20b --tp 1 --port 30000` |
| vLLM | `vllm serve openai/gpt-oss-20b --host 0.0.0.0 --port 8000` |
| Ollama | `ollama run gpt-oss:20b` |

#### Llama 3.1 8B (소형 모델)

| Framework | 명령어 |
|-----------|--------|
| SGLang | `python3 -m sglang.launch_server --model-path meta-llama/Llama-3.1-8B-Instruct --tp 1 --port 30000` |
| vLLM | `vllm serve meta-llama/Llama-3.1-8B-Instruct --host 0.0.0.0 --port 8000` |
| Ollama | `ollama run llama3.1:8b` |

---

## 4. 측정 메트릭

| 메트릭 | 설명 | 단위 |
|--------|------|------|
| **TTFT** | Time to First Token - 요청 전송~첫 토큰 수신 | ms |
| **Token Throughput** | 초당 생성 토큰 수 | tokens/sec |
| **Request Throughput** | 초당 완료 요청 수 | requests/sec |
| **Latency (p50/p95/p99)** | 요청 완료까지 소요 시간 분포 | ms |
| **GPU Memory** | 피크/평균 GPU 메모리 사용량 | MB |
| **GPU Utilization** | GPU 연산 활용률 | % |

---

## 5. 테스트 시나리오

### 5.1 시나리오 1: 단일 요청 기본 성능 (Single Request Baseline)

**목적**: 오버헤드 없는 기본 추론 성능 비교. 프레임워크 자체의 순수 추론 효율성 측정.

**방법**:
- 동시성: 1 (단일 요청)
- 입력 길이: 128 토큰, 512 토큰, 1024 토큰
- 출력 길이: 256 토큰 (고정)
- 반복: 각 설정 10회, 중앙값 사용
- 워밍업: 첫 3회 요청 결과 제외

**측정 메트릭**: TTFT, Token Throughput, 총 레이턴시, GPU 메모리

**예상 결과**:
- Ollama가 GGUF 최적화로 TTFT에서 경쟁력을 보일 수 있음
- SGLang/vLLM은 비슷한 수준의 처리량을 보일 것
- GPU 메모리 사용량은 SGLang/vLLM(FP16) > Ollama(Q4) 예상

### 5.2 시나리오 2: 동시 요청 부하 테스트 (Concurrent Load Test)

**목적**: 연속 배칭(SGLang/vLLM) vs 순차 처리(Ollama)의 동시성 처리 능력 검증. 가설 H2, H4 검증.

**방법**:
- 동시성 레벨: 1, 8, 16, 32, 64
- 입력 길이: 512 토큰 (고정)
- 출력 길이: 256 토큰 (고정)
- 각 동시성 레벨에서 총 100개 요청 처리
- 모든 요청에 동일 프롬프트 사용

**측정 메트릭**: Request Throughput, Token Throughput, TTFT, Latency (p50/p95/p99), GPU 활용률

**예상 결과**:
- SGLang/vLLM: 동시성 증가에 따라 처리량 증가 (연속 배칭 효과)
- Ollama: 동시성 증가 시 선형적 레이턴시 증가, 처리량 정체
- 64 동시 요청에서 Ollama는 타임아웃 또는 에러 발생 가능

### 5.3 시나리오 3: 긴 입력 처리 테스트 (Long Context Test)

**목적**: 긴 프롬프트(4K+ 토큰)에서의 Prefill 성능과 메모리 효율성 비교.

**방법**:
- 동시성: 1, 8
- 입력 길이: 2048, 4096 토큰
- 출력 길이: 256 토큰 (고정)
- 반복: 각 설정 5회

**측정 메트릭**: TTFT, Token Throughput, GPU 메모리 피크, 총 레이턴시

**예상 결과**:
- SGLang의 Chunked Prefill이 긴 입력에서 안정적인 TTFT 제공
- vLLM도 Chunked Prefill 지원으로 유사한 성능
- Ollama는 긴 입력에서 TTFT가 크게 증가할 수 있음

### 5.4 시나리오 4: 접두사 캐시 효율성 테스트 (Prefix Cache Efficiency Test)

**목적**: RadixAttention(SGLang) vs PagedAttention+PrefixCaching(vLLM) vs 기본(Ollama)의 캐시 효율성 비교. 가설 H1 검증.

**방법**:
- 공통 시스템 프롬프트(2048 토큰) + 다른 사용자 질문(128 토큰) 조합
- 동일한 시스템 프롬프트를 공유하는 요청 50개를 순차 전송
- 동시성: 1 (캐시 효과 순수 측정)
- 출력 길이: 256 토큰

**측정 메트릭**: TTFT (첫 요청 vs 후속 요청), Token Throughput (첫 요청 vs 후속 요청), 총 처리 시간

**예상 결과**:
- SGLang: RadixAttention 자동 접두사 감지로 후속 요청에서 TTFT 대폭 감소
- vLLM: Prefix Caching 활성화 시 유사한 효과, 미활성화 시 캐시 이점 없음
- Ollama: 캐시 메커니즘 없어 모든 요청에서 동일한 TTFT

### 5.5 시나리오 5: 한국어 성능 테스트 (Korean Language Test)

**목적**: 한국어 입력/출력 시 토큰 효율성, 처리량, 레이턴시를 영어 대비 비교. 토크나이저 특성(한국어 토큰화 효율)이 프레임워크별 성능에 미치는 영향을 검증. 가설 H5 검증.

**배경**:
- 한국어는 영어 대비 같은 의미를 전달하는 데 더 많은 토큰을 소비하는 경향이 있음
- 모델의 토크나이저에 따라 한국어 토큰화 효율이 크게 다름
- Ollama(GGUF)의 토크나이저와 SGLang/vLLM(HuggingFace)의 토크나이저가 다를 수 있음
- 한국어 생성 품질(자연스러운 문장, 어미 처리 등)도 정성적으로 확인

**방법**:
- 동시성: 1 (단일 요청), 8 (동시 요청)
- 입력: 한국어 프롬프트 (짧은 질문 ~128토큰, 긴 지문 ~512토큰)
- 출력: max_tokens 256
- 반복: 각 설정 10회
- 영어 동일 의미 프롬프트로 대조 실험

**테스트 프롬프트 예시**:

| 유형 | 한국어 프롬프트 | 영어 대조 프롬프트 |
|------|-------------|---------------|
| 짧은 질문 | "대한민국의 경제 발전 과정을 시대별로 자세히 설명해주세요." | "Please explain South Korea's economic development process in detail by era." |
| 긴 지문 요약 | 한국어 기술 문서 지문 (~512 토큰) + "위 내용을 요약해주세요." | 동일 의미 영어 기술 문서 + "Summarize the above." |
| 번역 | "Translate the following Korean text to English: [한국어 텍스트]" | (한→영 번역 태스크) |
| 한국어 생성 | "인공지능의 미래에 대한 에세이를 500자 내외로 작성해주세요." | "Write an essay about the future of AI in about 500 words." |

**측정 메트릭**: TTFT, Token Throughput, 총 레이턴시, 입력/출력 토큰 수 비교 (한국어 vs 영어 동일 의미)

**예상 결과**:
- 한국어 입력은 동일 의미 영어 대비 1.5~3배 많은 토큰 소비
- Token Throughput(tok/s)는 한국어/영어 간 유사하나, 실질 정보 처리량(정보/sec)은 한국어가 낮을 수 있음
- Ollama(GGUF)의 토크나이저가 한국어에 덜 최적화되어 있을 경우 토큰 오버헤드가 더 클 수 있음
- SGLang/vLLM은 동일 HuggingFace 토크나이저를 사용하므로 유사한 토큰 효율성 예상

---

## 6. 프레임워크별 서버 실행 가이드

### 6.1 SGLang 서버 실행

```bash
# 환경 활성화
cd /home/work/llm-serving-framework-benchmark-test
source sglang/sglang_env/bin/activate

# 기본 실행 (FP16)
python3 -m sglang.launch_server \
  --model-path openai/gpt-oss-20b \
  --tp 1 \
  --host 0.0.0.0 \
  --port 30000 \
  --mem-fraction-static 0.85

# 서버 준비 확인
curl -s http://localhost:30000/health
```

**주요 파라미터**:
- `--tp 1`: 텐서 병렬 1 (A100 단일 GPU)
- `--port 30000`: SGLang 기본 포트
- `--mem-fraction-static 0.85`: GPU 메모리의 85%를 KV 캐시에 할당

### 6.2 vLLM 서버 실행

```bash
# 환경 활성화
cd /home/work/llm-serving-framework-benchmark-test
source vllm/vllm_env/bin/activate

# 기본 실행 (FP16)
vllm serve openai/gpt-oss-20b \
  --host 0.0.0.0 \
  --port 8000 \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.85 \
  --enable-prefix-caching

# 서버 준비 확인
curl -s http://localhost:8000/health
```

**주요 파라미터**:
- `--tensor-parallel-size 1`: A100 단일 GPU
- `--port 8000`: vLLM 기본 포트
- `--gpu-memory-utilization 0.85`: GPU 메모리 85% 활용
- `--enable-prefix-caching`: Prefix Caching 활성화 (시나리오 4에서 중요)

### 6.3 Ollama 서버 실행

```bash
# 서버 시작 (별도 터미널 또는 백그라운드)
OLLAMA_HOST=0.0.0.0:11434 ollama serve

# 모델 사전 로드 (별도 터미널)
ollama pull gpt-oss:20b

# 서버 준비 확인
curl -s http://localhost:11434/api/tags
```

**주요 환경 변수**:
- `OLLAMA_HOST`: 바인드 주소:포트
- `OLLAMA_NUM_PARALLEL`: 동시 요청 수 (기본 1, 벤치마크에서는 기본값 사용)
- `OLLAMA_GPU_OVERHEAD`: GPU 메모리 오버헤드 예약

---

## 7. API 엔드포인트 정리

모든 프레임워크가 OpenAI 호환 API를 제공하므로, 동일한 클라이언트 코드로 테스트한다.

| Framework | Base URL | Chat Completions | Completions |
|-----------|----------|-------------------|-------------|
| SGLang | `http://localhost:30000` | `/v1/chat/completions` | `/v1/completions` |
| vLLM | `http://localhost:8000` | `/v1/chat/completions` | `/v1/completions` |
| Ollama | `http://localhost:11434` | `/v1/chat/completions` | `/api/generate` |

### 공통 요청 형식 (OpenAI Chat Completions)

```json
{
  "model": "<model_name>",
  "messages": [
    {"role": "system", "content": "<system_prompt>"},
    {"role": "user", "content": "<user_prompt>"}
  ],
  "max_tokens": 256,
  "temperature": 0,
  "stream": true
}
```

| Framework | model 값 |
|-----------|---------|
| SGLang | `openai/gpt-oss-20b` |
| vLLM | `openai/gpt-oss-20b` |
| Ollama | `gpt-oss:20b` |

---

## 8. 벤치마크 실행 절차

### 8.1 사전 준비

1. GPU 상태 확인: `nvidia-smi`
2. 다른 GPU 프로세스 종료 확인
3. 벤치마크 스크립트 의존성 설치:
   ```bash
   uv venv /home/work/llm-serving-framework-benchmark-test/bench/bench_env --python 3.12
   source /home/work/llm-serving-framework-benchmark-test/bench/bench_env/bin/activate
   uv pip install aiohttp numpy tqdm
   ```

### 8.2 실행 순서

각 프레임워크별로 다음 순서로 진행:

1. **서버 시작** (프레임워크별 가이드 참조)
2. **서버 준비 대기** (health check 통과까지)
3. **워밍업 요청** (3회)
4. **시나리오 1~4 순차 실행**
5. **결과 저장** (`results/<framework>/` 디렉토리)
6. **서버 종료**
7. **GPU 메모리 해제 확인** 후 다음 프레임워크 진행

### 8.3 전체 실행 스크립트

```bash
cd /home/work/llm-serving-framework-benchmark-test
bash bench/run_all.sh
```

---

## 9. 결과 분석 방향

### 9.1 시나리오별 분석 포인트

| 시나리오 | 핵심 분석 포인트 |
|---------|---------------|
| 단일 요청 | 프레임워크 오버헤드, 기본 추론 효율성 |
| 동시 요청 | 스케줄러 효율성, 배칭 전략의 실효성 |
| 긴 입력 | Prefill 효율성, 메모리 관리 능력 |
| 접두사 캐시 | KV 캐시 재사용 전략의 실제 효과 |
| 한국어 성능 | 토크나이저 효율성, 비영어 처리량, 실질 정보 처리 능력 |

### 9.2 기대 결론 방향

- **프로덕션 대규모 서빙**: SGLang >= vLLM >> Ollama
- **단일 사용자 로컬 추론**: Ollama의 간편성이 성능 차이를 상쇄
- **접두사 공유 워크로드**: SGLang > vLLM > Ollama
- **설치/운영 편의성**: Ollama > vLLM > SGLang

---

## 10. 주의사항

1. **공정한 비교**: 모든 프레임워크에서 동일한 `temperature=0` 사용 (결정론적 출력)
2. **워밍업**: 최초 3회 요청은 JIT 컴파일, 모델 로딩 등의 영향으로 제외
3. **GPU 독점 사용**: 벤치마크 중 다른 GPU 워크로드 없어야 함
4. **타임아웃 처리**: 요청당 최대 300초 타임아웃, 타임아웃 발생 시 실패로 기록
5. **양자화 차이**: Ollama는 GGUF Q4 양자화를 사용하므로, FP16 기반 SGLang/vLLM과 직접 비교 시 이를 명시
6. **반복 실행**: 결과의 신뢰성을 위해 각 설정에서 최소 5회 이상 반복
