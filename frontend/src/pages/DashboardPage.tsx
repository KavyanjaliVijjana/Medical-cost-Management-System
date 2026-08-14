import { useEffect, useState } from 'react'
import { Area, AreaChart, Bar, BarChart, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { api } from '../api/client'
import type { AnalyticsSummary, CostAlert, Dataset, DriverInsight, ForecastRun, Recommendation, ScenarioResult } from '../types/api'

type DashboardPageProps = {
  selectedDatasetId: number | null
  onDatasetChange: (datasetId: number) => void
}

const chartColors = ['#0f766e', '#0f3d5c', '#38bdf8', '#7c3aed', '#f59e0b', '#e11d48']

function currency(value: number | null) {
  return value === null ? '—' : new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value)
}

function number(value: number | null) {
  return value === null ? '—' : new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(value)
}

function percentage(value: number | null) {
  return value === null ? 'No prior month' : `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`
}

function monthLabel(value: string) {
  const [year, month] = value.split('-').map(Number)
  return new Intl.DateTimeFormat('en-US', { month: 'short', year: 'numeric' }).format(new Date(year, month - 1, 1))
}

function MetricCard({ label, value, supportingText }: { label: string; value: string; supportingText?: string }) {
  return (
    <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-sm font-medium text-slate-500">{label}</p>
      <p className="mt-3 text-2xl font-semibold tracking-tight text-slate-900">{value}</p>
      {supportingText && <p className="mt-2 text-xs text-slate-500">{supportingText}</p>}
    </article>
  )
}

type BusinessStory = {
  forecast: ForecastRun | null
  driver: DriverInsight | null
  alert: CostAlert | null
  recommendation: Recommendation | null
  scenario: ScenarioResult | null
}

function StoryStep({ label, value, detail, tone = 'slate' }: { label: string; value: string; detail: string; tone?: 'slate' | 'teal' | 'amber' }) {
  const styles = tone === 'amber' ? 'border-amber-200 bg-amber-50' : tone === 'teal' ? 'border-cyan-200 bg-cyan-50' : 'border-slate-200 bg-slate-50'
  return <div className={`rounded-lg border p-4 ${styles}`}><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p><p className="mt-2 text-sm font-semibold text-slate-900">{value}</p><p className="mt-1 text-xs leading-5 text-slate-600">{detail}</p></div>
}

export function DashboardPage({ selectedDatasetId, onDatasetChange }: DashboardPageProps) {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null)
  const [story, setStory] = useState<BusinessStory | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    api.listDatasets()
      .then((availableDatasets) => {
        if (!active) return
        setDatasets(availableDatasets)
        if (availableDatasets.length > 0 && !availableDatasets.some((dataset) => dataset.id === selectedDatasetId)) {
          onDatasetChange(availableDatasets[0].id)
        }
        if (availableDatasets.length === 0) setIsLoading(false)
      })
      .catch((loadError: unknown) => {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : 'Could not load datasets.')
          setIsLoading(false)
        }
      })
    return () => { active = false }
  }, [selectedDatasetId, onDatasetChange])

  useEffect(() => {
    if (selectedDatasetId === null) return
    let active = true
    setIsLoading(true)
    setError(null)
    api.getAnalyticsSummary(selectedDatasetId)
      .then((analytics) => {
        if (active) setSummary(analytics)
      })
      .catch((loadError: unknown) => {
        if (active) setError(loadError instanceof Error ? loadError.message : 'Could not load analytics.')
      })
      .finally(() => { if (active) setIsLoading(false) })
    return () => { active = false }
  }, [selectedDatasetId])

  useEffect(() => {
    if (selectedDatasetId === null) { setStory(null); return }
    let active = true
    Promise.all([
      api.getLatestForecast(selectedDatasetId).catch(() => null),
      api.getDrivers(selectedDatasetId),
      api.getAlerts(selectedDatasetId),
      api.getRecommendations(selectedDatasetId),
      api.getLatestScenario(selectedDatasetId).catch(() => null),
    ]).then(([forecast, drivers, alerts, recommendations, scenario]) => {
      if (active) setStory({ forecast, driver: drivers.find((item) => item.metric === 'Department cost contribution') ?? drivers[0] ?? null, alert: alerts[0] ?? null, recommendation: recommendations[0] ?? null, scenario })
    }).catch(() => { if (active) setStory(null) })
    return () => { active = false }
  }, [selectedDatasetId])

  const selectedDataset = datasets.find((dataset) => dataset.id === selectedDatasetId)

  return (
    <section className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-teal">Historical analytics</p>
          <h2 className="mt-1 text-3xl font-semibold tracking-tight text-slate-900">Medical cost dashboard</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">Actual historical medical-cost metrics from processed datasets.</p>
        </div>
        <label className="block text-sm font-medium text-slate-700">
          Dataset
          <select
            className="mt-1 block min-w-64 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 shadow-sm"
            disabled={datasets.length === 0}
            onChange={(event) => onDatasetChange(Number(event.target.value))}
            value={selectedDatasetId ?? ''}
          >
            {datasets.length === 0 ? <option value="">No processed datasets</option> : datasets.map((dataset) => <option key={dataset.id} value={dataset.id}>{dataset.name}{dataset.is_synthetic ? ' (Synthetic Demo Dataset)' : ''}</option>)}
          </select>
        </label>
      </header>

      {error && <p className="rounded-lg bg-rose-50 p-4 text-sm text-rose-700">{error}</p>}
      {!isLoading && !error && !summary && (
        <article className="rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center">
          <h3 className="text-base font-semibold text-slate-800">No processed dataset available</h3>
          <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-600">Use Data upload to load the Synthetic Demo Dataset or process a validated CSV. Analytics appear only after records are stored.</p>
        </article>
      )}
      {isLoading && selectedDatasetId !== null && <p className="rounded-xl border border-slate-200 bg-white p-6 text-sm text-slate-600">Loading analytics…</p>}

      {summary && !isLoading && (
        <>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <MetricCard label="Total cost" value={currency(summary.metrics.total_medical_cost)} supportingText={`${number(summary.metrics.average_monthly_cost)} average per month`} />
            <MetricCard label="Total patients" value={number(summary.metrics.total_patient_count)} supportingText={`${number(summary.metrics.average_monthly_patient_count)} average per month`} />
            <MetricCard label="Cost per patient" value={currency(summary.metrics.cost_per_patient)} supportingText="Across all processed records" />
            <MetricCard label="Latest monthly cost" value={currency(summary.metrics.latest_month_cost)} supportingText={summary.metrics.latest_month ? `${monthLabel(summary.metrics.latest_month)} · ${percentage(summary.metrics.month_over_month_cost_change_pct)} vs prior month` : 'No monthly records'} />
          </div>

          <article className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex flex-wrap items-start justify-between gap-3"><div><h3 className="text-base font-semibold text-slate-900">Cost-containment story</h3><p className="mt-1 text-sm text-slate-600">Historical evidence flows through the latest persisted forecast, insights, recommendation, and optional scenario.</p></div><span className="rounded-full bg-cyan-50 px-3 py-1.5 text-xs font-semibold text-teal">Selected dataset evidence</span></div>
            <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-6">
              <StoryStep label="Historical cost" value={currency(summary.metrics.total_medical_cost)} detail={`${summary.monthly_trend.length} monthly observations`} tone="teal" />
              <StoryStep label="Forecast" value={story?.forecast ? currency(story.forecast.forecast_points.reduce((total, point) => total + point.predicted_cost, 0)) : 'Not generated'} detail={story?.forecast ? `${story.forecast.horizon_months}-month projected total` : 'Generate a forecast to continue'} />
              <StoryStep label="Top driver" value={story?.driver?.metric ?? 'Not generated'} detail={story?.driver?.explanation ?? 'Generate insights to continue'} />
              <StoryStep label="Active alert" value={story?.alert ? `${story.alert.severity.toUpperCase()}: ${story.alert.metric}` : 'No active alert'} detail={story?.alert?.explanation ?? 'No alert evidence is available'} tone={story?.alert ? 'amber' : 'slate'} />
              <StoryStep label="Recommendation" value={story?.recommendation?.title ?? 'Not generated'} detail={story?.recommendation?.rationale ?? 'Generate recommendations when evidence exists'} tone="teal" />
              <StoryStep label="Scenario" value={story?.scenario ? currency(story.scenario.scenario_projected_cost) : 'Not calculated'} detail={story?.scenario ? `${story.scenario.department}: hypothetical estimate only` : 'Run a department reduction scenario'} tone="teal" />
            </div>
          </article>

          <div className="grid gap-6 xl:grid-cols-[minmax(0,1.6fr)_minmax(20rem,1fr)]">
            <article className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-start justify-between gap-4">
                <div><h3 className="text-base font-semibold text-slate-900">Monthly cost trend</h3><p className="mt-1 text-sm text-slate-600">Chronological monthly aggregation of total medical cost.</p></div>
                <span className="text-xs font-medium text-slate-500">{summary.monthly_trend.length} months</span>
              </div>
              <div className="mt-6 h-72">
                <ResponsiveContainer height="100%" width="100%">
                  <AreaChart data={summary.monthly_trend} margin={{ top: 8, right: 12, left: 12, bottom: 0 }}>
                    <defs><linearGradient id="costArea" x1="0" x2="0" y1="0" y2="1"><stop offset="5%" stopColor="#0f766e" stopOpacity={0.24} /><stop offset="95%" stopColor="#0f766e" stopOpacity={0} /></linearGradient></defs>
                    <XAxis dataKey="month" fontSize={12} tickFormatter={monthLabel} tickLine={false} axisLine={false} />
                    <YAxis fontSize={12} tickFormatter={(value) => `$${Math.round(value / 1000)}k`} tickLine={false} axisLine={false} width={48} />
                    <Tooltip formatter={(value: number) => currency(value)} labelFormatter={monthLabel} />
                    <Area dataKey="total_cost" fill="url(#costArea)" name="Total cost" stroke="#0f766e" strokeWidth={2.5} type="monotone" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </article>

            <article className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
              <h3 className="text-base font-semibold text-slate-900">Department contribution</h3>
              <p className="mt-1 text-sm text-slate-600">Share of total cost by department.</p>
              <div className="mt-3 h-48">
                <ResponsiveContainer height="100%" width="100%">
                  <PieChart><Pie data={summary.departments} dataKey="total_cost" innerRadius={45} outerRadius={72} paddingAngle={2}>{summary.departments.map((department, index) => <Cell fill={chartColors[index % chartColors.length]} key={department.department} />)}</Pie><Tooltip formatter={(value: number) => currency(value)} /></PieChart>
                </ResponsiveContainer>
              </div>
              <div className="space-y-2">
                {summary.departments.map((department, index) => <div className="flex items-center justify-between gap-2 text-sm" key={department.department}><span className="flex min-w-0 items-center gap-2 text-slate-700"><span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ backgroundColor: chartColors[index % chartColors.length] }} /> <span className="truncate">{department.department}</span></span><span className="font-medium text-slate-900">{department.contribution_pct?.toFixed(1) ?? '—'}%</span></div>)}
              </div>
            </article>
          </div>

          <article className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex flex-wrap items-start justify-between gap-3"><div><h3 className="text-base font-semibold text-slate-900">Department cost breakdown</h3><p className="mt-1 text-sm text-slate-600">Total cost, patient count, cost per patient, and contribution from stored records.</p></div>{summary.highest_cost_department && <p className="rounded-full bg-cyan-50 px-3 py-1.5 text-xs font-semibold text-teal">Highest cost: {summary.highest_cost_department.department}</p>}</div>
            <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1.4fr)_minmax(22rem,1fr)]">
              <div className="h-72"><ResponsiveContainer height="100%" width="100%"><BarChart data={summary.departments} layout="vertical" margin={{ top: 4, right: 18, left: 20, bottom: 4 }}><XAxis type="number" hide /><YAxis dataKey="department" type="category" fontSize={12} tickLine={false} axisLine={false} width={95} /><Tooltip formatter={(value: number) => currency(value)} /><Bar dataKey="total_cost" fill="#0f3d5c" name="Total cost" radius={[0, 4, 4, 0]} /></BarChart></ResponsiveContainer></div>
              <div className="overflow-x-auto"><table className="min-w-full text-left text-sm"><thead className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500"><tr><th className="pb-3 pr-4 font-semibold">Department</th><th className="pb-3 pr-4 font-semibold">Cost</th><th className="pb-3 pr-4 font-semibold">Patients</th><th className="pb-3 font-semibold">Cost/patient</th></tr></thead><tbody className="divide-y divide-slate-100">{summary.departments.map((department) => <tr key={department.department}><td className="py-3 pr-4 font-medium text-slate-800">{department.department}</td><td className="py-3 pr-4 text-slate-600">{currency(department.total_cost)}</td><td className="py-3 pr-4 text-slate-600">{number(department.patient_count)}</td><td className="py-3 text-slate-600">{currency(department.cost_per_patient)}</td></tr>)}</tbody></table></div>
            </div>
          </article>
        </>
      )}
      {selectedDataset && summary && <p className="text-xs text-slate-500">Dataset: {selectedDataset.name} · {selectedDataset.row_count} stored records · {selectedDataset.is_synthetic ? 'Synthetic Demo Dataset' : 'Uploaded dataset'}</p>}
    </section>
  )
}
