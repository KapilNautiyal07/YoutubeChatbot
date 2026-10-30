import { useState } from 'react'
import type { Source } from '../../api/types'
import { IconAlert, IconCheck, IconCopy } from '../ui/Icons'
import { LogoMark } from '../ui/Logo'
import { AnswerMarkdown } from './AnswerMarkdown'
import { SourceList } from './SourceList'

export interface ChatItem {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  model?: string | null
  pending?: boolean
  error?: string
}

interface Props {
  item: ChatItem
  onSeek: (seconds: number) => void
  onRetry?: () => void
}

function Thinking() {
  return (
    <div className="flex items-center gap-2 py-1 text-sm text-muted" aria-live="polite">
      <span className="flex gap-1">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="animate-blink size-1.5 rounded-full bg-ember-400"
            style={{ animationDelay: `${i * 0.15}s` }}
          />
        ))}
      </span>
      Rewatching the relevant parts…
    </div>
  )
}

export function MessageBubble({ item, onSeek, onRetry }: Props) {
  const [copied, setCopied] = useState(false)

  if (item.role === 'user') {
    return (
      <div className="animate-fade-up flex justify-end">
        <div className="max-w-[85%] rounded-3xl rounded-br-lg bg-ink px-4 py-2.5 text-[0.95rem] leading-relaxed whitespace-pre-wrap text-paper shadow-soft">
          {item.content}
        </div>
      </div>
    )
  }

  const copy = async () => {
    await navigator.clipboard.writeText(item.content)
    setCopied(true)
    window.setTimeout(() => setCopied(false), 1500)
  }

  return (
    <div className="animate-fade-up flex gap-3">
      <LogoMark className="mt-1 size-7 shrink-0" />
      <div className="min-w-0 flex-1">
        {item.error ? (
          <div className="flex items-start gap-2 rounded-2xl border border-ember-200 bg-ember-50 px-4 py-3 text-sm text-ember-700">
            <IconAlert className="mt-0.5 size-4 shrink-0" />
            <div>
              <p>{item.error}</p>
              {onRetry && (
                <button onClick={onRetry} className="mt-1.5 font-semibold underline underline-offset-2">
                  Try again
                </button>
              )}
            </div>
          </div>
        ) : item.content ? (
          <>
            <AnswerMarkdown content={item.content} onSeek={onSeek} />
            {item.pending && <span className="ml-0.5 inline-block h-4 w-1.5 animate-pulse rounded-sm bg-ember-400 align-middle" />}
          </>
        ) : (
          <Thinking />
        )}

        {!item.pending && !item.error && item.content && (
          <div className="mt-1 flex flex-wrap items-center gap-x-3">
            <SourceList sources={item.sources ?? []} onSeek={onSeek} />
            <button
              type="button"
              onClick={copy}
              className="mt-3 flex items-center gap-1 rounded-full px-2 py-1 text-xs font-semibold text-muted transition hover:bg-cream hover:text-ink"
            >
              {copied ? <IconCheck className="size-3.5" /> : <IconCopy className="size-3.5" />}
              {copied ? 'Copied' : 'Copy'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
