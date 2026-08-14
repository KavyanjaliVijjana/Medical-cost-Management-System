import type { ReactNode } from 'react'
import type { HealthStatus } from '../../types/api'

export type NavigationItem = 'Dashboard' | 'Executive report' | 'Data upload' | 'Analytics' | 'Forecast' | 'Insights' | 'Scenario' | 'Advisor'

type AppShellProps = {
  activeItem: NavigationItem
  onNavigate: (item: NavigationItem) => void
  health: HealthStatus | null
  healthError: string | null
  userName: string
  children: ReactNode
}

const navigation: Array<{ label: NavigationItem; icon: string }> = [
  { label: 'Dashboard', icon: '▦' },
  { label: 'Data upload', icon: '↑' },
  { label: 'Analytics', icon: '◫' },
  { label: 'Forecast', icon: '↗' },
  { label: 'Insights', icon: '◉' },
  { label: 'Scenario', icon: 'S' },
  { label: 'Executive report', icon: 'R' },
  { label: 'Advisor', icon: 'A' },
]

export function AppShell({ activeItem, onNavigate, health, healthError, userName, children }: AppShellProps) {
  const connected = Boolean(health && !healthError)

  return (
    <div className="min-h-screen bg-mist text-slate-800">
      <aside className="fixed inset-y-0 left-0 flex w-64 flex-col bg-navy-dark px-4 py-6 text-slate-100">
        <div className="mb-10 px-3">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-200">Medical economics</p>
          <h1 className="mt-2 text-lg font-semibold leading-tight">Cost Management</h1>
        </div>
        <nav className="space-y-1" aria-label="Primary navigation">
          {navigation.map((item) => (
            <button
              className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition ${
                activeItem === item.label ? 'bg-white/15 font-semibold text-white' : 'text-slate-300 hover:bg-white/10 hover:text-white'
              }`}
              key={item.label}
              onClick={() => onNavigate(item.label)}
              type="button"
            >
              <span aria-hidden="true" className="w-4 text-center text-cyan-200">{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>
        <div className="mt-auto space-y-4 px-3">
          <div className="border-t border-white/10 pt-4 text-xs text-slate-300">
            <p className="font-medium text-slate-100">{userName}</p>
            <p className="mt-1">Demo workspace</p>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <span className={`h-2 w-2 rounded-full ${connected ? 'bg-emerald-400' : healthError ? 'bg-rose-400' : 'bg-amber-300'}`} />
            <span>{connected ? 'Backend connected' : healthError ? 'Backend unavailable' : 'Checking backend…'}</span>
          </div>
        </div>
      </aside>
      <main className="ml-64 min-h-screen">{children}</main>
    </div>
  )
}
