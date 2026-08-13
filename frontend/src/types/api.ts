export type HealthStatus = {
  status: 'ok'
  service: string
  environment: string
  database: 'connected'
}

export type DemoUser = {
  id: number
  email: string
  display_name: string
  is_demo: boolean
}

export type ValidationErrorItem = {
  row: number | null
  field: string | null
  code: string
  message: string
}

export type ValidationSummary = {
  total_rows: number
  valid_rows: number
  invalid_rows: number
  duplicate_rows: number
  validation_errors: ValidationErrorItem[]
  is_valid: boolean
}

export type Dataset = {
  id: number
  name: string
  source_type: 'uploaded' | 'synthetic'
  is_synthetic: boolean
  uploaded_at: string
  row_count: number
  processing_status: 'ready' | 'processing' | 'completed' | 'failed'
}

export type DatasetValidationResponse = {
  dataset: Dataset | null
  validation: ValidationSummary
  preview: Array<Record<string, string | number | null>>
}

export type CostRecord = {
  id: number
  dataset_id: number
  record_date: string
  department: string
  patient_count: number
  total_cost: number
  [key: string]: string | number | null
}

export type DatasetPreviewResponse = {
  dataset: Dataset
  records: CostRecord[]
}

export type OverallMetrics = {
  total_medical_cost: number
  total_patient_count: number
  average_monthly_cost: number | null
  average_monthly_patient_count: number | null
  cost_per_patient: number | null
  latest_month: string | null
  latest_month_cost: number | null
  previous_month: string | null
  previous_month_cost: number | null
  month_over_month_cost_change_pct: number | null
}

export type MonthlyTrendPoint = {
  month: string
  total_cost: number
  patient_count: number
  cost_per_patient: number | null
  month_over_month_cost_change_pct: number | null
}

export type DepartmentAnalytics = {
  department: string
  total_cost: number
  patient_count: number
  cost_per_patient: number | null
  contribution_pct: number | null
}

export type AnalyticsSummary = {
  dataset: Dataset
  metrics: OverallMetrics
  monthly_trend: MonthlyTrendPoint[]
  departments: DepartmentAnalytics[]
  highest_cost_department: DepartmentAnalytics | null
}
