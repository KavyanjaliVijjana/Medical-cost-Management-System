import type { NavigationItem } from '../components/layout/AppShell'

type PlaceholderPageProps = { section: Exclude<NavigationItem, 'Dashboard' | 'Executive report' | 'Data upload' | 'Analytics' | 'Forecast' | 'Insights' | 'Scenario' | 'Advisor'> }

const descriptions: Record<PlaceholderPageProps['section'], string> = {
  Analytics: 'Historical analytics are available on the dashboard. This dedicated workspace remains planned for a later phase.',
}

export function PlaceholderPage({ section }: PlaceholderPageProps) {
  return (
    <section className="max-w-3xl">
      <p className="text-sm font-medium text-teal">Planned capability</p>
      <h2 className="mt-1 text-3xl font-semibold tracking-tight text-slate-900">{section}</h2>
      <div className="mt-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm leading-6 text-slate-600">{descriptions[section]}</p>
      </div>
    </section>
  )
}
