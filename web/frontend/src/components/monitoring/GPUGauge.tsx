import type { GPUStats } from '../../api/types'

function getColor(pct: number): string {
  if (pct < 50) return 'var(--success)'
  if (pct < 80) return 'var(--warning)'
  return 'var(--danger)'
}

export default function GPUGauge({ stats, label }: { stats: GPUStats; label: string }) {
  const memPct = stats.memory_total_mb > 0 ? (stats.memory_used_mb / stats.memory_total_mb) * 100 : 0

  const value = label === 'Memory' ? memPct : stats.gpu_utilization_pct
  const display =
    label === 'Memory'
      ? `${(stats.memory_used_mb / 1024).toFixed(1)} / ${(stats.memory_total_mb / 1024).toFixed(1)} GB`
      : `${stats.gpu_utilization_pct.toFixed(0)}%`

  return (
    <div className="card">
      <div className="card-title" style={{ marginBottom: 12 }}>
        GPU {label}
      </div>
      <div className="gauge-container">
        <div className="gauge-label" style={{ color: getColor(value) }}>
          {value.toFixed(1)}%
        </div>
        <div className="gauge-bar">
          <div
            className="gauge-fill"
            style={{
              width: `${Math.min(value, 100)}%`,
              background: getColor(value),
            }}
          />
        </div>
        <div className="gauge-sublabel">{display}</div>
      </div>
    </div>
  )
}
