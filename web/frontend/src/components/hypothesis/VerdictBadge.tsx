import { CheckCircle, XCircle, AlertTriangle, HelpCircle } from 'lucide-react'

const config: Record<string, { cls: string; Icon: typeof CheckCircle }> = {
  SUPPORTED: { cls: 'supported', Icon: CheckCircle },
  'NOT SUPPORTED': { cls: 'not-supported', Icon: XCircle },
  INCONCLUSIVE: { cls: 'inconclusive', Icon: AlertTriangle },
  'NO DATA': { cls: 'no-data', Icon: HelpCircle },
}

export default function VerdictBadge({ verdict }: { verdict: string }) {
  const c = config[verdict] || config['NO DATA']
  return (
    <span className={`verdict-badge ${c.cls}`}>
      <c.Icon size={14} />
      {verdict}
    </span>
  )
}
