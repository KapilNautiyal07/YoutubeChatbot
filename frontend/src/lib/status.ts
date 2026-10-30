import type { VideoStatus } from '../api/types'

export const PROCESSING: VideoStatus[] = ['pending', 'fetching_transcript', 'embedding']

export const isProcessing = (status: VideoStatus) => PROCESSING.includes(status)

export const STEPS: { key: VideoStatus; label: string; hint: string }[] = [
  { key: 'pending', label: 'Finding the video', hint: 'Checking the link and grabbing the details' },
  { key: 'fetching_transcript', label: 'Reading the transcript', hint: 'Pulling every caption with its timestamp' },
  { key: 'embedding', label: 'Understanding the content', hint: 'Breaking it into sections and learning what each covers' },
  { key: 'ready', label: 'Ready to chat', hint: 'Ask anything — answers link back to the exact moment' },
]

export function stepIndex(status: VideoStatus): number {
  const i = STEPS.findIndex((s) => s.key === status)
  return i === -1 ? 0 : i
}
