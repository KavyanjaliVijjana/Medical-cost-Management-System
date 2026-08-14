import { useEffect, useState } from 'react'

import { api } from '../api/client'
import type { AdvisorResponse, AdvisorToolEvidence, Dataset } from '../types/api'

const examples = [
  'Why are medical costs increasing?',
  'What is the expected cost trend?',
  'What are the biggest cost pressures?',
  'What should the medical economics team prioritize?',
  'What happens if Oncology costs are reduced by 5%?',
]

const currency = (value: unknown) => typeof value === 'number' ? new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value) : 'Not available'
const percentage = (value: unknown) => typeof value === 'number' ? `${value >= 0 ? '+' : ''}${value.toFixed(1)}%` : 'Not available'

export function AdvisorPage({ selectedDatasetId, onDatasetChange }: { selectedDatasetId: number | null; onDatasetChange: (datasetId: number) => void }) {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [question, setQuestion] = useState('')
  const [response, setResponse] = useState<AdvisorResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isAsking, setIsAsking] = useState(false)

  useEffect(() => {
    let active = true
    api.listDatasets().then((available) => {
      if (!active) return
      setDatasets(available)
      if (available.length && !available.some((dataset) => dataset.id === selectedDatasetId)) onDatasetChange(available[0].id)
    }).catch((loadError: unknown) => active && setError(loadError instanceof Error ? loadError.message : 'Could not load processed datasets.')).finally(() => active && setIsLoading(false))
    return () => { active = false }
  }, [onDatasetChange, selectedDatasetId])

  async function askAdvisor() {
    if (!selectedDatasetId || !question.trim()) return
    setError(null)
    setIsAsking(true)
    try {
      setResponse(await api.askAdvisor(selectedDatasetId, question.trim()))
    } catch (askError) {
      setError(askError instanceof Error ? askError.message : 'The advisor request could not be completed.')
    } finally {
      setIsAsking(false)
    }
  }

  return <section className="space-y-6">
    <header className="flex flex-wrap items-end justify-between gap-4"><div><p className="text-sm font-medium text-teal">Optional AI synthesis over verified evidence</p><h2 className="mt-1 text-3xl font-semibold tracking-tight text-slate-900">Ask Medical Economics Advisor</h2><p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">The advisor selects controlled deterministic tools for the selected dataset. It supports healthcare-finance and operational cost questions only.</p></div><label className="text-sm font-medium text-slate-700">Dataset<select className="mt-1 block min-w-64 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm" disabled={!datasets.length} value={selectedDatasetId ?? ''} onChange={(event) => { setResponse(null); onDatasetChange(Number(event.target.value)) }}>{datasets.length ? datasets.map((dataset) => <option key={dataset.id} value={dataset.id}>{dataset.name}</option>) : <option value="">No processed datasets</option>}</select></label></header>
    {isLoading && <p className="rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-600">Loading advisor workspace...</p>}
    {error && <p className="rounded-lg bg-rose-50 p-4 text-sm text-rose-700">{error}</p>}
    {!isLoading && <article className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"><label className="block text-sm font-semibold text-slate-800">Question<textarea className="mt-2 block min-h-28 w-full rounded-lg border border-slate-300 p-3 text-sm leading-6 text-slate-800" maxLength={2000} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask about cost trends, drivers, priorities, or a department-reduction scenario..." value={question} /></label><div className="mt-3 flex flex-wrap gap-2">{examples.map((example) => <button className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100" key={example} onClick={() => setQuestion(example)} type="button">{example}</button>)}</div><button className="mt-5 rounded-lg bg-navy px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50" disabled={!selectedDatasetId || !question.trim() || isAsking} onClick={() => void askAdvisor()} type="button">{isAsking ? 'Retrieving evidence...' : 'Ask advisor'}</button></article>}
    {response && <AdvisorResult response={response} />}
  </section>
}

function AdvisorResult({ response }: { response: AdvisorResponse }) {
  const unavailable = response.status === 'provider_unavailable' || response.status === 'provider_error'
  return <section className="space-y-4"><article className={`rounded-xl border p-6 shadow-sm ${unavailable ? 'border-amber-200 bg-amber-50' : 'border-cyan-200 bg-cyan-50'}`}><div className="flex flex-wrap items-start justify-between gap-3"><div><h3 className="text-base font-semibold text-slate-900">Advisor response</h3><p className="mt-1 text-sm text-slate-600">Dataset ID {response.dataset_id} · Provider: {response.provider}{response.model ? ` / ${response.model}` : ''}</p></div><span className="rounded-full bg-white px-3 py-1.5 text-xs font-semibold uppercase tracking-wide text-slate-700">{response.status.replace('_', ' ')}</span></div>{response.answer ? <p className="mt-4 whitespace-pre-wrap text-sm leading-6 text-slate-800">{response.answer}</p> : <p className="mt-4 text-sm leading-6 text-slate-700">{response.message}</p>}{unavailable && <p className="mt-3 text-xs text-slate-600">No AI narrative is shown when the provider is unavailable; the evidence below remains deterministic application data.</p>}</article><article className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"><h3 className="text-base font-semibold text-slate-900">Tools used</h3><div className="mt-3 flex flex-wrap gap-2">{response.tools_used.length ? response.tools_used.map((tool) => <span className="rounded-full bg-cyan-50 px-3 py-1.5 text-xs font-semibold text-teal" key={tool}>{tool.replace('_', ' ')}</span>) : <span className="text-sm text-slate-600">No tools were used.</span>}</div></article><article className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"><h3 className="text-base font-semibold text-slate-900">Key evidence</h3><p className="mt-1 text-sm text-slate-600">ACTUAL values are observed data, FORECAST values come from the stored model run, and HYPOTHETICAL values come from scenario analysis.</p><div className="mt-4 space-y-3">{response.evidence.map((evidence) => <EvidenceCard evidence={evidence} key={evidence.tool} />)}</div></article></section>
}

function EvidenceCard({ evidence }: { evidence: AdvisorToolEvidence }) {
  if (evidence.error) return <div className="rounded-lg border border-amber-200 bg-amber-50 p-4"><p className="font-semibold text-slate-900">{evidence.tool.replace('_', ' ')}</p><p className="mt-1 text-sm text-slate-700">Unavailable: {evidence.error}</p></div>
  const result = evidence.result ?? {}
  if (evidence.tool === 'analytics') {
    const metrics = result.metrics as Record<string, unknown> | undefined
    return <Evidence title="ACTUAL historical analytics" lines={[`Total cost: ${currency(metrics?.total_medical_cost)}`, `Patient volume: ${typeof metrics?.total_patient_count === 'number' ? metrics.total_patient_count.toLocaleString() : 'Not available'}`, `Cost per patient: ${currency(metrics?.cost_per_patient)}`, `Latest month-over-month change: ${percentage(metrics?.month_over_month_cost_change_pct)}`]} />
  }
  if (evidence.tool === 'forecast') {
    const points = result.forecast_points as Array<Record<string, unknown>> | undefined
    return <Evidence title="FORECAST stored model result" lines={[`Model: ${String(result.model_name ?? 'Not available')}`, `Horizon: ${String(result.horizon_months ?? 'Not available')} months`, `Forecast points: ${points?.length ?? 0}`, `Expected change: ${percentage(result.expected_change_pct)}`]} />
  }
  if (evidence.tool === 'cost_pressures') {
    const drivers = result.drivers as Array<Record<string, unknown>> | undefined
    const alerts = result.alerts as Array<Record<string, unknown>> | undefined
    return <Evidence title="ACTUAL drivers and alerts" lines={[...(drivers ?? []).slice(0, 3).map((item) => String(item.explanation ?? item.metric)), ...(alerts ?? []).slice(0, 2).map((item) => `${String(item.severity ?? 'active').toUpperCase()}: ${String(item.explanation ?? item.metric)}`)]} />
  }
  if (evidence.tool === 'recommendations') {
    const recommendations = result.recommendations as Array<Record<string, unknown>> | undefined
    return <Evidence title="Evidence-based recommendations" lines={(recommendations ?? []).map((item) => `${String(item.title)}: ${String(item.rationale)}`)} />
  }
  return <Evidence title="HYPOTHETICAL scenario result" lines={[`Department: ${String(result.department ?? 'Not available')}`, `Baseline projected cost: ${currency(result.baseline_projected_cost)}`, `Estimated reduction: ${currency(result.estimated_reduction_amount)}`, `Scenario projected cost: ${currency(result.scenario_projected_cost)}`, 'Hypothetical estimate - not guaranteed savings.']} />
}

function Evidence({ title, lines }: { title: string; lines: string[] }) {
  return <div className="rounded-lg bg-slate-50 p-4"><p className="font-semibold text-slate-900">{title}</p>{lines.length ? <ul className="mt-2 list-disc space-y-1 pl-5 text-sm leading-6 text-slate-700">{lines.map((line, index) => <li key={`${line}-${index}`}>{line}</li>)}</ul> : <p className="mt-2 text-sm text-slate-600">No stored evidence is available for this tool.</p>}</div>
}
