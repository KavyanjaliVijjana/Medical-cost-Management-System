import type { DemoUser } from '../types/api'

export function ProfilePage({ user, onLogout }: { user: DemoUser; onLogout: () => void }) {
  return <section className="max-w-3xl space-y-6">
    <header><p className="text-sm font-medium text-teal">Workspace profile</p><h2 className="mt-1 text-3xl font-semibold tracking-tight text-slate-900">Profile and settings</h2><p className="mt-2 text-sm leading-6 text-slate-600">A lightweight demo workspace profile for the medical economics application.</p></header>
    <article className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"><h3 className="text-base font-semibold text-slate-900">Account</h3><dl className="mt-5 grid gap-5 sm:grid-cols-2"><ProfileField label="Name" value={user.display_name} /><ProfileField label="Role" value="Medical Economics Analyst" /><ProfileField label="Account type" value={user.is_demo ? 'Demo workspace' : 'Workspace user'} /><ProfileField label="Email" value={user.email} /></dl></article>
    <article className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"><h3 className="text-base font-semibold text-slate-900">General preferences</h3><p className="mt-2 text-sm leading-6 text-slate-600">Evidence-first reporting is enabled. Financial and operational findings remain grounded in the selected dataset.</p></article>
    <article className="rounded-xl border border-rose-100 bg-rose-50 p-6"><h3 className="text-base font-semibold text-slate-900">Session</h3><p className="mt-2 text-sm leading-6 text-slate-700">Signing out clears this browser session and returns to the demo login screen.</p><button className="mt-4 rounded-lg bg-rose-700 px-4 py-2 text-sm font-semibold text-white hover:bg-rose-800" onClick={onLogout} type="button">Log out</button></article>
  </section>
}

function ProfileField({ label, value }: { label: string; value: string }) {
  return <div><dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</dt><dd className="mt-1 text-sm font-medium text-slate-900">{value}</dd></div>
}
