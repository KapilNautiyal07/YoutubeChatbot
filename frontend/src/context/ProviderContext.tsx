import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { api } from '../api/client'
import type { Provider } from '../api/types'
import { ProviderContext } from './providerState'

const STORAGE_KEY = 'tubewise.provider'

function readStored(): { provider?: string; models?: Record<string, string> } {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) ?? '{}')
  } catch {
    return {}
  }
}

export function ProviderProvider({ children }: { children: ReactNode }) {
  const [providers, setProviders] = useState<Provider[]>([])
  const [provider, setProviderState] = useState<string>(readStored().provider ?? '')
  const [chosenModels, setChosenModels] = useState<Record<string, string>>(readStored().models ?? {})
  const [models, setModels] = useState<string[]>([])
  const [liveDefault, setLiveDefault] = useState('')
  const [loadingModels, setLoadingModels] = useState(false)
  const [embeddingModel, setEmbeddingModel] = useState('')

  useEffect(() => {
    api
      .providers()
      .then((res) => {
        setProviders(res.providers)
        setEmbeddingModel(res.embedding_model)
        setProviderState((current) => {
          const valid = res.providers.find((p) => p.name === current && p.configured)
          if (valid) return current
          const preferred = res.providers.find((p) => p.name === res.default_provider && p.configured)
          return (preferred ?? res.providers.find((p) => p.configured) ?? res.providers[0])?.name ?? ''
        })
      })
      .catch(() => setProviders([]))
  }, [])

  useEffect(() => {
    if (!provider) return
    const info = providers.find((p) => p.name === provider)
    if (!info?.configured) {
      setModels(info ? [info.default_model] : [])
      return
    }
    let cancelled = false
    setLoadingModels(true)
    api
      .models(provider)
      .then((res) => {
        if (cancelled) return
        setModels(res.models)
        setLiveDefault(res.default_model)
      })
      .catch(() => !cancelled && setModels([info.default_model]))
      .finally(() => !cancelled && setLoadingModels(false))
    return () => {
      cancelled = true
    }
  }, [provider, providers])

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ provider, models: chosenModels }))
  }, [provider, chosenModels])

  const configuredDefault = providers.find((p) => p.name === provider)?.default_model ?? ''
  // The models endpoint reports the effective default, which may differ if the configured one is retired.
  const defaultModel = liveDefault && models.includes(liveDefault) ? liveDefault : configuredDefault
  const stored = chosenModels[provider]
  const model = stored && models.includes(stored) ? stored : defaultModel

  const setProvider = useCallback((name: string) => setProviderState(name), [])
  const setModel = useCallback(
    (m: string) => setChosenModels((prev) => ({ ...prev, [provider]: m })),
    [provider],
  )

  const value = useMemo(
    () => ({ providers, provider, model, models, loadingModels, embeddingModel, setProvider, setModel }),
    [providers, provider, model, models, loadingModels, embeddingModel, setProvider, setModel],
  )
  return <ProviderContext.Provider value={value}>{children}</ProviderContext.Provider>
}
