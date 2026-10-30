import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
import { IconSend, IconStop } from '../ui/Icons'

interface Props {
  onSend: (text: string) => void
  onStop: () => void
  busy: boolean
  disabled?: boolean
}

export function ChatInput({ onSend, onStop, busy, disabled }: Props) {
  const [text, setText] = useState('')
  const ref = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 180)}px`
  }, [text])

  const send = () => {
    const value = text.trim()
    if (!value || busy || disabled) return
    onSend(value)
    setText('')
  }

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault()
      send()
    }
  }

  return (
    <div className="rounded-[1.4rem] border border-sand bg-white p-2 shadow-lift transition focus-within:border-ember-200 focus-within:ring-4 focus-within:ring-ember-100">
      <div className="flex items-end gap-2">
        <textarea
          ref={ref}
          rows={1}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={onKeyDown}
          disabled={disabled}
          maxLength={4000}
          placeholder={disabled ? 'This video isn’t ready yet…' : 'Ask anything about this video…'}
          aria-label="Your question"
          className="scrollbar-soft max-h-44 min-h-11 flex-1 resize-none bg-transparent px-3 py-2.5 text-[0.95rem] leading-relaxed text-ink placeholder:text-muted/80 focus:outline-none disabled:cursor-not-allowed"
        />
        {busy ? (
          <button
            type="button"
            onClick={onStop}
            aria-label="Stop answering"
            className="grid size-11 shrink-0 place-items-center rounded-2xl bg-ink text-paper transition hover:bg-ink-soft"
          >
            <IconStop className="size-4" />
          </button>
        ) : (
          <button
            type="button"
            onClick={send}
            disabled={!text.trim() || disabled}
            aria-label="Send question"
            className="grid size-11 shrink-0 place-items-center rounded-2xl bg-ember-500 text-white shadow-soft transition hover:bg-ember-600 active:scale-95 disabled:bg-sand disabled:text-muted disabled:shadow-none"
          >
            <IconSend className="size-4" />
          </button>
        )}
      </div>
    </div>
  )
}
