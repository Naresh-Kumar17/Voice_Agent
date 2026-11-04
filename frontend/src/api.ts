export type EvaluationScenario = {
  scenario_id: string
  category: string
  name: string
  description: string
  expected_outcome: string
  is_safety_critical: boolean
}

export type EvaluationRun = {
  evaluation_run_id: string
  execution_status: string
  total_scenarios: number
  passed_scenarios: number
  failed_scenarios: number
  started_at: string
  completed_at?: string | null
}

export type EvaluationDetail = EvaluationRun & {
  results: Array<{
    scenario_id: string
    execution_status: string
    task_completion: boolean
    tool_accuracy: number
    safety_result: boolean
    latency_metrics: string
    failure_category?: string | null
    trace_summary?: string | null
  }>
}

export type Doctor = {
  doctor_id: string
  doctor_name: string
  specialization: string
  calendar_id: string
  timezone: string
  active_status: boolean
  working_hours_start: string
  working_hours_end: string
}

export type LiveKitCredentials = {
  server_url: string
  room_name: string
  participant_identity: string
  participant_token: string
}

const apiBase = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBase}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const detail = body?.detail
    throw new Error(typeof detail === 'string' ? detail : `Request failed (${response.status})`)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}
