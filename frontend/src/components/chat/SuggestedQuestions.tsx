import { IconSparkle } from '../ui/Icons'

interface Props {
  questions: string[]
  loading: boolean
  onPick: (q: string) => void
}

export function SuggestedQuestions({ questions, loading, onPick }: Props) {
  if (loading) {
    return (
      <div className="grid gap-2 sm:grid-cols-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-14 animate-pulse rounded-2xl bg-cream" />
        ))}
      </div>
    )
  }
  return (
    <div className="grid gap-2 sm:grid-cols-2">
      {questions.map((q, i) => (
        <button
          key={q}
          type="button"
          onClick={() => onPick(q)}
          style={{ animationDelay: `${i * 50}ms` }}
          className="animate-fade-up group flex items-start gap-2.5 rounded-2xl border border-sand/80 bg-white/80 px-4 py-3 text-left text-sm text-ink-soft shadow-soft transition hover:-translate-y-0.5 hover:border-ember-200 hover:bg-white hover:text-ink"
        >
          <IconSparkle className="mt-0.5 size-4 shrink-0 text-ember-400 transition group-hover:text-ember-500" />
          <span className="leading-snug">{q}</span>
        </button>
      ))}
    </div>
  )
}
