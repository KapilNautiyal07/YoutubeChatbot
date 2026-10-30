import { useEffect, useImperativeHandle, useRef, type Ref } from 'react'

export interface PlayerHandle {
  seekTo: (seconds: number) => void
}

interface YTPlayer {
  seekTo: (seconds: number, allowSeekAhead: boolean) => void
  playVideo: () => void
  destroy: () => void
}

interface YTNamespace {
  Player: new (el: HTMLElement, options: Record<string, unknown>) => YTPlayer
}

declare global {
  interface Window {
    YT?: YTNamespace
    onYouTubeIframeAPIReady?: () => void
  }
}

let apiPromise: Promise<YTNamespace> | null = null

function loadApi(): Promise<YTNamespace> {
  if (window.YT?.Player) return Promise.resolve(window.YT)
  if (!apiPromise) {
    apiPromise = new Promise((resolve) => {
      const previous = window.onYouTubeIframeAPIReady
      window.onYouTubeIframeAPIReady = () => {
        previous?.()
        resolve(window.YT!)
      }
      const script = document.createElement('script')
      script.src = 'https://www.youtube.com/iframe_api'
      script.async = true
      document.head.appendChild(script)
    })
  }
  return apiPromise
}

interface Props {
  videoId: string
  title?: string | null
  ref?: Ref<PlayerHandle>
}

export function YouTubePlayer({ videoId, title, ref }: Props) {
  const host = useRef<HTMLDivElement>(null)
  const player = useRef<YTPlayer | null>(null)
  const ready = useRef(false)
  const pendingSeek = useRef<number | null>(null)

  useEffect(() => {
    let cancelled = false
    ready.current = false
    loadApi().then((YT) => {
      if (cancelled || !host.current) return
      const mount = document.createElement('div')
      host.current.replaceChildren(mount)
      player.current = new YT.Player(mount, {
        videoId,
        width: '100%',
        height: '100%',
        playerVars: { rel: 0, modestbranding: 1, playsinline: 1 },
        events: {
          onReady: () => {
            ready.current = true
            if (pendingSeek.current !== null) {
              player.current?.seekTo(pendingSeek.current, true)
              player.current?.playVideo()
              pendingSeek.current = null
            }
          },
        },
      })
    })
    return () => {
      cancelled = true
      player.current?.destroy()
      player.current = null
    }
  }, [videoId])

  useImperativeHandle(ref, () => ({
    seekTo(seconds: number) {
      if (ready.current && player.current) {
        player.current.seekTo(seconds, true)
        player.current.playVideo()
      } else {
        pendingSeek.current = seconds
      }
    },
  }))

  return (
    <div className="relative aspect-video w-full overflow-hidden rounded-2xl bg-ink shadow-lift">
      <div ref={host} className="absolute inset-0 [&>iframe]:size-full" aria-label={title ?? 'YouTube video'} />
    </div>
  )
}
