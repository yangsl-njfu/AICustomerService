const PALETTES = [
  { start: '#153042', end: '#0f766e', accent: '#f97316' },
  { start: '#1f3c88', end: '#14b8a6', accent: '#f59e0b' },
  { start: '#4c1d95', end: '#7c3aed', accent: '#f97316' },
  { start: '#0f766e', end: '#115e59', accent: '#fb7185' },
  { start: '#7c2d12', end: '#ea580c', accent: '#22c55e' }
]

function pickPalette(seedText: string) {
  const seed = Array.from(seedText).reduce((sum, char) => sum + char.charCodeAt(0), 0)
  return PALETTES[seed % PALETTES.length]
}

function escapeXml(text: string) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;')
}

function normalizeTitle(title?: string) {
  const raw = title?.trim() || 'AI 商品'
  return raw.length > 28 ? `${raw.slice(0, 28)}...` : raw
}

function buildMonogram(title: string) {
  const compact = title.replace(/\s+/g, '')
  return compact.slice(0, 2).toUpperCase()
}

function isUnstableRemotePlaceholder(src?: string) {
  if (!src) return false
  return /picsum\.photos|source\.unsplash\.com/i.test(src)
}

export function buildProductPlaceholder(title?: string) {
  const safeTitle = normalizeTitle(title)
  const monogram = buildMonogram(safeTitle)
  const palette = pickPalette(safeTitle)

  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">
      <defs>
        <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="${palette.start}" />
          <stop offset="100%" stop-color="${palette.end}" />
        </linearGradient>
      </defs>
      <rect width="800" height="600" rx="36" fill="url(#bg)" />
      <circle cx="678" cy="116" r="116" fill="${palette.accent}" opacity="0.18" />
      <circle cx="118" cy="500" r="138" fill="#ffffff" opacity="0.08" />
      <rect x="58" y="56" width="132" height="42" rx="21" fill="#ffffff" opacity="0.12" />
      <text x="82" y="84" fill="#ffffff" opacity="0.82" font-family="Manrope, Noto Sans SC, sans-serif" font-size="22" font-weight="800">AI COMMERCE</text>
      <text x="58" y="352" fill="#ffffff" opacity="0.92" font-family="Manrope, Noto Sans SC, sans-serif" font-size="168" font-weight="800">${escapeXml(monogram)}</text>
      <text x="58" y="452" fill="#ffffff" opacity="0.92" font-family="Manrope, Noto Sans SC, sans-serif" font-size="42" font-weight="700">${escapeXml(safeTitle)}</text>
      <text x="58" y="500" fill="#ffffff" opacity="0.72" font-family="Manrope, Noto Sans SC, sans-serif" font-size="24" font-weight="500">Preview unavailable, using generated cover</text>
    </svg>
  `

  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`
}

export function resolveProductImage(src?: string, title?: string) {
  if (!src?.trim() || isUnstableRemotePlaceholder(src)) {
    return buildProductPlaceholder(title)
  }
  return src
}

export function handleImageFallback(event: Event, title?: string) {
  const target = event.target as HTMLImageElement | null
  if (!target) return

  target.onerror = null
  target.src = buildProductPlaceholder(title)
}
