import { useState, useEffect } from 'react'
import { api } from '../api/client'
import { useBenchmark } from '../hooks/useBenchmarkContext'
import type { ServerHealth } from '../api/types'
import BenchmarkForm from '../components/benchmark/BenchmarkForm'
import LogViewer from '../components/benchmark/LogViewer'
import { StopCircle } from 'lucide-react'

export default function BenchmarkPage() {
  const [health, setHealth] = useState<ServerHealth[]>([])
  const { jobId, running, logs, done, run, cancel } = useBenchmark()

  useEffect(() => {
    api.getHealth().then(setHealth).catch(() => {})
  }, [])

  const handleRun = async (params: {
    framework: string
    scenarios: string[]
    model: string
    trials: number
  }) => {
    try {
      await run(params)
    } catch (e) {
      alert(`Failed to start benchmark: ${e}`)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h2>Benchmark</h2>
        <p>Configure and run benchmarks with real-time log streaming</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        <div>
          <BenchmarkForm health={health} onRun={handleRun} running={running} />
        </div>

        <div>
          <div className="card">
            <div className="card-header">
              <span className="card-title">
                Output
                {running && <span className="spinner" style={{ display: 'inline-block', marginLeft: 8, width: 14, height: 14 }} />}
              </span>
              {running && (
                <button className="btn btn-danger" onClick={cancel} style={{ padding: '4px 12px', fontSize: 12 }}>
                  <StopCircle size={14} />
                  Cancel
                </button>
              )}
            </div>
            <LogViewer logs={logs} />
            {done && jobId && (
              <div style={{ marginTop: 12, fontSize: 13, color: 'var(--success)' }}>
                Benchmark completed. Check the Results page.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
