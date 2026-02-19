import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import type { ScenarioResult } from '../../api/types'
import { FW_LABELS } from '../../api/types'

interface Props {
  data: Record<string, ScenarioResult[]>
}

export default function KoreanVsEnglishChart({ data }: Props) {
  const chartData = Object.entries(data).map(([fw, results]) => {
    const koVals = results
      .filter((r) => r.scenario.startsWith('korean_korean_') && r.concurrency === 1)
      .map((r) => r.total_token_throughput)
    const enVals = results
      .filter((r) => r.scenario.startsWith('korean_english_') && r.concurrency === 1)
      .map((r) => r.total_token_throughput)

    return {
      framework: FW_LABELS[fw],
      korean: koVals.length > 0 ? koVals.reduce((a, b) => a + b, 0) / koVals.length : 0,
      english: enVals.length > 0 ? enVals.reduce((a, b) => a + b, 0) / enVals.length : 0,
    }
  })

  return (
    <div className="card">
      <div className="card-title" style={{ marginBottom: 16 }}>Korean vs English Throughput</div>
      <div className="chart-container">
        <ResponsiveContainer>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey="framework" stroke="var(--text-secondary)" />
            <YAxis stroke="var(--text-secondary)" label={{ value: 'tok/s', angle: -90, position: 'insideLeft', fill: 'var(--text-secondary)' }} />
            <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8 }} />
            <Legend />
            <Bar dataKey="korean" name="Korean" fill="#E91E63" radius={[4, 4, 0, 0]} />
            <Bar dataKey="english" name="English" fill="#3F51B5" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
