<template>
  <div class="auth-view">
    <div class="auth-bg">
      <div class="auth-stars"></div>
    </div>

    <div class="auth-container">
      <div class="auth-card">
        <div class="auth-logo">
          <span class="logo-glyph">◇</span>
          <h1 class="logo-text">文明星链</h1>
          <p class="logo-sub">历史探索之旅</p>
        </div>

        <div class="auth-tabs">
          <button
            class="tab-btn"
            :class="{ active: mode === 'login' }"
            @click="switchMode('login')"
          >
            登录
          </button>
          <button
            class="tab-btn"
            :class="{ active: mode === 'register' }"
            @click="switchMode('register')"
          >
            注册
          </button>
          <div class="tab-indicator" :class="{ right: mode === 'register' }"></div>
        </div>

        <form class="auth-form" @submit.prevent="handleSubmit">
          <Transition name="field-fade" mode="out-in">
            <div v-if="mode === 'register'" key="reg-user" class="field-group">
              <label class="field-label">用户名</label>
              <input
                v-model="form.username"
                class="cy-input auth-input"
                placeholder="设置用户名"
                autocomplete="username"
              />
            </div>
          </Transition>

          <Transition name="field-fade" mode="out-in">
            <div v-if="mode === 'login'" key="login-user" class="field-group">
              <label class="field-label">用户名 / 邮箱</label>
              <input
                v-model="form.username"
                class="cy-input auth-input"
                placeholder="输入用户名或邮箱"
                autocomplete="username"
              />
            </div>
          </Transition>

          <Transition name="field-fade" mode="out-in">
            <div v-if="mode === 'register'" key="reg-email" class="field-group">
              <label class="field-label">邮箱</label>
              <div class="code-row">
                <input
                  v-model="form.email"
                  type="email"
                  class="cy-input auth-input code-input"
                  placeholder="输入邮箱地址"
                  autocomplete="email"
                />
                <button
                  type="button"
                  class="send-code-btn"
                  :disabled="codeCooldown > 0 || codeSending"
                  @click="handleSendCode"
                >
                  <span v-if="codeSending" class="btn-loading"></span>
                  <span v-else>{{ codeCooldown > 0 ? `${codeCooldown}s` : '获取验证码' }}</span>
                </button>
              </div>
            </div>
          </Transition>

          <Transition name="field-fade" mode="out-in">
            <div v-if="mode === 'register'" key="reg-code" class="field-group">
              <label class="field-label">邮箱验证码</label>
              <input
                v-model="form.emailCode"
                class="cy-input auth-input"
                placeholder="输入6位验证码"
                maxlength="6"
                inputmode="numeric"
              />
            </div>
          </Transition>

          <div class="field-group">
            <label class="field-label">密码</label>
            <input
              v-model="form.password"
              type="password"
              class="cy-input auth-input"
              placeholder="输入密码"
              autocomplete="current-password"
            />
          </div>

          <Transition name="field-fade" mode="out-in">
            <div v-if="mode === 'register'" key="reg-nick" class="field-group">
              <label class="field-label">昵称 <span class="optional">（选填）</span></label>
              <input
                v-model="form.nickname"
                class="cy-input auth-input"
                placeholder="给自己取个昵称"
              />
            </div>
          </Transition>

          <div v-if="error" class="auth-error" :class="{ 'auth-error--hint': errorHint }">
            <span class="error-icon">{{ errorHint ? '💡' : '⚠' }}</span>
            <span>{{ error }}</span>
            <button
              v-if="errorHint"
              type="button"
              class="error-action"
              @click="switchMode('register')"
            >
              去注册 →
            </button>
          </div>

          <button
            type="submit"
            class="cy-btn auth-submit"
            :disabled="submitting"
          >
            <span v-if="submitting" class="btn-loading"></span>
            <span v-else>{{ mode === 'login' ? '进入星链' : '开启旅程' }}</span>
          </button>
        </form>

        <div class="auth-footer">
          <button class="skip-btn" @click="goHome">先逛逛 →</button>
        </div>
      </div>

      <div class="auth-decor">
        <div class="decor-ring ring-1"></div>
        <div class="decor-ring ring-2"></div>
        <div class="decor-ring ring-3"></div>
      </div>
    </div>

    <div class="cy-scanlines"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'

const router = useRouter()
const authStore = useAuthStore()
const appStore = useAppStore()

const mode = ref<'login' | 'register'>('login')
const submitting = ref(false)
const error = ref('')
const errorHint = ref(false)
const codeSending = ref(false)
const codeCooldown = ref(0)
let cooldownTimer: ReturnType<typeof setInterval> | null = null

const form = reactive({
  username: '',
  email: '',
  emailCode: '',
  password: '',
  nickname: ''
})

function switchMode(target: 'login' | 'register') {
  mode.value = target
  error.value = ''
  errorHint.value = false
}

async function handleSendCode() {
  error.value = ''
  errorHint.value = false

  if (!form.email.trim()) {
    error.value = '请先输入邮箱'
    return
  }
  const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRe.test(form.email.trim())) {
    error.value = '邮箱格式不正确'
    return
  }

  codeSending.value = true
  try {
    const res = await authStore.sendCode(form.email.trim().toLowerCase())
    if (res.code === 200) {
      appStore.showToast('success', '验证码已发送，请查收邮箱')
      codeCooldown.value = 60
      cooldownTimer = setInterval(() => {
        codeCooldown.value--
        if (codeCooldown.value <= 0) {
          clearInterval(cooldownTimer!)
          cooldownTimer = null
        }
      }, 1000)
    } else {
      error.value = res.message || '验证码发送失败'
    }
  } catch (e: any) {
    error.value = e?.response?.data?.detail || '验证码发送失败，请稍后重试'
  } finally {
    codeSending.value = false
  }
}

async function handleSubmit() {
  error.value = ''
  errorHint.value = false

  if (!form.username.trim()) {
    error.value = mode.value === 'login' ? '请输入用户名' : '请设置用户名'
    return
  }
  if (mode.value === 'register') {
    const u = form.username.trim()
    if (u.length < 3) {
      error.value = '用户名至少3个字符'
      return
    }
    if (!/^[\w\u4e00-\u9fa5-]+$/.test(u)) {
      error.value = '用户名只能包含字母、数字、下划线、连字符和中文'
      return
    }
  }
  if (mode.value === 'register' && !form.email.trim()) {
    error.value = '请输入邮箱'
    return
  }
  if (mode.value === 'register') {
    const em = form.email.trim()
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(em)) {
      error.value = '邮箱格式不正确'
      return
    }
  }
  if (mode.value === 'register' && !form.emailCode.trim()) {
    error.value = '请输入邮箱验证码'
    return
  }
  if (!form.password || form.password.length < 6) {
    error.value = '密码至少6位'
    return
  }

  submitting.value = true
  try {
    let result
    if (mode.value === 'login') {
      result = await authStore.login(form.username, form.password)
    } else {
      result = await authStore.register(
        form.username,
        form.email.trim().toLowerCase(),
        form.emailCode.trim(),
        form.password,
        form.nickname || undefined
      )
    }
    if (result.success) {
      appStore.showToast('success', '欢迎来到文明星链！')
      router.push({ name: 'Home' })
    } else {
      error.value = result.message
      if (mode.value === 'login' && /未注册/.test(result.message)) {
        errorHint.value = true
      }
    }
  } catch (e: any) {
    const detail = e?.response?.data?.detail || '操作失败，请稍后重试'
    error.value = detail
    if (mode.value === 'login' && /未注册/.test(detail)) {
      errorHint.value = true
    }
  } finally {
    submitting.value = false
  }
}

function goHome() {
  router.push({ name: 'Home' })
}

onUnmounted(() => {
  if (cooldownTimer) clearInterval(cooldownTimer)
})
</script>

<style scoped>
.auth-view {
  width: 100%;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  position: relative;
  background: var(--bg-primary);
}

.auth-bg {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at 30% 20%, rgba(49, 247, 255, 0.06), transparent 50%),
    radial-gradient(ellipse at 70% 80%, rgba(255, 53, 243, 0.04), transparent 50%),
    linear-gradient(180deg, #05070d 0%, #081525 50%, #05070d 100%);
}

.auth-stars {
  position: absolute;
  inset: 0;
  background-image:
    radial-gradient(1px 1px at 10% 15%, rgba(49,247,255,0.6), transparent),
    radial-gradient(1px 1px at 25% 60%, rgba(255,255,255,0.4), transparent),
    radial-gradient(1px 1px at 45% 30%, rgba(255,53,243,0.5), transparent),
    radial-gradient(1px 1px at 60% 80%, rgba(49,247,255,0.4), transparent),
    radial-gradient(1px 1px at 80% 25%, rgba(255,255,255,0.5), transparent),
    radial-gradient(1.5px 1.5px at 15% 85%, rgba(49,247,255,0.7), transparent),
    radial-gradient(1px 1px at 50% 50%, rgba(255,53,243,0.3), transparent),
    radial-gradient(1px 1px at 90% 70%, rgba(255,255,255,0.4), transparent),
    radial-gradient(1.5px 1.5px at 35% 90%, rgba(212,168,75,0.5), transparent),
    radial-gradient(1px 1px at 75% 10%, rgba(49,247,255,0.5), transparent);
  animation: starsTwinkle 8s ease-in-out infinite alternate;
}

@keyframes starsTwinkle {
  0% { opacity: 0.6; }
  100% { opacity: 1; }
}

.auth-container {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 60px;
}

.auth-card {
  width: 400px;
  padding: 36px 32px 28px;
  background: rgba(8, 15, 28, 0.88);
  border: 1px solid var(--border-cyan);
  border-radius: var(--radius-md);
  backdrop-filter: blur(16px);
  box-shadow: 0 0 40px rgba(49, 247, 255, 0.08), 0 0 80px rgba(49, 247, 255, 0.04);
}

.auth-logo {
  text-align: center;
  margin-bottom: 28px;
}

.logo-glyph {
  display: inline-block;
  font-size: 32px;
  color: var(--cyan-core);
  text-shadow: 0 0 20px var(--cyan-core);
  margin-bottom: 8px;
  animation: logoPulse 3s ease-in-out infinite;
}

@keyframes logoPulse {
  0%, 100% { text-shadow: 0 0 20px var(--cyan-core); transform: scale(1); }
  50% { text-shadow: 0 0 30px var(--cyan-core), 0 0 50px rgba(49,247,255,0.3); transform: scale(1.05); }
}

.logo-text {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: 2px;
  text-shadow: 0 0 16px rgba(49, 247, 255, 0.4);
}

.logo-sub {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
  font-family: var(--font-mono);
}

.auth-tabs {
  display: flex;
  position: relative;
  margin-bottom: 24px;
  background: var(--bg-input);
  border-radius: var(--radius-full);
  border: 1px solid var(--border-subtle);
  padding: 3px;
}

.tab-btn {
  flex: 1;
  padding: 8px 0;
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: color var(--transition-fast);
  position: relative;
  z-index: 1;
}

.tab-btn.active {
  color: #ffffff;
}

.tab-indicator {
  position: absolute;
  top: 3px;
  left: 3px;
  width: calc(50% - 3px);
  height: calc(100% - 6px);
  background: linear-gradient(135deg, rgba(49, 247, 255, 0.2), rgba(255, 53, 243, 0.1));
  border: 1px solid var(--border-cyan);
  border-radius: var(--radius-full);
  transition: transform 0.3s ease;
}

.tab-indicator.right {
  transform: translateX(100%);
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.optional {
  font-weight: 400;
  opacity: 0.6;
}

.auth-input {
  width: 100%;
  padding: 10px 14px;
  font-size: 14px;
}

.code-row {
  display: flex;
  gap: 8px;
}

.code-input {
  flex: 1;
}

.send-code-btn {
  flex-shrink: 0;
  width: 110px;
  padding: 10px 8px;
  font-size: 12px;
  font-weight: 600;
  color: var(--cyan-core);
  background: rgba(49, 247, 255, 0.08);
  border: 1px solid var(--border-cyan);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
  display: flex;
  align-items: center;
  justify-content: center;
}

.send-code-btn:hover:not(:disabled) {
  background: rgba(49, 247, 255, 0.15);
  box-shadow: 0 0 12px rgba(49, 247, 255, 0.2);
}

.send-code-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  color: var(--text-muted);
}

.auth-error {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: rgba(255, 60, 60, 0.1);
  border: 1px solid rgba(255, 60, 60, 0.3);
  border-radius: var(--radius-sm);
  font-size: 12px;
  color: #ff6b6b;
}

.auth-error--hint {
  background: rgba(49, 247, 255, 0.06);
  border-color: rgba(49, 247, 255, 0.25);
  color: #6be0ff;
}

.error-icon {
  font-size: 14px;
  flex-shrink: 0;
}

.error-action {
  margin-left: auto;
  flex-shrink: 0;
  padding: 2px 10px;
  font-size: 12px;
  font-weight: 600;
  color: #00e5ff;
  background: rgba(49, 247, 255, 0.12);
  border: 1px solid rgba(49, 247, 255, 0.4);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.error-action:hover {
  background: rgba(49, 247, 255, 0.22);
  box-shadow: 0 0 8px rgba(49, 247, 255, 0.3);
}

.auth-submit {
  width: 100%;
  padding: 12px;
  margin-top: 4px;
  font-size: 14px;
  font-weight: 600;
  font-family: var(--font-serif);
  background: linear-gradient(135deg, rgba(49, 247, 255, 0.15), rgba(255, 53, 243, 0.1));
  border: 1px solid var(--cyan-core);
  color: #ffffff;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-normal);
  box-shadow: 0 0 16px rgba(49, 247, 255, 0.2);
}

.auth-submit:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(49, 247, 255, 0.25), rgba(255, 53, 243, 0.18));
  box-shadow: 0 0 24px rgba(49, 247, 255, 0.4), 0 0 40px rgba(49, 247, 255, 0.15);
  transform: translateY(-1px);
}

.auth-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-loading {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.auth-footer {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.skip-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 12px;
  cursor: pointer;
  padding: 4px 8px;
  transition: color var(--transition-fast);
}

.skip-btn:hover {
  color: var(--cyan-core);
}

.auth-decor {
  position: relative;
  width: 280px;
  height: 280px;
}

.decor-ring {
  position: absolute;
  border-radius: 50%;
  border: 1px solid;
  animation: ringRotate linear infinite;
}

.ring-1 {
  inset: 0;
  border-color: rgba(49, 247, 255, 0.15);
  animation-duration: 20s;
}

.ring-2 {
  inset: 30px;
  border-color: rgba(255, 53, 243, 0.12);
  animation-duration: 15s;
  animation-direction: reverse;
}

.ring-3 {
  inset: 60px;
  border-color: rgba(212, 168, 75, 0.1);
  animation-duration: 25s;
}

.decor-ring::before {
  content: '';
  position: absolute;
  top: -3px;
  left: 50%;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  transform: translateX(-50%);
}

.ring-1::before {
  background: var(--cyan-core);
  box-shadow: 0 0 10px var(--cyan-core);
}

.ring-2::before {
  background: var(--pink-core);
  box-shadow: 0 0 10px var(--pink-core);
}

.ring-3::before {
  background: var(--accent-gold);
  box-shadow: 0 0 10px var(--accent-gold);
}

@keyframes ringRotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.field-fade-enter-active,
.field-fade-leave-active {
  transition: all 0.25s ease;
}

.field-fade-enter-from {
  opacity: 0;
  transform: translateY(-8px);
}

.field-fade-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

@media (max-width: 768px) {
  .auth-decor {
    display: none;
  }

  .auth-card {
    width: 360px;
    padding: 28px 24px 24px;
  }
}
</style>
