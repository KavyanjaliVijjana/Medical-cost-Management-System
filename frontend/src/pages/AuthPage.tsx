import { Activity, ArrowLeft, LogIn, UserPlus } from 'lucide-react'
import { type FormEvent, useState } from 'react'

import { api } from '../api/client'
import type { AuthenticationResponse } from '../types/api'

type AuthMode = 'landing' | 'sign-in' | 'register'

export function AuthPage({ onAuthenticated }: { onAuthenticated: (user: AuthenticationResponse) => void }) {
  const [mode, setMode] = useState<AuthMode>('landing')
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  function selectMode(nextMode: AuthMode) {
    setMode(nextMode)
    setError(null)
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setIsSubmitting(true)
    setError(null)
    try {
      const user = mode === 'register'
        ? await api.register({ full_name: fullName, email, password, confirm_password: confirmPassword })
        : await api.login({ email, password })
      onAuthenticated(user)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Unable to complete authentication.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="min-h-screen bg-mist px-6 py-10 text-slate-800 sm:flex sm:items-center sm:justify-center">
      <section className="w-full max-w-5xl overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm sm:grid sm:grid-cols-[1.15fr_0.85fr]">
        <div className="bg-navy-dark p-8 text-white sm:p-12">
          <div className="flex items-center gap-3 text-cyan-100"><Activity className="h-6 w-6" /><span className="text-sm font-semibold uppercase tracking-[0.18em]">Medical economics</span></div>
          <h1 className="mt-12 text-4xl font-semibold leading-tight tracking-tight">Medical Cost Advisor</h1>
          <p className="mt-5 max-w-md text-base leading-7 text-slate-200">AI-powered medical economics intelligence for forecasting, understanding and managing healthcare cost pressure.</p>
          <p className="mt-12 text-sm leading-6 text-slate-300">Use aggregated financial and utilization data to support evidence-based operational cost decisions.</p>
        </div>
        <div className="p-8 sm:p-10">
          {mode === 'landing' ? (
            <div className="flex min-h-full flex-col justify-center">
              <p className="text-sm font-medium text-teal">Welcome</p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-900">Access your workspace</h2>
              <p className="mt-3 text-sm leading-6 text-slate-600">Sign in to your account or create a lightweight workspace profile.</p>
              <div className="mt-8 space-y-3">
                <button className="flex w-full items-center justify-center gap-2 rounded-lg bg-navy px-4 py-3 text-sm font-semibold text-white hover:bg-navy-dark" onClick={() => selectMode('sign-in')} type="button"><LogIn className="h-4 w-4" />Sign in</button>
                <button className="flex w-full items-center justify-center gap-2 rounded-lg border border-slate-300 px-4 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50" onClick={() => selectMode('register')} type="button"><UserPlus className="h-4 w-4" />Create account</button>
              </div>
            </div>
          ) : (
            <form className="space-y-5" onSubmit={submit}>
              <button className="flex items-center gap-1 text-sm font-medium text-slate-500 hover:text-slate-800" onClick={() => selectMode('landing')} type="button"><ArrowLeft className="h-4 w-4" />Back</button>
              <div><p className="text-sm font-medium text-teal">{mode === 'register' ? 'New workspace account' : 'Welcome back'}</p><h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-900">{mode === 'register' ? 'Create account' : 'Sign in'}</h2></div>
              {mode === 'register' && <Field label="Full name" value={fullName} onChange={setFullName} autoComplete="name" />}
              <Field label="Email" value={email} onChange={setEmail} autoComplete="email" type="email" />
              <Field label="Password" value={password} onChange={setPassword} autoComplete={mode === 'register' ? 'new-password' : 'current-password'} type="password" />
              {mode === 'register' && <Field label="Confirm password" value={confirmPassword} onChange={setConfirmPassword} autoComplete="new-password" type="password" />}
              {error && <p className="rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}
              <button className="w-full rounded-lg bg-navy px-4 py-3 text-sm font-semibold text-white hover:bg-navy-dark disabled:cursor-not-allowed disabled:opacity-60" disabled={isSubmitting} type="submit">{isSubmitting ? 'Please wait…' : mode === 'register' ? 'Create account' : 'Sign in'}</button>
              {mode === 'sign-in' && <p className="rounded-lg bg-slate-50 p-3 text-xs leading-5 text-slate-600">Demo account: <span className="font-medium">demo@medicalcost.local</span> · <span className="font-medium">Demo@12345</span></p>}
            </form>
          )}
        </div>
      </section>
    </main>
  )
}

function Field({ label, value, onChange, type = 'text', autoComplete }: { label: string; value: string; onChange: (value: string) => void; type?: string; autoComplete: string }) {
  return <label className="block text-sm font-medium text-slate-700">{label}<input autoComplete={autoComplete} className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-slate-900 outline-none transition focus:border-teal focus:ring-2 focus:ring-teal/20" onChange={(event) => onChange(event.target.value)} required type={type} value={value} /></label>
}
