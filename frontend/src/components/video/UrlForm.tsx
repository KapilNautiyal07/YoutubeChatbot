import { useState, type FormEvent } from 'react'
import { IconLink, IconSend } from '../ui/Icons'
import { Spinner } from '../ui/Notice'

const YT_RE = /^(https?:\/\/)?((www|m|music)\.)?(youtube\.com|youtu\.be|youtube-nocookie\.com)\/.+|^[\w-]{11}$/i

interface Props {
  onSubmit: (url: string) => void
  busy?: boolean
}

export function UrlForm({ onSubmit, busy }: Props) {
  const [url, setUrl] = useState('')
  const [hint, setHint] = useState<string | null>(null)

  const submit = (e: FormEvent) => {
    e.preventDefault()
    const value = url.trim()
    if (!value) return setHint('Paste a YouTube link first.')
    if (!YT_RE.test(value)) return setHint('That doesn’t look like a YouTube link — try one from youtube.com or youtu.be.')
    setHint(null)
    onSubmit(value)
  }

  return (
    <form onSubmit={submit} className="w-full">
      <div className="group flex items-center gap-2 rounded-[1.4rem] border border-sand bg-white p-2 shadow-lift transition focus-within:border-ember-200 focus-within:ring-4 focus-within:ring-ember-100">
        <IconLink className="ml-3 size-5 shrink-0 text-muted group-focus-within:text-ember-500" />
        <input
          value={url}
          onChange={(e) => {
            setUrl(e.target.value)
            setHint(null)
          }}
          onPaste={(e) => {
            const text = e.clipboardData.getData('text').trim()
            if (YT_RE.test(text) && !busy) {
              e.preventDefault()
              setUrl(text)
              onSubmit(text)
            }
          }}
          type="text"
          inputMode="url"
          autoComplete="off"
          spellCheck={false}
          placeholder="Paste a YouTube link…"
          aria-label="YouTube video URL"
          className="min-w-0 flex-1 bg-transparent py-3 text-base text-ink placeholder:text-muted/80 focus:outline-none"
        />
        <button
          type="submit"
          disabled={busy}
          className="flex items-center gap-2 rounded-2xl bg-ember-500 px-4 py-3 text-sm font-semibold text-white shadow-soft transition hover:bg-ember-600 active:scale-[0.98] disabled:opacity-70 sm:px-5"
        >
          {busy ? <Spinner /> : <IconSend className="size-4" />}
          <span className="hidden sm:inline">{busy ? 'Starting…' : 'Process video'}</span>
        </button>
      </div>
      <p className={`mt-2.5 min-h-5 px-2 text-sm ${hint ? 'text-ember-600' : 'text-muted'}`}>
        {hint ?? 'Works with regular videos, Shorts, and live replays that have captions.'}
      </p>
    </form>
  )
}
