import { useEffect, useState } from 'react'

import { api } from '../api/client'
import type { AnalyticsSummary, CostAlert, Dataset, DriverInsight, ForecastRun, Recommendation, ScenarioResult } from '../types/api'

type ReportData = {
  analytics: AnalyticsSummary
  forecast: ForecastRun | null
  drivers: DriverInsight[]
  alerts: CostAlert[]
  recommendations: Recommendation[]
  scenario: ScenarioResult | null
}

const currency = (value: number | null) => value === null ? 'Not available' : new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value)
const number = (value: number | null) => value === null ? 'Not available' : new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(value)
const percent = (value: number | null) => value === null ? 'No prior month' : `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`

export function ExecutiveReportPage({ selectedDatasetId, onDatasetChange }: { selectedDatasetId: number | null; onDatasetChange: (datasetId: number) => void }) {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [report, setReport] = useState<ReportData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let active = true
    async function load() {
      setIsLoading(true)
      setError(null)
      try {
        const available = await api.listDatasets()
        if (!active) return
        setDatasets(available)
        const datasetId = available.some((item) => item.id === selectedDatasetId) ? selectedDatasetId : available[0]?.id
        if (!datasetId) { setReport(null); return }
        if (datasetId !== selectedDatasetId) onDatasetChange(datasetId)
        const [analytics, forecast, drivers, alerts, recommendations, scenario] = await Promise.all([
          api.getAnalyticsSummary(datasetId),
          api.getLatestForecast(datasetId).catch(() => null),
          api.getDrivers(datasetId),
          api.getAlerts(datasetId),
          api.getRecommendations(datasetId),
          api.getLatestScenario(datasetId).catch(() => null),
        ])
        const topDriver = drivers.find((item) => item.metric === 'Department cost contribution') ?? drivers[0]
        if (active) setReport({ analytics, forecast, drivers: topDriver ? [topDriver] : [], alerts, recommendations, scenario })
      } catch (loadError) {
        if (active) setError(loadError instanceof Error ? loadError.message : 'Could not assemble the executive report.')
      } finally {
        if (active) setIsLoading(false)
      }
    }
    void load()
    return () => { active = false }
  }, [onDatasetChange, selectedDatasetId])

  return <section className="space-y-6">
    <header className="flex flex-wrap items-end justify-between gap-4"><div><p className="text-sm font-medium text-teal">Decision-ready evidence</p><h2 className="mt-1 text-3xl font-semibold tracking-tight text-slate-900">Executive cost report</h2><p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">A concise view assembled from the selected dataset's stored analytics, forecast, insights, recommendation, and scenario results.</p></div><label className="text-sm font-medium text-slate-700">Dataset<select className="mt-1 block min-w-64 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm" value={selectedDatasetId ?? ''} onChange={(event) => onDatasetChange(Number(event.target.value))}>{datasets.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label></header>
    {isLoading && <p className="rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-600">Assembling report from stored results...</p>}
    {error && <p className="rounded-lg bg-rose-50 p-4 text-sm text-rose-700">{error}</p>}
    {!isLoading && !error && !report && <p className="rounded-xl border border-dashed border-slate-300 bg-white p-6 text-sm text-slate-600">No processed dataset is available for a report.</p>}
    {report && <>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">{[['Total medical cost', currency(report.analytics.metrics.total_medical_cost)], ['Patient volume', number(report.analytics.metrics.total_patient_count)], ['Cost per patient', currency(report.analytics.metrics.cost_per_patient)], ['Latest monthly change', percent(report.analytics.metrics.month_over_month_cost_change_pct)]].map(([label, value]) => <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm" key={label}><p className="text-sm font-medium text-slate-500">{label}</p><p className="mt-3 text-2xl font-semibold text-slate-900">{value}</p></article>)}</div>
      <article className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"><h3 className="text-base font-semibold text-slate-900">Executive summary</h3><div className="mt-4 grid gap-4 lg:grid-cols-2"><ReportBlock title="Historical trend" text={`${report.analytics.monthly_trend.length} monthly observations. Latest monthly cost is ${currency(report.analytics.metrics.latest_month_cost)} (${percent(report.analytics.metrics.month_over_month_cost_change_pct)} versus the prior month).`} /><ReportBlock title="Forecast" text={report.forecast ? `${report.forecast.model_name}: ${report.forecast.horizon_months}-month projected total of ${currency(report.forecast.forecast_points.reduce((sum, point) => sum + point.predicted_cost, 0))}. MAE ${currency(report.forecast.mae)}; RMSE ${currency(report.forecast.rmse)}.` : 'No persisted forecast is available for this dataset.'} /><ReportBlock title="Top cost driver" text={report.drivers[0] ? report.drivers[0].explanation : 'No driver insight has been generated for this dataset.'} /><ReportBlock title="Active cost-pressure alert" text={report.alerts[0] ? `${report.alerts[0].severity.toUpperCase()}: ${report.alerts[0].explanation}` : 'No active alert is available for this dataset.'} /><ReportBlock title="Recommendation" text={report.recommendations[0] ? `${report.recommendations[0].title}: ${report.recommendations[0].rationale}` : 'No evidence-based recommendation is available for this dataset.'} /><ReportBlock title="Scenario" text={report.scenario ? `${report.scenario.department} at ${report.scenario.reduction_pct.toFixed(1)}%: projected cost ${currency(report.scenario.scenario_projected_cost)}; estimated reduction ${currency(report.scenario.estimated_reduction_amount)}. Hypothetical estimate only.` : 'No saved scenario is available for this dataset.'} /></div></article>
      <article className="rounded-xl border border-cyan-200 bg-cyan-50 p-6"><h3 className="text-base font-semibold text-slate-900">Business story</h3><p className="mt-2 text-sm leading-6 text-slate-700">Historical Cost - Forecast - Drivers - Alerts - Recommendations - Scenario. Each item above is based on persisted application results for the selected dataset; scenario outputs are not guaranteed savings.</p></article>
    </>}
  </section>
}

function ReportBlock({ title, text }: { title: string; text: string }) {
  return <div className="rounded-lg bg-slate-50 p-4"><p className="text-sm font-semibold text-slate-900">{title}</p><p className="mt-2 text-sm leading-6 text-slate-600">{text}</p></div>
}
