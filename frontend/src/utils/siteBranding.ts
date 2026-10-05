import { sanitizeUrl } from '@/utils/url'

export const DEFAULT_SITE_NAME = 'BNDS AI普及计划'
export const DEFAULT_SITE_SUBTITLE = '让 AI 成为每个人的学习伙伴'

/** Preserve configured branding while migrating previous default names. */
export function resolveSiteName(value?: string): string {
  const name = value?.trim()
  return !name || /^(sub2api|relay)$/i.test(name) ? DEFAULT_SITE_NAME : name
}

export function resolveSiteSubtitle(value?: string): string {
  const subtitle = value?.trim()
  return !subtitle || /^(AI API Gateway Platform|Subscription to API Conversion Platform)$/i.test(subtitle)
    ? DEFAULT_SITE_SUBTITLE
    : subtitle
}

/** Hide upstream project links while preserving operator-provided documentation. */
export function resolveDocumentationUrl(value?: string): string {
  const url = sanitizeUrl(value || '')
  if (!url) return ''
  try {
    const parsed = new URL(url, window.location.origin)
    if (/(^|\.)sub2api\.(org|io|com)$/i.test(parsed.hostname) ||
        (parsed.hostname === 'github.com' && /^\/Wei-Shaw\/sub2api(?:\/|$)/i.test(parsed.pathname))) return ''
  } catch {
    return ''
  }
  return url
}
