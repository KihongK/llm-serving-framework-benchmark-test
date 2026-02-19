export interface GPUStats {
  memory_used_mb: number
  memory_total_mb: number
  gpu_utilization_pct: number
}

export interface ServerHealth {
  framework: string
  label: string
  healthy: boolean
  base_url: string
}

export interface ScenarioResult {
  scenario: string
  framework: string
  concurrency: number
  input_tokens: number
  output_tokens: number
  num_requests: number
  avg_ttft_ms: number
  p50_ttft_ms: number
  p95_ttft_ms: number
  p99_ttft_ms: number
  avg_latency_ms: number
  p50_latency_ms: number
  p95_latency_ms: number
  p99_latency_ms: number
  total_token_throughput: number
  request_throughput: number
  success_rate: number
  total_time_sec: number
  peak_memory_mb: number
  avg_memory_mb: number
  avg_gpu_util_pct: number
  first_5_avg_ttft_ms: number
  later_avg_ttft_ms: number
  cache_speedup_ratio: number
  gpu_memory_mb?: number
}

export interface FrameworkResults {
  framework: string
  model_preset: string
  model: string
  timestamp: string
  gpu_info: { memory_total_mb: number }
  trials: number
  results: ScenarioResult[]
  trial_summary?: TrialSummary[]
}

export interface TrialSummary {
  scenario: string
  framework: string
  num_trials: number
  mean_ttft_ms: number
  std_ttft_ms: number
  mean_throughput: number
  std_throughput: number
  mean_p99_latency_ms: number
  std_p99_latency_ms: number
  mean_success_rate: number
  mean_peak_memory_mb: number
}

export interface HypothesisResult {
  id: string
  title: string
  description: string
  verdict: 'SUPPORTED' | 'NOT SUPPORTED' | 'INCONCLUSIVE' | 'NO DATA'
  evidence: string[]
}

export interface BenchmarkJob {
  job_id: string
  status: string
  framework: string
  scenarios: string[]
  model: string
  trials: number
  log_lines: number
}

export interface ComparisonData {
  frameworks: string[]
  scenarios: Record<string, Record<string, ScenarioResult[]>>
}

export interface ManagedServerStatus {
  framework: string | null
  model: string | null
  status: 'starting' | 'running' | 'stopping' | 'stopped' | 'failed'
  managed: boolean
  pid: number | null
  uptime_sec: number | null
  log_lines: number
}

export interface ServerStartRequest {
  framework: string
  model: string
}

export const FW_COLORS: Record<string, string> = {
  sglang: '#2196F3',
  vllm: '#FF9800',
  ollama: '#4CAF50',
}

export const FW_LABELS: Record<string, string> = {
  sglang: 'SGLang',
  vllm: 'vLLM',
  ollama: 'Ollama',
}
