import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import type { ScenarioResult } from '../../api/types'
import { FW_COLORS, FW_LABELS } from '../../api/types'

interface Props {
  data: Record<string, ScenarioResult[]>
}

export default function TTFTChart({ data }: Props) {
  // Grouped bar chart: input_tokens on X, one bar per framework
  const inputLengths = new Set<number>()
  for (const results of Object.values(data)) {
    for (const r of results) inputLengths.add(r.input_tokens)
  }

  const chartData = [...inputLengths].sort((a, b) => a - b).map((il) => {
    const point: Record<string, number | string> = { input_tokens: `${il}` }
    for (const [fw, results] of Object.entries(data)) {
      const match = results.find((r) => r.input_tokens === il)
      if (match) point[fw] = match.avg_ttft_ms
    }
    return point
  })

  const frameworks = Object.keys(data)

  return (
    <div className="card">
      <div className="card-title" style={{ marginBottom: 16 }}>TTFT by Input Length</div>
      <div className="chart-container">
        <ResponsiveContainer>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey="input_tokens" stroke="var(--text-secondary)" label={{ value: 'Input Tokens', position: 'insideBottom', offset: -5, fill: 'var(--text-secondary)' }} />
            <YAxis stroke="var(--text-secondary)" label={{ value: 'ms', angle: -90, position: 'insideLeft', fill: 'var(--text-secondary)' }} />
            <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8 }} />
            <Legend />
            {frameworks.map((fw) => (
              <Bar key={fw} dataKey={fw} name={FW_LABELS[fw]} fill={FW_COLORS[fw]} radius={[4, 4, 0, 0]} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
