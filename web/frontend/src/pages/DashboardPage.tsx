import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { useGPUMonitor } from '../hooks/useGPUMonitor'
import { useServerManager } from '../hooks/useServerManager'
import type { ServerHealth, FrameworkResults } from '../api/types'
import { FW_LABELS } from '../api/types'
import ServerStatusCard from '../components/monitoring/ServerStatusCard'
import ServerLogModal from '../components/monitoring/ServerLogModal'
import GPUGauge from '../components/monitoring/GPUGauge'
import { Database } from 'lucide-react'

export default function DashboardPage() {
  const [health, setHealth] = useState<ServerHealth[]>([])
  const [allResults, setAllResults] = useState<Record<string, FrameworkResults> | null>(null)
  const [showLogs, setShowLogs] = useState(false)
  const gpu = useGPUMonitor()
  const mgr = useServerManager()

  useEffect(() => {
    api.getHealth().then(setHealth).catch(() => {})
    api.getAllResults().then(setAllResults).catch(() => {})
  }, [])

  // Refresh health when server status changes
  useEffect(() => {
    api.getHealth().then(setHealth).catch(() => {})
  }, [mgr.status.status])

  const handleViewLogs = () => {
    mgr.connectLogs()
    setShowLogs(true)
  }

  const handleCloseLogs = () => {
    setShowLogs(false)
    mgr.disconnectLogs()
  }

  // Latest results summary
  const summaryRows: { fw: string; scenario: string; throughput: number; ttft: number }[] = []
  if (allResults) {
    for (const [fw, fwData] of Object.entries(allResults)) {
      for (const r of fwData.results.slice(0, 3)) {
        summaryRows.push({
          fw,
          scenario: r.scenario,
          throughput: r.total_token_throughput,
          ttft: r.avg_ttft_ms,
        })
      }
    }
  }

  const servers = health.length > 0
    ? health
    : ['sglang', 'vllm', 'ollama'].map((fw) => ({
        framework: fw,
        label: FW_LABELS[fw],
        healthy: false,
        base_url: '...',
      }))

  return (
    <div>
      <div className="page-header">
        <h2>Dashboard</h2>
        <p>Server status, GPU monitoring, and recent results overview</p>
      </div>

      {/* Error message */}
      {mgr.error && (
        <div
          style={{
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid var(--danger)',
            borderRadius: 8,
            padding: '10px 16px',
            marginBottom: 16,
            fontSize: 13,
            color: 'var(--danger)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <span>{mgr.error}</span>
          <button
            onClick={mgr.clearError}
            style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer', fontSize: 16 }}
          >
            &times;
          </button>
        </div>
      )}

      {/* Server Status Cards */}
      <div className="grid-3">
        {servers.map((s) => (
          <ServerStatusCard
            key={s.framework}
            server={s}
            managed={mgr.status}
            loading={mgr.loading}
            onStart={mgr.startServer}
            onStop={() => mgr.stopServer()}
            onViewLogs={handleViewLogs}
          />
        ))}
      </div>

      {/* GPU Gauges */}
      <div className="grid-2">
        <GPUGauge stats={gpu} label="Memory" />
        <GPUGauge stats={gpu} label="Utilization" />
      </div>

      {/* Recent Results */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Recent Results</span>
          {allResults && (
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              {Object.keys(allResults).length} framework(s)
            </span>
          )}
        </div>
        {summaryRows.length > 0 ? (
          <table className="data-table">
            <thead>
              <tr>
                <th>Framework</th>
                <th>Scenario</th>
                <th>Throughput (tok/s)</th>
                <th>TTFT (ms)</th>
              </tr>
            </thead>
            <tbody>
              {summaryRows.map((r, i) => (
                <tr key={i}>
                  <td><span className={`fw-badge ${r.fw}`}>{FW_LABELS[r.fw]}</span></td>
                  <td>{r.scenario}</td>
                  <td>{r.throughput.toLocaleString(undefined, { maximumFractionDigits: 1 })}</td>
                  <td>{r.ttft.toLocaleString(undefined, { maximumFractionDigits: 1 })}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="empty-state">
            <Database size={40} />
            <h3>No Results Yet</h3>
            <p>Run a benchmark to see results here.</p>
          </div>
        )}
      </div>

      {/* Server Log Modal */}
      {showLogs && mgr.status.framework && (
        <ServerLogModal
          logs={mgr.logs}
          framework={FW_LABELS[mgr.status.framework] || mgr.status.framework}
          onClose={handleCloseLogs}
        />
      )}
    </div>
  )
}
