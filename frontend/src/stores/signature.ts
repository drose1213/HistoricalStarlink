import { defineStore } from 'pinia'
import { ref } from 'vue'
import { signatureApi } from '@/api/signature'
import type { SignatureRecord } from '@/types'

export const useSignatureStore = defineStore('signature', () => {
  const signatures = ref<SignatureRecord[]>([])
  const userSignatures = ref<SignatureRecord[]>([])
  const currentSignature = ref<SignatureRecord | null>(null)
  const isLoading = ref(false)

  async function uploadSignature(formData: FormData) {
    isLoading.value = true
    try {
      const res = await signatureApi.uploadSignature(formData)
      currentSignature.value = res.data
      userSignatures.value.unshift(res.data)
      return res.data
    } finally {
      isLoading.value = false
    }
  }

  async function fetchSignatures(page = 1) {
    isLoading.value = true
    try {
      const res = await signatureApi.getSignatureRecords(page)
      signatures.value = res.data.items
      return res.data
    } finally {
      isLoading.value = false
    }
  }

  async function fetchUserSignatures() {
    isLoading.value = true
    try {
      const res = await signatureApi.getUserSignatures()
      userSignatures.value = res.data
      return res.data
    } finally {
      isLoading.value = false
    }
  }

  async function deleteSignature(id: number) {
    await signatureApi.deleteSignature(id)
    signatures.value = signatures.value.filter(s => s.id !== id)
    userSignatures.value = userSignatures.value.filter(s => s.id !== id)
  }

  return {
    signatures,
    userSignatures,
    currentSignature,
    isLoading,
    uploadSignature,
    fetchSignatures,
    fetchUserSignatures,
    deleteSignature
  }
})
