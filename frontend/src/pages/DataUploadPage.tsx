import { ChangeEvent, useState } from 'react'

import { api } from '../api/client'
import type { Dataset, DatasetValidationResponse } from '../types/api'

type UploadState = 'idle' | 'uploading' | 'validating' | 'ready' | 'processing' | 'completed' | 'failed'

const stateLabels: Record<UploadState, string> = {
  idle: 'Select a CSV or load the synthetic demo dataset.',
  uploading: 'Uploading file…',
  validating: 'Validating required fields and records…',
  ready: 'Validation passed. Review the preview and confirm processing.',
  processing: 'Storing validated records…',
  completed: 'Dataset processing completed.',
  failed: 'Validation or processing failed. Review the details below.',
}

function formatValue(value: string | number | null | undefined) {
  return value === null || value === undefined ? '—' : String(value)
}

export function DataUploadPage({ onDatasetProcessed }: { onDatasetProcessed: (dataset: Dataset) => void }) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadState, setUploadState] = useState<UploadState>('idle')
  const [result, setResult] = useState<DatasetValidationResponse | null>(null)
  const [processedDataset, setProcessedDataset] = useState<Dataset | null>(null)
  const [requestError, setRequestError] = useState<string | null>(null)

  function resetForNewSource() {
    setResult(null)
    setProcessedDataset(null)
    setRequestError(null)
  }

  function onFileChange(event: ChangeEvent<HTMLInputElement>) {
    resetForNewSource()
    setSelectedFile(event.target.files?.[0] ?? null)
    setUploadState('idle')
  }

  async function validateFile() {
    if (!selectedFile) return
    resetForNewSource()
    setUploadState('uploading')
    try {
      setUploadState('validating')
      const validation = await api.validateDataset(selectedFile)
      setResult(validation)
      setUploadState(validation.validation.is_valid ? 'ready' : 'failed')
    } catch (error) {
      setRequestError(error instanceof Error ? error.message : 'Could not validate the CSV.')
      setUploadState('failed')
    }
  }

  async function loadDemoDataset() {
    resetForNewSource()
    setSelectedFile(null)
    setUploadState('validating')
    try {
      const validation = await api.validateDemoDataset()
      setResult(validation)
      setUploadState(validation.validation.is_valid ? 'ready' : 'failed')
    } catch (error) {
      setRequestError(error instanceof Error ? error.message : 'Could not load the demo dataset.')
      setUploadState('failed')
    }
  }

  async function confirmProcessing() {
    if (!result?.dataset) return
    setRequestError(null)
    setUploadState('processing')
    try {
      const dataset = await api.processDataset(result.dataset.id)
      setProcessedDataset(dataset)
      onDatasetProcessed(dataset)
      setUploadState('completed')
    } catch (error) {
      setRequestError(error instanceof Error ? error.message : 'Could not process the dataset.')
      setUploadState('failed')
    }
  }

  const preview = result?.preview ?? []
  const columns = preview.length > 0 ? Object.keys(preview[0]) : []
  const canValidateFile = Boolean(selectedFile) && !['uploading', 'validating', 'processing'].includes(uploadState)
  const canProcess = Boolean(result?.validation.is_valid && result.dataset) && uploadState === 'ready'

  return (
    <section className="space-y-7">
      <header>
        <p className="text-sm font-medium text-teal">Data foundation</p>
        <h2 className="mt-1 text-3xl font-semibold tracking-tight text-slate-900">Dataset ingestion</h2>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
          Upload a CSV using the required canonical fields, or load the clearly labeled Synthetic Demo Dataset. Data is not stored until you confirm processing.
        </p>
      </header>

      <article className="rounded-xl border border-cyan-200 bg-cyan-50 p-5">
        <h3 className="text-base font-semibold text-slate-900">CSV structure guidance</h3>
        <p className="mt-2 text-sm leading-6 text-slate-700">Required columns are needed for accurate core analysis. Optional fields enable additional driver and cost analysis.</p>
        <div className="mt-4 grid gap-4 lg:grid-cols-2"><div><p className="text-xs font-semibold uppercase tracking-wide text-teal">Required columns</p><p className="mt-2 text-sm text-slate-700"><code>record_date</code> (use <code>date</code> as the current upload header), <code>department</code>, <code>patient_count</code>, <code>total_cost</code></p></div><div><p className="text-xs font-semibold uppercase tracking-wide text-teal">Optional columns</p><p className="mt-2 text-sm leading-6 text-slate-700"><code>service_type</code>, <code>medicine_cost</code>, <code>lab_cost</code>, <code>treatment_cost</code>, <code>insurance_amount</code>, <code>provider_type</code>, <code>site_of_care</code>, <code>drug_category</code>, <code>unit_cost</code></p></div></div>
        <p className="mt-4 rounded-lg bg-white/80 p-3 text-sm font-medium text-slate-700">Upload aggregated medical-cost data only. Do not upload patient-identifiable information.</p>
      </article>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <article className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="text-base font-semibold text-slate-900">Upload CSV</h3>
          <p className="mt-1 text-sm text-slate-600">Required upload headers: date, department, patient_count, total_cost.</p>
          <input
            accept=".csv,text/csv"
            className="mt-5 block w-full cursor-pointer rounded-lg border border-slate-300 bg-slate-50 p-3 text-sm text-slate-700 file:mr-4 file:rounded-md file:border-0 file:bg-cyan-50 file:px-3 file:py-2 file:text-sm file:font-semibold file:text-teal hover:file:bg-cyan-100"
            onChange={onFileChange}
            type="file"
          />
          <div className="mt-4 flex flex-wrap gap-3">
            <button className="rounded-lg bg-navy px-4 py-2.5 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50" disabled={!canValidateFile} onClick={validateFile} type="button">
              Validate CSV
            </button>
            <button className="rounded-lg border border-teal px-4 py-2.5 text-sm font-semibold text-teal disabled:cursor-not-allowed disabled:opacity-50" disabled={['validating', 'processing'].includes(uploadState)} onClick={loadDemoDataset} type="button">
              Load Demo Dataset
            </button>
          </div>
        </article>

        <aside className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Processing status</p>
          <p className={`mt-3 text-base font-semibold ${uploadState === 'failed' ? 'text-rose-700' : uploadState === 'completed' ? 'text-emerald-700' : 'text-slate-900'}`}>
            {uploadState.charAt(0).toUpperCase() + uploadState.slice(1)}
          </p>
          <p className="mt-2 text-sm leading-6 text-slate-600">{stateLabels[uploadState]}</p>
        </aside>
      </div>

      {(result || requestError) && (
        <article className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="text-base font-semibold text-slate-900">Validation summary</h3>
          {result && (
            <div className="mt-4 grid gap-3 sm:grid-cols-4">
              {[
                ['Total rows', result.validation.total_rows],
                ['Valid rows', result.validation.valid_rows],
                ['Invalid rows', result.validation.invalid_rows],
                ['Duplicate rows', result.validation.duplicate_rows],
              ].map(([label, value]) => (
                <div className="rounded-lg bg-slate-50 p-3" key={String(label)}>
                  <p className="text-xs font-medium text-slate-500">{label}</p>
                  <p className="mt-1 text-lg font-semibold text-slate-900">{value}</p>
                </div>
              ))}
            </div>
          )}
          {requestError && <p className="mt-4 rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{requestError}</p>}
          {result && !result.validation.is_valid && (
            <div className="mt-5 space-y-2">
              <p className="text-sm font-semibold text-rose-700">Correct these validation issues before processing.</p>
              {result.validation.validation_errors.map((error, index) => (
                <p className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-800" key={`${error.row}-${error.field}-${index}`}>
                  {error.row ? `Row ${error.row}: ` : ''}{error.message}
                </p>
              ))}
            </div>
          )}
        </article>
      )}

      {result?.validation.is_valid && preview.length > 0 && (
        <article className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 p-6">
            <div>
              <h3 className="text-base font-semibold text-slate-900">Dataset preview</h3>
              <p className="mt-1 text-sm text-slate-600">First {preview.length} validated records. Confirm to save all {result.validation.valid_rows} records.</p>
            </div>
            <button className="rounded-lg bg-teal px-4 py-2.5 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50" disabled={!canProcess} onClick={confirmProcessing} type="button">
              Confirm processing
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>{columns.map((column) => <th className="px-5 py-3 font-semibold" key={column}>{column.replace('_', ' ')}</th>)}</tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {preview.map((row, index) => <tr key={index}>{columns.map((column) => <td className="whitespace-nowrap px-5 py-3 text-slate-700" key={column}>{formatValue(row[column])}</td>)}</tr>)}
              </tbody>
            </table>
          </div>
          {processedDataset && <p className="border-t border-emerald-100 bg-emerald-50 px-6 py-4 text-sm text-emerald-800">Completed: {processedDataset.row_count} records were stored in the dataset.</p>}
        </article>
      )}
    </section>
  )
}
