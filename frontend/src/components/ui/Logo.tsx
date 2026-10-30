import { Link } from 'react-router-dom'

export function LogoMark({ className = 'size-8' }: { className?: string }) {
  return (
    <svg viewBox="0 0 64 64" className={className} aria-hidden>
      <rect width="64" height="64" rx="18" fill="var(--color-ember-500)" />
      <path
        d="M14 22c0-4.4 3.6-8 8-8h20c4.4 0 8 3.6 8 8v13c0 4.4-3.6 8-8 8H29l-9 7v-7.3c-3.5-.9-6-4-6-7.7V22z"
        fill="#fff7ef"
      />
      <path d="M28 22.5v12l10-6-10-6z" fill="var(--color-ember-500)" />
    </svg>
  )
}

export function Logo() {
  return (
    <Link to="/" className="group flex items-center gap-2.5 rounded-xl" aria-label="Tubewise home">
      <LogoMark className="size-8 transition-transform group-hover:-rotate-6" />
      <span className="font-display text-xl font-semibold tracking-tight text-ink">Tubewise</span>
    </Link>
  )
}
