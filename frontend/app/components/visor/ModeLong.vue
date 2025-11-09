<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import GpsMap from '~/components/visor/GpsMap.vue'
import VideoStream from '~/components/visor/VideoStream.vue'

const props = defineProps({
  streams: {
    type: Object,
    required: true,
  },
})

// Estado del robot desde WebSocket
const { robotState } = useRobotControl()

// Telemetría adicional (no viene del robot)
const additionalData = ref({
  weather: { tempC: 31, desc: 'Soleado' },
  heading: 45, // grados (brújula) - calculado desde GPS en el futuro
})

// Hora local en vivo
const timeStr = ref(new Date().toLocaleTimeString())
let timeTimer

// Estado gamepad
const gamepadConnected = ref(false)
const currentAxes = ref({ axis1: 0, axis2: 0 }) // Para mostrar valores actuales

// WebSocket Control (robotState ya está extraído arriba)
const { isConnected: wsConnected, connectionStatus, connect, disconnect, sendControlCommand } = useRobotControl()

function updateGamepad() {
  const pads = navigator.getGamepads?.()
  if (pads && pads[0]) {
    gamepadConnected.value = true
    const gp = pads[0]

    // Obtener eje 1 (joystick derecho Y) y eje 2 (joystick derecho X)
    // axes[3] = joystick derecho Y (arriba/abajo)
    // axes[2] = joystick derecho X (izquierda/derecha)
    const axis1Raw = gp.axes[1] || 0  // Eje 1: adelante (negativo) / atrás (positivo)
    const axis2Raw = gp.axes[2] || 0  // Eje 2: izquierda (negativo) / derecha (positivo)

    // Guardar valores actuales para mostrar en UI
    currentAxes.value = {
      axis1: Math.round(axis1Raw * 1000),
      axis2: Math.round(axis2Raw * 1000),
    }

    // Enviar a través de WebSocket si está conectado
    if (wsConnected.value) {
      sendControlCommand(axis1Raw, axis2Raw)
    }
  } else {
    gamepadConnected.value = false
    currentAxes.value = { axis1: 0, axis2: 0 }
  }
  requestAnimationFrame(updateGamepad)
}

onMounted(() => {
  // Conectar WebSocket automáticamente al entrar en modo LONG
  if (!wsConnected.value) {
    connect()
  }

  timeTimer = window.setInterval(() => {
    timeStr.value = new Date().toLocaleTimeString()
    // Demo: variar heading levemente (hasta que tengamos cálculo real desde GPS)
    additionalData.value.heading = (additionalData.value.heading + 1) % 360
  }, 1000)

  window.addEventListener('gamepadconnected', () => {
    gamepadConnected.value = true
    // Auto-conectar WebSocket cuando se conecta el gamepad (si no está ya conectado)
    if (!wsConnected.value) {
      connect()
    }
  })
  window.addEventListener('gamepaddisconnected', () => { gamepadConnected.value = false })
  updateGamepad()
})

onBeforeUnmount(() => {
  if (timeTimer) clearInterval(timeTimer)
  disconnect()
})

function compassStyle() {
  return { transform: `rotate(${additionalData.value.heading}deg)` }
}
</script>

<template>
  <!-- HUD remoto: cámara principal con overlays y miniaturas abajo -->
  <section class="space-y-3">
    <!-- Contenedor principal con overlays -->
    <div class="relative w-full">
      <VideoStream
        :src="streams.main"
        alt="Cámara principal"
        class="w-full h-[22rem] md:h-[26rem] object-cover rounded-lg shadow-lg ring-1 ring-neutral-700"
        :low-latency="true"
      />


      <!-- Mini-mapa (arriba izquierda) -->
      <div class="absolute top-3 left-3 w-40 md:w-56 bg-neutral-900/60 rounded-md backdrop-blur ring-1 ring-neutral-700 overflow-hidden">
        <GpsMap :lat="robotState.gps.lat" :lng="robotState.gps.lng" :zoom="16" heightClass="h-28 md:h-32" />
      </div>

      <!-- Brújula (arriba derecha) -->
      <div class="absolute top-3 right-3 bg-neutral-900/60 rounded-md backdrop-blur ring-1 ring-neutral-700 p-2 flex flex-col items-center">
        <div class="relative w-16 h-16">
          <div class="absolute inset-0 rounded-full ring-2 ring-neutral-600" />
          <div class="absolute inset-1 rounded-full ring-1 ring-neutral-700" />
          <div class="absolute inset-0 flex items-center justify-center">
            <div class="w-1 h-5 bg-rose-500 origin-bottom" :style="compassStyle()" />
          </div>
          <div class="absolute top-1/2 left-0 -translate-y-1/2 text-[10px] text-neutral-300">W</div>
          <div class="absolute top-1/2 right-0 -translate-y-1/2 text-[10px] text-neutral-300">E</div>
          <div class="absolute top-0 left-1/2 -translate-x-1/2 text-[10px] text-neutral-300">N</div>
          <div class="absolute bottom-0 left-1/2 -translate-x-1/2 text-[10px] text-neutral-300">S</div>
        </div>
        <div class="mt-1 text-xs text-neutral-200">{{ Math.round(additionalData.heading) }}°</div>
      </div>

      <!-- Barra de estado (abajo) -->
      <div class="absolute bottom-3 left-3 right-3 grid grid-cols-2 md:grid-cols-4 gap-2">
        <!-- Batería -->
        <div class="bg-neutral-900/60 rounded-md backdrop-blur ring-1 ring-neutral-700 p-2">
          <div class="text-[11px] text-neutral-300">Batería</div>
          <div class="flex items-center gap-2">
            <div class="h-2 flex-1 bg-neutral-700 rounded">
              <div class="h-2 rounded bg-emerald-500" :style="{ width: robotState.battery + '%' }" />
            </div>
            <div class="text-xs">{{ robotState.battery }}%</div>
          </div>
          <div class="text-[10px] text-neutral-400 mt-0.5">{{ robotState.battery_voltage?.toFixed(2) || '0.00' }}V</div>
        </div>

        <!-- Hora local -->
        <div class="bg-neutral-900/60 rounded-md backdrop-blur ring-1 ring-neutral-700 p-2">
          <div class="text-[11px] text-neutral-300">Hora</div>
          <div class="text-xs">{{ timeStr }}</div>
        </div>

        <!-- Velocidad del Robot (RPM promedio) -->
        <div class="bg-neutral-900/60 rounded-md backdrop-blur ring-1 ring-neutral-700 p-2">
          <div class="text-[11px] text-neutral-300">Velocidad</div>
          <div class="text-xs">{{ Math.round((robotState.rpm_motor1 + robotState.rpm_motor2) / 2) || 0 }} RPM</div>
          <div class="text-[10px] text-neutral-400 mt-0.5">M1: {{ robotState.rpm_motor1?.toFixed(0) || 0 }} | M2: {{ robotState.rpm_motor2?.toFixed(0) || 0 }}</div>
        </div>

        <!-- Gamepad -->
        <div class="bg-neutral-900/60 rounded-md backdrop-blur ring-1 ring-neutral-700 p-2">
          <div class="text-[11px] text-neutral-300">Gamepad</div>
          <div class="text-xs" :class="gamepadConnected ? 'text-emerald-300' : 'text-rose-300'">
            {{ gamepadConnected ? 'Conectado' : 'No detectado' }}
          </div>
        </div>
      </div>
    </div>

    <!-- Miniaturas -->
    <div class="grid grid-cols-2 gap-2">
      <VideoStream
        :src="streams.left"
        alt="Cámara izquierda"
        class="w-full h-36 md:h-40 object-cover rounded-lg shadow"
        :low-latency="true"
      />
      <VideoStream
        :src="streams.right"
        alt="Cámara derecha"
        class="w-full h-36 md:h-40 object-cover rounded-lg shadow"
        :low-latency="true"
      />
    </div>

    <!-- Estado de Control Remoto -->
    <div class="bg-neutral-800/60 rounded-lg ring-1 ring-neutral-700 p-4">
      <div class="flex items-center justify-between mb-3">
        <h3 class="font-semibold">Estado de Control Remoto</h3>
        <div class="flex items-center gap-2">
          <!-- Estado WebSocket -->
          <div class="flex items-center gap-1.5">
            <div class="w-2 h-2 rounded-full" :class="{
              'bg-emerald-500 animate-pulse': connectionStatus === 'connected',
              'bg-amber-500': connectionStatus === 'connecting',
              'bg-neutral-500': connectionStatus === 'disconnected',
              'bg-rose-500': connectionStatus === 'error'
            }" />
            <span class="text-xs text-neutral-300">
              {{ connectionStatus === 'connected' ? 'Conectado' :
                 connectionStatus === 'connecting' ? 'Conectando...' :
                 connectionStatus === 'error' ? 'Error' : 'Desconectado' }}
            </span>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-4 gap-3">
        <!-- Estado del Robot -->
        <div class="bg-neutral-900/60 rounded-md p-3 ring-1 ring-neutral-700/60">
          <div class="text-xs text-neutral-400 mb-1">Robot</div>
          <div class="font-medium" :class="(robotState.operational ?? robotState.connected) ? 'text-emerald-300' : 'text-rose-300'">
            {{ (robotState.operational ?? robotState.connected) ? 'Operativo' : 'Desconectado' }}
          </div>
          <div class="text-[10px] text-neutral-500 mt-0.5">
            GPS: {{ robotState.gps.lat.toFixed(4) }}, {{ robotState.gps.lng.toFixed(4) }}
          </div>
          <div class="text-[10px] text-neutral-500 mt-0.5" v-if="robotState.remote_control">
            <span class="text-cyan-400">⚡ Control remoto activo</span>
          </div>
        </div>

        <!-- Estado Gamepad -->
        <div class="bg-neutral-900/60 rounded-md p-3 ring-1 ring-neutral-700/60">
          <div class="text-xs text-neutral-400 mb-1">Control Bluetooth</div>
          <div class="font-medium" :class="gamepadConnected ? 'text-emerald-300' : 'text-rose-300'">
            {{ gamepadConnected ? 'Conectado' : 'No detectado' }}
          </div>
        </div>

        <!-- Eje 1: Adelante/Atrás -->
        <div class="bg-neutral-900/60 rounded-md p-3 ring-1 ring-neutral-700/60">
          <div class="text-xs text-neutral-400 mb-1">Eje 1 (Adelante/Atrás)</div>
          <div class="font-mono text-sm" :class="currentAxes.axis1 !== 0 ? 'text-cyan-300' : 'text-neutral-300'">
            {{ currentAxes.axis1 > 0 ? '+' : '' }}{{ currentAxes.axis1 }}
          </div>
          <div class="text-[10px] text-neutral-500 mt-0.5">
            {{ currentAxes.axis1 < 0 ? 'Adelante' : currentAxes.axis1 > 0 ? 'Atrás' : 'Neutral' }}
          </div>
        </div>

        <!-- Eje 2: Izquierda/Derecha -->
        <div class="bg-neutral-900/60 rounded-md p-3 ring-1 ring-neutral-700/60">
          <div class="text-xs text-neutral-400 mb-1">Eje 2 (Izquierda/Derecha)</div>
          <div class="font-mono text-sm" :class="currentAxes.axis2 !== 0 ? 'text-cyan-300' : 'text-neutral-300'">
            {{ currentAxes.axis2 > 0 ? '+' : '' }}{{ currentAxes.axis2 }}
          </div>
          <div class="text-[10px] text-neutral-500 mt-0.5">
            {{ currentAxes.axis2 < 0 ? 'Izquierda' : currentAxes.axis2 > 0 ? 'Derecha' : 'Neutral' }}
          </div>
        </div>
      </div>

      <!-- Botones de control manual -->
      <div class="mt-3 flex gap-2">
        <button
          v-if="!wsConnected"
          @click="connect"
          class="px-3 py-1.5 text-sm bg-emerald-600 hover:bg-emerald-500 rounded-md transition-colors"
        >
          Conectar al Robot
        </button>
        <button
          v-else
          @click="disconnect"
          class="px-3 py-1.5 text-sm bg-rose-600 hover:bg-rose-500 rounded-md transition-colors"
        >
          Desconectar
        </button>
      </div>

      <div class="mt-3 text-xs text-neutral-400">
        {{ gamepadConnected && wsConnected
          ? 'Control activo: Los comandos se están enviando al robot en tiempo real.'
          : !gamepadConnected
          ? 'Conecta un control Bluetooth para comenzar.'
          : 'Conecta al robot para enviar comandos.' }}
      </div>
    </div>
  </section>
</template>
