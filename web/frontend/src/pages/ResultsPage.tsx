import { useState, useEffect } from 'react'
import { api } from '../api/client'
import type { FrameworkResults, ScenarioResult, ComparisonData } from '../api/types'
import { BarChart3 } from 'lucide-react'
import ScenarioSelector from '../components/results/ScenarioSelector'
import ComparisonTable from '../components/results/ComparisonTable'
import ThroughputChart from '../components/charts/ThroughputChart'
import LatencyChart from '../components/charts/LatencyChart'
import TTFTChart from '../components/charts/TTFTChart'
import GPUMemoryChart from '../components/charts/GPUMemoryChart'
import PrefixCacheChart from '../components/charts/PrefixCacheChart'
import KoreanVsEnglishChart from '../components/charts/KoreanVsEnglishChart'

export default function ResultsPage() {
  const [data, setData] = useState<Record<string, FrameworkResults> | null>(null)
  const [comparison, setComparison] = useState<ComparisonData | null>(null)
  const [scenario, setScenario] = useState('single_request')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([api.getAllResults(), api.getReport()])
      .then(([results, report]) => {
        setData(results)
        setComparison(report)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div className="loading-container"><div className="spinner" /> Loading results...</div>
  }

  if (!data || Object.keys(data).length === 0) {
    return (
      <div>
        <div className="page-header">
          <h2>Results</h2>
          <p>Benchmark results comparison and visualization</p>
        </div>
        <div className="card">
          <div className="empty-state">
            <BarChart3 size={40} />
            <h3>No Results Available</h3>
            <p>Run a benchmark first to see results here.</p>
          </div>
        </div>
      </div>
    )
  }

  const available = comparison ? Object.keys(comparison.scenarios) : []
  const scenarioData = comparison?.scenarios[scenario] || {}

  // Get concurrent data for charts
  const concurrentData = comparison?.scenarios['concurrent_load'] || {}
  const singleData = comparison?.scenarios['single_request'] || {}
  const prefixData = comparison?.scenarios['prefix_cache'] || {}
  const koreanData = comparison?.scenarios['korean'] || {}

  return (
    <div>
      <div className="page-header">
        <h2>Results</h2>
        <p>
          Comparing {Object.keys(data).length} framework(s):{' '}
          {Object.keys(data).join(', ')}
        </p>
      </div>

      <ScenarioSelector active={scenario} onChange={setScenario} available={available} />

      {/* Comparison Table */}
      {Object.keys(scenarioData).length > 0 ? (
        <div className="card" style={{ marginBottom: 24 }}>
          <div className="card-title" style={{ marginBottom: 12 }}>Comparison Table</div>
          <ComparisonTable results={scenarioData} scenario={scenario} />
        </div>
      ) : (
        <div className="card" style={{ marginBottom: 24 }}>
          <div className="empty-state">
            <p>No data for this scenario. Run the benchmark with this scenario first.</p>
          </div>
        </div>
      )}

      {/* Charts */}
      {scenario === 'concurrent_load' && Object.keys(concurrentData).length > 0 && (
        <div className="grid-2">
          <ThroughputChart data={concurrentData} />
          <LatencyChart data={concurrentData} />
        </div>
      )}

      {scenario === 'single_request' && Object.keys(singleData).length > 0 && (
        <div className="grid-2">
          <TTFTChart data={singleData} />
          <GPUMemoryChart data={data} />
        </div>
      )}

      {scenario === 'prefix_cache' && Object.keys(prefixData).length > 0 && (
        <PrefixCacheChart data={prefixData} />
      )}

      {scenario === 'korean' && Object.keys(koreanData).length > 0 && (
        <KoreanVsEnglishChart data={koreanData} />
      )}

      {/* Always show GPU memory and throughput charts at bottom */}
      {scenario !== 'single_request' && scenario !== 'concurrent_load' && (
        <div className="grid-2" style={{ marginTop: 24 }}>
          {Object.keys(concurrentData).length > 0 && <ThroughputChart data={concurrentData} />}
          <GPUMemoryChart data={data} />
        </div>
      )}
    </div>
  )
}
