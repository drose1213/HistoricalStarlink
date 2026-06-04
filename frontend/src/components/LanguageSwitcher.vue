<template>
  <div class="lang-switcher" role="group" :aria-label="t('common.language')">
    <button
      type="button"
      class="lang-switcher__btn"
      :class="{ 'is-active': appStore.locale === 'zh' }"
      :aria-pressed="appStore.locale === 'zh'"
      @click="switchTo('zh')"
    >
      <span class="lang-switcher__dot" aria-hidden="true"></span>
      <span class="lang-switcher__label">{{ t('common.chinese') }}</span>
    </button>
    <button
      type="button"
      class="lang-switcher__btn"
      :class="{ 'is-active': appStore.locale === 'en' }"
      :aria-pressed="appStore.locale === 'en'"
      @click="switchTo('en')"
    >
      <span class="lang-switcher__dot" aria-hidden="true"></span>
      <span class="lang-switcher__label">{{ t('common.english') }}</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { useAppStore } from '@/stores/app'
import { useI18n } from '@/composables/useI18n'

const appStore = useAppStore()
const { t, setLocale } = useI18n()

function switchTo(locale: 'zh' | 'en') {
  if (appStore.locale === locale) return
  setLocale(locale)
}
</script>

<style scoped>
.lang-switcher {
  display: inline-flex;
  align-items: center;
  gap: 0;
  padding: 3px;
  border: 1px solid #8bffe1;
  border-radius: 999px;
  background: rgba(2, 5, 11, 0.55);
  box-shadow:
    0 0 0 1px rgba(139, 255, 225, 0.18) inset,
    0 0 14px rgba(139, 255, 225, 0.18);
  backdrop-filter: blur(8px);
  font-family: var(--font-display, 'Orbitron', 'Noto Sans SC', system-ui, sans-serif);
  flex: 0 0 auto;
  max-width: 100%;
  min-width: 0;
  transition: box-shadow 0.25s ease, border-color 0.25s ease;
}

.lang-switcher:hover {
  border-color: #c6ffec;
  box-shadow:
    0 0 0 1px rgba(139, 255, 225, 0.32) inset,
    0 0 22px rgba(139, 255, 225, 0.42);
}

.lang-switcher__btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: rgba(243, 255, 249, 0.55);
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  line-height: 1;
  letter-spacing: 0.02em;
  white-space: nowrap;
  transition:
    color 0.2s ease,
    background 0.2s ease,
    box-shadow 0.2s ease,
    text-shadow 0.2s ease;
  max-width: 100%;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}

.lang-switcher__btn + .lang-switcher__btn {
  margin-left: 0;
}

.lang-switcher__btn:hover {
  color: #c6ffec;
}

.lang-switcher__btn:focus-visible {
  outline: 1px solid #8bffe1;
  outline-offset: 2px;
}

.lang-switcher__btn.is-active {
  color: #0c1a16;
  background: linear-gradient(180deg, #b6ffe6 0%, #8bffe1 100%);
  box-shadow:
    0 0 0 1px rgba(139, 255, 225, 0.6) inset,
    0 0 14px rgba(139, 255, 225, 0.7);
  text-shadow: none;
}

.lang-switcher__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: rgba(139, 255, 225, 0.45);
  box-shadow: 0 0 0 0 rgba(139, 255, 225, 0);
  flex: 0 0 auto;
  transition: background 0.2s ease, box-shadow 0.2s ease;
}

.lang-switcher__btn:hover .lang-switcher__dot {
  background: #c6ffec;
  box-shadow: 0 0 8px rgba(139, 255, 225, 0.7);
}

.lang-switcher__btn.is-active .lang-switcher__dot {
  background: #0c1a16;
  box-shadow: 0 0 6px rgba(12, 26, 22, 0.6);
}

.lang-switcher__label {
  white-space: nowrap;
}

/* Mobile: tighten paddings so the switcher fits a 375px viewport. */
@media (max-width: 480px) {
  .lang-switcher {
    padding: 2px;
  }
  .lang-switcher__btn {
    padding: 3px 9px;
    font-size: 11px;
    gap: 5px;
  }
  .lang-switcher__dot {
    width: 6px;
    height: 6px;
  }
}
</style>
