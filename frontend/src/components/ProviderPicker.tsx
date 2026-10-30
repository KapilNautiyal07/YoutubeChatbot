import { useEffect, useRef, useState } from 'react'
import { useProviders } from '../context/providerState'
import { IconCheck, IconChevronDown } from './ui/Icons'
import { Spinner } from './ui/Notice'

const ACCENTS: Record<string, string> = {
  groq: 'bg-ember-500',
  gemini: 'bg-sage-500',
}

export function ProviderPicker({ compact = false }: { compact?: boolean }) {
  const { providers, provider, model, models, loadingModels, setProvider, setModel } = useProviders()
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const onClick = (e: MouseEvent) => !ref.current?.contains(e.target as Node) && setOpen(false)
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(false)
    document.addEventListener('mousedown', onClick)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onClick)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  const current = providers.find((p) => p.name === provider)
  if (!providers.length) return null

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="dialog"
        aria-expanded={open}
        className="flex items-center gap-2 rounded-full border border-sand bg-white/80 py-1.5 pr-3 pl-2.5 text-sm shadow-soft backdrop-blur transition hover:border-ember-200 hover:bg-white"
      >
        <span className={`size-2.5 rounded-full ${ACCENTS[provider] ?? 'bg-muted'}`} />
        <span className="font-semibold text-ink">{current?.label ?? 'Choose AI'}</span>
        {!compact && model && (
          <span className="hidden max-w-40 truncate text-muted sm:inline">· {model}</span>
        )}
        <IconChevronDown className={`size-4 text-muted transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div
          role="dialog"
          aria-label="Choose the AI that answers"
          className="animate-fade-up absolute right-0 z-50 mt-2 w-80 rounded-2xl border border-sand bg-white p-3 shadow-lift"
        >
          <p className="px-1 pb-2 text-xs font-semibold tracking-wide text-muted uppercase">Who should answer?</p>
          <div className="space-y-1.5">
            {providers.map((p) => {
              const active = p.name === provider
              return (
                <button
                  key={p.name}
                  type="button"
                  disabled={!p.configured}
                  onClick={() => setProvider(p.name)}
                  className={`flex w-full items-center gap-3 rounded-xl border px-3 py-2.5 text-left transition ${
                    active ? 'border-ember-200 bg-ember-50' : 'border-transparent hover:bg-cream'
                  } disabled:cursor-not-allowed disabled:opacity-50`}
                >
                  <span className={`size-3 shrink-0 rounded-full ${ACCENTS[p.name] ?? 'bg-muted'}`} />
                  <span className="min-w-0 flex-1">
                    <span className="block text-sm font-semibold text-ink">{p.label}</span>
                    <span className="block text-xs text-muted">
                      {p.configured ? p.description : 'Not set up on the server yet'}
                    </span>
                  </span>
                  {active && <IconCheck className="size-4 text-ember-600" />}
                </button>
              )
            })}
          </div>

          <label className="mt-3 block px-1">
            <span className="flex items-center gap-2 text-xs font-semibold tracking-wide text-muted uppercase">
              Model {loadingModels && <Spinner className="size-3" />}
            </span>
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              disabled={!current?.configured || loadingModels}
              className="mt-1.5 w-full rounded-xl border border-sand bg-paper px-3 py-2 text-sm text-ink focus:border-ember-400 focus:outline-none"
            >
              {(models.length ? models : [model]).map((m) => (
                <option key={m} value={m}>
                  {m}
                  {m === current?.default_model ? ' (recommended)' : ''}
                </option>
              ))}
            </select>
          </label>
          <p className="mt-3 px-1 text-xs leading-relaxed text-muted">
            You can switch any time — even mid-conversation. Your videos don’t need to be processed again.
          </p>
        </div>
      )}
    </div>
  )
}
