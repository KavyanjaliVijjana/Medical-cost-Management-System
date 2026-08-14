import { BarChart3, Bot, FileText, LayoutDashboard, Lightbulb, LogOut, SlidersHorizontal, TrendingUp, UploadCloud, UserCircle } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'

import type { HealthStatus } from '../../types/api'

export type NavigationItem = 'Dashboard' | 'Executive report' | 'Data upload' | 'Analytics' | 'Forecast' | 'Insights' | 'Scenario' | 'Advisor' | 'Profile'

type AppShellProps = {
  activeItem: NavigationItem
  onNavigate: (item: NavigationItem) => void
  onLogout: () => void
  health: HealthStatus | null
  healthError: string | null
  userName: string
  children: ReactNode
}

const navigation: Array<{ label: NavigationItem; icon: LucideIcon }> = [
  { label: 'Dashboard', icon: LayoutDashboard },
  { label: 'Data upload', icon: UploadCloud },
  { label: 'Analytics', icon: BarChart3 },
  { label: 'Forecast', icon: TrendingUp },
  { label: 'Insights', icon: Lightbulb },
  { label: 'Scenario', icon: SlidersHorizontal },
  { label: 'Executive report', icon: FileText },
  { label: 'Advisor', icon: Bot },
  { label: 'Profile', icon: UserCircle },
]

export function AppShell({ activeItem, onNavigate, onLogout, health, healthError, userName, children }: AppShellProps) {
  const connected = Boolean(health && !healthError)

  return (
    <div className="min-h-screen bg-mist text-slate-800">
      <aside className="fixed inset-y-0 left-0 flex w-64 flex-col bg-navy-dark px-4 py-6 text-slate-100">
        <div className="mb-10 px-3"><p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-200">Medical economics</p><h1 className="mt-2 text-lg font-semibold leading-tight">Cost Management</h1></div>
        <nav aria-label="Primary navigation" className="space-y-1">
          {navigation.map((item) => {
            const Icon = item.icon
            return <button className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition ${activeItem === item.label ? 'bg-white/15 font-semibold text-white' : 'text-slate-300 hover:bg-white/10 hover:text-white'}`} key={item.label} onClick={() => onNavigate(item.label)} type="button"><Icon aria-hidden="true" className="h-4 w-4 shrink-0 text-cyan-200" />{item.label}</button>
          })}
        </nav>
        <div className="mt-auto space-y-4 px-3">
          <div className="border-t border-white/10 pt-4 text-xs text-slate-300"><button className="font-medium text-slate-100 hover:text-cyan-100" onClick={() => onNavigate('Profile')} type="button">{userName}</button><p className="mt-1">Workspace account</p></div>
          <div className="flex items-center gap-2 text-xs"><span className={`h-2 w-2 rounded-full ${connected ? 'bg-emerald-400' : healthError ? 'bg-rose-400' : 'bg-amber-300'}`} /><span>{connected ? 'Backend connected' : healthError ? 'Backend unavailable' : 'Checking backend…'}</span></div>
          <button className="flex items-center gap-2 text-xs font-medium text-slate-300 hover:text-white" onClick={onLogout} type="button"><LogOut className="h-3.5 w-3.5" />Log out</button>
        </div>
      </aside>
      <main className="ml-64 min-h-screen">{children}</main>
    </div>
  )
}
