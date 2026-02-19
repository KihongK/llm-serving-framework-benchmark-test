import { useState } from 'react'
import type { ServerHealth, ManagedServerStatus } from '../../api/types'
import { FW_LABELS } from '../../api/types'

const MODELS = ['gpt-oss-20b', 'llama3.1-8b']

interface Props {
  server: ServerHealth
  managed: ManagedServerStatus
  loading: boolean
  onStart: (framework: string, model: string) => void
  onStop: () => void
  onViewLogs: () => void
}

function formatUptime(sec: number): string {
  if (sec < 60) return `${Math.floor(sec)}s`
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  if (m < 60) return `${m}m ${s}s`
  const h = Math.floor(m / 60)
  return `${h}h ${m % 60}m`
}

export default function ServerStatusCard({
  server,
  managed,
  loading,
  onStart,
  onStop,
  onViewLogs,
}: Props) {
  const [selectedModel, setSelectedModel] = useState(MODELS[0])

  const isThisFramework = managed.framework === server.framework
  const isOtherRunning = managed.framework !== null && !isThisFramework &&
    ['starting', 'running'].includes(managed.status)
  const isRunning = isThisFramework && managed.status === 'running'
  const isStarting = isThisFramework && managed.status === 'starting'
  const isStopping = isThisFramework && managed.status === 'stopping'
  const isFailed = isThisFramework && managed.status === 'failed'

  const dotClass = isRunning
    ? 'healthy'
    : isStarting
      ? 'starting'
      : 'unhealthy'

  const statusText = isRunning
    ? `Running${managed.uptime_sec ? ` (${formatUptime(managed.uptime_sec)})` : ''}${!managed.managed ? ' (external)' : ''}`
    : isStarting
      ? 'Starting...'
      : isStopping
        ? 'Stopping...'
        : isFailed
          ? 'Failed'
          : 'Offline'

  return (
    <div className="card">
      <div className="card-header">
        <span className={`fw-badge ${server.framework}`}>{server.label}</span>
        <span className={`status-dot ${dotClass}`} />
      </div>

      <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
        {server.base_url}
      </div>

      {/* Blocked by another framework */}
      {isOtherRunning && (
        <div className="server-blocked">
          {FW_LABELS[managed.framework!]}이(가) 실행 중입니다.<br />
          먼저 종료해주세요.
        </div>
      )}

      {/* Idle — show model selector + start */}
      {!isOtherRunning && !isRunning && !isStarting && !isStopping && (
        <>
          <div style={{ marginTop: 8 }}>
            <select
              className="form-select"
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              style={{ padding: '4px 8px', fontSize: 12 }}
            >
              {MODELS.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>
          <div style={{ marginTop: 4, fontSize: 14, fontWeight: 600 }}>
            {isFailed ? 'Failed' : 'Offline'}
          </div>
          <div className="server-actions">
            <button
              className="btn btn-success btn-sm"
              disabled={loading}
              onClick={() => onStart(server.framework, selectedModel)}
            >
              &#9654; Start Server
            </button>
            {isFailed && (
              <button
                className="btn btn-secondary btn-sm"
                onClick={onViewLogs}
              >
                View Logs
              </button>
            )}
          </div>
        </>
      )}

      {/* Starting */}
      {isStarting && (
        <>
          <div className="server-info">{managed.model}</div>
          <div style={{ marginTop: 4, fontSize: 14, fontWeight: 600 }}>Starting...</div>
          <div className="server-actions">
            <button
              className="btn btn-danger btn-sm"
              disabled={loading}
              onClick={onStop}
            >
              &#9632; Cancel
            </button>
            <button className="btn btn-secondary btn-sm" onClick={onViewLogs}>
              View Logs
            </button>
          </div>
        </>
      )}

      {/* Running */}
      {isRunning && (
        <>
          <div className="server-info">{managed.model}</div>
          <div style={{ marginTop: 4, fontSize: 14, fontWeight: 600 }}>
            {statusText}
          </div>
          <div className="server-actions">
            <button
              className="btn btn-danger btn-sm"
              disabled={loading}
              onClick={onStop}
            >
              &#9632; Stop
            </button>
            <button className="btn btn-secondary btn-sm" onClick={onViewLogs}>
              View Logs
            </button>
          </div>
        </>
      )}

      {/* Stopping */}
      {isStopping && (
        <>
          <div style={{ marginTop: 8, fontSize: 14, fontWeight: 600 }}>Stopping...</div>
        </>
      )}
    </div>
  )
}
