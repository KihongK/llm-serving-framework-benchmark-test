import { useState, useEffect, useRef } from 'react'
import type { GPUStats } from '../api/types'
import { connectGPUMonitorWS } from '../api/websocket'

export function useGPUMonitor() {
  const [stats, setStats] = useState<GPUStats>({
    memory_used_mb: 0,
    memory_total_mb: 0,
    gpu_utilization_pct: 0,
  })
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    const ws = connectGPUMonitorWS((data) => setStats(data))
    wsRef.current = ws

    return () => {
      ws.close()
      wsRef.current = null
    }
  }, [])

  return stats
}
