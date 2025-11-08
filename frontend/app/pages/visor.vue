<script setup>
import { ref, computed, watch } from 'vue'
import HeaderBar from '~/components/visor/HeaderBar.vue'
import ModeShort from '~/components/visor/ModeShort.vue'
import ModeLong from '~/components/visor/ModeLong.vue'
import ModeSurvey from '~/components/visor/ModeSurvey.vue'

// Obtener funciones del composable
const { testConnection, setRobotMode } = useRobotControl()

// Streams de ejemplo (reemplazar por URLs de las cámaras reales)
const streams = {
  main: 'https://cam1.sednarobot.org/?action=stream',
  left: 'https://cam2.sednarobot.org/?action=stream',
  right: 'https://cam3.sednarobot.org/?action=stream',
}

// Modos de control
const modes = [
  { value: 'short', label: 'Control cercano' },
  { value: 'long', label: 'Control remoto' },
  { value: 'survey', label: 'Sondeo de mapa' },
]
const mode = ref('short')

// Watch para cambiar el modo del robot cuando cambia la pestaña
watch(mode, async (newMode) => {
  console.log(`🔄 Cambiando a pestaña: ${newMode}`)

  // Mapear modo de pestaña a modo del robot
  let robotMode = 'idle'

  if (newMode === 'short') {
    robotMode = 'short'
  } else if (newMode === 'long') {
    robotMode = 'long'
  } else if (newMode === 'survey') {
    robotMode = 'idle'  // Modo survey = idle por ahora
  }

  // Cambiar modo en el backend
  const success = await setRobotMode(robotMode)
  if (success) {
    console.log(`✅ Backend en modo: ${robotMode}`)
  } else {
    console.error(`❌ Error cambiando modo del backend`)
  }
}, { immediate: true })  // immediate: true para que se ejecute al cargar

// Estado global del visor
const poweredOn = ref(false)
// idle | testing | ok | fail
const connectionStatus = ref('idle')
const latency = ref(null)

function onTogglePower() {
  poweredOn.value = !poweredOn.value
}

async function onTestConnection() {
  if (connectionStatus.value === 'testing') return
  connectionStatus.value = 'testing'
  latency.value = null

  try {
    const result = await testConnection()

    if (result.success) {
      connectionStatus.value = 'ok'
      latency.value = result.latency
      console.log(`✅ Conexión exitosa - Latencia: ${result.latency}ms`)
    } else {
      connectionStatus.value = 'fail'
      console.error(`❌ Test de conexión falló: ${result.error}`)
    }
  } catch (e) {
    connectionStatus.value = 'fail'
    console.error('❌ Error inesperado en test de conexión:', e)
  } finally {
    // Regresar a idle tras 5 segundos
    setTimeout(() => {
      if (connectionStatus.value !== 'testing') {
        connectionStatus.value = 'idle'
        latency.value = null
      }
    }, 5000)
  }
}
</script>

<template>
  <div class="min-h-screen flex flex-col bg-neutral-900 text-white">
    <HeaderBar
      :modes="modes"
      v-model:mode="mode"
      :poweredOn="poweredOn"
      :connectionStatus="connectionStatus"
      @toggle-power="onTogglePower"
      @test-connection="onTestConnection"
    />

    <main class="flex-1 max-w-7xl mx-auto w-full px-4 py-4">
      <!-- Mostrar resultado del test de conexión -->
      <div v-if="connectionStatus !== 'idle' && latency !== null"
           class="mb-4 p-3 rounded-lg ring-1"
           :class="{
             'bg-emerald-900/40 ring-emerald-700': connectionStatus === 'ok',
             'bg-rose-900/40 ring-rose-700': connectionStatus === 'fail'
           }">
        <div class="flex items-center gap-3">
          <div class="text-lg">
            {{ connectionStatus === 'ok' ? '✅' : '❌' }}
          </div>
          <div>
            <div class="font-medium">
              {{ connectionStatus === 'ok' ? 'Conexión estable' : 'Problemas de conexión' }}
            </div>
            <div class="text-sm text-neutral-300">
              Latencia: {{ latency }}ms
              {{ latency < 100 ? '(Excelente)' : latency < 300 ? '(Buena)' : latency < 500 ? '(Regular)' : '(Lenta)' }}
            </div>
          </div>
        </div>
      </div>

      <ModeShort v-if="mode === 'short'" :streams="streams" />
      <ModeLong v-else-if="mode === 'long'" :streams="streams" />
      <ModeSurvey v-else :streams="streams" />
    </main>
  </div>
</template>
