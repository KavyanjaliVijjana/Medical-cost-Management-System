import { Save } from 'lucide-react'
import { useEffect, useState } from 'react'

import { api } from '../api/client'
import type { ApplicationUser } from '../types/api'

export function ProfilePage({ user, onLogout, onUserUpdated }: { user: ApplicationUser; onLogout: () => void; onUserUpdated: (user: ApplicationUser) => void }) {
  const [name, setName] = useState(user.display_name)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => setName(user.display_name), [user.display_name])

  async function saveName() {
    setIsSaving(true)
    setError(null)
    setMessage(null)
    try {
      onUserUpdated(await api.updateProfile(name))
      setMessage('Profile updated.')
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Unable to save your profile.')
    } finally {
      setIsSaving(false)
    }
  }

  return <section className="max-w-3xl space-y-6">
    <header><p className="text-sm font-medium text-teal">Workspace profile</p><h2 className="mt-1 text-3xl font-semibold tracking-tight text-slate-900">Profile and settings</h2><p className="mt-2 text-sm leading-6 text-slate-600">Manage the account used to access the medical economics workspace.</p></header>
    <article className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"><h3 className="text-base font-semibold text-slate-900">Account</h3><div className="mt-5 grid gap-5 sm:grid-cols-2"><label className="text-xs font-semibold uppercase tracking-wide text-slate-500">Full name<input className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium normal-case tracking-normal text-slate-900 outline-none focus:border-teal focus:ring-2 focus:ring-teal/20" onChange={(event) => setName(event.target.value)} value={name} /></label><ProfileField label="Email" value={user.email} /><ProfileField label="Role" value={user.role} /><ProfileField label="Account type" value={user.account_type} /><ProfileField label="Member since" value={new Date(user.created_at).toLocaleDateString()} /></div><div className="mt-5 flex items-center gap-3"><button className="flex items-center gap-2 rounded-lg bg-navy px-4 py-2 text-sm font-semibold text-white hover:bg-navy-dark disabled:cursor-not-allowed disabled:opacity-60" disabled={isSaving} onClick={saveName} type="button"><Save className="h-4 w-4" />{isSaving ? 'Saving…' : 'Save changes'}</button>{message && <p className="text-sm text-emerald-700">{message}</p>}{error && <p className="text-sm text-rose-700">{error}</p>}</div></article>
    <article className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"><h3 className="text-base font-semibold text-slate-900">General preferences</h3><p className="mt-2 text-sm leading-6 text-slate-600">Evidence-first reporting is enabled. Financial and operational findings remain grounded in the selected dataset.</p></article>
    <article className="rounded-xl border border-rose-100 bg-rose-50 p-6"><h3 className="text-base font-semibold text-slate-900">Session</h3><p className="mt-2 text-sm leading-6 text-slate-700">Signing out clears this browser session and returns to the authentication page.</p><button className="mt-4 rounded-lg bg-rose-700 px-4 py-2 text-sm font-semibold text-white hover:bg-rose-800" onClick={onLogout} type="button">Log out</button></article>
  </section>
}

function ProfileField({ label, value }: { label: string; value: string }) {
  return <div><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p><p className="mt-1 text-sm font-medium text-slate-900">{value}</p></div>
}
