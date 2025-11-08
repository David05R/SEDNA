<script setup>
import VideoStream from '~/components/visor/VideoStream.vue'

const props = defineProps({
  streams: {
    type: Object,
    required: true,
  },
  // Futuro: props para telemetría / rutas / mapa
})
</script>

<template>
  <!-- Principal + panel lateral de mapa/telemetría -->
  <!-- Optimizado para streams MJPEG con componente VideoStream de baja latencia -->
  <section class="grid grid-cols-1 md:grid-cols-3 gap-3 items-start">
    <div class="md:col-span-2">
      <VideoStream
        :src="streams.main"
        alt="Cámara principal"
        class="w-full h-[26rem] md:h-[28rem] object-cover rounded-lg shadow-lg ring-1 ring-neutral-700"
        :low-latency="true"
      />
      <div class="mt-3 grid grid-cols-2 gap-3">
        <VideoStream
          :src="streams.left"
          alt="Cámara izquierda"
          class="w-full h-40 object-cover rounded-lg shadow"
          :low-latency="true"
        />
        <VideoStream
          :src="streams.right"
          alt="Cámara derecha"
          class="w-full h-40 object-cover rounded-lg shadow"
          :low-latency="true"
        />
      </div>
    </div>
    <aside class="bg-neutral-800/60 rounded-lg p-4 h-full ring-1 ring-neutral-700">
      <h2 class="font-semibold mb-2">Mapa / Telemetría</h2>
      <p class="text-neutral-300 text-sm">Panel de ejemplo para integrar mapa, rutas y sensores.</p>
      <ul class="mt-3 space-y-1 text-sm text-neutral-300 list-disc ml-5">
        <li>GPS y rumbo</li>
        <li>Velocidad y batería</li>
        <li>Ruta planificada</li>
      </ul>
    </aside>
  </section>
</template>
