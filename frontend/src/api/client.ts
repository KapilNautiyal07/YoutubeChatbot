import axios, { AxiosError } from 'axios'
import type {
  ChatRequest,
  Conversation,
  ConversationDetail,
  Message,
  ModelsResponse,
  ProcessVideoResponse,
  ProvidersResponse,
  StreamMeta,
  Video,
} from './types'

export const API_BASE = import.meta.env.VITE_API_URL ?? '/api'

const http = axios.create({ baseURL: API_BASE, timeout: 120_000 })

export class ApiError extends Error {
  code: string
  status: number

  constructor(message: string, code = 'error', status = 0) {
    super(message)
    this.code = code
    this.status = status
  }
}

interface ErrorBody {
  error?: { code?: string; message?: string }
}

function toApiError(err: unknown): ApiError {
  if (err instanceof ApiError) return err
  if (axios.isAxiosError(err)) {
    const e = err as AxiosError<ErrorBody>
    const body = e.response?.data?.error
    if (body?.message) return new ApiError(body.message, body.code, e.response?.status)
    if (!e.response) return new ApiError("We can't reach the server. Is the backend running?", 'network')
    return new ApiError('Something went wrong. Please try again.', 'http_error', e.response.status)
  }
  return new ApiError('Something unexpected happened.')
}

async function call<T>(promise: Promise<{ data: T }>): Promise<T> {
  try {
    return (await promise).data
  } catch (err) {
    throw toApiError(err)
  }
}

export const api = {
  processVideo: (url: string, force = false) =>
    call<ProcessVideoResponse>(http.post('/videos/process', { url, force })),
  listVideos: () => call<Video[]>(http.get('/videos')),
  getVideo: (id: string) => call<Video>(http.get(`/videos/${id}`)),
  deleteVideo: (id: string) => call<void>(http.delete(`/videos/${id}`)),
  reindexVideo: (id: string) => call<ProcessVideoResponse>(http.post(`/videos/${id}/reindex`)),
  suggestedQuestions: (id: string, provider?: string) =>
    call<{ questions: string[] }>(http.post(`/videos/${id}/suggested-questions`, { provider })),
  listConversations: (videoId: string) => call<Conversation[]>(http.get(`/videos/${videoId}/conversations`)),
  getConversation: (id: string) => call<ConversationDetail>(http.get(`/conversations/${id}`)),
  deleteConversation: (id: string) => call<void>(http.delete(`/conversations/${id}`)),
  providers: () => call<ProvidersResponse>(http.get('/providers')),
  models: (provider: string) => call<ModelsResponse>(http.get(`/providers/${provider}/models`)),
}

export interface StreamHandlers {
  onMeta?: (meta: StreamMeta) => void
  onToken?: (text: string) => void
  onDone?: (message: Message) => void
}

/** Streams an answer over server-sent events. Axios can't stream in browsers, so this uses fetch. */
export async function streamChat(body: ChatRequest, handlers: StreamHandlers, signal?: AbortSignal) {
  let response: Response
  try {
    response = await fetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal,
    })
  } catch (err) {
    if ((err as Error).name === 'AbortError') throw err
    throw new ApiError("We can't reach the server. Is the backend running?", 'network')
  }

  if (!response.ok || !response.body) {
    let payload: ErrorBody = {}
    try {
      payload = await response.json()
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(
      payload.error?.message ?? 'Something went wrong. Please try again.',
      payload.error?.code,
      response.status,
    )
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  const dispatch = (raw: string) => {
    let event = 'message'
    const data: string[] = []
    for (const line of raw.split('\n')) {
      if (line.startsWith('event:')) event = line.slice(6).trim()
      else if (line.startsWith('data:')) data.push(line.slice(5).trimStart())
    }
    if (!data.length) return
    const payload = JSON.parse(data.join('\n'))
    if (event === 'meta') handlers.onMeta?.(payload)
    else if (event === 'token') handlers.onToken?.(payload.text)
    else if (event === 'done') handlers.onDone?.(payload.message)
    else if (event === 'error') throw new ApiError(payload.message, payload.code)
  }

  for (;;) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, '\n')
    let boundary
    while ((boundary = buffer.indexOf('\n\n')) !== -1) {
      const raw = buffer.slice(0, boundary)
      buffer = buffer.slice(boundary + 2)
      dispatch(raw)
    }
  }
  if (buffer.trim()) dispatch(buffer)
}
