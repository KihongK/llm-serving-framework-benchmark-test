import { useState } from 'react'
import { Play } from 'lucide-react'
import type { ServerHealth } from '../../api/types'

const SCENARIOS = ['all', 'single', 'concurrent', 'long_context', 'prefix_cache', 'korean']
const MODELS = ['gpt-oss-20b', 'llama3.1-8b']

interface Props {
  health: ServerHealth[]
  onRun: (params: { framework: string; scenarios: string[]; model: string; trials: number }) => void
  running: boolean
}

export default function BenchmarkForm({ health, onRun, running }: Props) {
  const [framework, setFramework] = useState('sglang')
  const [scenarios, setScenarios] = useState<string[]>(['all'])
  const [model, setModel] = useState('gpt-oss-20b')
  const [trials, setTrials] = useState(1)

  const serverOk = health.find((h) => h.framework === framework)?.healthy ?? false

  const toggleScenario = (s: string) => {
    if (s === 'all') {
      setScenarios(['all'])
      return
    }
    let next = scenarios.filter((x) => x !== 'all')
    if (next.includes(s)) {
      next = next.filter((x) => x !== s)
    } else {
      next.push(s)
    }
    if (next.length === 0) next = ['all']
    setScenarios(next)
  }

  return (
    <div className="card">
      <div className="card-title" style={{ marginBottom: 16 }}>Configuration</div>

      <div className="form-group">
        <label className="form-label">Framework</label>
        <div className="radio-group">
          {['sglang', 'vllm', 'ollama'].map((fw) => {
            const isHealthy = health.find((h) => h.framework === fw)?.healthy
            return (
              <label key={fw} className={`radio-option ${framework === fw ? 'selected' : ''}`}>
                <input type="radio" name="framework" checked={framework === fw} onChange={() => setFramework(fw)} />
                <span className={`status-dot ${isHealthy ? 'healthy' : 'unhealthy'}`} />
                <span className={`fw-badge ${fw}`}>{fw === 'sglang' ? 'SGLang' : fw === 'vllm' ? 'vLLM' : 'Ollama'}</span>
              </label>
            )
          })}
        </div>
      </div>

      <div className="form-group">
        <label className="form-label">Scenarios</label>
        <div className="checkbox-group">
          {SCENARIOS.map((s) => (
            <label key={s} className={`checkbox-option ${scenarios.includes(s) ? 'selected' : ''}`} onClick={() => toggleScenario(s)}>
              {s}
            </label>
          ))}
        </div>
      </div>

      <div style={{ display: 'flex', gap: 16 }}>
        <div className="form-group" style={{ flex: 1 }}>
          <label className="form-label">Model</label>
          <select className="form-select" value={model} onChange={(e) => setModel(e.target.value)}>
            {MODELS.map((m) => <option key={m} value={m}>{m}</option>)}
          </select>
        </div>
        <div className="form-group" style={{ width: 100 }}>
          <label className="form-label">Trials</label>
          <input
            className="form-input"
            type="number"
            min={1}
            max={10}
            value={trials}
            onChange={(e) => setTrials(Number(e.target.value))}
          />
        </div>
      </div>

      <button
        className="btn btn-primary"
        disabled={running || !serverOk}
        onClick={() => onRun({ framework, scenarios, model, trials })}
        style={{ marginTop: 8 }}
      >
        <Play size={16} />
        {running ? 'Running...' : serverOk ? 'Run Benchmark' : 'Server Offline'}
      </button>

      {!serverOk && !running && (
        <div style={{ marginTop: 8, fontSize: 13, color: 'var(--danger)' }}>
          Selected framework server is offline. Start it first.
        </div>
      )}
    </div>
  )
}
