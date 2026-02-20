import { useState } from 'react'
import type { ScenarioResult } from '../../api/types'
import { FW_LABELS } from '../../api/types'
import TechTooltip from './TechTooltip'
import ScenarioTechBar from './ScenarioTechBar'
import MetricLabel from './MetricLabel'

interface Props {
  results: Record<string, ScenarioResult[]>
  scenario: string
}

function fmt(val: number | undefined, unit = ''): string {
  if (val === undefined || val === null) return 'N/A'
  if (val === 0) return `0${unit}`
  return `${val.toLocaleString(undefined, { maximumFractionDigits: 2 })}${unit}`
}

function formatDuration(sec: number | undefined): string {
  if (sec === undefined || sec === null) return 'N/A'
  if (sec < 60) return `${sec.toFixed(1)}s`
  const m = Math.floor(sec / 60)
  const s = Math.round(sec % 60)
  return `${m}m ${s}s`
}

type SortKey = string
type SortDir = 'asc' | 'desc'

export default function ComparisonTable({ results, scenario }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>('framework')
  const [sortDir, setSortDir] = useState<SortDir>('asc')

  // Flatten results into rows
  const rows: (ScenarioResult & { fw: string })[] = []
  for (const [fw, list] of Object.entries(results)) {
    for (const r of list) {
      rows.push({ ...r, fw })
    }
  }

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDir('asc')
    }
  }

  rows.sort((a, b) => {
    const av = (a as unknown as Record<string, unknown>)[sortKey]
    const bv = (b as unknown as Record<string, unknown>)[sortKey]
    const cmp = typeof av === 'number' && typeof bv === 'number' ? av - bv : String(av).localeCompare(String(bv))
    return sortDir === 'asc' ? cmp : -cmp
  })

  const arrow = (key: string) => (sortKey === key ? (sortDir === 'asc' ? ' ^' : ' v') : '')

  const frameworks = Object.keys(results)

  const fwBadge = (fw: string) => (
    <TechTooltip fw={fw} scenario={scenario}>
      <span className={`fw-badge ${fw}`}>{FW_LABELS[fw]}</span>
    </TechTooltip>
  )

  if (scenario === 'prefix_cache') {
    return (
      <>
        <ScenarioTechBar scenario={scenario} frameworks={frameworks} />
        <table className="data-table">
          <thead>
            <tr>
              <th onClick={() => handleSort('fw')}>Framework{arrow('fw')}</th>
              <th onClick={() => handleSort('first_5_avg_ttft_ms')}><MetricLabel label="First 5 TTFT" suffix={arrow('first_5_avg_ttft_ms')} /></th>
              <th onClick={() => handleSort('later_avg_ttft_ms')}><MetricLabel label="Cached TTFT" suffix={arrow('later_avg_ttft_ms')} /></th>
              <th onClick={() => handleSort('cache_speedup_ratio')}><MetricLabel label="Speedup" suffix={arrow('cache_speedup_ratio')} /></th>
              <th onClick={() => handleSort('total_token_throughput')}><MetricLabel label="Throughput" suffix={arrow('total_token_throughput')} /></th>
              <th onClick={() => handleSort('success_rate')}><MetricLabel label="Success" suffix={arrow('success_rate')} /></th>
              <th onClick={() => handleSort('total_time_sec')}><MetricLabel label="Duration" suffix={arrow('total_time_sec')} /></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i}>
                <td>{fwBadge(r.fw)}</td>
                <td>{fmt(r.first_5_avg_ttft_ms, 'ms')}</td>
                <td>{fmt(r.later_avg_ttft_ms, 'ms')}</td>
                <td>{fmt(r.cache_speedup_ratio, 'x')}</td>
                <td>{fmt(r.total_token_throughput, ' tok/s')}</td>
                <td>{fmt(r.success_rate, '%')}</td>
                <td>{formatDuration(r.total_time_sec)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </>
    )
  }

  if (scenario === 'concurrent_load') {
    return (
      <>
        <ScenarioTechBar scenario={scenario} frameworks={frameworks} />
        <table className="data-table">
          <thead>
            <tr>
              <th onClick={() => handleSort('fw')}>Framework{arrow('fw')}</th>
              <th onClick={() => handleSort('concurrency')}><MetricLabel label="Concurrency" suffix={arrow('concurrency')} /></th>
              <th onClick={() => handleSort('request_throughput')}><MetricLabel label="Req/s" suffix={arrow('request_throughput')} /></th>
              <th onClick={() => handleSort('total_token_throughput')}><MetricLabel label="Tok/s" suffix={arrow('total_token_throughput')} /></th>
              <th onClick={() => handleSort('p50_ttft_ms')}><MetricLabel label="TTFT p50" suffix={arrow('p50_ttft_ms')} /></th>
              <th onClick={() => handleSort('p99_latency_ms')}><MetricLabel label="p99 Latency" suffix={arrow('p99_latency_ms')} /></th>
              <th onClick={() => handleSort('success_rate')}><MetricLabel label="Success" suffix={arrow('success_rate')} /></th>
              <th onClick={() => handleSort('total_time_sec')}><MetricLabel label="Duration" suffix={arrow('total_time_sec')} /></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i}>
                <td>{fwBadge(r.fw)}</td>
                <td>{r.concurrency}</td>
                <td>{fmt(r.request_throughput)}</td>
                <td>{fmt(r.total_token_throughput)}</td>
                <td>{fmt(r.p50_ttft_ms, 'ms')}</td>
                <td>{fmt(r.p99_latency_ms, 'ms')}</td>
                <td>{fmt(r.success_rate, '%')}</td>
                <td>{formatDuration(r.total_time_sec)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </>
    )
  }

  // Default table for single_request, long_context, korean
  return (
    <>
      <ScenarioTechBar scenario={scenario} frameworks={frameworks} />
      <table className="data-table">
        <thead>
          <tr>
            <th onClick={() => handleSort('fw')}>Framework{arrow('fw')}</th>
            <th onClick={() => handleSort('input_tokens')}><MetricLabel label="Input Tokens" suffix={arrow('input_tokens')} /></th>
            <th onClick={() => handleSort('concurrency')}><MetricLabel label="Concurrency" suffix={arrow('concurrency')} /></th>
            <th onClick={() => handleSort('avg_ttft_ms')}><MetricLabel label="TTFT" suffix={arrow('avg_ttft_ms')} /></th>
            <th onClick={() => handleSort('total_token_throughput')}><MetricLabel label="Throughput" suffix={arrow('total_token_throughput')} /></th>
            <th onClick={() => handleSort('p99_latency_ms')}><MetricLabel label="p99 Latency" suffix={arrow('p99_latency_ms')} /></th>
            <th onClick={() => handleSort('success_rate')}><MetricLabel label="Success" suffix={arrow('success_rate')} /></th>
            <th onClick={() => handleSort('total_time_sec')}><MetricLabel label="Duration" suffix={arrow('total_time_sec')} /></th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>
              <td>{fwBadge(r.fw)}</td>
              <td>{r.input_tokens}</td>
              <td>{r.concurrency}</td>
              <td>{fmt(r.avg_ttft_ms, 'ms')}</td>
              <td>{fmt(r.total_token_throughput, ' tok/s')}</td>
              <td>{fmt(r.p99_latency_ms, 'ms')}</td>
              <td>{fmt(r.success_rate, '%')}</td>
              <td>{formatDuration(r.total_time_sec)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  )
}
