import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import type { ScenarioResult } from '../../api/types'
import { FW_COLORS, FW_LABELS } from '../../api/types'
import MetricLabel from '../results/MetricLabel'

interface Props {
  data: Record<string, ScenarioResult[]>
}

export default function ThroughputChart({ data }: Props) {
  // Build chart data: [{concurrency, sglang, vllm, ollama}, ...]
  const concurrencies = new Set<number>()
  for (const results of Object.values(data)) {
    for (const r of results) concurrencies.add(r.concurrency)
  }

  const chartData = [...concurrencies].sort((a, b) => a - b).map((c) => {
    const point: Record<string, number> = { concurrency: c }
    for (const [fw, results] of Object.entries(data)) {
      const match = results.find((r) => r.concurrency === c)
      if (match) point[fw] = match.total_token_throughput
    }
    return point
  })

  const frameworks = Object.keys(data)

  return (
    <div className="card">
      <div className="card-title" style={{ marginBottom: 16 }}><MetricLabel label="Throughput vs Concurrency" /></div>
      <div className="chart-container">
        <ResponsiveContainer>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey="concurrency" stroke="var(--text-secondary)" label={{ value: 'Concurrency', position: 'insideBottom', offset: -5, fill: 'var(--text-secondary)' }} />
            <YAxis stroke="var(--text-secondary)" label={{ value: 'tok/s', angle: -90, position: 'insideLeft', fill: 'var(--text-secondary)' }} />
            <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8 }} />
            <Legend />
            {frameworks.map((fw) => (
              <Line
                key={fw}
                type="monotone"
                dataKey={fw}
                name={FW_LABELS[fw]}
                stroke={FW_COLORS[fw]}
                strokeWidth={2}
                dot={{ r: 5 }}
                activeDot={{ r: 7 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
