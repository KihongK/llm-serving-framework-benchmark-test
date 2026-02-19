const BASE = '/api/v1'

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

import type {
  GPUStats,
  ServerHealth,
  FrameworkResults,
  HypothesisResult,
  BenchmarkJob,
  ComparisonData,
  ManagedServerStatus,
  ServerStartRequest,
} from './types'

export const api = {
  // Results
  getResultFiles: () => get<Record<string, string[]>>('/results/'),
  getAllResults: () => get<Record<string, FrameworkResults>>('/results/all'),
  getFrameworkResults: (fw: string) => get<FrameworkResults>(`/results/${fw}`),

  // Server
  getHealth: () => get<ServerHealth[]>('/server/health'),
  getGPU: () => get<GPUStats>('/server/gpu'),
  getManagedStatus: () => get<ManagedServerStatus>('/server/managed'),
  startServer: (params: ServerStartRequest) => post<ManagedServerStatus>('/server/start', params),
  stopServer: (force = false) => post<ManagedServerStatus>('/server/stop', { force }),

  // Benchmark
  runBenchmark: (params: {
    framework: string
    scenarios: string[]
    model: string
    trials: number
  }) => post<{ job_id: string; status: string }>('/benchmark/run', params),

  getBenchmarkStatus: (jobId: string) => get<BenchmarkJob>(`/benchmark/status/${jobId}`),
  cancelBenchmark: (jobId: string) => post<{ job_id: string; status: string }>(`/benchmark/cancel/${jobId}`),

  // Analysis
  getHypotheses: () => get<HypothesisResult[]>('/analysis/hypotheses'),
  getReport: () => get<ComparisonData>('/analysis/report'),
}
