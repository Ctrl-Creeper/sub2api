import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

import { enableAutoUnmount, mount, RouterLinkStub } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { useAppStore } from '@/stores/app'
import HomeView from '@/views/HomeView.vue'
import KeyUsageView from '@/views/KeyUsageView.vue'

vi.mock('vue-i18n', async (importOriginal) => ({
  ...await importOriginal<typeof import('vue-i18n')>(),
  useI18n: () => ({
    t: (key: string) => key,
    locale: { value: 'en' },
  }),
}))

enableAutoUnmount(afterEach)

const dir = dirname(fileURLToPath(import.meta.url))
const headerSource = readFileSync(resolve(dir, '../AppHeader.vue'), 'utf8')

describe('doc_url sanitization', () => {
  it('AppHeader imports sanitizeUrl', () => {
    expect(headerSource).toContain("import { sanitizeUrl } from '@/utils/url'")
  })

  it('AppHeader applies sanitizeUrl to docUrl', () => {
    expect(headerSource).toContain('sanitizeUrl(appStore.docUrl)')
  })

  describe.each([
    { name: 'HomeView', view: HomeView, compact: false, linkCount: 2 },
    { name: 'HomeView compact', view: HomeView, compact: true, linkCount: 1 },
    { name: 'KeyUsageView', view: KeyUsageView, compact: false, linkCount: 2 },
  ])('$name rendered documentation links', ({ view, compact, linkCount }) => {
    beforeEach(() => {
      localStorage.clear()
      setActivePinia(createPinia())
    })

    describe.each(['cached', 'fallback'])('%s doc_url', (source) => {
      it.each([
        [' https://DOCS.example.com ', 'https://docs.example.com/'],
        ['http://docs.example.com/guide', 'http://docs.example.com/guide'],
        ['javascript:alert(1)', ''],
        ['JaVaScRiPt:alert(1)', ''],
        ['data:text/html,<script>alert(1)</script>', ''],
        ['//docs.example.com/guide', ''],
        ['', ''],
        ['https://sub2api.org/docs', ''],
        ['https://github.com/Wei-Shaw/sub2api', ''],
      ])('renders %j as %j', (input, expected) => {
        useAppStore().$patch({
          publicSettingsLoaded: true,
          docUrl: source === 'fallback' ? input : '',
          cachedPublicSettings: {
            doc_url: source === 'cached' ? input : '',
            compact_home_enabled: compact,
          },
        })

        const wrapper = mount(view, {
          global: {
            stubs: {
              RouterLink: RouterLinkStub,
              LocaleSwitcher: true,
              Icon: true,
            },
          },
        })
        const links = wrapper.findAll('a[target="_blank"]')

        expect(links).toHaveLength(expected ? linkCount : 0)
        for (const link of links) {
          expect(link.attributes('href')).toBe(expected)
          expect(link.attributes('rel')).toBe('noopener noreferrer')
        }
      })
    })
  })
})
