import { METRIC_DESCRIPTIONS } from '../../api/techData'

interface Props {
  label: string
  suffix?: string
  className?: string
}

export default function MetricLabel({ label, suffix = '', className }: Props) {
  const desc = METRIC_DESCRIPTIONS[label]
  if (!desc) return <>{label}{suffix}</>

  return (
    <span className={`metric-label-wrapper ${className || ''}`}>
      <span className="metric-label-text">{label}{suffix}</span>
      <span className="metric-tooltip">{desc}</span>
    </span>
  )
}
