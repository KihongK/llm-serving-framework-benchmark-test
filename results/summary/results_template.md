# LLM 서빙 프레임워크 벤치마크 결과

> 테스트 일시: YYYY-MM-DD
> 환경: A100-SXM4-80GB, Ubuntu 22.04, CUDA 12.1
> 모델: openai/gpt-oss-20b (FP16) / gpt-oss:20b (GGUF Q4 - Ollama)

---

## 1. 시나리오 1: 단일 요청 기본 성능 (Single Request Baseline)

### 1.1 Input 128 tokens, Output 256 tokens

| 메트릭 | SGLang | vLLM | Ollama |
|--------|--------|------|--------|
| TTFT (avg, ms) | | | |
| TTFT (p50, ms) | | | |
| TTFT (p95, ms) | | | |
| Token Throughput (tok/s) | | | |
| Total Latency (avg, ms) | | | |
| Total Latency (p99, ms) | | | |
| GPU Memory (MB) | | | |
| Success Rate (%) | | | |

### 1.2 Input 512 tokens, Output 256 tokens

| 메트릭 | SGLang | vLLM | Ollama |
|--------|--------|------|--------|
| TTFT (avg, ms) | | | |
| TTFT (p50, ms) | | | |
| TTFT (p95, ms) | | | |
| Token Throughput (tok/s) | | | |
| Total Latency (avg, ms) | | | |
| Total Latency (p99, ms) | | | |
| GPU Memory (MB) | | | |
| Success Rate (%) | | | |

### 1.3 Input 1024 tokens, Output 256 tokens

| 메트릭 | SGLang | vLLM | Ollama |
|--------|--------|------|--------|
| TTFT (avg, ms) | | | |
| TTFT (p50, ms) | | | |
| TTFT (p95, ms) | | | |
| Token Throughput (tok/s) | | | |
| Total Latency (avg, ms) | | | |
| Total Latency (p99, ms) | | | |
| GPU Memory (MB) | | | |
| Success Rate (%) | | | |

---

## 2. 시나리오 2: 동시 요청 부하 테스트 (Concurrent Load Test)

> Input: 512 tokens, Output: 256 tokens, Total: 100 requests per level

### 2.1 Request Throughput (req/s)

| Concurrency | SGLang | vLLM | Ollama |
|-------------|--------|------|--------|
| 1 | | | |
| 8 | | | |
| 16 | | | |
| 32 | | | |
| 64 | | | |

### 2.2 Token Throughput (tok/s)

| Concurrency | SGLang | vLLM | Ollama |
|-------------|--------|------|--------|
| 1 | | | |
| 8 | | | |
| 16 | | | |
| 32 | | | |
| 64 | | | |

### 2.3 TTFT (ms)

| Concurrency | SGLang p50 | SGLang p95 | vLLM p50 | vLLM p95 | Ollama p50 | Ollama p95 |
|-------------|-----------|-----------|---------|---------|-----------|-----------|
| 1 | | | | | | |
| 8 | | | | | | |
| 16 | | | | | | |
| 32 | | | | | | |
| 64 | | | | | | |

### 2.4 Latency Distribution (ms)

| Concurrency | SGLang p50 | SGLang p95 | SGLang p99 | vLLM p50 | vLLM p95 | vLLM p99 | Ollama p50 | Ollama p95 | Ollama p99 |
|-------------|-----------|-----------|-----------|---------|---------|---------|-----------|-----------|-----------|
| 1 | | | | | | | | | |
| 8 | | | | | | | | | |
| 16 | | | | | | | | | |
| 32 | | | | | | | | | |
| 64 | | | | | | | | | |

### 2.5 Success Rate (%)

| Concurrency | SGLang | vLLM | Ollama |
|-------------|--------|------|--------|
| 1 | | | |
| 8 | | | |
| 16 | | | |
| 32 | | | |
| 64 | | | |

---

## 3. 시나리오 3: 긴 입력 처리 테스트 (Long Context Test)

### 3.1 Input 2048 tokens

| 메트릭 | SGLang (c=1) | SGLang (c=8) | vLLM (c=1) | vLLM (c=8) | Ollama (c=1) | Ollama (c=8) |
|--------|-------------|-------------|-----------|-----------|-------------|-------------|
| TTFT (avg, ms) | | | | | | |
| Token Throughput (tok/s) | | | | | | |
| Total Latency (p99, ms) | | | | | | |
| GPU Memory Peak (MB) | | | | | | |
| Success Rate (%) | | | | | | |

### 3.2 Input 4096 tokens

| 메트릭 | SGLang (c=1) | SGLang (c=8) | vLLM (c=1) | vLLM (c=8) | Ollama (c=1) | Ollama (c=8) |
|--------|-------------|-------------|-----------|-----------|-------------|-------------|
| TTFT (avg, ms) | | | | | | |
| Token Throughput (tok/s) | | | | | | |
| Total Latency (p99, ms) | | | | | | |
| GPU Memory Peak (MB) | | | | | | |
| Success Rate (%) | | | | | | |

---

## 4. 시나리오 4: 접두사 캐시 효율성 테스트 (Prefix Cache Efficiency)

> Shared system prompt (~2048 tokens) + 50 different user questions
> Concurrency: 1 (sequential)

### 4.1 TTFT 비교: 첫 요청 vs 후속 요청

| 메트릭 | SGLang | vLLM | Ollama |
|--------|--------|------|--------|
| First 5 requests TTFT (avg, ms) | | | |
| Remaining requests TTFT (avg, ms) | | | |
| Cache Speedup (first/later ratio) | | | |

### 4.2 전체 결과

| 메트릭 | SGLang | vLLM | Ollama |
|--------|--------|------|--------|
| TTFT (avg, ms) | | | |
| TTFT (p50, ms) | | | |
| TTFT (p95, ms) | | | |
| Token Throughput (tok/s) | | | |
| Total Time (sec) | | | |
| Success Rate (%) | | | |

---

## 5. 시나리오 5: 한국어 성능 테스트 (Korean Language Test)

### 5.1 한국어 vs 영어 단일 요청 비교 (Concurrency: 1)

#### 짧은 질문 (경제 발전 과정 설명)

| 메트릭 | SGLang (한국어) | SGLang (영어) | vLLM (한국어) | vLLM (영어) | Ollama (한국어) | Ollama (영어) |
|--------|--------------|-------------|-------------|-----------|--------------|-------------|
| TTFT (avg, ms) | | | | | | |
| Token Throughput (tok/s) | | | | | | |
| Avg Tokens Generated | | | | | | |
| Total Latency (avg, ms) | | | | | | |
| Success Rate (%) | | | | | | |

#### 에세이 작성

| 메트릭 | SGLang (한국어) | SGLang (영어) | vLLM (한국어) | vLLM (영어) | Ollama (한국어) | Ollama (영어) |
|--------|--------------|-------------|-------------|-----------|--------------|-------------|
| TTFT (avg, ms) | | | | | | |
| Token Throughput (tok/s) | | | | | | |
| Avg Tokens Generated | | | | | | |
| Total Latency (avg, ms) | | | | | | |
| Success Rate (%) | | | | | | |

#### 기술 설명 (트랜스포머 어텐션)

| 메트릭 | SGLang (한국어) | SGLang (영어) | vLLM (한국어) | vLLM (영어) | Ollama (한국어) | Ollama (영어) |
|--------|--------------|-------------|-------------|-----------|--------------|-------------|
| TTFT (avg, ms) | | | | | | |
| Token Throughput (tok/s) | | | | | | |
| Avg Tokens Generated | | | | | | |
| Total Latency (avg, ms) | | | | | | |
| Success Rate (%) | | | | | | |

### 5.2 한국어 동시 요청 성능 (Concurrency: 8)

| 프롬프트 유형 | SGLang Throughput | SGLang p99 | vLLM Throughput | vLLM p99 | Ollama Throughput | Ollama p99 |
|-------------|-----------------|-----------|----------------|---------|-----------------|-----------|
| 짧은 질문 (한국어) | | | | | | |
| 에세이 (한국어) | | | | | | |
| 기술 설명 (한국어) | | | | | | |
| 긴 지문 요약 (한국어) | | | | | | |
| 긴 지문 요약 (영어) | | | | | | |

### 5.3 토큰 효율성 비교 (한국어 vs 영어)

> 동일 의미 프롬프트에 대한 입력/출력 토큰 수 비교

| 프롬프트 유형 | SGLang 한국어 출력 토큰 | SGLang 영어 출력 토큰 | 한/영 비율 | vLLM 한국어 | vLLM 영어 | Ollama 한국어 | Ollama 영어 |
|-------------|---------------------|--------------------|---------|-----------|---------|-----------| ---------|
| 짧은 질문 | | | | | | | |
| 에세이 | | | | | | | |
| 기술 설명 | | | | | | | |

### 5.4 한국어 성능 핵심 발견

1. **토큰 효율성**: 한국어는 영어 대비 동일 의미 전달에 약 ___배 많은 토큰 소비
2. **처리량 차이**: 한국어 tok/s vs 영어 tok/s — 실질 정보 처리 속도 차이
3. **프레임워크별 차이**: 토크나이저 차이에 따른 프레임워크별 한국어 처리 효율
4. **Ollama GGUF 영향**: GGUF 토크나이저의 한국어 토큰화 효율성

---

## 6. GPU 리소스 사용량

| 메트릭 | SGLang | vLLM | Ollama |
|--------|--------|------|--------|
| 모델 로딩 후 VRAM (MB) | | | |
| 피크 VRAM (MB) | | | |
| 평균 GPU 활용률 (%) | | | |

---

## 6. 핵심 발견 요약

### 6.1 가설 검증 결과

| 가설 | 결과 | 근거 |
|------|------|------|
| H1: SGLang > vLLM (접두사 캐시) | TBD | |
| H2: SGLang/vLLM >> Ollama (동시 요청) | TBD | |
| H3: Ollama 단일 요청 경쟁력 | TBD | |
| H4: 프레임워크별 성능 저하 패턴 상이 | TBD | |
| H5: 한국어 토큰 효율성/처리량 프레임워크별 차이 | TBD | |

### 6.2 주요 발견

1. **처리량 (Throughput)**:
2. **레이턴시 (Latency)**:
3. **캐시 효율성**:
4. **동시성 확장성**:
5. **GPU 메모리 효율**:
6. **한국어 성능**:

---

## 부록: 테스트 환경 상세

```
OS: Ubuntu 22.04.3 LTS
GPU: NVIDIA A100-SXM4-80GB
CPU: Intel Xeon Platinum 8468, 96C/192T
RAM: ~1 TiB
NVIDIA Driver: 570.86.10
CUDA: 12.1

SGLang: v0.5.6.post2 (pip)
vLLM: v0.15.1 (pip)
Ollama: v0.15.6 (binary)

Model: openai/gpt-oss-20b (FP16 for SGLang/vLLM, GGUF Q4 for Ollama)
```
