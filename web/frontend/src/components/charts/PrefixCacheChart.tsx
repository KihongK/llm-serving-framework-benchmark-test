import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import type { ScenarioResult } from '../../api/types'
import { FW_LABELS } from '../../api/types'
import MetricLabel from '../results/MetricLabel'

interface Props {
  data: Record<string, ScenarioResult[]>
}

export default function PrefixCacheChart({ data }: Props) {
  const chartData = Object.entries(data).map(([fw, results]) => {
    const r = results[0]
    return {
      framework: FW_LABELS[fw],
      cold: r.first_5_avg_ttft_ms || r.avg_ttft_ms,
      cached: r.later_avg_ttft_ms || r.avg_ttft_ms,
    }
  })

  return (
    <div className="card">
      <div className="card-title" style={{ marginBottom: 16 }}><MetricLabel label="Prefix Cache: Cold vs Cached TTFT" /></div>
      <div className="chart-container">
        <ResponsiveContainer>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey="framework" stroke="var(--text-secondary)" />
            <YAxis stroke="var(--text-secondary)" label={{ value: 'ms', angle: -90, position: 'insideLeft', fill: 'var(--text-secondary)' }} />
            <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8 }} />
            <Legend />
            <Bar dataKey="cold" name="First 5 (Cold)" fill="#EF5350" radius={[4, 4, 0, 0]} />
            <Bar dataKey="cached" name="Remaining (Cached)" fill="#66BB6A" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
