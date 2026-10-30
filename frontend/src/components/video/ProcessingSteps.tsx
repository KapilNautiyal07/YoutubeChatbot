import type { Video } from '../../api/types'
import { STEPS, stepIndex } from '../../lib/status'
import { IconCheck } from '../ui/Icons'
import { Spinner } from '../ui/Notice'

export function ProcessingSteps({ video }: { video: Video }) {
  const current = stepIndex(video.status)
  return (
    <ol className="space-y-1">
      {STEPS.map((step, i) => {
        const done = i < current || video.status === 'ready'
        const active = i === current && video.status !== 'ready'
        return (
          <li
            key={step.key}
            className={`flex items-start gap-3 rounded-xl px-3 py-2.5 transition ${active ? 'bg-ember-50' : ''}`}
          >
            <span
              className={`mt-0.5 grid size-6 shrink-0 place-items-center rounded-full text-xs font-bold transition ${
                done
                  ? 'bg-sage-500 text-white'
                  : active
                    ? 'bg-ember-500 text-white'
                    : 'border border-sand bg-white text-muted'
              }`}
            >
              {done ? <IconCheck className="size-3.5" /> : active ? <Spinner className="size-3.5" /> : i + 1}
            </span>
            <span className="min-w-0">
              <span className={`block text-sm font-semibold ${done || active ? 'text-ink' : 'text-muted'}`}>
                {step.label}
              </span>
              <span className="block text-xs text-muted">
                {active && video.status_message ? video.status_message : step.hint}
              </span>
            </span>
          </li>
        )
      })}
    </ol>
  )
}
