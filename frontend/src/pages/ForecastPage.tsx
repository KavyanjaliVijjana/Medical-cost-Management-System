import { useEffect, useMemo, useState } from 'react'
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { api } from '../api/client'
import type { Dataset, ForecastRun } from '../types/api'

const horizons = [1, 3, 6, 12]

function currency(value: number | null) {
  return value === null ? '—' : new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value)
}

function metric(value: number | null, decimals = 2) {
  return value === null ? 'Not applicable' : value.toFixed(decimals)
}

function monthLabel(value: string) {
  const [year, month] = value.split('-').map(Number)
  return new Intl.DateTimeFormat('en-US', { month: 'short', year: 'numeric' }).format(new Date(year, month - 1, 1))
}

export function ForecastPage({ selectedDatasetId, onDatasetChange }: { selectedDatasetId: number | null; onDatasetChange: (datasetId: number) => void }) {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [horizon, setHorizon] = useState(3)
  const [forecast, setForecast] = useState<ForecastRun | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isRunning, setIsRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    api.listDatasets().then((available) => {
      if (!active) return
      setDatasets(available)
      if (available.length > 0 && !available.some((dataset) => dataset.id === selectedDatasetId)) onDatasetChange(available[0].id)
      setIsLoading(false)
    }).catch((loadError: unknown) => {
      if (active) {
        setError(loadError instanceof Error ? loadError.message : 'Could not load processed datasets.')
        setIsLoading(false)
      }
    })
    return () => { active = false }
  }, [onDatasetChange, selectedDatasetId])

  const chartData = useMemo(() => {
    if (!forecast) return []
    return [
      ...forecast.historical_monthly_cost.map((point) => ({ month: point.month.slice(0, 7), historical: point.total_cost, forecast: null as number | null })),
      ...forecast.forecast_points.map((point, index) => ({
        month: point.forecast_month.slice(0, 7),
        historical: index === 0 ? forecast.historical_monthly_cost[forecast.historical_monthly_cost.length - 1]?.total_cost ?? null : null,
        forecast: point.predicted_cost,
      })),
    ]
  }, [forecast])

  async function runForecast() {
    if (selectedDatasetId === null) return
    setIsRunning(true)
    setError(null)
    try {
      setForecast(await api.createForecast(selectedDatasetId, horizon))
    } catch (runError) {
      setForecast(null)
      setError(runError instanceof Error ? runError.message : 'Could not generate forecast.')
    } finally {
      setIsRunning(false)
    }
  }

  return (
    <section className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div><p className="text-sm font-medium text-teal">Explainable baseline</p><h2 className="mt-1 text-3xl font-semibold tracking-tight text-slate-900">Medical cost forecast</h2><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">Monthly total cost forecast using a chronological Linear Regression baseline.</p></div>
        <div className="flex flex-wrap gap-3">
          <label className="text-sm font-medium text-slate-700">Dataset<select className="mt-1 block min-w-56 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm" disabled={datasets.length === 0} onChange={(event) => onDatasetChange(Number(event.target.value))} value={selectedDatasetId ?? ''}>{datasets.length === 0 ? <option value="">No processed datasets</option> : datasets.map((dataset) => <option key={dataset.id} value={dataset.id}>{dataset.name}{dataset.is_synthetic ? ' (Synthetic Demo Dataset)' : ''}</option>)}</select></label>
          <label className="text-sm font-medium text-slate-700">Horizon<select className="mt-1 block rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm" onChange={(event) => setHorizon(Number(event.target.value))} value={horizon}>{horizons.map((months) => <option key={months} value={months}>{months} month{months > 1 ? 's' : ''}</option>)}</select></label>
          <button className="mt-6 rounded-lg bg-navy px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50" disabled={selectedDatasetId === null || isRunning || isLoading} onClick={runForecast} type="button">{isRunning ? 'Generating…' : 'Generate forecast'}</button>
        </div>
      </header>
      {isLoading && <p className="rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-600">Loading processed datasets…</p>}
      {error && <p className="rounded-lg bg-rose-50 p-4 text-sm text-rose-700">{error}</p>}
      {!isLoading && datasets.length === 0 && <article className="rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center"><h3 className="font-semibold text-slate-800">No processed dataset available</h3><p className="mt-2 text-sm text-slate-600">Process a validated CSV or the Synthetic Demo Dataset before forecasting.</p></article>}
      {forecast && <>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {[['Forecast horizon', `${forecast.horizon_months} month${forecast.horizon_months > 1 ? 's' : ''}`], ['Expected change', forecast.expected_change_pct === null ? '—' : `${forecast.expected_change_pct >= 0 ? '+' : ''}${forecast.expected_change_pct.toFixed(1)}%`], ['MAE', currency(forecast.mae)], ['RMSE', currency(forecast.rmse)]].map(([label, value]) => <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm" key={label}><p className="text-sm font-medium text-slate-500">{label}</p><p className="mt-3 text-xl font-semibold text-slate-900">{value}</p></article>)}
        </div>
        <article className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex flex-wrap items-start justify-between gap-4"><div><h3 className="text-base font-semibold text-slate-900">Historical cost and forecast</h3><p className="mt-1 text-sm text-slate-600">Solid teal is historical monthly cost; dashed navy is future forecast.</p></div><div className="text-right text-xs text-slate-500"><p>{forecast.model_name}</p><p className="mt-1">R²: {metric(forecast.r_squared, 4)}</p></div></div><div className="mt-6 h-80"><ResponsiveContainer height="100%" width="100%"><LineChart data={chartData} margin={{ top: 8, right: 18, left: 8, bottom: 0 }}><CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" vertical={false} /><XAxis dataKey="month" fontSize={12} tickFormatter={monthLabel} tickLine={false} axisLine={false} /><YAxis fontSize={12} tickFormatter={(value) => `$${Math.round(value / 1000)}k`} tickLine={false} axisLine={false} width={50} /><Tooltip formatter={(value: number) => currency(value)} labelFormatter={monthLabel} /><Legend /><Line connectNulls dataKey="historical" dot={{ r: 3 }} name="Historical cost" stroke="#0f766e" strokeWidth={2.5} type="monotone" /><Line connectNulls dataKey="forecast" dot={{ r: 3 }} name="Forecast cost" stroke="#0f3d5c" strokeDasharray="7 5" strokeWidth={2.5} type="monotone" /></LineChart></ResponsiveContainer></div></article>
        <article className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div><h3 className="text-base font-semibold text-slate-900">Chronological holdout comparison</h3><p className="mt-1 text-sm text-slate-600">Both baselines use the same final historical months. Lower error is better.</p></div>
            <span className="rounded-full bg-cyan-50 px-3 py-1.5 text-xs font-semibold text-teal">Better baseline: {forecast.model_comparison.better_model}</span>
          </div>
          <div className="mt-5 grid gap-4 md:grid-cols-2">
            {[forecast.model_comparison.linear_regression, forecast.model_comparison.naive_last_observed].map((comparison) => <div className="rounded-lg bg-slate-50 p-4" key={comparison.model_name}><p className="font-semibold text-slate-800">{comparison.model_name}</p><p className="mt-2 text-sm text-slate-600">MAE: <span className="font-medium text-slate-900">{currency(comparison.mae)}</span></p><p className="mt-1 text-sm text-slate-600">RMSE: <span className="font-medium text-slate-900">{currency(comparison.rmse)}</span></p>{comparison.r_squared !== null && <p className="mt-1 text-sm text-slate-600">R²: <span className="font-medium text-slate-900">{metric(comparison.r_squared, 4)}</span></p>}</div>)}
          </div>
        </article>
        <article className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"><h3 className="text-base font-semibold text-slate-900">Forecast monthly values</h3><div className="mt-4 overflow-x-auto"><table className="min-w-full text-left text-sm"><thead className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500"><tr><th className="pb-3 pr-6">Month</th><th className="pb-3">Predicted medical cost</th></tr></thead><tbody className="divide-y divide-slate-100">{forecast.forecast_points.map((point) => <tr key={point.forecast_month}><td className="py-3 pr-6 font-medium text-slate-800">{monthLabel(point.forecast_month.slice(0, 7))}</td><td className="py-3 text-slate-700">{currency(point.predicted_cost)}</td></tr>)}</tbody></table></div></article>
      </>}
    </section>
  )
}
