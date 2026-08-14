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

export type HistoricalCostPoint = {
  month: string
  total_cost: number
}

export type ForecastPoint = {
  forecast_month: string
  predicted_cost: number
}

export type ForecastModelMetrics = {
  model_name: string
  mae: number | null
  rmse: number | null
  r_squared: number | null
}

export type ForecastModelComparison = {
  linear_regression: ForecastModelMetrics
  naive_last_observed: ForecastModelMetrics
  better_model: string
}

export type ForecastRun = {
  id: number
  dataset_id: number
  horizon_months: number
  model_name: string
  mae: number | null
  rmse: number | null
  r_squared: number | null
  created_at: string
  expected_change_pct: number | null
  model_comparison: ForecastModelComparison
  historical_monthly_cost: HistoricalCostPoint[]
  forecast_points: ForecastPoint[]
  dataset: Dataset
}

export type DriverInsight = {
  id: number
  dataset_id: number
  metric: string
  observed_value: number
  baseline_value: number | null
  change_pct: number | null
  period: string
  explanation: string
  created_at: string
}

export type CostAlert = {
  id: number
  dataset_id: number
  severity: 'medium' | 'high'
  metric: string
  observed_value: number
  threshold_value: number
  period: string
  explanation: string
  status: 'active'
  created_at: string
}

export type Recommendation = {
  id: number
  dataset_id: number
  title: string
  category: string
  priority: 'medium' | 'high'
  rationale: string
  supporting_evidence: string[]
  triggering_metric: string
  period: string
  created_at: string
}

export type ScenarioResult = {
  id: number
  dataset_id: number
  forecast_run_id: number
  department: string
  department_cost_share_pct: number
  reduction_pct: number
  baseline_projected_cost: number
  estimated_reduction_amount: number
  scenario_projected_cost: number
  impact_pct: number
  created_at: string
  disclaimer: string
}
