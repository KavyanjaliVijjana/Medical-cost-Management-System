import { useEffect, useState } from 'react'

import { api } from '../api/client'
import type { AnalyticsSummary, Dataset, ScenarioResult } from '../types/api'

const currency = (value: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value)

export function ScenarioPage({ selectedDatasetId, onDatasetChange }: { selectedDatasetId: number | null; onDatasetChange: (datasetId: number) => void }) {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null)
  const [department, setDepartment] = useState('')
  const [reductionPct, setReductionPct] = useState('5')
  const [result, setResult] = useState<ScenarioResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isCalculating, setIsCalculating] = useState(false)

  useEffect(() => {
    let active = true
    async function load() {
      try {
        const available = await api.listDatasets()
        if (!active) return
        setDatasets(available)
        const datasetId = available.some((item) => item.id === selectedDatasetId) ? selectedDatasetId : available[0]?.id
        if (!datasetId) return
        if (datasetId !== selectedDatasetId) onDatasetChange(datasetId)
        const analytics = await api.getAnalyticsSummary(datasetId)
        if (!active) return
        setSummary(analytics)
        setDepartment((current) => analytics.departments.some((item) => item.department === current) ? current : analytics.departments[0]?.department ?? '')
      } catch (loadError) {
        if (active) setError(loadError instanceof Error ? loadError.message : 'Could not load scenario inputs.')
      } finally {
        if (active) setIsLoading(false)
      }
    }
    void load()
    return () => { active = false }
  }, [onDatasetChange, selectedDatasetId])

  async function changeDataset(datasetId: number) {
    onDatasetChange(datasetId)
    setResult(null)
    setError(null)
    try {
      const analytics = await api.getAnalyticsSummary(datasetId)
      setSummary(analytics)
      setDepartment(analytics.departments[0]?.department ?? '')
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Could not load departments.')
    }
  }

  async function calculate() {
    if (!selectedDatasetId || !department) return
    setError(null)
    setIsCalculating(true)
    try {
      setResult(await api.createScenario(selectedDatasetId, department, Number(reductionPct)))
    } catch (calculationError) {
      setError(calculationError instanceof Error ? calculationError.message : 'Could not calculate scenario.')
    } finally {
      setIsCalculating(false)
    }
  }

  return <section className="space-y-6">
    <header><p className="text-sm font-medium text-teal">Transparent what-if estimate</p><h2 className="mt-1 text-3xl font-semibold tracking-tight text-slate-900">Department reduction scenario</h2><p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">Applies a hypothetical reduction to the selected department’s actual historical cost share of the latest persisted forecast. It does not predict or guarantee savings.</p></header>
    {error && <p className="rounded-lg bg-rose-50 p-4 text-sm text-rose-700">{error}</p>}
    {isLoading && <p className="rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-600">Loading scenario inputs…</p>}
    {!isLoading && <article className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"><div className="grid gap-4 md:grid-cols-3"><label className="text-sm font-medium text-slate-700">Dataset<select className="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm" value={selectedDatasetId ?? ''} onChange={(event) => void changeDataset(Number(event.target.value))}>{datasets.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label className="text-sm font-medium text-slate-700">Department<select className="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm" value={department} onChange={(event) => setDepartment(event.target.value)}>{summary?.departments.map((item) => <option key={item.department} value={item.department}>{item.department} ({item.contribution_pct?.toFixed(1) ?? '0.0'}% historical share)</option>)}</select></label><label className="text-sm font-medium text-slate-700">Reduction percentage<input className="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm" min="0.01" max="100" step="0.1" type="number" value={reductionPct} onChange={(event) => setReductionPct(event.target.value)} /></label></div><button className="mt-5 rounded-lg bg-navy px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50" disabled={!selectedDatasetId || !department || isCalculating} onClick={() => void calculate()} type="button">{isCalculating ? 'Calculating…' : 'Calculate hypothetical scenario'}</button></article>}
    {result && <article className="rounded-xl border border-cyan-200 bg-cyan-50 p-6 shadow-sm"><div className="flex flex-wrap items-start justify-between gap-4"><div><h3 className="text-base font-semibold text-slate-900">Scenario result: {result.department}</h3><p className="mt-1 text-sm text-slate-700">Historical department share: {result.department_cost_share_pct.toFixed(2)}% · Reduction entered: {result.reduction_pct.toFixed(2)}%</p></div><span className="rounded-full bg-white px-3 py-1.5 text-xs font-semibold text-teal">Hypothetical estimate</span></div><div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{[['Baseline projected cost', currency(result.baseline_projected_cost)], ['Estimated reduction amount', currency(result.estimated_reduction_amount)], ['Scenario projected cost', currency(result.scenario_projected_cost)], ['Forecast impact', `${result.impact_pct.toFixed(2)}%`]].map(([label, value]) => <div className="rounded-lg bg-white p-4" key={label}><p className="text-sm font-medium text-slate-500">{label}</p><p className="mt-2 text-xl font-semibold text-slate-900">{value}</p></div>)}</div><p className="mt-5 text-sm font-medium text-slate-700">{result.disclaimer}</p></article>}
  </section>
}
