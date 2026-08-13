import { useEffect, useState } from 'react'

import { api } from '../api/client'
import type { CostAlert, Dataset, DriverInsight, Recommendation } from '../types/api'

const currency = (value: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value)
const number = (value: number) => new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(value)

function driverEvidence(driver: DriverInsight) {
  if (driver.metric === 'Patient utilization') return `Observed: ${number(driver.observed_value)} patients · Baseline: ${driver.baseline_value === null ? '—' : number(driver.baseline_value)} patients · ${driver.period}`
  if (driver.metric === 'Department cost contribution') return `Share of total cost: ${driver.change_pct === null ? '—' : `${driver.change_pct.toFixed(1)}%`} · Department cost: ${currency(driver.observed_value)} · ${driver.period}`
  return `Observed: ${currency(driver.observed_value)} · Baseline: ${driver.baseline_value === null ? '—' : currency(driver.baseline_value)} · ${driver.period}`
}

export function InsightsPage({ selectedDatasetId, onDatasetChange }: { selectedDatasetId: number | null; onDatasetChange: (datasetId: number) => void }) {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [drivers, setDrivers] = useState<DriverInsight[]>([])
  const [alerts, setAlerts] = useState<CostAlert[]>([])
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  async function loadExisting(datasetId: number) {
    const [existingDrivers, existingAlerts, existingRecommendations] = await Promise.all([api.getDrivers(datasetId), api.getAlerts(datasetId), api.getRecommendations(datasetId)])
    setDrivers(existingDrivers); setAlerts(existingAlerts); setRecommendations(existingRecommendations)
  }

  useEffect(() => {
    let active = true
    api.listDatasets().then(async (available) => {
      if (!active) return
      setDatasets(available)
      const datasetId = available.some((dataset) => dataset.id === selectedDatasetId) ? selectedDatasetId : available[0]?.id
      if (datasetId) { if (datasetId !== selectedDatasetId) onDatasetChange(datasetId); await loadExisting(datasetId) }
    }).catch((loadError: unknown) => active && setError(loadError instanceof Error ? loadError.message : 'Could not load insights.')).finally(() => active && setIsLoading(false))
    return () => { active = false }
  }, [onDatasetChange, selectedDatasetId])

  async function generate() {
    if (!selectedDatasetId) return
    setIsLoading(true); setError(null)
    try {
      const [generatedDrivers, generatedAlerts] = await Promise.all([api.generateDrivers(selectedDatasetId), api.generateAlerts(selectedDatasetId)])
      const generatedRecommendations = await api.generateRecommendations(selectedDatasetId)
      setDrivers(generatedDrivers); setAlerts(generatedAlerts); setRecommendations(generatedRecommendations)
    } catch (generationError) { setError(generationError instanceof Error ? generationError.message : 'Could not generate insights.') } finally { setIsLoading(false) }
  }

  return <section className="space-y-6"><header className="flex flex-wrap items-end justify-between gap-4"><div><p className="text-sm font-medium text-teal">Cost pressure evidence</p><h2 className="mt-1 text-3xl font-semibold tracking-tight text-slate-900">Drivers, alerts and recommendations</h2><p className="mt-2 text-sm text-slate-600">Deterministic evidence and financial/operational actions from processed historical cost data.</p></div><div className="flex gap-3"><select className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm" value={selectedDatasetId ?? ''} onChange={(event) => onDatasetChange(Number(event.target.value))}>{datasets.map((dataset) => <option key={dataset.id} value={dataset.id}>{dataset.name}</option>)}</select><button className="rounded-lg bg-navy px-4 py-2 text-sm font-semibold text-white disabled:opacity-50" disabled={!selectedDatasetId || isLoading} onClick={generate}>Generate insights</button></div></header>{error && <p className="rounded-lg bg-rose-50 p-4 text-sm text-rose-700">{error}</p>}{isLoading && <p className="rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-600">Loading insights…</p>} {!isLoading && <><div className="grid gap-6 xl:grid-cols-2"><article className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"><h3 className="text-base font-semibold text-slate-900">Top drivers</h3><div className="mt-4 space-y-3">{drivers.length ? drivers.map((driver) => <div className="rounded-lg bg-slate-50 p-4" key={driver.id}><div className="flex justify-between gap-3"><p className="font-semibold text-slate-800">{driver.metric}</p><p className="text-sm font-medium text-teal">{driver.metric === 'Department cost contribution' ? `Share: ${driver.change_pct?.toFixed(1) ?? '—'}%` : driver.change_pct === null ? '—' : `${driver.change_pct >= 0 ? '+' : ''}${driver.change_pct.toFixed(1)}%`}</p></div><p className="mt-2 text-sm text-slate-600">{driver.explanation}</p><p className="mt-2 text-xs text-slate-500">{driverEvidence(driver)}</p></div>) : <p className="text-sm text-slate-600">Generate insights to view data-backed drivers.</p>}</div></article><article className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"><h3 className="text-base font-semibold text-slate-900">Active alerts</h3><div className="mt-4 space-y-3">{alerts.length ? alerts.map((alert) => <div className="rounded-lg border-l-4 border-amber-500 bg-amber-50 p-4" key={alert.id}><div className="flex justify-between gap-3"><p className="font-semibold text-slate-800">{alert.metric}</p><span className="text-xs font-bold uppercase text-amber-800">{alert.severity}</span></div><p className="mt-2 text-sm text-slate-700">{alert.explanation}</p><p className="mt-2 text-xs text-slate-600">Observed: {alert.observed_value.toFixed(1)} · Threshold: {alert.threshold_value.toFixed(1)} · {alert.period}</p></div>) : <p className="text-sm text-slate-600">No active alerts generated for this dataset.</p>}</div></article></div><article className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"><h3 className="text-base font-semibold text-slate-900">Cost-containment recommendations</h3><p className="mt-1 text-sm text-slate-600">Operational actions generated only when supporting evidence exists. No savings are estimated.</p><div className="mt-4 space-y-3">{recommendations.length ? recommendations.map((recommendation) => <div className="rounded-lg bg-cyan-50 p-4" key={recommendation.id}><div className="flex flex-wrap justify-between gap-2"><div><p className="font-semibold text-slate-900">{recommendation.title}</p><p className="mt-1 text-xs font-semibold uppercase tracking-wide text-teal">{recommendation.category} · {recommendation.priority} priority</p></div><span className="text-xs text-slate-600">{recommendation.period}</span></div><p className="mt-3 text-sm text-slate-700">{recommendation.rationale}</p><ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-slate-600">{recommendation.supporting_evidence.map((evidence) => <li key={evidence}>{evidence}</li>)}</ul><p className="mt-3 text-xs text-slate-500">Triggered by: {recommendation.triggering_metric}</p></div>) : <p className="text-sm text-slate-600">No recommendation is generated without matching driver or alert evidence.</p>}</div></article></>}</section>
}
