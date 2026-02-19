import { useEffect, useRef } from 'react'

export default function LogViewer({ logs }: { logs: string[] }) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (ref.current) {
      ref.current.scrollTop = ref.current.scrollHeight
    }
  }, [logs])

  return (
    <div className="log-viewer" ref={ref}>
      {logs.length === 0 ? (
        <span style={{ color: 'var(--text-muted)' }}>Waiting for output...</span>
      ) : (
        logs.map((line, i) => <span key={i}>{line}</span>)
      )}
    </div>
  )
}
