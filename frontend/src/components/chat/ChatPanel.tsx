import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError, api, streamChat } from '../../api/client'
import type { Video } from '../../api/types'
import { useProviders } from '../../context/providerState'
import { ErrorNotice, Spinner } from '../ui/Notice'
import { ChatInput } from './ChatInput'
import { MessageBubble, type ChatItem } from './MessageBubble'
import { SuggestedQuestions } from './SuggestedQuestions'

interface Props {
  video: Video
  conversationId: string | null
  onConversationCreated: (id: string) => void
  onActivity: () => void
  onSeek: (seconds: number) => void
}

let localId = 0
const nextId = () => `local-${++localId}`

export function ChatPanel({ video, conversationId, onConversationCreated, onActivity, onSeek }: Props) {
  const { provider, model } = useProviders()
  const [items, setItems] = useState<ChatItem[]>([])
  const [busy, setBusy] = useState(false)
  const [loadingHistory, setLoadingHistory] = useState(false)
  const [historyError, setHistoryError] = useState<string | null>(null)
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [loadingSuggestions, setLoadingSuggestions] = useState(true)

  const abortRef = useRef<AbortController | null>(null)
  const createdHere = useRef<string | null>(null)
  const scroller = useRef<HTMLDivElement>(null)
  const stickToBottom = useRef(true)

  // Load history whenever the selected conversation changes (but not for one we just created).
  useEffect(() => {
    if (conversationId && conversationId === createdHere.current) {
      createdHere.current = null
      return
    }
    abortRef.current?.abort()
    setHistoryError(null)
    if (!conversationId) {
      setItems([])
      return
    }
    let cancelled = false
    setLoadingHistory(true)
    api
      .getConversation(conversationId)
      .then((c) => {
        if (cancelled) return
        setItems(
          c.messages.map((m) => ({ id: m.id, role: m.role, content: m.content, sources: m.sources, model: m.model })),
        )
        stickToBottom.current = true
      })
      .catch((err: ApiError) => !cancelled && setHistoryError(err.message))
      .finally(() => !cancelled && setLoadingHistory(false))
    return () => {
      cancelled = true
    }
  }, [conversationId])

  useEffect(() => {
    let cancelled = false
    setLoadingSuggestions(true)
    api
      .suggestedQuestions(video.id, provider || undefined)
      .then((r) => !cancelled && setSuggestions(r.questions))
      .catch(() => !cancelled && setSuggestions(['Summarize this video.', 'What are the key takeaways?']))
      .finally(() => !cancelled && setLoadingSuggestions(false))
    return () => {
      cancelled = true
    }
    // Suggestions are cached per video on the server; provider changes don't need a refetch.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [video.id])

  useEffect(() => () => abortRef.current?.abort(), [])

  useEffect(() => {
    const el = scroller.current
    if (el && stickToBottom.current) el.scrollTo({ top: el.scrollHeight })
  }, [items])

  const onScroll = () => {
    const el = scroller.current
    if (el) stickToBottom.current = el.scrollHeight - el.scrollTop - el.clientHeight < 120
  }

  const patch = (id: string, update: (item: ChatItem) => Partial<ChatItem>) =>
    setItems((prev) => prev.map((it) => (it.id === id ? { ...it, ...update(it) } : it)))

  const ask = useCallback(
    async (question: string, existing: ChatItem[] = items) => {
      const userItem: ChatItem = { id: nextId(), role: 'user', content: question }
      const answerId = nextId()
      setItems([...existing, userItem, { id: answerId, role: 'assistant', content: '', pending: true }])
      stickToBottom.current = true
      setBusy(true)

      const controller = new AbortController()
      abortRef.current = controller
      try {
        await streamChat(
          { video_id: video.id, conversation_id: conversationId, question, provider, model },
          {
            onMeta: (meta) => {
              patch(answerId, () => ({ sources: meta.sources, model: meta.model }))
              if (!conversationId) {
                createdHere.current = meta.conversation_id
                onConversationCreated(meta.conversation_id)
              }
            },
            onToken: (text) => patch(answerId, (it) => ({ content: it.content + text })),
            onDone: (message) =>
              patch(answerId, () => ({ id: message.id, content: message.content, sources: message.sources, pending: false })),
          },
          controller.signal,
        )
      } catch (err) {
        if ((err as Error).name === 'AbortError') {
          patch(answerId, (it) => ({ pending: false, content: it.content ? `${it.content}\n\n*— stopped*` : '*Stopped.*' }))
        } else {
          patch(answerId, () => ({ pending: false, error: (err as ApiError).message ?? 'Something went wrong.' }))
        }
      } finally {
        patch(answerId, () => ({ pending: false }))
        setBusy(false)
        abortRef.current = null
        onActivity()
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [items, video.id, conversationId, provider, model],
  )

  const retry = (index: number) => {
    const userItem = items[index - 1]
    if (!userItem || userItem.role !== 'user') return
    ask(userItem.content, items.slice(0, index - 1))
  }

  const empty = !items.length && !loadingHistory

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div ref={scroller} onScroll={onScroll} className="scrollbar-soft min-h-0 flex-1 overflow-y-auto">
        <div className="mx-auto w-full max-w-3xl px-4 py-6 sm:px-6">
          {historyError && <ErrorNotice title="Couldn’t load this conversation">{historyError}</ErrorNotice>}
          {loadingHistory && (
            <div className="flex items-center justify-center gap-2 py-16 text-sm text-muted">
              <Spinner /> Loading your conversation…
            </div>
          )}

          {empty && (
            <div className="animate-fade-up py-4 sm:py-8">
              <p className="text-sm font-semibold text-ember-600">Ready when you are</p>
              <h2 className="mt-1 font-display text-2xl font-semibold tracking-tight text-ink sm:text-3xl">
                What would you like to know?
              </h2>
              <p className="mt-2 max-w-xl text-sm leading-relaxed text-muted">
                I’ve gone through the whole transcript. Ask me anything — I’ll answer from what’s actually said and
                point you to the exact moments.
              </p>
              <div className="mt-6">
                <SuggestedQuestions questions={suggestions} loading={loadingSuggestions} onPick={(q) => ask(q)} />
              </div>
            </div>
          )}

          <div className="space-y-6">
            {items.map((item, i) => (
              <MessageBubble
                key={item.id}
                item={item}
                onSeek={onSeek}
                onRetry={item.error && !busy ? () => retry(i) : undefined}
              />
            ))}
          </div>
        </div>
      </div>

      <div className="border-t border-sand/60 bg-paper/90 backdrop-blur">
        <div className="mx-auto w-full max-w-3xl px-4 pt-3 pb-4 sm:px-6">
          <ChatInput onSend={(q) => ask(q)} onStop={() => abortRef.current?.abort()} busy={busy} />
          <p className="mt-2 text-center text-[11px] text-muted">
            Answers come from the video’s transcript — tap a timestamp to jump there.
          </p>
        </div>
      </div>
    </div>
  )
}
