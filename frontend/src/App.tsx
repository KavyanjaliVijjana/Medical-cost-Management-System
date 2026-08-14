import { useCallback, useEffect, useState } from 'react'

import { api } from './api/client'
import { AppShell, type NavigationItem } from './components/layout/AppShell'
import { AuthPage } from './pages/AuthPage'
import { AdvisorPage } from './pages/AdvisorPage'
import { DashboardPage } from './pages/DashboardPage'
import { DataUploadPage } from './pages/DataUploadPage'
import { ExecutiveReportPage } from './pages/ExecutiveReportPage'
import { ForecastPage } from './pages/ForecastPage'
import { InsightsPage } from './pages/InsightsPage'
import { PlaceholderPage } from './pages/PlaceholderPage'
import { ProfilePage } from './pages/ProfilePage'
import { ScenarioPage } from './pages/ScenarioPage'
import type { ApplicationUser, AuthenticationResponse, HealthStatus } from './types/api'

const sessionUserKey = 'medical-cost-current-user'
const storedDatasetKey = 'medical-cost-selected-dataset'

function savedSessionUser(): ApplicationUser | null {
  const saved = window.sessionStorage.getItem(sessionUserKey)
  if (!api.hasAccessToken()) return null
  try {
    return saved ? JSON.parse(saved) as ApplicationUser : null
  } catch {
    return null
  }
}

export default function App() {
  const [user, setUser] = useState<ApplicationUser | null>(savedSessionUser)
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

  const logout = useCallback(() => {
    void api.logout().catch(() => undefined)
    api.clearAccessToken()
    window.sessionStorage.removeItem(sessionUserKey)
    setUser(null)
    setActiveItem('Dashboard')
  }, [])

  const saveUser = useCallback((authenticatedUser: AuthenticationResponse) => {
    const { access_token, ...applicationUser } = authenticatedUser
    api.setAccessToken(access_token)
    window.sessionStorage.setItem(sessionUserKey, JSON.stringify(applicationUser))
    setUser(applicationUser)
  }, [])

  const saveProfileUser = useCallback((updatedUser: ApplicationUser) => {
    window.sessionStorage.setItem(sessionUserKey, JSON.stringify(updatedUser))
    setUser(updatedUser)
  }, [])

  if (!user) return <AuthPage onAuthenticated={saveUser} />

  return (
    <AppShell activeItem={activeItem} health={health} healthError={healthError} onLogout={logout} onNavigate={setActiveItem} userName={user.display_name}>
      <div className="mx-auto max-w-7xl px-8 py-10">
        {activeItem === 'Dashboard'
          ? <DashboardPage mode="dashboard" onDatasetChange={selectDataset} selectedDatasetId={selectedDatasetId} />
          : activeItem === 'Analytics'
            ? <DashboardPage mode="analytics" onDatasetChange={selectDataset} selectedDatasetId={selectedDatasetId} />
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
                      : activeItem === 'Advisor'
                        ? <AdvisorPage onDatasetChange={selectDataset} selectedDatasetId={selectedDatasetId} />
                        : activeItem === 'Profile'
                          ? <ProfilePage onLogout={logout} onUserUpdated={saveProfileUser} user={user} />
                          : <PlaceholderPage section={activeItem} />}
      </div>
    </AppShell>
  )
}
