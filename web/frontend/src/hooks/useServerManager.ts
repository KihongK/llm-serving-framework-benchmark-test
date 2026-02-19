import { useState, useEffect, useRef, useCallback } from 'react'
import type { ManagedServerStatus } from '../api/types'
import { api } from '../api/client'
import { connectServerLogsWS } from '../api/websocket'

const POLL_INTERVAL = 3000

export function useServerManager() {
  const [status, setStatus] = useState<ManagedServerStatus>({
    framework: null,
    model: null,
    status: 'stopped',
    managed: true,
    pid: null,
    uptime_sec: null,
    log_lines: 0,
  })
  const [logs, setLogs] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Poll managed status
  const fetchStatus = useCallback(async () => {
    try {
      const s = await api.getManagedStatus()
      setStatus(s)
    } catch {
      // ignore poll errors
    }
  }, [])

  useEffect(() => {
    fetchStatus()
    pollRef.current = setInterval(fetchStatus, POLL_INTERVAL)
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [fetchStatus])

  // Connect WebSocket for logs when server is active
  const connectLogs = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setLogs([])
    const ws = connectServerLogsWS(
      (line) => setLogs((prev) => [...prev, line]),
      () => {},
      () => {},
    )
    wsRef.current = ws
  }, [])

  const disconnectLogs = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }, [])

  const startServer = useCallback(async (framework: string, model: string) => {
    setLoading(true)
    setError(null)
    setLogs([])
    try {
      const s = await api.startServer({ framework, model })
      setStatus(s)
      // Connect to log stream
      connectLogs()
    } catch (e: any) {
      setError(e.message || 'Failed to start server')
    } finally {
      setLoading(false)
    }
  }, [connectLogs])

  const stopServer = useCallback(async (force = false) => {
    setLoading(true)
    setError(null)
    try {
      const s = await api.stopServer(force)
      setStatus(s)
      disconnectLogs()
    } catch (e: any) {
      if (e.message?.includes('409')) {
        setError('벤치마크가 실행 중입니다. 먼저 벤치마크를 취소하세요.')
      } else {
        setError(e.message || 'Failed to stop server')
      }
    } finally {
      setLoading(false)
    }
  }, [disconnectLogs])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnectLogs()
    }
  }, [disconnectLogs])

  return {
    status,
    logs,
    loading,
    error,
    startServer,
    stopServer,
    connectLogs,
    disconnectLogs,
    clearError: () => setError(null),
  }
}
