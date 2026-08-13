import type { AnalyticsSummary, Dataset, DatasetPreviewResponse, DatasetValidationResponse, DemoUser, HealthStatus } from '../types/api'

const baseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const isFormData = init?.body instanceof FormData
  const response = await fetch(`${baseUrl}${path}`, {
    headers: { ...(isFormData ? {} : { 'Content-Type': 'application/json' }), ...init?.headers },
    ...init,
  })

  if (!response.ok) {
    const payload = await response.json().catch(() => null) as { detail?: string } | null
    throw new Error(payload?.detail ?? `Request failed (${response.status})`)
  }

  return response.json() as Promise<T>
}

export const api = {
  getHealth: () => request<HealthStatus>('/health'),
  demoLogin: () => request<DemoUser>('/auth/demo-login', {
    method: 'POST',
    body: JSON.stringify({ email: 'demo@medicalcost.local' }),
  }),
  validateDataset: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return request<DatasetValidationResponse>('/datasets/validate', { method: 'POST', body: formData })
  },
  validateDemoDataset: () => request<DatasetValidationResponse>('/datasets/demo/validate', { method: 'POST' }),
  processDataset: (datasetId: number) => request<Dataset>(`/datasets/${datasetId}/process`, { method: 'POST' }),
  getDatasetPreview: (datasetId: number) => request<DatasetPreviewResponse>(`/datasets/${datasetId}/preview`),
  listDatasets: () => request<Dataset[]>('/datasets'),
  getAnalyticsSummary: (datasetId: number) => request<AnalyticsSummary>(`/analytics/datasets/${datasetId}/summary`),
}
