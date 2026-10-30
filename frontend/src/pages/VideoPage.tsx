import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import type { Conversation, Video } from '../api/types'
import { AppHeader } from '../components/AppHeader'
import { ChatPanel } from '../components/chat/ChatPanel'
import { IconArrowLeft, IconClose, IconMenu, IconRefresh } from '../components/ui/Icons'
import { ErrorNotice, Spinner } from '../components/ui/Notice'
import { ProcessingSteps } from '../components/video/ProcessingSteps'
import { VideoSidebar } from '../components/video/VideoSidebar'
import { YouTubePlayer, type PlayerHandle } from '../components/video/YouTubePlayer'
import { useVideo } from '../hooks/useVideo'

export function VideoPage() {
  const { id } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()
  const conversationId = params.get('c')

  const { video, error, refresh } = useVideo(id, (location.state as { video?: Video } | null)?.video)
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [retrying, setRetrying] = useState(false)
  const player = useRef<PlayerHandle>(null)

  const ready = video?.status === 'ready'

  const loadConversations = useCallback(async () => {
    if (!id) return
    try {
      setConversations(await api.listConversations(id))
    } catch {
      /* the list is non-critical; the chat still works */
    }
  }, [id])

  useEffect(() => {
    if (ready) loadConversations()
  }, [ready, loadConversations])

  const selectConversation = (cid: string | null) => {
    setParams(cid ? { c: cid } : {}, { replace: false })
    setDrawerOpen(false)
  }

  const deleteConversation = async (cid: string) => {
    if (!window.confirm('Delete this conversation?')) return
    setConversations((list) => list.filter((c) => c.id !== cid))
    if (cid === conversationId) selectConversation(null)
    await api.deleteConversation(cid).catch(() => loadConversations())
  }

  const seek = useCallback((seconds: number) => {
    player.current?.seekTo(seconds)
  }, [])

  const retry = async () => {
    if (!video) return
    setRetrying(true)
    try {
      await api.reindexVideo(video.id)
      refresh()
    } finally {
      setRetrying(false)
    }
  }

  if (error && !video) {
    return (
      <div className="min-h-full">
        <AppHeader />
        <div className="mx-auto max-w-lg px-4 py-20">
          <ErrorNotice
            title={error.status === 404 ? 'We couldn’t find that video' : 'Something went wrong'}
            action={
              <Link to="/" className="font-semibold underline underline-offset-2">
                Back home
              </Link>
            }
          >
            {error.message}
          </ErrorNotice>
        </div>
      </div>
    )
  }

  if (!video) {
    return (
      <div className="min-h-full">
        <AppHeader />
        <div className="flex items-center justify-center gap-2 py-32 text-muted">
          <Spinner /> Loading…
        </div>
      </div>
    )
  }

  if (!ready) {
    const failed = video.status === 'failed'
    return (
      <div className="min-h-full">
        <AppHeader />
        <main className="mx-auto max-w-xl px-4 py-12 sm:py-16">
          <Link to="/" className="mb-6 inline-flex items-center gap-1.5 text-sm font-semibold text-muted hover:text-ink">
            <IconArrowLeft className="size-4" /> All videos
          </Link>
          <div className="animate-fade-up overflow-hidden rounded-3xl border border-sand/80 bg-white shadow-lift">
            <div className="relative aspect-video bg-cream">
              {video.thumbnail_url && (
                <img src={video.thumbnail_url} alt="" className={`size-full object-cover ${failed ? 'grayscale' : ''}`} />
              )}
              <div className="absolute inset-0 bg-gradient-to-t from-ink/70 via-ink/10 to-transparent" />
              <div className="absolute right-5 bottom-4 left-5 text-white">
                <p className="line-clamp-2 font-display text-xl font-semibold">{video.title ?? 'Getting video details…'}</p>
                {video.channel_name && <p className="text-sm text-white/80">{video.channel_name}</p>}
              </div>
            </div>
            <div className="p-5 sm:p-6">
              {failed ? (
                <ErrorNotice
                  title="We couldn’t prepare this video"
                  action={
                    <button
                      onClick={retry}
                      disabled={retrying}
                      className="inline-flex items-center gap-1.5 font-semibold underline underline-offset-2"
                    >
                      {retrying ? <Spinner className="size-3.5" /> : <IconRefresh className="size-3.5" />} Try again
                    </button>
                  }
                >
                  {video.error_message ?? 'Something went wrong while processing.'}
                </ErrorNotice>
              ) : (
                <>
                  <p className="mb-3 text-sm text-ink-soft">
                    Hang tight — I’m reading the whole video so I can answer properly. Longer videos take a little
                    longer.
                  </p>
                  <ProcessingSteps video={video} />
                </>
              )}
            </div>
          </div>
        </main>
      </div>
    )
  }

  const sidebar = (
    <VideoSidebar
      video={video}
      conversations={conversations}
      activeId={conversationId}
      onSelect={selectConversation}
      onNew={() => selectConversation(null)}
      onDelete={deleteConversation}
    />
  )

  return (
    <div className="flex h-dvh flex-col">
      <AppHeader
        left={
          <button
            type="button"
            onClick={() => setDrawerOpen(true)}
            className="rounded-xl p-2 text-ink-soft hover:bg-cream lg:hidden"
            aria-label="Open video details and conversations"
          >
            <IconMenu />
          </button>
        }
      />

      <div className="flex min-h-0 flex-1">
        <aside className="hidden w-72 shrink-0 border-r border-sand/70 bg-cream/40 lg:block">{sidebar}</aside>

        {drawerOpen && (
          <div className="fixed inset-0 z-50 lg:hidden" role="dialog" aria-modal="true">
            <div className="absolute inset-0 bg-ink/30 backdrop-blur-sm" onClick={() => setDrawerOpen(false)} />
            <aside className="animate-fade-up absolute inset-y-0 left-0 w-80 max-w-[85vw] bg-paper shadow-lift">
              <div className="flex justify-between px-4 pt-3">
                <button
                  onClick={() => navigate('/')}
                  className="inline-flex items-center gap-1.5 text-sm font-semibold text-muted hover:text-ink"
                >
                  <IconArrowLeft className="size-4" /> All videos
                </button>
                <button onClick={() => setDrawerOpen(false)} className="rounded-lg p-1.5 hover:bg-cream" aria-label="Close">
                  <IconClose className="size-5" />
                </button>
              </div>
              {sidebar}
            </aside>
          </div>
        )}

        <main className="flex min-w-0 flex-1 flex-col xl:flex-row-reverse">
          <section className="shrink-0 border-b border-sand/60 p-3 sm:p-4 xl:w-[440px] xl:border-b-0 xl:border-l xl:p-5 2xl:w-[520px]">
            <div className="mx-auto max-w-2xl lg:max-w-md xl:sticky xl:top-5 xl:max-w-none">
              <YouTubePlayer ref={player} videoId={video.youtube_video_id} title={video.title} />
              <p className="mt-3 hidden text-xs leading-relaxed text-muted xl:block">
                Tip: click any <span className="font-semibold text-ember-600">▶ timestamp</span> in an answer and the
                video jumps right there.
              </p>
            </div>
          </section>
          <section className="min-h-0 flex-1">
            <ChatPanel
              key={video.id}
              video={video}
              conversationId={conversationId}
              onConversationCreated={(cid) => setParams({ c: cid }, { replace: true })}
              onActivity={loadConversations}
              onSeek={seek}
            />
          </section>
        </main>
      </div>
    </div>
  )
}
