import { useCallback, useEffect, useState } from 'react'
import { api, type EvaluationDetail, type EvaluationRun, type EvaluationScenario } from './api'

function readTrace(value?: string | null): { transcript?: Array<{ speaker: string; text: string }>; tool_calls?: Array<{ tool: string; params?: Record<string, unknown> }> } {
  if (!value) return {}
  try { return JSON.parse(value) as ReturnType<typeof readTrace> } catch { return {} }
}

export default function Dashboard() {
  const [scenarios, setScenarios] = useState<EvaluationScenario[]>([])
  const [runs, setRuns] = useState<EvaluationRun[]>([])
  const [selected, setSelected] = useState<EvaluationDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
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
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not load evaluation data.')
    } finally { setLoading(false) }
  }, [])

  useEffect(() => { void refresh() }, [refresh])

  const runSuite = async (scenarioIds?: string[]) => {
    setRunning(true)
    setError('')
    try {
      const result = await api<EvaluationDetail & { reports: unknown[] }>('/api/v1/evaluations/run', {
        method: 'POST', body: JSON.stringify(scenarioIds ? { scenario_ids: scenarioIds } : {}),
      })
      await refresh()
      const details = await api<EvaluationDetail>(`/api/v1/evaluations/runs/${result.evaluation_run_id}`)
      setSelected(details)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Evaluation run failed.')
    } finally { setRunning(false) }
  }

  const openRun = async (id: string) => {
    try {
      setSelected(await api<EvaluationDetail>(`/api/v1/evaluations/runs/${id}`))
      setError('')
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Could not load this run.') }
  }

  const successRate = selected && selected.total_scenarios
    ? Math.round(selected.passed_scenarios * 100 / selected.total_scenarios) : null

  return (
    <section className="dashboard" aria-labelledby="dashboard-title">
      <div className="section-heading">
        <div><span className="eyebrow">QUALITY & SAFETY</span><h2 id="dashboard-title">Evaluation dashboard</h2><p>Review simulated patient runs and their results.</p></div>
        <button className="button button-primary" disabled={running || loading} onClick={() => void runSuite()}>{running ? <><span className="spinner" />Running suite…</> : 'Run all scenarios'}</button>
      </div>
      {error && <div className="inline-error" role="alert">{error}</div>}
      {loading ? <div className="loading-card"><span className="spinner" />Loading evaluation data…</div> : (
        <>
          <div className="metric-grid">
            <article className="metric-card"><span>Available scenarios</span><strong>{scenarios.length}</strong><small>Defined in this build</small></article>
            <article className="metric-card"><span>Evaluation runs</span><strong>{runs.length}</strong><small>Saved run history</small></article>
            <article className="metric-card"><span>Latest pass rate</span><strong>{successRate === null ? '—' : `${successRate}%`}</strong><small>{selected ? `${selected.passed_scenarios} of ${selected.total_scenarios} passed` : 'Select a run to inspect'}</small></article>
          </div>
          <div className="dashboard-columns">
            <div className="panel">
              <div className="panel-heading"><h3>Recent runs</h3><button className="text-button" onClick={() => void refresh()}>Refresh</button></div>
              {runs.length === 0 ? <p className="empty-state">No evaluation runs yet. Run the suite to create the first report.</p> :
                <ul className="run-list">{runs.map(run => <li key={run.evaluation_run_id}>
                  <button className={`run-row ${selected?.evaluation_run_id === run.evaluation_run_id ? 'selected' : ''}`} onClick={() => void openRun(run.evaluation_run_id)}>
                    <span className={`status-dot ${run.execution_status.toLowerCase()}`} />
                    <span className="run-main"><strong>{run.evaluation_run_id}</strong><small>{new Date(run.started_at).toLocaleString()}</small></span>
                    <span className="run-score">{run.passed_scenarios}/{run.total_scenarios}</span>
                  </button>
                </li>)}</ul>}
            </div>
            <div className="panel inspector">
              <div className="panel-heading"><h3>Run inspector</h3>{selected && <span className={`status-label ${selected.execution_status.toLowerCase()}`}>{selected.execution_status}</span>}</div>
              {!selected ? <p className="empty-state">Choose a run to inspect scenario outcomes and metrics.</p> : selected.results.length === 0 ? <p className="empty-state">This run has no saved scenario results.</p> :
                <ul className="result-list">{selected.results.map(result => <li key={result.scenario_id}>
                  <div className="result-top"><strong>{result.scenario_id}</strong><span className={`status-label ${result.execution_status.toLowerCase()}`}>{result.execution_status}</span></div>
                  <div className="result-metrics"><span>Task {result.task_completion ? 'passed' : 'failed'}</span><span>Tools {Math.round(result.tool_accuracy * 100)}%</span><span>Safety {result.safety_result ? 'passed' : 'failed'}</span></div>
                  {result.failure_category && <small className="failure-category">{result.failure_category}</small>}
                  {(readTrace(result.trace_summary).transcript?.length || readTrace(result.trace_summary).tool_calls?.length) ? <details className="trace-details">
                    <summary>Conversation &amp; tool calls</summary>
                    {readTrace(result.trace_summary).transcript?.map((turn, index) => <p className="trace-turn" key={`${turn.speaker}-${index}`}><strong>{turn.speaker}</strong>{turn.text}</p>)}
                    {readTrace(result.trace_summary).tool_calls?.map((call, index) => <p className="trace-tool" key={`${call.tool}-${index}`}>Tool: <strong>{call.tool}</strong> · {JSON.stringify(call.params || {})}</p>)}
                  </details> : null}
                </li>)}</ul>}
            </div>
          </div>
          <div className="scenario-strip"><span className="eyebrow">SCENARIO LIBRARY</span><span>{scenarios.length ? scenarios.map(s => s.scenario_id).join(' · ') : 'Scenario definitions are unavailable.'}</span></div>
          <details className="scenario-details">
            <summary>Browse scenarios and run one</summary>
            {scenarios.length === 0 ? <p className="empty-state">No scenarios are available.</p> : <ul className="scenario-list">{scenarios.map(scenario => <li key={scenario.scenario_id}>
              <div><strong>{scenario.scenario_id} · {scenario.name}</strong><small>{scenario.category} · Expected: {scenario.expected_outcome}{scenario.is_safety_critical ? ' · Safety critical' : ''}</small></div>
              <button className="text-button" disabled={running} onClick={() => void runSuite([scenario.scenario_id])}>Run</button>
            </li>)}</ul>}
          </details>
        </>
      )}
    </section>
  )
}
