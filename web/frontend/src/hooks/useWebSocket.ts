import { useEffect, useRef, useState, useCallback } from 'react'
import { connectBenchmarkWS } from '../api/websocket'

export function useBenchmarkWS(jobId: string | null) {
  const [logs, setLogs] = useState<string[]>([])
  const [done, setDone] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    if (!jobId) return

    setLogs([])
    setDone(false)

    const ws = connectBenchmarkWS(
      jobId,
      (line) => setLogs((prev) => [...prev, line]),
      () => setDone(true),
      () => setDone(true),
    )
    wsRef.current = ws

    return () => {
      ws.close()
      wsRef.current = null
    }
  }, [jobId])

  return { logs, done }
}
