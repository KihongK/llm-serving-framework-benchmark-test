# LLM 서빙 프레임워크 심층 조사 보고서

> SGLang v0.5.8.post1 | vLLM v0.15.1 | Ollama v0.16.2
> 작성일: 2026-02-12

---

## 1. 개요

본 보고서는 LLM(대규모 언어 모델) 추론 및 서빙을 위한 세 가지 주요 오픈소스 프레임워크인 **SGLang**, **vLLM**, **Ollama**를 심층 비교 분석한다. 각 프레임워크의 아키텍처, 핵심 기술, 지원 기능, 커뮤니티 활성도, 프로덕션 배포 사례를 조사하고, 장단점을 구체적 근거와 함께 정리한다.

### 프레임워크 포지셔닝

| 프레임워크 | 주요 포지션 | 대상 사용자 |
|-----------|-----------|-----------|
| SGLang | 고성능 구조화 생성 최적화 서빙 엔진 | 프로덕션/연구 |
| vLLM | 범용 고처리량 추론 서빙 엔진 | 프로덕션/엔터프라이즈 |
| Ollama | 로컬 LLM 실행 간편화 도구 | 개인/개발자/프로토타이핑 |

---

## 2. SGLang 상세 분석

### 2.1 아키텍처와 핵심 기술

SGLang은 LLM 추론 시스템의 프로그래밍 인터페이스와 런타임 시스템을 공동 설계(co-design)하여 복잡한 다단계 생성 워크플로우를 최적화하는 고성능 서빙 프레임워크이다.

#### 어텐션 백엔드: RadixAttention

SGLang의 가장 핵심적인 혁신은 **RadixAttention**이다. 기존 PagedAttention이 고정 크기 블록으로 KV 캐시를 관리하는 것과 달리, SGLang은 **기수 트리(Radix Tree, 압축 접두사 트리)** 자료구조를 사용하여 요청 간 자동, 세밀한 접두사 공유를 구현한다.

- 생성 요청 완료 후 KV 캐시를 버리지 않고, 프롬프트와 생성 결과 모두의 KV 캐시를 기수 트리에 보존
- LRU(Least Recently Used) 축출 정책으로 메모리 관리
- 캐시-인식 스케줄링(Cache-Aware Scheduling)으로 캐시 적중률 극대화
- 실험 결과 벤치마크 전반에 걸쳐 **50%~99%**의 캐시 적중률 달성

#### 스케줄링 방식: Zero-Overhead CPU Scheduler

- GPU가 현재 배치를 처리하는 동안 CPU가 다음 배치를 준비하는 **오버랩 스케줄링** 아키텍처
- GPU 유휴 시간을 제거하여 GPU 활용률 100%에 근접
- 공유 접두사가 있는 요청을 함께 배치하여 캐시 적중률 향상
- 깊이 우선 탐색(DFS)을 근사하는 캐시-인식 요청 우선순위 배정

#### KV 캐시 관리

- 기수 트리 기반 자동 접두사 매칭 및 재사용
- Token Attention (Paged Attention 호환)
- FP8 E5M2 KV 캐시 양자화 지원
- Chunked Prefill로 긴 프롬프트 효율적 처리

#### 양자화 지원

| 방식 | 지원 여부 |
|------|---------|
| FP8 | O (온라인/오프라인) |
| FP4 | O |
| INT4 | O |
| AWQ | O |
| GPTQ | O |
| Marlin | O |
| AWQ Marlin | O |
| GPTQ Marlin | O |
| BitsAndBytes | O |
| GGUF | O (예정/부분 지원) |

### 2.2 지원 모델 범위와 호환성

#### 지원 모델 아키텍처

- **언어 모델**: Llama, Qwen, DeepSeek, Kimi, GLM, GPT, Gemma, Mistral, Nemotron, MiniMax, LLaDA (Diffusion LLM) 등
- **멀티모달 모델**: 비전-언어 모델 지원
- **임베딩 모델**: e5-mistral, gte, mcdse
- **보상 모델**: Skywork
- **디퓨전 모델**: WAN, Qwen-Image (2026년 1월 추가)

#### 모델 포맷

- HuggingFace Transformers 포맷 (기본)
- SafeTensors
- GPTQ/AWQ 사전 양자화 체크포인트
- FP8 체크포인트 직접 로드

### 2.3 주요 기능

| 기능 | 지원 여부 | 비고 |
|------|---------|------|
| 연속 배칭 (Continuous Batching) | O | |
| 텐서 병렬 (Tensor Parallelism) | O | |
| 파이프라인 병렬 (Pipeline Parallelism) | O | |
| 데이터 병렬 (Data Parallelism) | O | |
| 전문가 병렬 (Expert Parallelism) | O | MoE 모델용 |
| 구조화 출력 (Structured Output) | O | JSON, 정규식, 문법 |
| Speculative Decoding | O | |
| Prefix Caching | O | RadixAttention 기반, 자동 |
| Chunked Prefill | O | |
| Multi-LoRA Batching | O | |
| Prefill-Decode 분리 | O | |
| 멀티 노드 분산 서빙 | O | sgl-router (Rust 기반) |

### 2.4 설치/설정 난이도

- **설치 단계**: `pip install "sglang[all]"` 한 줄로 설치 가능 (pre-built wheels 제공)
- **의존성**: CUDA 12.x, PyTorch 2.x, FlashInfer 등 자동 설치
- **서버 실행**: `python -m sglang.launch_server --model-path <model> --tp <n>` 으로 간편 실행
- **설정 파라미터**: `--tp`, `--dp`, `--quantization`, `--kv-cache-dtype` 등 CLI 플래그 기반
- **난이도 평가**: 중간 - pip 설치는 간편하나, 최적 성능을 위한 튜닝 파라미터가 다양함

### 2.5 커뮤니티 활성도와 업데이트 주기

| 지표 | 수치 (2026년 2월 기준) |
|------|---------------------|
| GitHub Stars | ~23,500 |
| Contributors | 1,554 |
| Forks | 3,700+ |
| 릴리스 주기 | 2~4주 (활발) |
| 최신 안정 버전 | v0.5.8 (2026년 1월) |
| 커뮤니티 채널 | Slack, GitHub Discussions |

- 2025년 3월 PyTorch 생태계에 공식 편입
- 2025년 6월 a]16z 오픈소스 AI 그랜트 수상
- NVIDIA 공식 컨테이너에 포함 (NVIDIA Docs에서 릴리스 노트 제공)

### 2.6 프로덕션 배포 사례

| 기업/기관 | 용도 |
|----------|------|
| xAI | LLM 추론 인프라 |
| LinkedIn | AI 기능 서빙 |
| Cursor | 코드 생성 AI 서빙 |
| AMD, NVIDIA, Intel | 하드웨어 파트너 / 추론 최적화 |
| Oracle Cloud, Google Cloud, MS Azure, AWS | 클라우드 서빙 |
| MIT, Stanford, UC Berkeley, UCLA, 칭화대 | 연구 |

- 전 세계 **400,000개 이상의 GPU**에서 운영
- 매일 **수조(trillions) 개의 토큰** 생성

---

## 3. vLLM 상세 분석

### 3.1 아키텍처와 핵심 기술

vLLM은 UC Berkeley에서 시작된 고처리량, 메모리 효율적 LLM 추론 및 서빙 엔진이다. 운영체제의 가상 메모리 개념에서 영감을 받은 PagedAttention이 핵심이다.

#### 어텐션 백엔드: PagedAttention

- 운영체제의 가상 메모리와 페이징에서 영감을 받은 어텐션 알고리즘
- KV 캐시를 **고정 크기 블록**으로 분할하여 비연속 메모리 공간에 저장
- 외부 단편화 제거, 내부 단편화 최소화
- 기존 시스템 대비 KV 캐시 메모리 낭비를 60~80%에서 **4% 미만**으로 감소
- FlashAttention, FlashInfer와 통합

#### 스케줄링 방식

- 연속 배칭(Continuous Batching) 기반 스케줄러
- V1 엔진(v0.9.0+)에서 MoE 모델을 위한 DP Attention 지원
- 비동기 스케줄링으로 speculative decoding과 연계

#### KV 캐시 관리

- PagedAttention 기반 블록 단위 메모리 관리
- Prefix Caching 지원 (수동/자동)
- FP8 KV 캐시 양자화 지원
- 메모리 공유로 parallel sampling, beam search 시 메모리 55% 절감

#### 양자화 지원

| 방식 | 지원 여부 |
|------|---------|
| FP8 | O (활성화 양자화 포함) |
| INT8 | O |
| GPTQ | O (Marlin/Machete 커널) |
| AWQ | O (Marlin/Machete 커널) |
| AQLM | O |
| QQQ | O |
| HQQ | O |
| BitsAndBytes | O |
| GGUF | O |
| wNa16 | O |

> 전체 vLLM 배포의 20% 이상이 양자화를 사용 중

### 3.2 지원 모델 범위와 호환성

#### 지원 모델 아키텍처

vLLM은 가장 넓은 모델 호환성을 보유한다:
- **Decoder-only**: Llama, GPT-2/J/NeoX, Mistral, Qwen, DeepSeek (V2/V3/R1), Falcon, Gemma, Phi, OLMo, StarCoder 등
- **Encoder-Decoder**: T5, BART, Whisper 등
- **MoE (Mixture of Experts)**: Mixtral, DeepSeek-MoE, DBRX 등
- **멀티모달**: LLaVA, InternVL, Pixtral 등
- **임베딩**: 다양한 임베딩 모델 지원
- **MLA/MQA 아키텍처**: DeepSeek-V2/V3 전용 DP Attention

#### 모델 포맷

- HuggingFace Transformers (기본)
- SafeTensors
- GPTQ/AWQ 사전 양자화 체크포인트
- GGUF
- FP8 체크포인트

### 3.3 주요 기능

| 기능 | 지원 여부 | 비고 |
|------|---------|------|
| 연속 배칭 (Continuous Batching) | O | 핵심 기능 |
| 텐서 병렬 (Tensor Parallelism) | O | NVLink/InfiniBand 권장 |
| 파이프라인 병렬 (Pipeline Parallelism) | O | 멀티 노드 시 유용 |
| 데이터 병렬 (Data Parallelism) | O | V1 엔진 |
| 전문가 병렬 (Expert Parallelism) | O | MoE 모델용 |
| 구조화 출력 (Structured Output) | O | JSON, 정규식, 문법, guided_choice |
| Speculative Decoding | O | Draft 모델, n-gram, Medusa, EAGLE |
| Prefix Caching | O | 수동/자동 |
| Chunked Prefill | O | |
| Multi-LoRA | O | |
| 멀티 노드 분산 서빙 | O | Ray 백엔드 기반 |
| Production Stack | O | K8s 네이티브 배포 참조 구현 |

### 3.4 설치/설정 난이도

- **설치 단계**: `pip install vllm` 한 줄로 설치 가능
- **의존성**: CUDA, PyTorch 자동 설치 / NVIDIA 공식 컨테이너 제공
- **서버 실행**: `vllm serve <model> --host 0.0.0.0 --port 8000` 으로 OpenAI 호환 API 서버 즉시 기동
- **설정 파라미터**: `--tensor-parallel-size`, `--quantization`, `--max-model-len` 등
- **K8s 배포**: vLLM Production Stack으로 단일 인스턴스에서 분산 배포까지 코드 변경 없이 확장
- **난이도 평가**: 낮음~중간 - OpenAI API 호환으로 기존 코드 마이그레이션 용이

### 3.5 커뮤니티 활성도와 업데이트 주기

| 지표 | 수치 (2026년 2월 기준) |
|------|---------------------|
| GitHub Stars | ~70,100 |
| Contributors | 1,200+ |
| Forks | 10,000+ |
| 릴리스 주기 | 1~2주 (매우 활발) |
| 최신 안정 버전 | v0.15.1 |
| 커뮤니티 채널 | Discord, GitHub Discussions |

- 15명 이상의 풀타임 컨트리뷰터 (6개 이상 조직)
- 20개 이상 조직이 핵심 이해관계자/스폰서
- UC Berkeley, Neural Magic, Anyscale, Roblox, IBM, AMD, Intel, NVIDIA 참여
- Red Hat 공식 지원 및 기술 블로그 연재

### 3.6 프로덕션 배포 사례

| 기업 | 용도 | 규모 |
|------|------|------|
| Amazon (Rufus) | 쇼핑 어시스턴트 | 2.5억 고객, 80,000+ 추론 칩 |
| LinkedIn | 50+ AI 기능 | 수천 대 호스트 |
| Meta | LLM 추론 인프라 | - |
| Roblox | 언어 작업 (speculative decoding 활용) | 글로벌 사용자 기반 |
| Mistral AI | 모델 서빙 | - |
| Cohere | 추론 엔진 | - |
| IBM | 엔터프라이즈 AI | - |
| Stripe | 추론 비용 73% 절감 | - |

---

## 4. Ollama 상세 분석

### 4.1 아키텍처와 핵심 기술

Ollama는 llama.cpp 위에 구축된 추상화 계층으로, C/C++ 기반 추론 엔진의 성능을 활용하면서도 사용자 친화적인 API와 모델 오케스트레이션을 제공하는 로컬 LLM 실행 도구이다.

#### 어텐션 백엔드

- llama.cpp의 어텐션 구현 사용
- FlashAttention 지원 (llama.cpp 백엔드 경유)
- PagedAttention, RadixAttention 같은 고급 KV 캐시 관리 미지원

#### 스케줄링 방식

- 순차 처리(Sequential Processing) 기반
- 제한적 병렬 요청 처리 (동시 요청 시 1~3 req/sec 수준)
- 연속 배칭(Continuous Batching) 미지원 또는 매우 제한적
- VRAM 가용량에 따른 동적 컨텍스트 길이 조정

#### KV 캐시 관리

- llama.cpp 기본 KV 캐시 관리
- 고급 캐시 재사용/공유 메커니즘 없음
- 모델별 전체 VRAM 할당 필요 (부분 로드 미지원)

#### 양자화 지원

| 방식 | 지원 여부 | 비고 |
|------|---------|------|
| GGUF (Q2_K ~ Q8_0) | O | 기본 포맷 |
| IQ2, IQ3 | O | 중요도 행렬 기반 |
| 1.5-bit ~ 8-bit | O | 다양한 양자화 수준 |
| FP16 | O | |
| FP8 | X | llama.cpp 제한 |
| GPTQ | X | |
| AWQ | X | |

> 기본값: Q4_K_M 양자화 사용

### 4.2 지원 모델 범위와 호환성

#### 지원 모델

- Llama 3.x, Qwen 2.5/3, DeepSeek, Gemma, Mistral, Phi, GPT-OSS, GLM, Kimi 등
- HuggingFace Hub의 45,000+ GGUF 체크포인트 실행 가능
- Modelfile을 통한 HuggingFace 모델 자동 변환

#### 모델 포맷

- **GGUF** (기본 및 유일한 네이티브 포맷)
- SafeTensors -> GGUF 변환 필요
- HuggingFace 모델 자동 변환 지원

### 4.3 주요 기능

| 기능 | 지원 여부 | 비고 |
|------|---------|------|
| 연속 배칭 (Continuous Batching) | X | 순차 처리 |
| 텐서 병렬 (Tensor Parallelism) | X | 레이어 분산만 가능 |
| 파이프라인 병렬 (Pipeline Parallelism) | X | |
| 멀티 GPU | △ | 레이어 분산(model splitting), 진정한 병렬 아님 |
| 구조화 출력 (Structured Output) | O | JSON mode 지원 |
| Tool Calling | O | 2025년 추가 |
| Speculative Decoding | X | |
| Prefix Caching | X | |
| Modelfile | O | Docker 스타일 모델 설정 |
| REST API | O | OpenAI 호환 |
| 데스크톱 앱 | O | macOS, Windows, Linux |
| CPU 추론 | O | GPU 없이도 실행 가능 |
| Sub-agent 지원 | O | CLI 복잡 작업 오케스트레이션 |

### 4.4 설치/설정 난이도

- **설치 단계**: `curl -fsSL https://ollama.com/install.sh | sh` 한 줄 설치 또는 데스크톱 앱 설치
- **의존성**: Go 바이너리로 배포, Python/CUDA 별도 설치 불필요
- **서버 실행**: `ollama serve` / `ollama run <model>` 으로 즉시 사용
- **모델 다운로드**: `ollama pull llama3` 형태로 원클릭 모델 관리
- **설정 파라미터**: 매우 적음 (환경 변수 기반)
- **난이도 평가**: **매우 낮음** - 개발 환경 설정 없이 즉시 사용 가능

### 4.5 커뮤니티 활성도와 업데이트 주기

| 지표 | 수치 (2026년 2월 기준) |
|------|---------------------|
| GitHub Stars | ~158,000 |
| Contributors | 500+ |
| Forks | 12,000+ |
| 릴리스 주기 | 1~2주 |
| 최신 안정 버전 | v0.15.6 |
| 커뮤니티 채널 | Discord, GitHub Issues |

- GitHub Stars 기준 세 프레임워크 중 가장 높은 인기
- Open WebUI, LangChain, LlamaIndex 등 풍부한 생태계 통합
- 데스크톱 사용자 중심 커뮤니티

### 4.6 프로덕션 배포 사례

#### 개인/로컬 용도

| 사용 사례 | 설명 |
|----------|------|
| 로컬 AI 개발 | 개인 개발자의 LLM 프로토타이핑 |
| 프라이버시 중심 AI | 데이터가 외부로 나가지 않는 로컬 추론 |
| AI 에이전트 개발 | LangChain, CrewAI 등과 통합한 에이전트 |
| 교육/학습 | LLM 학습 및 실험 |

#### 프로덕션 용도

| 사용 사례 | 설명 |
|----------|------|
| 온프레미스 엔터프라이즈 | 규제 산업에서 데이터 프라이버시 확보 |
| 소규모 배포 | 단일 사용자 또는 소규모 팀 내부 도구 |
| 에지 디바이스 | 로컬 추론이 필요한 에지 배포 |

> 프로덕션 대규모 배포 사례는 제한적. 높은 동시성/처리량이 필요한 경우 vLLM 또는 SGLang 권장.

---

## 5. 세 프레임워크 비교 요약표

### 5.1 아키텍처 및 핵심 기술 비교

| 항목 | SGLang | vLLM | Ollama |
|------|--------|------|--------|
| 어텐션 백엔드 | RadixAttention (기수 트리 기반) | PagedAttention (가상 메모리 기반) | llama.cpp 기본 |
| KV 캐시 관리 | 기수 트리 + LRU + 캐시-인식 스케줄링 | 블록 기반 + Prefix Caching | 기본 (고급 관리 없음) |
| 스케줄러 | Zero-Overhead 오버랩 스케줄러 | 연속 배칭 스케줄러 | 순차 처리 |
| 연속 배칭 | O | O | X |
| 구현 언어 | Python + C++/CUDA + Rust (라우터) | Python + C++/CUDA | Go + C/C++ (llama.cpp) |

### 5.2 병렬 처리 및 분산 서빙 비교

| 항목 | SGLang | vLLM | Ollama |
|------|--------|------|--------|
| 텐서 병렬 | O | O | X |
| 파이프라인 병렬 | O | O | X |
| 데이터 병렬 | O | O | X |
| 전문가 병렬 | O | O | X |
| 멀티 노드 | O (sgl-router) | O (Ray) | X |
| 멀티 GPU | O | O | △ (레이어 분산만) |

### 5.3 양자화 지원 비교

| 양자화 방식 | SGLang | vLLM | Ollama |
|-----------|--------|------|--------|
| FP8 | O | O | X |
| FP4 | O | X | X |
| INT4 | O | O | O (GGUF Q4) |
| INT8 | O | O | O (GGUF Q8) |
| GPTQ | O | O | X |
| AWQ | O | O | X |
| GGUF | △ | O | O (기본) |
| BitsAndBytes | O | O | X |

### 5.4 기능 비교

| 기능 | SGLang | vLLM | Ollama |
|------|--------|------|--------|
| 구조화 출력 | O (JSON, 정규식, 문법) | O (JSON, 정규식, 문법) | O (JSON) |
| Speculative Decoding | O | O | X |
| Prefix Caching | O (자동, RadixAttention) | O (수동/자동) | X |
| Tool Calling | O | O | O |
| Multi-LoRA | O | O | X |
| OpenAI 호환 API | O | O | O |
| 멀티모달 | O | O | O |
| CPU 전용 추론 | △ | △ | O |
| 데스크톱 앱 | X | X | O |

### 5.5 성능 비교 (독립 벤치마크 기준)

| 지표 | SGLang | vLLM | Ollama |
|------|--------|------|--------|
| 처리량 (tok/s) | 16,215 | 12,553 | ~484 |
| TTFT (ms) | 79 | 103 | 65 (단일) |
| ITL (ms) | 6.0 | 7.1 | - |
| 128 동시 요청 안정성 | 100% | 100% | 실패 |
| P99 지연 (피크) | 낮음 | 80ms | 673ms |
| SGLang 대비 처리량 | 기준 (1.0x) | 0.77x | 0.03x |

> 주: 벤치마크 결과는 하드웨어(H100), 모델, 워크로드에 따라 달라질 수 있음

### 5.6 설치 및 운영 비교

| 항목 | SGLang | vLLM | Ollama |
|------|--------|------|--------|
| 설치 난이도 | 중간 | 낮음~중간 | 매우 낮음 |
| 최소 의존성 | CUDA, Python 3.10+ | CUDA, Python 3.9+ | 없음 (Go 바이너리) |
| GPU 필수 여부 | 사실상 필수 | 사실상 필수 | 선택 (CPU 가능) |
| K8s 배포 지원 | 커뮤니티 | 공식 (Production Stack) | 커뮤니티 |
| 문서 품질 | 양호 | 우수 | 양호 |

### 5.7 커뮤니티 및 생태계 비교

| 항목 | SGLang | vLLM | Ollama |
|------|--------|------|--------|
| GitHub Stars | ~23,500 | ~70,100 | ~158,000 |
| Contributors | 1,554 | 1,200+ | 500+ |
| 주요 후원 | a16z, PyTorch 생태계 | Red Hat, Anyscale, Neural Magic | Ollama Inc. |
| 생태계 통합 | NVIDIA, AMD, 클라우드 | NVIDIA, AMD, Red Hat, 클라우드 | Open WebUI, LangChain |

---

## 6. 각 프레임워크별 장단점 정리

### 6.1 SGLang

#### 장점

1. **RadixAttention 기반 최고 수준의 캐시 효율성**: 기수 트리 자료구조로 요청 간 자동 접두사 공유를 구현하여 50~99% 캐시 적중률 달성. 특히 챗봇, few-shot 학습 등 공유 접두사가 많은 워크로드에서 vLLM 대비 29% 높은 처리량을 보임.

2. **Zero-Overhead 스케줄링으로 GPU 활용률 극대화**: CPU-GPU 오버랩 스케줄링으로 GPU 유휴 시간을 실질적으로 제거. 지속적 워크로드에서 GPU 활용률 100%에 근접.

3. **구조화 생성(Structured Generation) 최적화**: DSL(Domain-Specific Language)과 런타임의 공동 설계로 복잡한 다단계 생성 워크플로우를 효율적으로 처리. JSON, 정규식, 문법 기반 구조화 출력에서 탁월한 성능.

4. **가장 넓은 하드웨어 지원**: NVIDIA (GB200/B300/H100/A100), AMD (MI355/MI300), Intel Xeon, Google TPU, Ascend NPU 등을 모두 지원. 400,000+ GPU에서 검증됨.

5. **빠른 최신 모델 지원**: 주요 오픈소스 모델 출시 당일(day-0) 지원 제공. DeepSeek, Qwen, Mistral, LLaDA 등 최신 모델을 가장 빠르게 서빙 가능.

#### 단점

1. **vLLM 대비 작은 커뮤니티**: GitHub Stars 23.5K vs vLLM 70.1K로, 커뮤니티 규모와 서드파티 통합 생태계가 vLLM보다 작음. 문제 발생 시 참고할 수 있는 자료가 상대적으로 적음.

2. **K8s 프로덕션 배포 도구 부족**: vLLM이 공식 Production Stack (K8s 네이티브)을 제공하는 반면, SGLang은 sgl-router 기반 분산 서빙은 가능하나 공식 K8s 배포 참조 구현이 상대적으로 미흡.

3. **GGUF 포맷 지원 제한**: GGUF 모델 직접 로드가 완전하지 않아 양자화된 소형 모델 실행 시 vLLM 대비 불편. GPTQ/AWQ/FP8 위주 양자화에 초점.

4. **학습 곡선**: RadixAttention, 캐시-인식 스케줄링 등 고유 개념이 많아 최적 설정을 위한 이해 비용이 존재. DSL 활용 시 추가 학습 필요.

### 6.2 vLLM

#### 장점

1. **가장 넓은 모델 호환성과 생태계**: Decoder-only, Encoder-Decoder, MoE, 멀티모달, 임베딩 모델까지 가장 다양한 아키텍처를 지원. HuggingFace, GGUF, SafeTensors 등 모든 주요 포맷 호환.

2. **검증된 대규모 프로덕션 배포**: Amazon Rufus(2.5억 고객), LinkedIn(50+ AI 기능, 수천 호스트), Meta, Roblox 등에서 대규모 프로덕션 운영 검증. Stripe는 추론 비용 73% 절감.

3. **PagedAttention 기반 최적 메모리 효율**: KV 캐시 메모리 낭비를 4% 미만으로 줄여 동일 GPU에서 더 큰 배치 크기와 더 긴 시퀀스 처리 가능. Parallel sampling, beam search 시 메모리 55% 절감.

4. **K8s 네이티브 프로덕션 스택**: 공식 Production Stack으로 단일 인스턴스에서 분산 배포까지 코드 변경 없이 확장. Ray 백엔드 기반 멀티 노드 분산 서빙.

5. **강력한 커뮤니티와 기업 지원**: 70K+ Stars, Red Hat 공식 지원, 15+ 풀타임 컨트리뷰터, 20+ 참여 조직. 문서, 튜토리얼, 문제 해결 자료가 풍부.

#### 단점

1. **SGLang 대비 낮은 처리량**: 독립 벤치마크에서 SGLang 대비 20~29% 낮은 처리량. 특히 접두사 공유가 많은 워크로드에서 격차가 벌어짐.

2. **Prefix Caching의 수동적 특성**: SGLang의 RadixAttention이 자동으로 접두사를 감지하고 캐싱하는 반면, vLLM의 Prefix Caching은 명시적 설정이 필요하고 캐시 적중률이 상대적으로 낮음.

3. **설치/의존성 복잡도**: CUDA, PyTorch, 다수의 C++ 확장 의존성으로 인해 환경 설정에서 충돌이 발생할 수 있음. 소스 빌드 시 이슈가 빈번.

4. **분산 서빙 시 Ray 의존성**: 멀티 노드 서빙에 Ray 클러스터가 필요하여 인프라 복잡도가 증가. SGLang의 독립적인 sgl-router 대비 설정이 번거로움.

### 6.3 Ollama

#### 개인/로컬 용도 관점

##### 장점

1. **압도적 설치 편의성**: 한 줄 설치(`curl | sh`) 또는 데스크톱 앱으로 Python, CUDA 등 개발 환경 없이 즉시 LLM 사용 가능. 비개발자도 접근 가능한 유일한 프레임워크.

2. **CPU 추론 지원**: GPU 없이도 CPU만으로 LLM 실행 가능. 노트북, 데스크톱 등 일반 하드웨어에서 작동. macOS(Apple Silicon), Windows, Linux 모두 지원.

3. **풍부한 모델 생태계**: `ollama pull` 한 줄로 모델 다운로드 및 실행. HuggingFace의 45,000+ GGUF 모델 즉시 사용 가능. Modelfile로 커스텀 모델 생성 간편.

4. **완전한 로컬 프라이버시**: 모든 추론이 로컬에서 수행되어 데이터가 외부로 전송되지 않음. 규제가 엄격한 환경(의료, 금융)에서 프라이버시 확보.

5. **활발한 생태계 통합**: Open WebUI, LangChain, LlamaIndex, CrewAI 등 주요 AI 프레임워크와 손쉬운 통합. 158K GitHub Stars로 가장 큰 사용자 커뮤니티.

##### 단점

1. **GGUF 포맷 전용**: GPTQ, AWQ, FP8 등 GPU 최적화 양자화 포맷을 지원하지 않아, GPU 환경에서 최적 성능을 낼 수 없음.

2. **제한적 추론 성능**: 단일 사용자 시나리오에서도 vLLM/SGLang 대비 10~30배 낮은 처리량. 복잡한 태스크나 긴 컨텍스트에서 체감 속도 차이가 큼.

3. **고급 기능 부재**: Speculative Decoding, Prefix Caching, Multi-LoRA 등 추론 최적화 기능이 없어 고급 사용 시나리오에서 제한적.

#### 프로덕션 용도 관점

##### 장점

1. **극도로 간단한 배포**: Docker 컨테이너 또는 바이너리 하나로 배포 완료. 복잡한 인프라 설정 없이 즉시 서비스 가능.

2. **낮은 운영 비용**: 의존성이 적어 유지보수가 간편. Go 바이너리로 메모리/CPU 오버헤드가 낮음.

##### 단점

1. **연속 배칭 미지원으로 동시성 부족**: 동시 요청 시 1~3 req/sec 수준으로, 다수 사용자 서비스에 부적합. 128 동시 요청에서 실패.

2. **텐서/파이프라인 병렬 미지원**: 진정한 멀티 GPU 병렬 처리가 불가능하여 대형 모델 서빙이나 수평 확장에 근본적 한계.

3. **프로덕션 관측성/관리 도구 부족**: 네이티브 메트릭, 분산 트레이싱, 로드 밸런싱 등 프로덕션 운영에 필요한 도구가 내장되지 않음.

4. **메모리 관리 비효율**: 모델당 전체 VRAM 할당이 필요하고, KV 캐시 최적화가 없어 동일 GPU에서 처리 가능한 배치 크기와 동시 요청 수가 크게 제한됨.

5. **대규모 프로덕션 배포 사례 부재**: Amazon, LinkedIn, Meta 등에서 검증된 vLLM/SGLang과 달리, Ollama의 대규모 프로덕션 배포 사례는 보고되지 않음.

---

## 참고 자료

- [SGLang GitHub Repository](https://github.com/sgl-project/sglang)
- [SGLang Documentation](https://sgl-project.github.io/)
- [Fast and Expressive LLM Inference with RadixAttention and SGLang (LMSYS)](https://lmsys.org/blog/2024-01-17-sglang/)
- [vLLM GitHub Repository](https://github.com/vllm-project/vllm)
- [vLLM Documentation](https://docs.vllm.ai/en/stable/)
- [vLLM: Easy, Fast, and Cheap LLM Serving with PagedAttention](https://blog.vllm.ai/2023/06/20/vllm.html)
- [Efficient Memory Management for Large Language Model Serving with PagedAttention (arXiv)](https://arxiv.org/abs/2309.06180)
- [vLLM 2024 Retrospective and 2025 Vision](https://blog.vllm.ai/2025/01/10/vllm-2024-wrapped-2025-vision.html)
- [Ollama GitHub Repository](https://github.com/ollama/ollama)
- [Ollama vs. vLLM: Performance Benchmarking (Red Hat)](https://developers.redhat.com/articles/2025/08/08/ollama-vs-vllm-deep-dive-performance-benchmarking)
- [Choosing your LLM framework: Ollama, vLLM, SGLang and TensorRT-LLM](https://medium.com/ordina-data/choosing-your-llm-framework-a-comparison-of-ollama-vllm-sglang-and-tensorrt-llm-e0cb4a0d1cb8)
- [SGLang vs vLLM: Which is Better for Your Needs in 2026?](https://kanerika.com/blogs/sglang-vs-vllm/)
- [How Amazon scaled Rufus with vLLM](https://aws.amazon.com/blogs/machine-learning/how-amazon-scaled-rufus-by-building-multi-node-inference-using-aws-trainium-chips-and-vllm/)
- [LinkedIn touts vLLM brilliance for 50 AI use cases](https://www.thestack.technology/linkedin-touts-vllm-brilliance-for-50-ai-use-cases/)
