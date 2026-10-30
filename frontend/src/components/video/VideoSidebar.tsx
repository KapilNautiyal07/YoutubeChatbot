import type { Conversation, Video } from '../../api/types'
import { formatDuration, timeAgo } from '../../lib/format'
import { IconChat, IconClock, IconPlus, IconTrash } from '../ui/Icons'

interface Props {
  video: Video
  conversations: Conversation[]
  activeId: string | null
  onSelect: (id: string) => void
  onNew: () => void
  onDelete: (id: string) => void
}

export function VideoSidebar({ video, conversations, activeId, onSelect, onNew, onDelete }: Props) {
  return (
    <div className="flex h-full flex-col">
      <div className="p-4">
        <div className="overflow-hidden rounded-2xl border border-sand/80 bg-white shadow-soft">
          {video.thumbnail_url && (
            <img src={video.thumbnail_url} alt="" className="aspect-video w-full object-cover" />
          )}
          <div className="p-3.5">
            <h2 className="line-clamp-3 text-sm font-semibold leading-snug text-ink">{video.title ?? 'Untitled video'}</h2>
            <p className="mt-1 truncate text-xs text-muted">{video.channel_name}</p>
            <div className="mt-3 flex flex-wrap gap-1.5 text-[11px] font-medium">
              {video.duration ? (
                <span className="flex items-center gap-1 rounded-full bg-cream px-2 py-0.5 text-ink-soft">
                  <IconClock className="size-3" /> {formatDuration(video.duration)}
                </span>
              ) : null}
              {video.transcript_language && (
                <span className="rounded-full bg-sage-50 px-2 py-0.5 text-sage-700">
                  {video.transcript_language}
                </span>
              )}
              {video.transcript_is_generated && (
                <span
                  className="rounded-full bg-cream px-2 py-0.5 text-muted"
                  title="Captions were generated automatically, so a few words may be off."
                >
                  auto-captions
                </span>
              )}
            </div>
            <a
              href={`https://www.youtube.com/watch?v=${video.youtube_video_id}`}
              target="_blank"
              rel="noreferrer noopener"
              className="mt-3 inline-block text-xs font-semibold text-ember-600 hover:underline"
            >
              Open on YouTube ↗
            </a>
          </div>
        </div>

        <button
          type="button"
          onClick={onNew}
          className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-ink px-4 py-2.5 text-sm font-semibold text-paper shadow-soft transition hover:bg-ink-soft active:scale-[0.98]"
        >
          <IconPlus className="size-4" /> New conversation
        </button>
      </div>

      <div className="min-h-0 flex-1 px-2 pb-4">
        <p className="px-3 pb-2 text-xs font-semibold tracking-wide text-muted uppercase">Conversations</p>
        <div className="scrollbar-soft h-full overflow-y-auto">
          {conversations.length === 0 ? (
            <p className="px-3 text-sm leading-relaxed text-muted">
              Nothing here yet. Your chats about this video will show up here.
            </p>
          ) : (
            <ul className="space-y-0.5">
              {conversations.map((c) => {
                const active = c.id === activeId
                return (
                  <li key={c.id} className="group relative">
                    <button
                      type="button"
                      onClick={() => onSelect(c.id)}
                      className={`flex w-full items-start gap-2.5 rounded-xl px-3 py-2.5 pr-9 text-left transition ${
                        active ? 'bg-white shadow-soft' : 'hover:bg-white/60'
                      }`}
                    >
                      <IconChat className={`mt-0.5 size-4 shrink-0 ${active ? 'text-ember-500' : 'text-muted'}`} />
                      <span className="min-w-0">
                        <span className="line-clamp-2 block text-sm leading-snug text-ink">{c.title}</span>
                        <span className="mt-0.5 block text-[11px] text-muted">
                          {timeAgo(c.updated_at)} · {Math.ceil(c.message_count / 2)} question
                          {Math.ceil(c.message_count / 2) === 1 ? '' : 's'}
                        </span>
                      </span>
                    </button>
                    <button
                      type="button"
                      onClick={() => onDelete(c.id)}
                      aria-label={`Delete conversation ${c.title}`}
                      className="absolute top-2 right-1.5 rounded-lg p-1.5 text-muted transition hover:bg-ember-50 hover:text-ember-600 focus:opacity-100 sm:opacity-0 sm:group-hover:opacity-100"
                    >
                      <IconTrash className="size-3.5" />
                    </button>
                  </li>
                )
              })}
            </ul>
          )}
        </div>
      </div>
    </div>
  )
}
