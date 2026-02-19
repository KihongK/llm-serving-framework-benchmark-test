import { useState, useEffect } from 'react'
import { api } from '../api/client'
import type { HypothesisResult } from '../api/types'
import HypothesisCard from '../components/hypothesis/HypothesisCard'
import { FlaskConical } from 'lucide-react'

export default function HypothesisPage() {
  const [hypotheses, setHypotheses] = useState<HypothesisResult[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .getHypotheses()
      .then(setHypotheses)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div className="loading-container"><div className="spinner" /> Loading hypotheses...</div>
  }

  const supported = hypotheses.filter((h) => h.verdict === 'SUPPORTED').length
  const total = hypotheses.length

  return (
    <div>
      <div className="page-header">
        <h2>Hypothesis Verification</h2>
        <p>
          H1-H5 hypothesis validation results
          {total > 0 && ` — ${supported}/${total} supported`}
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {hypotheses.map((h) => (
          <HypothesisCard key={h.id} h={h} />
        ))}
      </div>

      {hypotheses.length === 0 && (
        <div className="card">
          <div className="empty-state">
            <FlaskConical size={40} />
            <h3>No Data</h3>
            <p>Run benchmarks first to verify hypotheses.</p>
          </div>
        </div>
      )}
    </div>
  )
}
