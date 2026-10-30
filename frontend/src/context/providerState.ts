import { createContext, useContext } from 'react'
import type { Provider } from '../api/types'

export interface ProviderState {
  providers: Provider[]
  provider: string
  model: string
  models: string[]
  loadingModels: boolean
  embeddingModel: string
  setProvider: (name: string) => void
  setModel: (model: string) => void
}

export const ProviderContext = createContext<ProviderState | null>(null)

export function useProviders(): ProviderState {
  const ctx = useContext(ProviderContext)
  if (!ctx) throw new Error('useProviders must be used inside ProviderProvider')
  return ctx
}
