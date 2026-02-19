import { useEffect, useRef } from 'react'

interface Props {
  logs: string[]
  framework: string
  onClose: () => void
}

export default function ServerLogModal({ logs, framework, onClose }: Props) {
  const logRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight
    }
  }, [logs])

  // Close on ESC
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Server Logs — {framework}</h3>
          <button className="modal-close" onClick={onClose}>&times;</button>
        </div>
        <div className="modal-body">
          <div className="log-viewer" ref={logRef}>
            {logs.length > 0 ? logs.join('') : 'No logs yet...'}
          </div>
        </div>
      </div>
    </div>
  )
}
