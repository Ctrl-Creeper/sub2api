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
  @apply flex min-h-screen items-center justify-center bg-gray-50 dark:bg-dark-950;
  padding: 48px 24px;
}

.auth-frame {
  width: 100%;
  max-width: 600px;
}

.auth-brand-panel {
  @apply text-gray-900 dark:text-white;
  position: relative;
  margin-bottom: 28px;
}

.auth-brand-content {
  display: grid;
  grid-template-columns: 56px minmax(0, 1fr);
  gap: 4px 20px;
  align-items: center;
}

.auth-logo {
  grid-row: span 2;
  width: 56px;
  height: 56px;
}

.auth-brand-content h1 {
  font-size: 30px;
  font-weight: 650;
  line-height: 1.3;
  letter-spacing: -0.04em;
  overflow-wrap: anywhere;
}

.auth-brand-content p {
  @apply text-gray-500 dark:text-dark-400;
  font-size: 13px;
  line-height: 1.7;
  overflow-wrap: anywhere;
}

.auth-brand-rule {
  height: 4px;
  width: 100%;
  margin-top: 24px;
  background: linear-gradient(to right, #e8340c 25%, #f5a100 25% 50%, #81b934 50% 75%, #0b75be 75%);
}

.auth-form-panel {
  @apply border border-gray-200 bg-white dark:border-dark-700 dark:bg-dark-900;
  border-radius: 4px;
  padding: 40px 48px 28px;
  box-shadow: 0 8px 32px -24px rgb(11 117 190 / 0.25);
}

.auth-card {
  width: 100%;
  min-width: 0;
}

.auth-card :deep(.input) {
  min-height: 46px;
  border-radius: 4px;
}

.auth-card :deep(.btn) {
  min-height: 44px;
  border-radius: 4px;
}

.auth-card :deep(h2) {
  font-size: 28px;
  letter-spacing: -0.04em;
}

@media (max-width: 639px) {
  .auth-layout {
    padding: 32px 16px;
    align-items: flex-start;
  }

  .auth-brand-content {
    grid-template-columns: 44px minmax(0, 1fr);
    gap: 4px 14px;
  }

  .auth-logo {
    width: 44px;
    height: 44px;
  }

  .auth-brand-content h1 {
    font-size: 24px;
  }

  .auth-brand-content p {
    font-size: 12px;
  }

  .auth-form-panel {
    padding: 28px 24px 24px;
  }

}
</style>
