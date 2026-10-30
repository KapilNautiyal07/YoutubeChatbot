import type { ReactNode } from 'react'
import { IconAlert, IconClose } from './Icons'

interface NoticeProps {
  title?: string
  children: ReactNode
  onDismiss?: () => void
  action?: ReactNode
}

export function ErrorNotice({ title = 'Hmm, that didn’t work', children, onDismiss, action }: NoticeProps) {
  return (
    <div
      role="alert"
      className="animate-fade-up flex items-start gap-3 rounded-2xl border border-ember-200 bg-ember-50 px-4 py-3 text-sm text-ember-700"
    >
      <IconAlert className="mt-0.5 size-5 shrink-0" />
      <div className="min-w-0 flex-1">
        <p className="font-semibold">{title}</p>
        <div className="mt-0.5 text-ember-700/90">{children}</div>
        {action && <div className="mt-2">{action}</div>}
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="rounded-lg p-1 text-ember-600 hover:bg-ember-100"
          aria-label="Dismiss"
        >
          <IconClose className="size-4" />
        </button>
      )}
    </div>
  )
}

export function Spinner({ className = 'size-4' }: { className?: string }) {
  return (
    <svg className={`animate-spin ${className}`} viewBox="0 0 24 24" aria-hidden>
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeOpacity="0.2" strokeWidth="3" fill="none" />
      <path d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" strokeWidth="3" fill="none" strokeLinecap="round" />
    </svg>
  )
}
