<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import GpsMap from '~/components/visor/GpsMap.vue'
import VideoStream from '~/components/visor/VideoStream.vue'

const props = defineProps({
  streams: {
    type: Object,
    required: true,
    // expected: { main: string, left: string, right: string }
  },
})

// Estado del robot desde WebSocket
const { robotState } = useRobotControl()

// Datos adicionales (no vienen del robot)
const additionalData = ref({
  poweredOn: true,
  uptime: '00:00:00',
  storage: 35, // % de llenado (basura) - por implementar en el backend
})

// Calcular uptime
let uptimeTimer = null
const startTime = Date.now()

onMounted(() => {
  // Conectar WebSocket para recibir telemetría en tiempo real
  const { connect, disconnect } = useRobotControl()
  connect()

  uptimeTimer = setInterval(() => {
    const elapsed = Math.floor((Date.now() - startTime) / 1000)
    const hours = Math.floor(elapsed / 3600).toString().padStart(2, '0')
    const minutes = Math.floor((elapsed % 3600) / 60).toString().padStart(2, '0')
    const seconds = (elapsed % 60).toString().padStart(2, '0')
    additionalData.value.uptime = `${hours}:${minutes}:${seconds}`
  }, 1000)

  // Limpiar al desmontar
  onBeforeUnmount(() => {
    if (uptimeTimer) clearInterval(uptimeTimer)
    disconnect()
  })
})

onBeforeUnmount(() => {
  if (uptimeTimer) clearInterval(uptimeTimer)
})
</script>

<template>
  <div class="space-y-3">
    <!-- Tres cámaras en fila, centro más ancho; misma altura (~40% pantalla) -->
    <!-- Optimizado para streams MJPEG con componente VideoStream de baja latencia -->
    <section class="flex gap-2 items-stretch">
      <div class="w-1/4">
        <VideoStream
          :src="streams.left"
          alt="Cámara izquierda"
          class="w-full h-[40vh] object-cover rounded-md ring-1 ring-neutral-700/60"
          :low-latency="true"
        />
      </div>
      <div class="flex-1">
        <VideoStream
          :src="streams.main"
          alt="Cámara principal"
          class="w-full h-[40vh] object-cover rounded-md ring-1 ring-neutral-700"
          :low-latency="true"
        />
      </div>
      <div class="w-1/4">
        <VideoStream
          :src="streams.right"
          alt="Cámara derecha"
          class="w-full h-[40vh] object-cover rounded-md ring-1 ring-neutral-700/60"
          :low-latency="true"
        />
      </div>
    </section>

    <!-- Paneles inferiores: GPS/Mapa (izq) + Estado del robot (der) -->
    <section class="grid grid-cols-1 md:grid-cols-2 gap-3">
      <!-- GPS / Mapa -->
      <div class="bg-neutral-800/60 rounded-lg ring-1 ring-neutral-700 p-4">
        <div class="flex items-center justify-between mb-3">
          <h3 class="font-semibold">Ubicación (GPS)</h3>
          <span class="text-xs text-neutral-300">{{ robotState.gps.lat.toFixed(4) }}, {{ robotState.gps.lng.toFixed(4) }}</span>
        </div>
        <GpsMap :lat="robotState.gps.lat" :lng="robotState.gps.lng" :zoom="16" />
      </div>

      <!-- Estado del robot -->
      <div class="bg-neutral-800/60 rounded-lg ring-1 ring-neutral-700 p-4">
        <h3 class="font-semibold mb-3">Estado del robot</h3>

        <div class="grid grid-cols-2 gap-3 mb-4">
          <div class="bg-neutral-900/60 rounded-md p-3 ring-1 ring-neutral-700/60">
            <div class="text-xs text-neutral-400">Modo de Control</div>
            <div class="mt-1 font-medium flex items-center gap-1.5">
              <span v-if="robotState.mode === 'short'" class="text-cyan-300">📡 Cercano (RF)</span>
              <span v-else-if="robotState.mode === 'long'" class="text-purple-300">🌐 Remoto (WS)</span>
              <span v-else class="text-neutral-400">⏸️ Inactivo</span>
            </div>
          </div>
          <div class="bg-neutral-900/60 rounded-md p-3 ring-1 ring-neutral-700/60">
            <div class="text-xs text-neutral-400">Estado Robot</div>
            <div class="mt-1 font-medium" :class="(robotState.operational ?? robotState.connected) ? 'text-emerald-300' : 'text-rose-300'">
              {{ (robotState.operational ?? robotState.connected) ? 'Operativo' : 'Desconectado' }}
            </div>
          </div>
          <div class="bg-neutral-900/60 rounded-md p-3 ring-1 ring-neutral-700/60">
            <div class="text-xs text-neutral-400">Tiempo de funcionamiento</div>
            <div class="mt-1 font-medium">{{ additionalData.uptime }}</div>
          </div>
          <div class="bg-neutral-900/60 rounded-md p-3 ring-1 ring-neutral-700/60">
            <div class="text-xs text-neutral-400">Velocidad</div>
            <div class="mt-1 font-medium">{{ Math.round((robotState.rpm_motor1 + robotState.rpm_motor2) / 2) || 0 }} RPM</div>
            <div class="text-[10px] text-neutral-500 mt-0.5">
              M1: {{ robotState.rpm_motor1?.toFixed(0) || 0 }} | M2: {{ robotState.rpm_motor2?.toFixed(0) || 0 }}
            </div>
          </div>
        </div>

        <!-- Batería -->
        <div class="mb-4">
          <div class="flex items-center justify-between mb-1">
            <span class="text-sm">Batería</span>
            <span class="text-sm text-neutral-300">{{ robotState.battery }}% ({{ robotState.battery_voltage?.toFixed(2) || '0.00' }}V)</span>
          </div>
          <div class="h-2 bg-neutral-700 rounded">
            <div class="h-2 rounded bg-emerald-500" :style="{ width: robotState.battery + '%' }" />
          </div>
        </div>

        <!-- Capacidad de almacenamiento de basura -->
        <div>
          <div class="flex items-center justify-between mb-1">
            <span class="text-sm">Almacenamiento de basura</span>
            <span class="text-sm text-neutral-300">{{ additionalData.storage }}%</span>
          </div>
          <div class="h-2 bg-neutral-700 rounded">
            <div class="h-2 rounded bg-amber-500" :style="{ width: additionalData.storage + '%' }" />
          </div>
          <div class="mt-2 text-xs text-neutral-400">Visual: lleno al {{ additionalData.storage }}% (boceto)</div>
        </div>
      </div>
    </section>
  </div>
</template>
