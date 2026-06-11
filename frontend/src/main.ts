import { createApp, nextTick } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useAppStore } from './stores/app'
import { loadEvents } from './data/events'
import { trackEventIfEnabled } from './utils/analytics'
import './styles/global.css'

async function bootstrap() {
  await loadEvents()

  const app = createApp(App)
  const pinia = createPinia()

  app.use(pinia)
  app.use(router)

  // 同步初始化 store 中的 locale 状态,确保 <html lang> 与 data-locale 属性正确
  const appStore = useAppStore()
  appStore.setLocale(appStore.locale)

  app.mount('#app')

  // app_enter 埋点: 用 nextTick 异步触发, 不阻塞应用启动
  // 走 trackEventIfEnabled 包装, 支持 ?analytics=off 关闭 (演示用)
  nextTick(() => {
    trackEventIfEnabled('app_enter', {
      user_agent: typeof navigator !== 'undefined' ? navigator.userAgent : '',
      referrer: typeof document !== 'undefined' ? document.referrer : '',
      url: typeof window !== 'undefined' ? window.location.href : '',
      path: typeof window !== 'undefined' ? window.location.pathname : '',
    })
  })
}

bootstrap()
