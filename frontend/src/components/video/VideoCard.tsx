import { Link } from 'react-router-dom'
import type { Video } from '../../api/types'
import { formatDuration, timeAgo } from '../../lib/format'
import { isProcessing } from '../../lib/status'
import { IconAlert, IconChat, IconTrash } from '../ui/Icons'
import { Spinner } from '../ui/Notice'

interface Props {
  video: Video
  onDelete: (video: Video) => void
}

export function VideoCard({ video, onDelete }: Props) {
  const processing = isProcessing(video.status)
  const failed = video.status === 'failed'
  return (
    <article className="group relative overflow-hidden rounded-2xl border border-sand/80 bg-white shadow-soft transition hover:-translate-y-0.5 hover:shadow-lift">
      <Link to={`/videos/${video.id}`} className="block">
        <div className="relative aspect-video overflow-hidden bg-cream">
          {video.thumbnail_url && (
            <img
              src={video.thumbnail_url}
              alt=""
              loading="lazy"
              className={`size-full object-cover transition duration-500 group-hover:scale-105 ${failed ? 'grayscale' : ''}`}
            />
          )}
          {video.duration ? (
            <span className="absolute right-2 bottom-2 rounded-md bg-ink/80 px-1.5 py-0.5 text-xs font-medium text-white">
              {formatDuration(video.duration)}
            </span>
          ) : null}
          {processing && (
            <div className="absolute inset-0 grid place-items-center bg-ink/40 backdrop-blur-[2px]">
              <span className="flex items-center gap-2 rounded-full bg-white/95 px-3 py-1.5 text-xs font-semibold text-ink">
                <Spinner className="size-3.5 text-ember-500" /> Getting ready…
              </span>
            </div>
          )}
        </div>
        <div className="p-4">
          <h3 className="line-clamp-2 font-semibold leading-snug text-ink">
            {video.title ?? 'Untitled video'}
          </h3>
          <p className="mt-1 truncate text-sm text-muted">{video.channel_name ?? 'Unknown channel'}</p>
          <div className="mt-3 flex items-center justify-between text-xs">
            {failed ? (
              <span className="flex items-center gap-1 font-medium text-ember-600">
                <IconAlert className="size-3.5" /> Couldn’t process
              </span>
            ) : processing ? (
              <span className="font-medium text-muted">{video.status_message ?? 'Processing…'}</span>
            ) : (
              <span className="flex items-center gap-1 font-medium text-sage-700">
                <IconChat className="size-3.5" /> Ready to chat
              </span>
            )}
            <span className="text-muted">{timeAgo(video.updated_at)}</span>
          </div>
        </div>
      </Link>
      <button
        type="button"
        onClick={() => onDelete(video)}
        aria-label={`Remove ${video.title ?? 'video'}`}
        className="absolute top-2 right-2 rounded-full bg-white/90 p-2 text-ink-soft shadow-soft transition hover:text-ember-600 focus:opacity-100 sm:opacity-0 sm:group-hover:opacity-100"
      >
        <IconTrash className="size-4" />
      </button>
    </article>
  )
}
