import type { SVGProps } from 'react'

type IconProps = SVGProps<SVGSVGElement>

const base = (props: IconProps) => ({
  width: 20,
  height: 20,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.8,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
  'aria-hidden': true,
  ...props,
})

export const IconSend = (p: IconProps) => (
  <svg {...base(p)}><path d="M5 12h13M12 5l7 7-7 7" /></svg>
)
export const IconPlus = (p: IconProps) => (
  <svg {...base(p)}><path d="M12 5v14M5 12h14" /></svg>
)
export const IconTrash = (p: IconProps) => (
  <svg {...base(p)}><path d="M4 7h16M10 11v6M14 11v6M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12M9 7V4h6v3" /></svg>
)
export const IconChat = (p: IconProps) => (
  <svg {...base(p)}><path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z" /></svg>
)
export const IconPlay = (p: IconProps) => (
  <svg {...base(p)}><path d="M8 5.5v13l10-6.5-10-6.5z" fill="currentColor" stroke="none" /></svg>
)
export const IconClock = (p: IconProps) => (
  <svg {...base(p)}><circle cx="12" cy="12" r="8.5" /><path d="M12 7.5V12l3 2" /></svg>
)
export const IconCheck = (p: IconProps) => (
  <svg {...base(p)}><path d="M5 12.5l4.5 4.5L19 7.5" /></svg>
)
export const IconAlert = (p: IconProps) => (
  <svg {...base(p)}><path d="M12 8v5M12 16.5v.01" /><circle cx="12" cy="12" r="9" /></svg>
)
export const IconChevronDown = (p: IconProps) => (
  <svg {...base(p)}><path d="M6 9l6 6 6-6" /></svg>
)
export const IconArrowLeft = (p: IconProps) => (
  <svg {...base(p)}><path d="M19 12H5M11 5l-7 7 7 7" /></svg>
)
export const IconMenu = (p: IconProps) => (
  <svg {...base(p)}><path d="M4 7h16M4 12h16M4 17h10" /></svg>
)
export const IconClose = (p: IconProps) => (
  <svg {...base(p)}><path d="M6 6l12 12M18 6L6 18" /></svg>
)
export const IconSparkle = (p: IconProps) => (
  <svg {...base(p)}><path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3zM19 16l.8 2.2L22 19l-2.2.8L19 22l-.8-2.2L16 19l2.2-.8L19 16z" /></svg>
)
export const IconLink = (p: IconProps) => (
  <svg {...base(p)}><path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1" /></svg>
)
export const IconStop = (p: IconProps) => (
  <svg {...base(p)}><rect x="7" y="7" width="10" height="10" rx="2" fill="currentColor" stroke="none" /></svg>
)
export const IconRefresh = (p: IconProps) => (
  <svg {...base(p)}><path d="M20 11a8 8 0 1 0-2.3 5.7M20 5v6h-6" /></svg>
)
export const IconCopy = (p: IconProps) => (
  <svg {...base(p)}><rect x="9" y="9" width="11" height="11" rx="2" /><path d="M5 15V6a2 2 0 0 1 2-2h8" /></svg>
)
export const IconQuote = (p: IconProps) => (
  <svg {...base(p)}><path d="M7 17c-2 0-3-1.5-3-3.5C4 10 6 7.5 9 7M17 17c-2 0-3-1.5-3-3.5 0-3.5 2-6 5-6.5" /></svg>
)
