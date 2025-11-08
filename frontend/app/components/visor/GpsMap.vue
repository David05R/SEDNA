<script setup>
import { ref, watch, defineAsyncComponent } from 'vue'
// Cargar componentes asíncronos para evitar problemas SSR
const LMap = defineAsyncComponent(() => import('@vue-leaflet/vue-leaflet').then(m => m.LMap))
const LTileLayer = defineAsyncComponent(() => import('@vue-leaflet/vue-leaflet').then(m => m.LTileLayer))
const LCircleMarker = defineAsyncComponent(() => import('@vue-leaflet/vue-leaflet').then(m => m.LCircleMarker))

const props = defineProps({
  lat: { type: Number, required: true },
  lng: { type: Number, required: true },
  zoom: { type: Number, default: 16 },
  heightClass: { type: String, default: 'h-64 md:h-72' },
})

const center = ref([props.lat, props.lng])
const currentZoom = ref(props.zoom)

watch(() => [props.lat, props.lng], ([lat, lng]) => {
  center.value = [lat, lng]
})
</script>

<template>
  <ClientOnly>
    <div class="w-full rounded-md overflow-hidden ring-1 ring-neutral-700/60" :class="heightClass">
      <LMap :zoom="currentZoom" :center="center" class="h-full w-full">
        <LTileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution="&copy; OpenStreetMap contributors"
        />
        <LCircleMarker :lat-lng="center" :radius="10" :color="'#38bdf8'" :fillColor="'#38bdf8'" :fillOpacity="0.8" />
      </LMap>
    </div>
  </ClientOnly>
</template>
