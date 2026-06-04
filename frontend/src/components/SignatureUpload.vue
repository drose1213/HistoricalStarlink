<template>
  <div class="signature-upload">
    <div class="upload-header">
      <h3 class="cy-subtitle">
        <span class="header-icon">✎</span>
        {{ t('signature.title') }}
      </h3>
    </div>

    <div class="upload-area" v-if="!previewUrl">
      <div
        class="dropzone"
        :class="{ 'dropzone--dragover': isDragOver }"
        @dragover.prevent="isDragOver = true"
        @dragleave="isDragOver = false"
        @drop.prevent="handleDrop"
        @click="triggerFileInput"
      >
        <div class="dropzone-icon">⬡</div>
        <p class="dropzone-text">{{ t('signature.dropText') }}</p>
        <p class="dropzone-hint">{{ t('signature.dropHint') }}</p>
      </div>
      <input
        ref="fileInput"
        type="file"
        accept="image/jpeg,image/png"
        style="display: none"
        @change="handleFileSelect"
      />
    </div>

    <div class="preview-area" v-else>
      <div class="preview-image-wrapper">
        <img :src="previewUrl" :alt="t('signature.preview')" class="preview-image" />
        <button class="remove-btn" @click="clearFile">✕</button>
      </div>

      <div class="upload-form">
        <input
          v-model="title"
          class="cy-input"
          :placeholder="t('signature.titlePh')"
          maxlength="50"
        />
        <textarea
          v-model="description"
          class="cy-textarea"
          :placeholder="t('signature.descPh')"
          rows="2"
          maxlength="200"
        ></textarea>
      </div>

      <div class="upload-actions">
        <button
          class="cy-btn cy-btn--pink"
          :disabled="isUploading"
          @click="handleUpload"
        >
          {{ isUploading ? t('signature.uploading') : t('signature.confirm') }}
        </button>
        <button class="cy-btn" @click="clearFile">{{ t('signature.cancel') }}</button>
      </div>
    </div>

    <div class="upload-progress" v-if="isUploading">
      <div class="progress-track">
        <div class="progress-bar" :style="{ width: uploadProgress + '%' }"></div>
      </div>
      <span class="progress-text">{{ uploadProgress }}%</span>
    </div>

    <div class="signatures-section" v-if="userSignatures.length > 0">
      <div class="cy-divider"></div>
      <h4 class="signatures-title">{{ t('signature.mySignatures') }}</h4>
      <div class="signatures-grid">
        <div
          v-for="sig in userSignatures"
          :key="sig.id"
          class="signature-card"
        >
          <img :src="sig.image_url" :alt="sig.title" class="signature-thumb" />
          <div class="signature-info">
            <span class="signature-title">{{ sig.title || t('signature.unnamed') }}</span>
            <span class="signature-time">{{ formatDate(sig.created_at) }}</span>
          </div>
          <button class="delete-btn" @click="handleDelete(sig.id)">✕</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useSignatureStore } from '@/stores/signature'
import { useAppStore } from '@/stores/app'
import { useI18n } from '@/composables/useI18n'

const signatureStore = useSignatureStore()
const appStore = useAppStore()
const { t } = useI18n()

const fileInput = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const previewUrl = ref('')
const title = ref('')
const description = ref('')
const isDragOver = ref(false)
const isUploading = ref(false)
const uploadProgress = ref(0)

const userSignatures = computed(() => signatureStore.userSignatures)

function triggerFileInput() {
  fileInput.value?.click()
}

function handleFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files && input.files[0]) {
    validateAndSetFile(input.files[0])
  }
}

function handleDrop(e: DragEvent) {
  isDragOver.value = false
  if (e.dataTransfer?.files && e.dataTransfer.files[0]) {
    validateAndSetFile(e.dataTransfer.files[0])
  }
}

function validateAndSetFile(file: File) {
  if (!['image/jpeg', 'image/png'].includes(file.type)) {
    appStore.showToast('error', t('toast.sigOnlyJpgPng'))
    return
  }
  if (file.size > 5 * 1024 * 1024) {
    appStore.showToast('error', t('toast.sigTooLarge'))
    return
  }
  selectedFile.value = file
  previewUrl.value = URL.createObjectURL(file)
}

function clearFile() {
  selectedFile.value = null
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
  }
  previewUrl.value = ''
  title.value = ''
  description.value = ''
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

async function handleUpload() {
  if (!selectedFile.value) return

  const formData = new FormData()
  formData.append('image', selectedFile.value)
  if (title.value) formData.append('title', title.value)
  if (description.value) formData.append('description', description.value)

  isUploading.value = true
  uploadProgress.value = 0

  const progressInterval = setInterval(() => {
    if (uploadProgress.value < 90) {
      uploadProgress.value += Math.random() * 15
    }
  }, 200)

  try {
    await signatureStore.uploadSignature(formData)
    uploadProgress.value = 100
    appStore.showToast('success', t('toast.sigUploadOk'))
    clearFile()
  } catch {
    appStore.showToast('error', t('toast.sigUploadFail'))
  } finally {
    clearInterval(progressInterval)
    isUploading.value = false
    uploadProgress.value = 0
  }
}

async function handleDelete(id: number) {
  try {
    await signatureStore.deleteSignature(id)
    appStore.showToast('success', t('toast.sigDeleted'))
  } catch {
    appStore.showToast('error', t('toast.deleteFail'))
  }
}

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, '0')}-${d.getDate().toString().padStart(2, '0')}`
}

onMounted(() => {
  signatureStore.fetchUserSignatures()
})
</script>

<style scoped>
.signature-upload {
  padding: 20px;
  background: var(--bg-card);
  border: 1px solid var(--border-cyan);
  border-radius: var(--radius-md);
  backdrop-filter: blur(10px);
  box-shadow: var(--glow-cyan);
}

.upload-header {
  margin-bottom: 16px;
}

.upload-header h3 {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-icon {
  color: var(--cyan-core);
  text-shadow: 0 0 10px var(--cyan-core);
  font-size: 18px;
}

.dropzone {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  border: 2px dashed var(--border-cyan);
  border-radius: var(--radius-md);
  background: var(--bg-input);
  cursor: pointer;
  transition: all 0.3s;
}

.dropzone:hover,
.dropzone--dragover {
  border-color: var(--cyan-core);
  background: rgba(49, 247, 255, 0.06);
  box-shadow: var(--glow-cyan);
}

.dropzone-icon {
  font-size: 40px;
  color: var(--cyan-core);
  text-shadow: 0 0 20px var(--cyan-core);
  margin-bottom: 12px;
  opacity: 0.6;
}

.dropzone-text {
  font-size: 14px;
  color: var(--text-light);
  margin-bottom: 6px;
}

.dropzone-hint {
  font-size: 11px;
  color: var(--text-muted);
}

.preview-area {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.preview-image-wrapper {
  position: relative;
  border-radius: var(--radius-sm);
  overflow: hidden;
  border: 1px solid var(--border-cyan);
}

.preview-image {
  width: 100%;
  max-height: 240px;
  object-fit: contain;
  display: block;
  background: var(--bg-input);
}

.remove-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.7);
  border: 1px solid var(--pink-core);
  color: var(--pink-core);
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.remove-btn:hover {
  background: rgba(255, 53, 243, 0.2);
  box-shadow: 0 0 8px var(--pink-soft);
}

.upload-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.upload-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
}

.upload-progress {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
}

.progress-track {
  flex: 1;
  height: 4px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 2px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, var(--cyan-core), var(--pink-core));
  box-shadow: 0 0 8px var(--cyan-core);
  transition: width 0.3s;
  border-radius: 2px;
}

.progress-text {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--cyan-core);
  min-width: 36px;
  text-align: right;
}

.signatures-section {
  margin-top: 8px;
}

.signatures-title {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 12px;
  letter-spacing: 1px;
}

.signatures-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 240px;
  overflow-y: auto;
}

.signature-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  background: var(--bg-input);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  transition: border-color 0.2s;
}

.signature-card:hover {
  border-color: var(--border-cyan);
}

.signature-thumb {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-sm);
  object-fit: cover;
  border: 1px solid var(--border-subtle);
}

.signature-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.signature-title {
  font-size: 13px;
  color: var(--text-light);
}

.signature-time {
  font-size: 10px;
  font-family: var(--font-mono);
  color: var(--text-muted);
}

.delete-btn {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: transparent;
  border: 1px solid var(--border-pink);
  color: var(--pink-core);
  font-size: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.5;
  transition: all 0.2s;
}

.delete-btn:hover {
  opacity: 1;
  background: rgba(255, 53, 243, 0.15);
  box-shadow: 0 0 8px var(--pink-soft);
}
</style>
