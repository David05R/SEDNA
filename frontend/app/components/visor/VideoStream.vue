<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'

const props = defineProps({
  src: {
    type: String,
    required: true,
  },
  class: {
    type: String,
    default: '',
  },
  alt: {
    type: String,
    default: 'Video stream',
  },
  // Opciones de optimización
  lowLatency: {
    type: Boolean,
    default: true,
  },
  reconnectDelay: {
    type: Number,
    default: 1000, // ms
  },
  maxReconnectAttempts: {
    type: Number,
    default: 5,
  },
})

const imgRef = ref(null)
const isLoading = ref(true)
const hasError = ref(false)
const reconnectAttempts = ref(0)
let reconnectTimeout = null

// Generar URL única con timestamp para evitar caché
const getStreamUrl = () => {
  if (!props.src) return ''

  // Añadir timestamp para evitar caché del navegador
  const separator = props.src.includes('?') ? '&' : '?'
  return `${props.src}${separator}_t=${Date.now()}`
}

const streamUrl = ref(getStreamUrl())

// Función para reconectar automáticamente
const attemptReconnect = () => {
  if (reconnectAttempts.value >= props.maxReconnectAttempts) {
    console.error(`❌ Max reconnect attempts (${props.maxReconnectAttempts}) reached for ${props.src}`)
    return
  }

  reconnectAttempts.value++
  console.log(`🔄 Reconectando stream (intento ${reconnectAttempts.value}/${props.maxReconnectAttempts})...`)

  reconnectTimeout = setTimeout(() => {
    hasError.value = false
    isLoading.value = true
    streamUrl.value = getStreamUrl()
  }, props.reconnectDelay)
}

// Manejadores de eventos
const handleLoad = () => {
  isLoading.value = false
  hasError.value = false
  reconnectAttempts.value = 0

  if (imgRef.value && props.lowLatency) {
    // Forzar decodificación inmediata
    imgRef.value.decode().catch(() => {
      // Ignorar errores de decodificación
    })
  }
}

const handleError = (event) => {
  console.warn(`⚠️ Error en stream: ${props.src}`, event)
  isLoading.value = false
  hasError.value = true
  attemptReconnect()
}

// Limpiar timeout al desmontar
onBeforeUnmount(() => {
  if (reconnectTimeout) {
    clearTimeout(reconnectTimeout)
  }
})

// Reiniciar stream cuando cambia la URL
watch(() => props.src, () => {
  reconnectAttempts.value = 0
  hasError.value = false
  isLoading.value = true
  streamUrl.value = getStreamUrl()
})
</script>

<template>
  <div class="relative" :class="props.class">
    <!-- Indicador de carga -->
    <div
      v-if="isLoading"
      class="absolute inset-0 bg-neutral-900 flex items-center justify-center rounded-md"
    >
      <div class="flex flex-col items-center gap-2">
        <div class="w-8 h-8 border-4 border-neutral-700 border-t-cyan-500 rounded-full animate-spin" />
        <span class="text-xs text-neutral-400">Conectando stream...</span>
      </div>
    </div>

    <!-- Indicador de error -->
    <div
      v-if="hasError && !isLoading"
      class="absolute inset-0 bg-neutral-900 flex items-center justify-center rounded-md"
    >
      <div class="flex flex-col items-center gap-2 text-center px-4">
        <span class="text-3xl">📡</span>
        <span class="text-sm text-rose-400">Stream no disponible</span>
        <span class="text-xs text-neutral-500">
          Intento {{ reconnectAttempts }}/{{ maxReconnectAttempts }}
        </span>
      </div>
    </div>

    <!-- Stream de video optimizado -->
    <img
      ref="imgRef"
      :src="streamUrl"
      :alt="alt"
      :class="[props.class, { 'opacity-0': isLoading || hasError }]"
      @load="handleLoad"
      @error="handleError"
      loading="eager"
      decoding="async"
      fetchpriority="high"
      referrerpolicy="no-referrer"
      crossorigin="anonymous"
    />
  </div>
</template>

<style scoped>
/* Optimizaciones CSS para reducir latencia */
img {
  image-rendering: -webkit-optimize-contrast;
  image-rendering: crisp-edges;
  will-change: auto;
  contain: layout style paint;
  content-visibility: auto;
}

/* Forzar aceleración de hardware */
img {
  transform: translateZ(0);
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
}
</style>
