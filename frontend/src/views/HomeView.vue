<template>
  <!-- Custom Home Content: Full Page Mode -->
  <div v-if="hasHomeContent" class="min-h-screen">
    <!-- iframe mode -->
    <iframe
      v-if="isHomeContentUrl"
      :src="homeContent.trim()"
      class="h-screen w-full border-0"
      allowfullscreen
    ></iframe>
    <!-- HTML mode - SECURITY: homeContent is admin-only setting, XSS risk is acceptable -->
    <div v-else v-html="homeContent"></div>
  </div>

  <!-- Compact Home Page -->
  <div
    v-else-if="compactHomeEnabled"
    data-testid="compact-home"
    class="flex min-h-screen flex-col bg-gray-50 text-gray-900 dark:bg-dark-950 dark:text-white"
  >
    <header class="border-b border-gray-200 px-4 py-4 sm:px-6 dark:border-dark-800">
      <nav class="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3 sm:gap-4">
        <div class="flex min-w-0 flex-1 items-center gap-3">
          <img
            :src="siteLogo || '/logo.svg'"
            alt="Logo"
            class="h-9 w-9 shrink-0 rounded-lg object-contain"
          />
          <span class="min-w-0 truncate text-base font-semibold">{{ siteName }}</span>
        </div>
        <div class="flex max-w-full shrink-0 flex-wrap items-center justify-end gap-2">
          <LocaleSwitcher />
          <a
            v-if="docUrl"
            :href="docUrl"
            target="_blank"
            rel="noopener noreferrer"
            class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-gray-500 hover:bg-gray-100 dark:text-dark-400 dark:hover:bg-dark-800"
            :title="t('home.viewDocs')"
          >
            <Icon name="book" size="md" />
          </a>
          <router-link
            v-if="showModelPlazaEntry"
            to="/model-plaza"
            class="flex h-10 shrink-0 items-center gap-1.5 rounded-lg px-2.5 text-sm font-medium text-gray-500 hover:bg-gray-100 hover:text-gray-700 dark:text-dark-400 dark:hover:bg-dark-800 dark:hover:text-white"
            :title="t('nav.modelPlaza')"
          >
            <Icon name="grid" size="md" />
            <span class="hidden sm:inline">{{ t('nav.modelPlaza') }}</span>
          </router-link>
          <button
            class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-gray-500 hover:bg-gray-100 dark:text-dark-400 dark:hover:bg-dark-800"
            :title="isDark ? t('home.switchToLight') : t('home.switchToDark')"
            @click="toggleTheme"
          >
            <Icon v-if="isDark" name="sun" size="md" />
            <Icon v-else name="moon" size="md" />
          </button>
          <router-link
            :to="isAuthenticated ? dashboardPath : '/login'"
            class="inline-flex min-h-10 shrink-0 items-center justify-center rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800 dark:bg-white dark:text-gray-900 dark:hover:bg-gray-200"
          >
            {{ isAuthenticated ? t('home.dashboard') : t('home.login') }}
          </router-link>
        </div>
      </nav>
    </header>

    <main class="compact-home-content flex min-w-0 flex-1 items-center justify-center px-4 py-16 sm:px-6">
      <div class="min-w-0 max-w-2xl text-center">
        <img
          :src="siteLogo || '/logo.svg'"
          alt="Logo"
          class="mx-auto mb-6 h-20 w-20 rounded-2xl object-contain"
        />
        <h1 class="[overflow-wrap:anywhere] text-3xl font-bold md:text-4xl">{{ siteName }}</h1>
        <p class="mt-4 whitespace-pre-wrap [overflow-wrap:anywhere] text-base text-gray-600 dark:text-dark-300">{{ siteSubtitle }}</p>
        <router-link
          :to="isAuthenticated ? dashboardPath : '/login'"
          class="mt-8 inline-flex min-h-10 items-center justify-center rounded-lg bg-primary-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-primary-700"
        >
          {{ isAuthenticated ? t('home.goToDashboard') : t('home.login') }}
        </router-link>
      </div>
    </main>

    <footer class="min-w-0 border-t border-gray-200 px-4 py-5 text-center text-sm text-gray-500 [overflow-wrap:anywhere] sm:px-6 dark:border-dark-800 dark:text-dark-400">
      &copy; {{ currentYear }} {{ siteName }}
    </footer>
  </div>

  <!-- Default Home Page -->
  <div
    v-else
    class="relay-home relative flex min-h-screen flex-col bg-white dark:bg-dark-950"
  >
    <!-- Header -->
    <header class="relative z-20 border-b border-gray-200 px-4 py-5 dark:border-dark-700 sm:px-6">
      <nav class="home-navigation mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3">
        <!-- Logo -->
        <div class="flex min-w-0 items-center gap-3">
          <div class="h-10 w-10 shrink-0 overflow-hidden rounded-lg">
            <img :src="siteLogo || '/logo.svg'" alt="Logo" class="h-full w-full object-contain" />
          </div>
          <span class="[overflow-wrap:anywhere] text-base sm:text-lg font-semibold tracking-tight">{{ siteName }}</span>
        </div>

        <!-- Nav Actions -->
        <div class="flex flex-wrap items-center gap-2">
          <!-- Language Switcher -->
          <LocaleSwitcher />

          <!-- Doc Link -->
          <a
            v-if="docUrl"
            :href="docUrl"
            target="_blank"
            rel="noopener noreferrer"
            class="rounded-lg p-2 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700 dark:text-dark-400 dark:hover:bg-dark-800 dark:hover:text-white"
            :title="t('home.viewDocs')"
          >
            <Icon name="book" size="md" />
          </a>

          <!-- Model Plaza Link -->
          <router-link
            v-if="showModelPlazaEntry"
            to="/model-plaza"
            class="inline-flex items-center gap-1.5 rounded-lg p-2 text-sm text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700 dark:text-dark-400 dark:hover:bg-dark-800 dark:hover:text-white"
            :title="t('nav.modelPlaza')"
          >
            <Icon name="grid" size="md" />
            <span class="hidden sm:inline">{{ t('nav.modelPlaza') }}</span>
          </router-link>

          <!-- Theme Toggle -->
          <button
            @click="toggleTheme"
            class="rounded-lg p-2 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700 dark:text-dark-400 dark:hover:bg-dark-800 dark:hover:text-white"
            :title="isDark ? t('home.switchToLight') : t('home.switchToDark')"
          >
            <Icon v-if="isDark" name="sun" size="md" />
            <Icon v-else name="moon" size="md" />
          </button>

          <!-- Login / Dashboard Button -->
          <router-link
            v-if="isAuthenticated"
            :to="dashboardPath"
            class="inline-flex items-center gap-1.5 rounded-full bg-gray-900 py-1 pl-1 pr-2.5 transition-colors hover:bg-gray-800 dark:bg-gray-800 dark:hover:bg-gray-700"
          >
            <span
              class="flex h-5 w-5 items-center justify-center rounded-full bg-gradient-to-br from-primary-400 to-primary-600 text-[10px] font-semibold text-white"
            >
              {{ userInitial }}
            </span>
            <span class="text-xs font-medium text-white">{{ t('home.dashboard') }}</span>
            <svg
              class="h-3 w-3 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M4.5 19.5l15-15m0 0H8.25m11.25 0v11.25"
              />
            </svg>
          </router-link>
          <router-link
            v-else
            to="/login"
            class="inline-flex items-center rounded-lg bg-primary-700 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-gray-800 dark:bg-gray-800 dark:hover:bg-gray-700"
          >
            {{ t('home.login') }}
          </router-link>
        </div>
      </nav>
    </header>

    <main class="home-content">
      <div class="home-hero">
        <div class="home-introduction">
          <h1>{{ siteName }}</h1>
          <p class="home-subtitle">{{ siteSubtitle }}</p>
          <router-link
            :to="isAuthenticated ? dashboardPath : '/login'"
            class="btn btn-primary home-start"
          >
            {{ isAuthenticated ? t('home.goToDashboard') : t('home.getStarted') }}
            <Icon name="arrowRight" size="md" :stroke-width="2" />
          </router-link>
          <div class="home-service-notes">
            <span>{{ t('home.tags.officialGpt') }}</span>
            <span>{{ t('home.tags.studentPricing') }}</span>
            <span>{{ t('home.tags.usageBilling') }}</span>
          </div>
        </div>

        <aside class="home-model" :aria-label="t('home.providers.title')">
          <div class="home-model-heading">
            <h2>GPT</h2>
            <p>{{ t('home.providers.description') }}</p>
            <span class="home-model-status">{{ t('home.providers.supported') }}</span>
          </div>
          <div class="terminal-container">
            <div class="terminal-window">
              <div class="terminal-header">OpenAI API</div>
              <div class="terminal-body">
                <div class="code-line"><span class="code-prompt">$</span> curl -X POST</div>
                <div class="code-line code-url">/v1/chat/completions</div>
                <div class="code-line code-success">200 OK</div>
                <div class="code-line code-response">{ "object": "chat.completion" }</div>
              </div>
            </div>
          </div>
        </aside>
      </div>

      <section class="home-features">
        <div v-for="(feature, index) in features" :key="feature.title" class="home-feature">
          <span class="home-feature-number" aria-hidden="true">{{ String(index + 1).padStart(2, '0') }}</span>
          <h3>{{ feature.title }}</h3>
          <p>{{ feature.description }}</p>
        </div>
      </section>
    </main>

    <!-- Footer -->
    <footer class="relative z-10 border-t border-gray-200/50 px-6 py-8 dark:border-dark-800/50">
      <div
        class="mx-auto flex max-w-6xl flex-col items-center justify-center gap-4 text-center sm:flex-row sm:text-left"
      >
        <p class="text-sm text-gray-500 dark:text-dark-400">
          &copy; {{ currentYear }} {{ siteName }}. {{ t('home.footer.allRightsReserved') }}
        </p>
        <div v-if="docUrl" class="flex items-center gap-4">
          <a
            :href="docUrl"
            target="_blank"
            rel="noopener noreferrer"
            class="text-sm text-gray-500 transition-colors hover:text-gray-700 dark:text-dark-400 dark:hover:text-white"
          >
            {{ t('home.docs') }}
          </a>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore, useAppStore } from '@/stores'
import LocaleSwitcher from '@/components/common/LocaleSwitcher.vue'
import Icon from '@/components/icons/Icon.vue'
import { DEFAULT_SITE_SUBTITLE, resolveDocumentationUrl, resolveSiteName, resolveSiteSubtitle } from '@/utils/siteBranding'
import { sanitizeUrl } from '@/utils/url'
import { FeatureFlags, isFeatureFlagEnabled } from '@/utils/featureFlags'

const { t } = useI18n()

const authStore = useAuthStore()
const appStore = useAppStore()

const features = computed(() => [
  { title: t('home.features.officialService'), description: t('home.features.officialServiceDesc') },
  { title: t('home.features.studentPricing'), description: t('home.features.studentPricingDesc') },
  { title: t('home.features.usageBilling'), description: t('home.features.usageBillingDesc') }
])

// Site settings - directly from appStore (already initialized from injected config)
const siteName = computed(() => resolveSiteName(appStore.cachedPublicSettings?.site_name || appStore.siteName))
const siteLogo = computed(() => sanitizeUrl(appStore.cachedPublicSettings?.site_logo || appStore.siteLogo || '', { allowRelative: true, allowDataUrl: true }))
const siteSubtitle = computed(() => {
  const subtitle = resolveSiteSubtitle(appStore.cachedPublicSettings?.site_subtitle)
  return subtitle === DEFAULT_SITE_SUBTITLE ? t('home.heroDescription') : subtitle
})
const docUrl = computed(() => resolveDocumentationUrl(appStore.cachedPublicSettings?.doc_url || appStore.docUrl))
const homeContent = computed(() => appStore.cachedPublicSettings?.home_content || '')
const hasHomeContent = computed(() => homeContent.value.trim().length > 0)
const compactHomeEnabled = computed(() => appStore.cachedPublicSettings?.compact_home_enabled === true)
const modelPlazaEnabled = computed(() => isFeatureFlagEnabled(FeatureFlags.modelPlaza))

// Check if homeContent is a URL (for iframe display)
const isHomeContentUrl = computed(() => {
  const content = homeContent.value.trim()
  return content.startsWith('http://') || content.startsWith('https://')
})

// Theme
const isDark = ref(document.documentElement.classList.contains('dark'))


// Auth state
const isAuthenticated = computed(() => authStore.isAuthenticated)
const modelPlazaRequiresAuth = computed(
  () => appStore.cachedPublicSettings?.model_plaza_require_auth === true,
)
const showModelPlazaEntry = computed(
  () => modelPlazaEnabled.value && (isAuthenticated.value || !modelPlazaRequiresAuth.value),
)
const isAdmin = computed(() => authStore.isAdmin)
const dashboardPath = computed(() => isAdmin.value ? '/admin/dashboard' : '/dashboard')
const userInitial = computed(() => {
  const user = authStore.user
  if (!user || !user.email) return ''
  return user.email.charAt(0).toUpperCase()
})

// Current year for footer
const currentYear = computed(() => new Date().getFullYear())

// Toggle theme
function toggleTheme() {
  isDark.value = !isDark.value
  document.documentElement.classList.toggle('dark', isDark.value)
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
}

// Initialize theme
function initTheme() {
  const savedTheme = localStorage.getItem('theme')
  if (
    savedTheme === 'dark' ||
    (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)
  ) {
    isDark.value = true
    document.documentElement.classList.add('dark')
  }
}

onMounted(() => {
  initTheme()

  // Check auth state
  authStore.checkAuth()

  // Ensure public settings are loaded (will use cache if already loaded from injected config)
  if (!appStore.publicSettingsLoaded) {
    appStore.fetchPublicSettings()
  }
})
</script>

<style scoped>
.relay-home::before {
  content: '';
  height: 5px;
  background: linear-gradient(to right, #e8340c 25%, #f5a100 25% 50%, #81b934 50% 75%, #0b75be 75%);
}

.home-navigation {
  min-height: 44px;
}

.home-content {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 72px 24px 64px;
  flex: 1;
}

.home-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(0, 1fr);
  gap: 64px;
  align-items: center;
}

.home-introduction {
  min-width: 0;
}

.home-introduction h1 {
  @apply text-gray-900 dark:text-white;
  font-size: clamp(40px, 5.4vw, 76px);
  font-weight: 650;
  line-height: 1.15;
  letter-spacing: -0.045em;
  overflow-wrap: anywhere;
  max-width: 9em;
}

.home-subtitle {
  @apply text-gray-600 dark:text-dark-300;
  max-width: 30em;
  margin-top: 28px;
  font-size: 18px;
  line-height: 1.8;
  overflow-wrap: anywhere;
}

.home-start {
  margin-top: 32px;
  min-height: 48px;
  padding: 12px 24px;
  border-radius: 4px;
}

.home-service-notes {
  @apply text-gray-500 dark:text-dark-400;
  display: flex;
  flex-wrap: wrap;
  gap: 12px 24px;
  margin-top: 28px;
  font-size: 12px;
}

.home-service-notes span {
  display: flex;
  align-items: center;
  gap: 8px;
}

.home-service-notes span::before {
  content: '';
  width: 5px;
  height: 5px;
  background: #e8340c;
}

.home-service-notes span:nth-child(2)::before {
  background: #f5a100;
}

.home-service-notes span:nth-child(3)::before {
  background: #81b934;
}

.home-model {
  min-width: 0;
  border-radius: 4px;
  overflow: hidden;
  background: #0b75be;
  color: white;
}

.home-model-heading {
  padding: 32px;
}

.home-model h2 {
  font-size: clamp(64px, 8vw, 112px);
  font-weight: 650;
  letter-spacing: -0.075em;
  line-height: 1;
}

.home-model p {
  margin-top: 16px;
  font-size: 14px;
  line-height: 1.6;
}

.home-model-status {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: 28px;
  font-size: 12px;
}

.home-model-status::before {
  content: '';
  height: 7px;
  width: 7px;
  border-radius: 50%;
  background: #d2efb0;
}

.terminal-container {
  border-top: 1px solid rgb(255 255 255 / 0.2);
}

.terminal-window {
  background: #162c40;
}

.terminal-header {
  padding: 14px 24px;
  border-bottom: 1px solid rgb(255 255 255 / 0.12);
  color: #b6cbdc;
  font-size: 11px;
}

.terminal-body {
  padding: 20px 24px;
  font-family: ui-monospace, monospace;
  font-size: 12px;
  line-height: 2;
}

.code-line {
  overflow-wrap: anywhere;
}

.code-prompt {
  color: #b8dd86;
  padding-right: 6px;
}

.code-url {
  color: #f8c563;
}

.code-success {
  margin-top: 12px;
  color: #b8dd86;
}

.code-response {
  color: #c8deee;
}

.home-features {
  margin-top: 72px;
  border-top: 2px solid #162c40;
}

.home-feature {
  @apply border-b border-gray-200 dark:border-dark-700;
  display: grid;
  grid-template-columns: 56px minmax(0, 1fr) minmax(0, 1.2fr);
  align-items: start;
  gap: 24px;
  padding: 28px 0;
}

.home-feature-number {
  font-family: ui-monospace, monospace;
  font-size: 13px;
  color: #0b75be;
  padding-top: 4px;
}

.home-feature:nth-child(2) .home-feature-number {
  color: #a06400;
}

.home-feature:nth-child(3) .home-feature-number {
  color: #487819;
}

.home-feature h3 {
  @apply text-gray-900 dark:text-white;
  font-size: 20px;
  font-weight: 600;
  line-height: 1.5;
}

.home-feature p {
  @apply text-gray-500 dark:text-dark-300;
  font-size: 14px;
  line-height: 1.8;
}

.dark .home-features {
  border-top-color: #aac5dd;
}

.dark .home-feature-number {
  color: #82c1ed;
}

.dark .home-feature:nth-child(2) .home-feature-number {
  color: #f8c563;
}

.dark .home-feature:nth-child(3) .home-feature-number {
  color: #b8dd86;
}

.compact-home-content > div {
  text-align: left;
}

.compact-home-content img {
  margin-left: 0;
}

.compact-home-content h1 {
  line-height: 1.25;
  letter-spacing: -0.04em;
}

@media (max-width: 767px) {
  .home-content {
    padding: 40px 20px;
  }

  .home-hero {
    grid-template-columns: 1fr;
    gap: 36px;
  }

  .home-introduction h1 {
    font-size: 44px;
    max-width: 100%;
  }

  .home-subtitle {
    margin-top: 20px;
    font-size: 16px;
  }

  .home-model {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  }

  .home-model-heading {
    padding: 24px 20px;
  }

  .home-model h2 {
    font-size: 52px;
  }

  .home-model p {
    font-size: 12px;
  }

  .home-model-status {
    margin-top: 20px;
  }

  .terminal-container {
    border-top: 0;
    border-left: 1px solid rgb(255 255 255 / 0.2);
  }

  .terminal-header {
    padding: 14px 16px;
  }

  .terminal-body {
    padding: 16px;
    font-size: 11px;
  }

  .home-features {
    margin-top: 40px;
  }

  .home-feature {
    grid-template-columns: 28px minmax(0, 1fr);
    gap: 8px 16px;
    padding: 24px 0;
  }

  .home-feature h3 {
    font-size: 18px;
  }

  .home-feature p {
    grid-column: 2;
  }

}

@media (max-width: 359px) {
  .home-model {
    grid-template-columns: 1fr;
  }

  .terminal-container {
    border-left: 0;
    border-top: 1px solid rgb(255 255 255 / 0.2);
  }

}
</style>
