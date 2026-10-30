import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError, api } from '../api/client'
import type { Video } from '../api/types'
import { isProcessing } from '../lib/status'

/** Loads a video and keeps polling while it is still being processed. */
export function useVideo(id: string | undefined, initial?: Video | null) {
  const [video, setVideo] = useState<Video | null>(initial ?? null)
  const [error, setError] = useState<ApiError | null>(null)
  const [generation, setGeneration] = useState(0)
  const timer = useRef<number | undefined>(undefined)

  useEffect(() => {
    if (!id) return
    let cancelled = false

    async function poll() {
      try {
        const v = await api.getVideo(id!)
        if (cancelled) return
        setVideo(v)
        setError(null)
        if (isProcessing(v.status)) timer.current = window.setTimeout(poll, 1500)
      } catch (err) {
        if (cancelled) return
        setError(err as ApiError)
        // Keep retrying transient failures; stop on 404.
        if ((err as ApiError).status !== 404) timer.current = window.setTimeout(poll, 4000)
      }
    }

    poll()
    return () => {
      cancelled = true
      window.clearTimeout(timer.current)
    }
  }, [id, generation])

  const refresh = useCallback(() => setGeneration((g) => g + 1), [])

  return { video, error, refresh }
}
