import { Link } from 'react-router-dom'
import { AppHeader } from '../components/AppHeader'

export function NotFoundPage() {
  return (
    <div className="min-h-full">
      <AppHeader />
      <div className="mx-auto max-w-md px-4 py-24 text-center">
        <p className="font-display text-6xl font-semibold text-ember-500">404</p>
        <h1 className="mt-3 font-display text-2xl font-semibold text-ink">This page wandered off</h1>
        <p className="mt-2 text-muted">Let’s get you back to your videos.</p>
        <Link
          to="/"
          className="mt-6 inline-block rounded-xl bg-ink px-5 py-2.5 text-sm font-semibold text-paper hover:bg-ink-soft"
        >
          Go home
        </Link>
      </div>
    </div>
  )
}
