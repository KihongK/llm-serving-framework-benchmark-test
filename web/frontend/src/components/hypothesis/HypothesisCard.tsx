import type { HypothesisResult } from '../../api/types'
import VerdictBadge from './VerdictBadge'

export default function HypothesisCard({ h }: { h: HypothesisResult }) {
  const cls = h.verdict === 'SUPPORTED' ? 'supported' : h.verdict === 'NOT SUPPORTED' ? 'not-supported' : 'inconclusive'
  return (
    <div className={`card hypothesis-card ${cls}`}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
        <div>
          <div className="hypothesis-id">{h.id}</div>
          <div className="hypothesis-title">{h.title}</div>
          <div className="hypothesis-desc">{h.description}</div>
        </div>
        <VerdictBadge verdict={h.verdict} />
      </div>
      {h.evidence.length > 0 && (
        <ul className="evidence-list">
          {h.evidence.map((e, i) => (
            <li key={i}>{e}</li>
          ))}
        </ul>
      )}
    </div>
  )
}
