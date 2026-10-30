import type { ReactNode } from 'react'
import { ProviderPicker } from './ProviderPicker'
import { Logo } from './ui/Logo'

export function AppHeader({ left }: { left?: ReactNode }) {
  return (
    <header className="sticky top-0 z-40 border-b border-sand/70 bg-paper/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-3 px-4 sm:px-6">
        <div className="flex items-center gap-2">
          {left}
          <Logo />
        </div>
        <ProviderPicker />
      </div>
    </header>
  )
}
