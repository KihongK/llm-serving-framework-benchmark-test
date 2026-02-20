export type TechStatus = 'on' | 'off' | 'partial'

export interface TechEntry {
  label: string
  sglang: { value: string; status: TechStatus }
  vllm: { value: string; status: TechStatus }
  ollama: { value: string; status: TechStatus }
}

export const TECH_STACK: TechEntry[] = [
  {
    label: 'Attention',
    sglang: { value: 'Triton Backend', status: 'on' },
    vllm: { value: 'TRITON_ATTN', status: 'on' },
    ollama: { value: 'llama.cpp Flash', status: 'on' },
  },
  {
    label: 'KV Cache',
    sglang: { value: 'RadixAttention (token)', status: 'on' },
    vllm: { value: 'PagedAttention (block)', status: 'on' },
    ollama: { value: 'Ring Buffer (slot)', status: 'on' },
  },
  {
    label: 'Batching',
    sglang: { value: 'Continuous', status: 'on' },
    vllm: { value: 'Continuous', status: 'on' },
    ollama: { value: 'Slot-based', status: 'partial' },
  },
  {
    label: 'Prefix Caching',
    sglang: { value: 'Radix Tree (ON)', status: 'on' },
    vllm: { value: 'APC hash-based (ON)', status: 'on' },
    ollama: { value: 'Slot-internal (partial)', status: 'partial' },
  },
  {
    label: 'Chunked Prefill',
    sglang: { value: 'ON (8192 tok)', status: 'on' },
    vllm: { value: 'ON (2048 tok)', status: 'on' },
    ollama: { value: 'OFF', status: 'off' },
  },
  {
    label: 'CUDA Graphs',
    sglang: { value: 'ON (max_bs=256)', status: 'on' },
    vllm: { value: 'ON (torch.compile)', status: 'on' },
    ollama: { value: 'OFF', status: 'off' },
  },
  {
    label: 'Overlap Scheduling',
    sglang: { value: 'ON (zero-overhead)', status: 'on' },
    vllm: { value: 'OFF', status: 'off' },
    ollama: { value: 'OFF', status: 'off' },
  },
  {
    label: 'Scheduling',
    sglang: { value: 'FCFS', status: 'on' },
    vllm: { value: 'Iteration-level', status: 'on' },
    ollama: { value: 'FIFO Queue', status: 'on' },
  },
  {
    label: 'MXFP4 Kernel',
    sglang: { value: 'Triton kernel', status: 'on' },
    vllm: { value: 'Marlin kernel', status: 'on' },
    ollama: { value: 'GGML kernel', status: 'on' },
  },
  {
    label: 'Memory',
    sglang: { value: 'Static 85%', status: 'on' },
    vllm: { value: 'Static 85%', status: 'on' },
    ollama: { value: 'Dynamic', status: 'partial' },
  },
]

export type ScenarioKey =
  | 'single_request'
  | 'concurrent_load'
  | 'long_context'
  | 'prefix_cache'
  | 'korean'

export interface ScenarioTechMapping {
  keys: string[]
  reason: string
}

export const SCENARIO_TECH_MAP: Record<ScenarioKey, ScenarioTechMapping> = {
  single_request: {
    keys: ['Attention', 'CUDA Graphs', 'Memory'],
    reason: 'Single-request latency depends on kernel efficiency, CUDA graphs, and memory allocation speed',
  },
  concurrent_load: {
    keys: ['Batching', 'Scheduling', 'Overlap Scheduling', 'Chunked Prefill'],
    reason: 'Concurrent throughput depends on batching strategy and scheduling policy',
  },
  long_context: {
    keys: ['Attention', 'Chunked Prefill', 'KV Cache', 'Memory'],
    reason: 'Long context depends on attention scaling, chunking strategy, and KV cache management',
  },
  prefix_cache: {
    keys: ['Prefix Caching', 'KV Cache', 'Attention'],
    reason: 'Directly tests cache implementation: Radix Tree vs APC vs Slot',
  },
  korean: {
    keys: ['Attention', 'MXFP4 Kernel', 'Batching'],
    reason: 'Korean tokenizer differences and dequantization kernel impact',
  },
}

export function getTechForScenario(scenario: string): TechEntry[] {
  const mapping = SCENARIO_TECH_MAP[scenario as ScenarioKey]
  if (!mapping) return []
  return TECH_STACK.filter((t) => mapping.keys.includes(t.label))
}

export interface LaunchParam {
  param: string
  value: string
}

export const SERVER_LAUNCH_PARAMS: Record<string, LaunchParam[]> = {
  sglang: [
    { param: 'Version', value: '0.5.8.post1' },
    { param: 'Model', value: 'openai/gpt-oss-20b' },
    { param: 'TP', value: '1' },
    { param: 'Port', value: '30000' },
    { param: 'GPU Memory', value: '85% (static)' },
    { param: 'Prefix Cache', value: 'Radix Tree (default ON)' },
    { param: 'Chunked Prefill', value: '8192 tokens' },
  ],
  vllm: [
    { param: 'Version', value: '0.15.1' },
    { param: 'Model', value: 'openai/gpt-oss-20b' },
    { param: 'Host', value: '0.0.0.0' },
    { param: 'Port', value: '8000' },
    { param: 'GPU Memory', value: '85% (utilization)' },
    { param: 'Prefix Cache', value: 'APC (--enable-prefix-caching)' },
    { param: 'Chunked Prefill', value: '2048 tokens (default)' },
  ],
  ollama: [
    { param: 'Version', value: '0.16.2' },
    { param: 'Model', value: 'gpt-oss:20b' },
    { param: 'Host', value: '0.0.0.0:11434' },
    { param: 'Port', value: '11434' },
    { param: 'GPU Memory', value: 'Dynamic' },
    { param: 'Prefix Cache', value: 'Slot-internal (partial)' },
    { param: 'Chunked Prefill', value: 'OFF' },
  ],
}

export const SERVER_LAUNCH_COMMANDS: Record<string, string> = {
  sglang: `python -m sglang.launch_server \\
  --model-path openai/gpt-oss-20b \\
  --tp 1 --port 30000 \\
  --mem-fraction-static 0.85`,
  vllm: `vllm serve openai/gpt-oss-20b \\
  --host 0.0.0.0 --port 8000 \\
  --gpu-memory-utilization 0.85 \\
  --enable-prefix-caching`,
  ollama: `OLLAMA_HOST=0.0.0.0:11434 ollama serve
ollama pull gpt-oss:20b`,
}

/** Metric label → hover description mapping */
export const METRIC_DESCRIPTIONS: Record<string, string> = {
  // Table column headers
  'TTFT': 'Time To First Token — 요청 전송 후 첫 번째 토큰이 도착하기까지의 지연 시간 (ms). 사용자가 체감하는 응답 시작 속도를 나타냄',
  'TTFT p50': 'TTFT의 중앙값 (50th percentile). 전체 요청 중 절반이 이 시간 이내에 첫 토큰을 받음',
  'First 5 TTFT': '처음 5개 요청의 평균 TTFT. KV Cache가 비어있는 Cold 상태에서의 성능',
  'Cached TTFT': '이후 요청들의 평균 TTFT. Prefix Cache가 적용된 Warm 상태에서의 성능',
  'Speedup': 'Cold TTFT 대비 Cached TTFT의 속도 향상 비율. 높을수록 캐시 효과가 큼',
  'Throughput': '전체 토큰 처리량 (tok/s). 초당 생성하는 총 토큰 수로, 서버의 전반적 처리 능력을 나타냄',
  'Tok/s': '초당 총 토큰 처리량 (Total Token Throughput). 입력+출력 토큰을 합산한 초당 처리량',
  'Req/s': '초당 완료되는 요청 수 (Request Throughput). 동시 요청 처리 시 서버의 효율성을 나타냄',
  'p99 Latency': '99th percentile 전체 응답 지연 시간 (ms). 가장 느린 1%를 제외한 최악의 응답 시간. Tail latency 지표',
  'Success': '전체 요청 중 성공적으로 완료된 요청의 비율 (%)',
  'Duration': '해당 시나리오의 전체 실행 시간 (벽시계 시간)',
  'Input Tokens': '요청에 포함된 입력 프롬프트의 토큰 수',
  'Concurrency': '동시에 전송하는 요청 수. 서버의 동시 처리 능력을 테스트하는 변수',
  // Chart titles
  'Throughput vs Concurrency': '동시 요청 수 증가에 따른 토큰 처리량 변화. 선형 증가가 이상적이며, 꺾이는 지점이 서버 한계를 나타냄',
  'p99 Latency vs Concurrency': '동시 요청 수 증가에 따른 Tail Latency 변화. 급격한 증가는 서버 과부하를 의미함',
  'TTFT by Input Length': '입력 길이별 첫 토큰 도착 시간. 입력이 길어질수록 Prefill 연산이 증가해 TTFT가 늘어남',
  'Peak GPU Memory Usage': '벤치마크 중 측정된 최대 GPU 메모리 사용량 (MB). A100 80GB 기준선 포함',
  'Prefix Cache: Cold vs Cached TTFT': 'KV Cache 미적중(Cold) vs 적중(Cached) 시의 TTFT 비교. 캐시 효과를 직접 확인 가능',
  'Korean vs English Throughput': '한국어와 영어 프롬프트의 토큰 처리량 비교. 토크나이저 효율과 멀티바이트 처리 차이를 보여줌',
}

export function getTechForFramework(
  fw: string,
  scenario?: string,
): { label: string; value: string; status: TechStatus }[] {
  const entries = scenario ? getTechForScenario(scenario) : TECH_STACK
  return entries.map((t) => {
    const fwData = t[fw as keyof Pick<TechEntry, 'sglang' | 'vllm' | 'ollama'>]
    return {
      label: t.label,
      value: fwData?.value ?? 'N/A',
      status: fwData?.status ?? 'off',
    }
  })
}
