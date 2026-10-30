import { useState } from 'react'
import type { Source } from '../../api/types'
import { formatTime } from '../../lib/format'
import { IconChevronDown, IconQuote } from '../ui/Icons'

interface Props {
  sources: Source[]
  onSeek: (seconds: number) => void
}

export function SourceList({ sources, onSeek }: Props) {
  const [open, setOpen] = useState(false)
  if (!sources.length) return null
  return (
    <div className="mt-3">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="flex items-center gap-1.5 rounded-full px-2 py-1 text-xs font-semibold text-muted transition hover:bg-cream hover:text-ink"
      >
        <IconQuote className="size-3.5" />
        Based on {sources.length} moment{sources.length > 1 ? 's' : ''} in the video
        <IconChevronDown className={`size-3.5 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && (
        <ul className="animate-fade-up mt-2 space-y-2">
          {sources.map((s) => (
            <li key={s.chunk_index}>
              <button
                type="button"
                onClick={() => onSeek(s.start_time)}
                className="group w-full rounded-xl border border-sand/80 bg-paper px-3 py-2.5 text-left transition hover:border-ember-200 hover:bg-ember-50/60"
              >
                <span className="flex items-center justify-between gap-2 text-xs font-semibold text-ember-700">
                  <span>
                    {formatTime(s.start_time)} – {formatTime(s.end_time)}
                  </span>
                  <span className="text-muted opacity-0 transition group-hover:opacity-100">Play from here →</span>
                </span>
                <span className="mt-1 line-clamp-3 block text-sm leading-relaxed text-ink-soft">“{s.content}”</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
