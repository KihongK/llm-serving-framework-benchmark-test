export function connectBenchmarkWS(
  jobId: string,
  onLog: (line: string) => void,
  onDone: () => void,
  onError: (err: Event) => void,
): WebSocket {
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
  const ws = new WebSocket(`${proto}//${location.host}/ws/benchmark/${jobId}`)

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data)
    if (msg.type === 'log') {
      onLog(msg.data)
    } else if (msg.type === 'done') {
      onDone()
    } else if (msg.type === 'error') {
      onLog(`[Error] ${msg.data}\n`)
      onDone()
    }
  }

  ws.onerror = onError
  ws.onclose = () => onDone()
  return ws
}

export function connectGPUMonitorWS(
  onData: (stats: { memory_used_mb: number; memory_total_mb: number; gpu_utilization_pct: number }) => void,
): WebSocket {
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
  const ws = new WebSocket(`${proto}//${location.host}/ws/gpu`)

  ws.onmessage = (event) => {
    const stats = JSON.parse(event.data)
    onData(stats)
  }

  return ws
}

export function connectServerLogsWS(
  onLog: (line: string) => void,
  onDone: () => void,
  onError: (err: Event) => void,
): WebSocket {
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
  const ws = new WebSocket(`${proto}//${location.host}/ws/server/logs`)

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data)
    if (msg.type === 'log') {
      onLog(msg.data)
    } else if (msg.type === 'done') {
      onDone()
    } else if (msg.type === 'error') {
      onLog(`[Error] ${msg.data}\n`)
      onDone()
    }
  }

  ws.onerror = onError
  ws.onclose = () => onDone()
  return ws
}
