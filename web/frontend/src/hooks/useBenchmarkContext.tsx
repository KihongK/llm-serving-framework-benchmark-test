import { createContext, useContext, useState, useEffect, useRef, useCallback, type ReactNode } from 'react'
import { api } from '../api/client'
import { connectBenchmarkWS } from '../api/websocket'

interface BenchmarkState {
  jobId: string | null
  running: boolean
  logs: string[]
  done: boolean
  run: (params: { framework: string; scenarios: string[]; model: string; trials: number }) => Promise<void>
  cancel: () => Promise<void>
}

const BenchmarkContext = createContext<BenchmarkState | null>(null)

export function BenchmarkProvider({ children }: { children: ReactNode }) {
  const [jobId, setJobId] = useState<string | null>(null)
  const [running, setRunning] = useState(false)
  const [logs, setLogs] = useState<string[]>([])
  const [done, setDone] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  // Connect WebSocket when jobId changes
  useEffect(() => {
    if (!jobId) return

    // Close previous WS
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    setLogs([])
    setDone(false)

    const ws = connectBenchmarkWS(
      jobId,
      (line) => setLogs((prev) => [...prev, line]),
      () => {
        setDone(true)
        setRunning(false)
      },
      () => {
        setDone(true)
        setRunning(false)
      },
    )
    wsRef.current = ws

    return () => {
      ws.close()
      wsRef.current = null
    }
  }, [jobId])

  const run = useCallback(async (params: { framework: string; scenarios: string[]; model: string; trials: number }) => {
    const { job_id } = await api.runBenchmark(params)
    setJobId(job_id)
    setRunning(true)
    setDone(false)
  }, [])

  const cancel = useCallback(async () => {
    if (jobId) {
      try {
        await api.cancelBenchmark(jobId)
        setRunning(false)
      } catch {
        // Already stopped
      }
    }
  }, [jobId])

  return (
    <BenchmarkContext.Provider value={{ jobId, running, logs, done, run, cancel }}>
      {children}
    </BenchmarkContext.Provider>
  )
}

export function useBenchmark() {
  const ctx = useContext(BenchmarkContext)
  if (!ctx) throw new Error('useBenchmark must be used within BenchmarkProvider')
  return ctx
}
