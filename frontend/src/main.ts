import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useAppStore } from './stores/app'
import { loadEvents } from './data/events'
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
}

bootstrap()
