import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Cell } from 'recharts'
import type { FrameworkResults } from '../../api/types'
import { FW_COLORS, FW_LABELS } from '../../api/types'

interface Props {
  data: Record<string, FrameworkResults>
}

export default function GPUMemoryChart({ data }: Props) {
  const chartData = Object.entries(data).map(([fw, fwData]) => {
    const peaks = fwData.results.map((r) => r.peak_memory_mb || r.gpu_memory_mb || 0)
    return {
      framework: FW_LABELS[fw],
      fw,
      peak_memory: Math.max(...peaks, 0),
    }
  })

  return (
    <div className="card">
      <div className="card-title" style={{ marginBottom: 16 }}>Peak GPU Memory Usage</div>
      <div className="chart-container">
        <ResponsiveContainer>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey="framework" stroke="var(--text-secondary)" />
            <YAxis stroke="var(--text-secondary)" label={{ value: 'MB', angle: -90, position: 'insideLeft', fill: 'var(--text-secondary)' }} />
            <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8 }} />
            <ReferenceLine y={81920} stroke="#ef4444" strokeDasharray="5 5" label={{ value: 'A100 80GB', position: 'top', fill: '#ef4444', fontSize: 12 }} />
            <Bar dataKey="peak_memory" name="Peak Memory (MB)" radius={[4, 4, 0, 0]}>
              {chartData.map((d) => (
                <Cell key={d.fw} fill={FW_COLORS[d.fw]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
