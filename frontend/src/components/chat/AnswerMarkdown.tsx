import { memo } from 'react'
import ReactMarkdown, { type Components } from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { linkifyTimestamps } from '../../lib/format'
import { IconPlay } from '../ui/Icons'

interface Props {
  content: string
  onSeek: (seconds: number) => void
}

export function TimestampChip({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={`Jump to ${label}`}
      className="mx-0.5 inline-flex translate-y-[-1px] items-center gap-0.5 rounded-full bg-ember-50 px-2 py-0.5 align-middle font-sans text-xs font-semibold text-ember-700 ring-1 ring-ember-200 transition hover:bg-ember-500 hover:text-white hover:ring-ember-500"
    >
      <IconPlay className="size-3" />
      {label}
    </button>
  )
}

export const AnswerMarkdown = memo(function AnswerMarkdown({ content, onSeek }: Props) {
  const components: Components = {
    a({ href, children, ...rest }) {
      if (href?.startsWith('#t=')) {
        const seconds = Number(href.slice(3))
        return <TimestampChip label={String(children)} onClick={() => onSeek(seconds)} />
      }
      return (
        <a href={href} target="_blank" rel="noreferrer noopener" {...rest}>
          {children}
        </a>
      )
    },
  }
  return (
    <div className="prose-chat">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {linkifyTimestamps(content)}
      </ReactMarkdown>
    </div>
  )
})
