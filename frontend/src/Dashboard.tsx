import { useCallback, useEffect, useState } from 'react'
import { api, type EvaluationDetail, type EvaluationRun, type EvaluationScenario } from './api'

function readTrace(value?: string | null): {
  transcript?: Array<{ speaker: string; text: string }>
  tool_calls?: Array<{ tool: string; params?: Record<string, unknown>; result?: unknown }>
} {
  if (!value) return {}
  try {
    return JSON.parse(value) as ReturnType<typeof readTrace>
  } catch {
    return {}
  }
}

export default function Dashboard() {
  const [scenarios, setScenarios] = useState<EvaluationScenario[]>([])
  const [runs, setRuns] = useState<EvaluationRun[]>([])
  const [selected, setSelected] = useState<EvaluationDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const [categoryFilter, setCategoryFilter] = useState<string>('ALL')
  const [error, setError] = useState('')

  const refresh = useCallback(async () => {
    setError('')
    try {
      const [scenarioRows, runRows] = await Promise.all([
        api<EvaluationScenario[]>('/api/v1/evaluations/scenarios'),
        api<EvaluationRun[]>('/api/v1/evaluations/runs'),
      ])
      setScenarios(scenarioRows)
      setRuns(runRows)
      if (runRows.length > 0 && !selected) {
        const first = await api<EvaluationDetail>(`/api/v1/evaluations/runs/${runRows[0].evaluation_run_id}`)
        setSelected(first)
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not load evaluation data.')
    } finally {
      setLoading(false)
    }
  }, [selected])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const runSuite = async (scenarioIds?: string[]) => {
    setRunning(true)
    setError('')
    try {
      const result = await api<EvaluationDetail & { reports: unknown[] }>('/api/v1/evaluations/run', {
        method: 'POST',
        body: JSON.stringify(scenarioIds ? { scenario_ids: scenarioIds } : {}),
      })
      await refresh()
      const details = await api<EvaluationDetail>(`/api/v1/evaluations/runs/${result.evaluation_run_id}`)
      setSelected(details)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Evaluation run failed.')
    } finally {
      setRunning(false)
    }
  }

  const openRun = async (id: string) => {
    try {
      setSelected(await api<EvaluationDetail>(`/api/v1/evaluations/runs/${id}`))
      setError('')
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not load this run.')
    }
  }

  const categories = ['ALL', ...Array.from(new Set(scenarios.map(s => s.category)))]
  const filteredScenarios = categoryFilter === 'ALL'
    ? scenarios
    : scenarios.filter(s => s.category === categoryFilter)

  const successRate = selected && selected.total_scenarios
    ? Math.round((selected.passed_scenarios * 100) / selected.total_scenarios)
    : null

  return (
    <section className="dashboard lumora-glass-card" aria-labelledby="dashboard-title">
      {/* Header */}
      <div className="section-heading">
        <div>
          <span className="eyebrow">
            <span className="eyebrow-dot" />
            BENCHMARK & CLINICAL SAFETY
          </span>
          <h2 id="dashboard-title">Autonomous Evaluation Engine</h2>
          <p>Closed-loop simulated patient conversations with ground-truth database verification</p>
        </div>
        <button
          className="button button-call-start"
          disabled={running || loading}
          onClick={() => void runSuite()}
          id="btn-run-all"
        >
          {running ? (
            <>
              <span className="spinner" />
              <span>Simulating 15 Patient Calls…</span>
            </>
          ) : (
            <>
              <span>▶ Run Full Test Suite (15 Cases)</span>
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="inline-error" role="alert">
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="loading-card">
          <span className="spinner" />
          <span>Synchronizing evaluation records…</span>
        </div>
      ) : (
        <>
          {/* Key Metric Gauges */}
          <div className="metric-grid">
            <article className="metric-card">
              <span className="metric-label">DEFINED SCENARIOS</span>
              <strong className="metric-val">{scenarios.length}</strong>
              <small className="metric-sub">Categories A–F across PRD</small>
            </article>

            <article className="metric-card">
              <span className="metric-label">EVALUATION RUNS</span>
              <strong className="metric-val">{runs.length}</strong>
              <small className="metric-sub">Persisted run records</small>
            </article>

            <article className="metric-card highlight">
              <span className="metric-label">OVERALL PASS RATE</span>
              <strong className="metric-val text-neon">
                {successRate === null ? '—' : `${successRate}%`}
              </strong>
              <small className="metric-sub">
                {selected ? `${selected.passed_scenarios} of ${selected.total_scenarios} passed` : 'Select a run'}
              </small>
            </article>
          </div>

          {/* Two-Column Run Browser and Inspector */}
          <div className="dashboard-columns">
            {/* Left: Saved Runs */}
            <div className="panel lumora-panel">
              <div className="panel-heading">
                <h3>Evaluation History</h3>
                <button className="text-button" onClick={() => void refresh()}>
                  ↻ Refresh
                </button>
              </div>

              {runs.length === 0 ? (
                <p className="empty-state">No evaluation runs yet. Run the suite to benchmark the agent.</p>
              ) : (
                <ul className="run-list">
                  {runs.map(run => (
                    <li key={run.evaluation_run_id}>
                      <button
                        className={`run-row ${selected?.evaluation_run_id === run.evaluation_run_id ? 'selected' : ''}`}
                        onClick={() => void openRun(run.evaluation_run_id)}
                      >
                        <span className={`status-dot ${run.execution_status.toLowerCase()}`} />
                        <span className="run-main">
                          <strong>{run.evaluation_run_id}</strong>
                          <small>{new Date(run.started_at).toLocaleString()}</small>
                        </span>
                        <span className="run-score">
                          {run.passed_scenarios} / {run.total_scenarios}
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {/* Right: Inspector */}
            <div className="panel lumora-panel inspector">
              <div className="panel-heading">
                <h3>Run Inspector</h3>
                {selected && (
                  <span className={`status-label ${selected.execution_status.toLowerCase()}`}>
                    {selected.execution_status}
                  </span>
                )}
              </div>

              {!selected ? (
                <p className="empty-state">Choose an evaluation run on the left to inspect scenario outcomes.</p>
              ) : selected.results.length === 0 ? (
                <p className="empty-state">This run has no recorded scenario results.</p>
              ) : (
                <ul className="result-list">
                  {selected.results.map(result => {
                    const trace = readTrace(result.trace_summary)
                    return (
                      <li key={result.scenario_id} className="result-item">
                        <div className="result-top">
                          <strong className="result-id">{result.scenario_id}</strong>
                          <span className={`status-label ${result.execution_status.toLowerCase()}`}>
                            {result.execution_status}
                          </span>
                        </div>

                        <div className="result-metrics">
                          <span className={result.task_completion ? 'metric-ok' : 'metric-fail'}>
                            Task: {result.task_completion ? '✓ Pass' : '✕ Fail'}
                          </span>
                          <span className="metric-info">
                            Tools: {Math.round(result.tool_accuracy * 100)}%
                          </span>
                          <span className={result.safety_result ? 'metric-ok' : 'metric-fail'}>
                            Safety: {result.safety_result ? '✓ Compliant' : '✕ Violated'}
                          </span>
                        </div>

                        {result.failure_category && (
                          <small className="failure-category">Reason: {result.failure_category}</small>
                        )}

                        {(trace.transcript?.length || trace.tool_calls?.length) && (
                          <details className="trace-details">
                            <summary>View Multi-Turn Dialogue & Tool Calls</summary>
                            <div className="trace-content">
                              {trace.transcript?.map((turn, index) => (
                                <p className="trace-turn" key={`${turn.speaker}-${index}`}>
                                  <strong>{turn.speaker}:</strong> {turn.text}
                                </p>
                              ))}
                              {trace.tool_calls?.map((call, index) => (
                                <p className="trace-tool" key={`${call.tool}-${index}`}>
                                  ⚙️ Tool: <strong>{call.tool}</strong> · params: {JSON.stringify(call.params || {})}
                                </p>
                              ))}
                            </div>
                          </details>
                        )}
                      </li>
                    )
                  })}
                </ul>
              )}
            </div>
          </div>

          {/* Scenario Library Explorer */}
          <div className="scenario-library-box">
            <div className="library-header">
              <span className="eyebrow">
                <span className="eyebrow-dot" />
                SCENARIO BENCHMARK LIBRARY
              </span>
              <div className="filter-pills">
                {categories.map(cat => (
                  <button
                    key={cat}
                    className={`filter-pill ${categoryFilter === cat ? 'active' : ''}`}
                    onClick={() => setCategoryFilter(cat)}
                  >
                    {cat}
                  </button>
                ))}
              </div>
            </div>

            <ul className="scenario-list">
              {filteredScenarios.map(sc => (
                <li key={sc.scenario_id} className="scenario-card">
                  <div className="scenario-meta">
                    <strong className="scenario-name">
                      {sc.scenario_id} · {sc.name}
                    </strong>
                    <small className="scenario-cat">
                      Category: {sc.category} | Expected: {sc.expected_outcome}
                      {sc.is_safety_critical && <span className="safety-tag">Safety Critical</span>}
                    </small>
                  </div>
                  <button
                    className="button button-run-single"
                    disabled={running}
                    onClick={() => void runSuite([sc.scenario_id])}
                  >
                    Run Test
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </>
      )}
    </section>
  )
}
