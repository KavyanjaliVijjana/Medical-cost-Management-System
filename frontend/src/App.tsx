import { useCallback, useEffect, useState } from 'react'

import { api } from './api/client'
import { AppShell, type NavigationItem } from './components/layout/AppShell'
import { DashboardPage } from './pages/DashboardPage'
import { DataUploadPage } from './pages/DataUploadPage'
import { ForecastPage } from './pages/ForecastPage'
import { InsightsPage } from './pages/InsightsPage'
import { ExecutiveReportPage } from './pages/ExecutiveReportPage'
import { ScenarioPage } from './pages/ScenarioPage'
import { PlaceholderPage } from './pages/PlaceholderPage'
import type { DemoUser, HealthStatus } from './types/api'

const storedUserKey = 'medical-cost-demo-user'
const storedDatasetKey = 'medical-cost-selected-dataset'

function LoginScreen({ onLogin }: { onLogin: (user: DemoUser) => void }) {
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  async function handleLogin() {
    setIsLoading(true)
    setError(null)
    try {
      const user = await api.demoLogin()
      window.localStorage.setItem(storedUserKey, JSON.stringify(user))
      onLogin(user)
    } catch (loginError) {
      setError(loginError instanceof Error ? loginError.message : 'Unable to reach the demo workspace.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-mist p-6">
      <section className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-teal">Medical economics</p>
        <h1 className="mt-3 text-2xl font-semibold tracking-tight text-slate-900">Cost Management</h1>
        <p className="mt-3 text-sm leading-6 text-slate-600">Access the seeded hackathon demo workspace.</p>
        <button
          className="mt-7 w-full rounded-lg bg-navy px-4 py-3 text-sm font-semibold text-white transition hover:bg-navy-dark disabled:cursor-not-allowed disabled:opacity-60"
          disabled={isLoading}
          onClick={handleLogin}
          type="button"
        >
          {isLoading ? 'Opening workspace…' : 'Continue as demo user'}
        </button>
        {error && <p className="mt-4 rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}
      </section>
    </main>
  )
}

export default function App() {
  const [user, setUser] = useState<DemoUser | null>(() => {
    const saved = window.localStorage.getItem(storedUserKey)
    return saved ? JSON.parse(saved) as DemoUser : null
  })
  const [activeItem, setActiveItem] = useState<NavigationItem>('Dashboard')
  const [selectedDatasetId, setSelectedDatasetId] = useState<number | null>(() => {
    const saved = window.localStorage.getItem(storedDatasetKey)
    return saved ? Number(saved) : null
  })
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [healthError, setHealthError] = useState<string | null>(null)

  useEffect(() => {
    api.getHealth().then(setHealth).catch((error: unknown) => {
      setHealthError(error instanceof Error ? error.message : 'Connection check failed')
    })
  }, [])

  const selectDataset = useCallback((datasetId: number) => {
    window.localStorage.setItem(storedDatasetKey, String(datasetId))
    setSelectedDatasetId(datasetId)
  }, [])

  if (!user) return <LoginScreen onLogin={setUser} />

  return (
    <AppShell
      activeItem={activeItem}
      health={health}
      healthError={healthError}
      onNavigate={setActiveItem}
      userName={user.display_name}
    >
      <div className="mx-auto max-w-7xl px-8 py-10">
        {activeItem === 'Dashboard'
          ? <DashboardPage onDatasetChange={selectDataset} selectedDatasetId={selectedDatasetId} />
          : activeItem === 'Executive report'
            ? <ExecutiveReportPage onDatasetChange={selectDataset} selectedDatasetId={selectedDatasetId} />
          : activeItem === 'Data upload'
            ? <DataUploadPage onDatasetProcessed={(dataset) => selectDataset(dataset.id)} />
            : activeItem === 'Forecast'
              ? <ForecastPage onDatasetChange={selectDataset} selectedDatasetId={selectedDatasetId} />
              : activeItem === 'Insights'
                ? <InsightsPage onDatasetChange={selectDataset} selectedDatasetId={selectedDatasetId} />
                : activeItem === 'Scenario'
                  ? <ScenarioPage onDatasetChange={selectDataset} selectedDatasetId={selectedDatasetId} />
                : <PlaceholderPage section={activeItem} />}
      </div>
    </AppShell>
  )
}
