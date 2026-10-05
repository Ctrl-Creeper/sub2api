<template>
  <div class="auth-layout">
    <div class="auth-frame">
      <aside class="auth-brand-panel">
        <div v-if="settingsLoaded" class="auth-brand-content">
          <img :src="siteLogo || '/logo.svg'" :alt="siteName" class="auth-logo" />
          <h1>{{ siteName }}</h1>
          <p>{{ siteSubtitle }}</p>
        </div>
        <div class="auth-brand-rule" aria-hidden="true"></div>
      </aside>

      <div class="auth-form-panel">
        <div class="auth-card">
          <slot />
        </div>
        <div class="mt-6 text-center text-sm">
          <slot name="footer" />
        </div>
        <div class="mt-8 text-center text-xs text-gray-500 dark:text-dark-400">
          &copy; {{ currentYear }} {{ siteName }}. All rights reserved.
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useAppStore } from '@/stores'
import { sanitizeUrl } from '@/utils/url'
import { resolveSiteName, resolveSiteSubtitle } from '@/utils/siteBranding'

const appStore = useAppStore()
const siteName = computed(() => resolveSiteName(appStore.siteName))
const siteLogo = computed(() => sanitizeUrl(appStore.siteLogo || '', { allowRelative: true, allowDataUrl: true }))
const siteSubtitle = computed(() => resolveSiteSubtitle(appStore.cachedPublicSettings?.site_subtitle))
const settingsLoaded = computed(() => appStore.publicSettingsLoaded)
const currentYear = computed(() => new Date().getFullYear())

onMounted(() => {
  appStore.fetchPublicSettings()
})
</script>

<style scoped>
.auth-layout {
  @apply flex min-h-screen items-center justify-center bg-gray-50 p-4 dark:bg-dark-950 sm:p-8;
}

.auth-frame {
  @apply grid w-full max-w-5xl overflow-hidden rounded-2xl border border-gray-200 bg-white dark:border-dark-700 dark:bg-dark-900;
  box-shadow: 0 20px 80px -32px rgb(11 117 190 / 0.18);
}

.auth-brand-panel {
  @apply relative flex flex-col justify-center p-6 sm:p-8;
  background: #0b75be;
  color: #ffffff;
}

.auth-brand-content {
  @apply relative z-10;
}

.auth-logo {
  @apply mb-5 h-12 w-12 sm:h-14 sm:w-14;
}

.auth-brand-content h1 {
  @apply text-3xl font-semibold tracking-tight sm:text-4xl;
  overflow-wrap: anywhere;
}

.auth-brand-content p {
  @apply mt-4 max-w-xs text-sm leading-7;
  color: #e5eef7;
  overflow-wrap: anywhere;
}

.auth-brand-rule {
  @apply mt-8 h-px w-16;
  background: #f5a100;
}

.auth-form-panel {
  @apply min-w-0 px-6 py-8 sm:p-10;
}

.auth-card {
  @apply mx-auto w-full max-w-md;
}

@media (min-width: 768px) {
  .auth-frame {
    grid-template-columns: 0.85fr 1.15fr;
    min-height: 620px;
  }

  .auth-brand-panel {
    @apply p-12;
  }

  .auth-brand-rule {
    @apply absolute bottom-12 left-12;
  }

  .auth-form-panel {
    @apply flex flex-col justify-center p-12;
  }
}

@media (max-width: 767px) {
  .auth-brand-content {
    @apply grid items-center gap-x-4;
    grid-template-columns: auto 1fr;
  }

  .auth-logo {
    @apply row-span-2 mb-0 h-12 w-12;
  }

  .auth-brand-content h1 {
    @apply text-2xl;
  }

  .auth-brand-content p {
    @apply mt-1 max-w-none text-xs leading-5;
  }

  .auth-brand-rule {
    @apply hidden;
  }
}
</style>
