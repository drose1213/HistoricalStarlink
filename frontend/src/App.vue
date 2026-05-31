<template>
  <router-view v-slot="{ Component }">
    <transition name="cy-fade" mode="out-in">
      <component :is="Component" />
    </transition>
  </router-view>

  <div class="toast-container">
    <transition-group name="cy-slide-up">
      <div
        v-for="toast in appStore.toasts"
        :key="toast.id"
        class="cy-toast"
        :class="`cy-toast--${toast.type}`"
        @click="appStore.removeToast(toast.id)"
      >
        {{ toast.message }}
      </div>
    </transition-group>
  </div>
</template>

<script setup lang="ts">
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 300;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
</style>
