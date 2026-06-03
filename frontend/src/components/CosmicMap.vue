<template>
  <ConstellationMap
    :graph="homeGraph"
    :search-keyword="searchKeyword"
    mode="home"
    @select-event="eventId => emit('selectEvent', eventId)"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import ConstellationMap from '@/components/ConstellationMap.vue'
import { allEvents } from '@/data/events'
import { buildHomeStarlinkGraph } from '@/utils/starlinkGraph'

defineProps<{ searchKeyword?: string }>()

const emit = defineEmits<{
  selectEvent: [id: string]
}>()

const homeGraph = computed(() => buildHomeStarlinkGraph(allEvents))
</script>
