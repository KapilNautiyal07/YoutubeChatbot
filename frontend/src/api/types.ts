export type VideoStatus = 'pending' | 'fetching_transcript' | 'embedding' | 'ready' | 'failed'

export interface Video {
  id: string
  youtube_video_id: string
  title: string | null
  channel_name: string | null
  thumbnail_url: string | null
  duration: number | null
  transcript_language: string | null
  transcript_language_code: string | null
  transcript_is_generated: boolean | null
  transcript_is_translated: boolean
  status: VideoStatus
  status_message: string | null
  error_message: string | null
  embedding_model: string | null
  chunk_count: number
  created_at: string
  updated_at: string
}

export interface ProcessVideoResponse {
  video: Video
  created: boolean
  message: string
}

export interface Source {
  chunk_index: number
  start_time: number
  end_time: number
  score: number | null
  content: string
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  provider?: string | null
  model?: string | null
  sources: Source[]
  created_at: string
}

export interface Conversation {
  id: string
  video_id: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
}

export interface ConversationDetail extends Conversation {
  messages: Message[]
}

export interface Provider {
  name: string
  label: string
  description: string
  configured: boolean
  default_model: string
}

export interface ProvidersResponse {
  default_provider: string
  embedding_model: string
  providers: Provider[]
}

export interface ModelsResponse {
  provider: string
  default_model: string
  models: string[]
}

export interface ChatRequest {
  video_id: string
  conversation_id?: string | null
  question: string
  provider?: string
  model?: string
}

export interface StreamMeta {
  conversation_id: string
  user_message_id: string
  provider: string
  model: string
  sources: Source[]
}
