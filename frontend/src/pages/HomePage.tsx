import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiError, api } from '../api/client'
import type { Video } from '../api/types'
import { AppHeader } from '../components/AppHeader'
import { ErrorNotice } from '../components/ui/Notice'
import { UrlForm } from '../components/video/UrlForm'
import { VideoCard } from '../components/video/VideoCard'
import { isProcessing } from '../lib/status'

const HOW_IT_WORKS = [
  { title: 'Paste a link', body: 'Any YouTube video with captions — lectures, podcasts, tutorials, talks.' },
  { title: 'We read it all', body: 'The full transcript is split into moments and indexed, not just skimmed.' },
  { title: 'Ask like a friend', body: 'Follow-ups welcome. Every answer links to the exact second it came from.' },
]

export function HomePage() {
  const navigate = useNavigate()
  const [videos, setVideos] = useState<Video[] | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [listError, setListError] = useState<string | null>(null)

  const loadVideos = useCallback(async () => {
    try {
      setVideos(await api.listVideos())
      setListError(null)
    } catch (err) {
      setListError((err as ApiError).message)
      setVideos((v) => v ?? [])
    }
  }, [])

  useEffect(() => {
    loadVideos()
  }, [loadVideos])

  // Refresh the grid while anything is still processing.
  useEffect(() => {
    if (!videos?.some((v) => isProcessing(v.status))) return
    const t = window.setTimeout(loadVideos, 2500)
    return () => window.clearTimeout(t)
  }, [videos, loadVideos])

  const process = async (url: string) => {
    setBusy(true)
    setError(null)
    try {
      const res = await api.processVideo(url)
      navigate(`/videos/${res.video.id}`, { state: { video: res.video } })
    } catch (err) {
      setError((err as ApiError).message)
    } finally {
      setBusy(false)
    }
  }

  const remove = async (video: Video) => {
    if (!window.confirm(`Remove “${video.title ?? 'this video'}” and all its conversations?`)) return
    setVideos((list) => list?.filter((v) => v.id !== video.id) ?? null)
    try {
      await api.deleteVideo(video.id)
    } catch (err) {
      setListError((err as ApiError).message)
      loadVideos()
    }
  }

  return (
    <div className="min-h-full">
      <AppHeader />

      <main className="mx-auto max-w-6xl px-4 sm:px-6">
        <section className="mx-auto max-w-2xl pt-14 pb-12 text-center sm:pt-20">
          <span className="inline-flex items-center gap-2 rounded-full border border-ember-100 bg-white/70 px-3 py-1 text-xs font-semibold text-ember-700 shadow-soft">
            <span className="size-1.5 rounded-full bg-ember-500" /> Your study buddy for YouTube
          </span>
          <h1 className="mt-5 font-display text-4xl leading-[1.08] font-semibold tracking-tight text-ink sm:text-6xl">
            Watch less.
            <br />
            <span className="text-ember-500 italic">Understand</span> more.
          </h1>
          <p className="mx-auto mt-5 max-w-lg text-base leading-relaxed text-ink-soft sm:text-lg">
            Paste any YouTube link and have a real conversation with it. Answers come with timestamps, so you can jump
            straight to the moment that matters.
          </p>
          <div className="mt-8 text-left">
            <UrlForm onSubmit={process} busy={busy} />
          </div>
          {error && (
            <div className="mt-2 text-left">
              <ErrorNotice onDismiss={() => setError(null)}>{error}</ErrorNotice>
            </div>
          )}
        </section>

        {videos && videos.length === 0 && !listError && (
          <section className="mx-auto grid max-w-4xl gap-4 pb-20 sm:grid-cols-3">
            {HOW_IT_WORKS.map((step, i) => (
              <div key={step.title} className="rounded-2xl border border-sand/80 bg-white/70 p-5 shadow-soft">
                <span className="grid size-8 place-items-center rounded-full bg-ember-50 font-display text-sm font-bold text-ember-600">
                  {i + 1}
                </span>
                <h3 className="mt-3 font-semibold text-ink">{step.title}</h3>
                <p className="mt-1 text-sm leading-relaxed text-muted">{step.body}</p>
              </div>
            ))}
          </section>
        )}

        {(videos === null || videos.length > 0 || listError) && (
          <section className="pb-20">
            <div className="mb-5 flex items-end justify-between">
              <div>
                <h2 className="font-display text-2xl font-semibold tracking-tight text-ink">Pick up where you left off</h2>
                <p className="mt-1 text-sm text-muted">Videos you’ve already explored</p>
              </div>
            </div>
            {listError && <ErrorNotice title="Couldn’t load your videos">{listError}</ErrorNotice>}
            <div className="mt-4 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {videos === null
                ? Array.from({ length: 3 }).map((_, i) => (
                    <div key={i} className="overflow-hidden rounded-2xl border border-sand/60 bg-white">
                      <div className="aspect-video animate-pulse bg-cream" />
                      <div className="space-y-2 p-4">
                        <div className="h-4 w-4/5 animate-pulse rounded bg-cream" />
                        <div className="h-3 w-1/2 animate-pulse rounded bg-cream" />
                      </div>
                    </div>
                  ))
                : videos.map((v) => <VideoCard key={v.id} video={v} onDelete={remove} />)}
            </div>
          </section>
        )}
      </main>
    </div>
  )
}
