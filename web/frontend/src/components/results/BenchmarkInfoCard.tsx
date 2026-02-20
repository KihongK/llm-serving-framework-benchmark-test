import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import type { FrameworkResults } from '../../api/types'
import { FW_LABELS } from '../../api/types'
import { SERVER_LAUNCH_PARAMS, SERVER_LAUNCH_COMMANDS } from '../../api/techData'

interface Props {
  data: Record<string, FrameworkResults>
}

function formatDuration(sec: number): string {
  if (sec < 60) return `${sec.toFixed(1)}s`
  const m = Math.floor(sec / 60)
  const s = Math.round(sec % 60)
  return `${m}m ${s}s`
}

function totalDuration(fw: FrameworkResults): number {
  return fw.results.reduce((sum, r) => sum + (r.total_time_sec || 0), 0)
}

export default function BenchmarkInfoCard({ data }: Props) {
  const [open, setOpen] = useState(false)
  const frameworks = Object.keys(data)

  return (
    <div className="card benchmark-info-card">
      <button className="benchmark-info-toggle" onClick={() => setOpen((v) => !v)}>
        {open ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        Benchmark Configuration
      </button>
      {open && (
        <div className="benchmark-info-body">
          {/* Benchmark Run Info */}
          <div className="benchmark-info-section-title">Benchmark Run</div>
          <div className="info-grid">
            {frameworks.map((fw) => {
              const d = data[fw]
              return (
                <div key={fw} className="info-grid-item">
                  <span className="info-grid-label">{FW_LABELS[fw] || fw}</span>
                  <span className="info-grid-value">{d.model}</span>
                  <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                    {d.trials} trial{d.trials !== 1 ? 's' : ''} &middot; {formatDuration(totalDuration(d))}
                  </span>
                  <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                    {d.timestamp}
                  </span>
                </div>
              )
            })}
          </div>

          {/* Server Launch Parameters */}
          <div className="benchmark-info-section-title">Server Launch Parameters</div>
          <table className="tech-stack-table">
            <thead>
              <tr>
                <th>Parameter</th>
                {frameworks.map((fw) => (
                  <th key={fw}>{FW_LABELS[fw] || fw}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {(SERVER_LAUNCH_PARAMS[frameworks[0]] || []).map((_, i) => {
                const paramName = SERVER_LAUNCH_PARAMS[frameworks[0]]?.[i]?.param
                if (!paramName) return null
                return (
                  <tr key={paramName}>
                    <td className="tech-label">{paramName}</td>
                    {frameworks.map((fw) => {
                      const entry = SERVER_LAUNCH_PARAMS[fw]?.find((p) => p.param === paramName)
                      return <td key={fw}>{entry?.value ?? 'N/A'}</td>
                    })}
                  </tr>
                )
              })}
            </tbody>
          </table>

          {/* Launch Commands */}
          <div className="benchmark-info-section-title" style={{ marginTop: 20 }}>
            Launch Commands
          </div>
          {frameworks.map((fw) => (
            <div key={fw} style={{ marginBottom: 12 }}>
              <div className="cmd-block-label">{FW_LABELS[fw] || fw}</div>
              <div className="cmd-block">{SERVER_LAUNCH_COMMANDS[fw] || 'N/A'}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
