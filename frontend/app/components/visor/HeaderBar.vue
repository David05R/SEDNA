<script setup>
const props = defineProps({
  modes: { type: Array, required: true },
  mode: { type: String, required: true },
  poweredOn: { type: Boolean, default: false },
  connectionStatus: { type: String, default: 'idle' }, // idle | testing | ok | fail
})
const emit = defineEmits(['update:mode', 'toggle-power', 'test-connection'])

function onChange(e) {
  emit('update:mode', e.target.value)
}

function onTogglePower() {
  emit('toggle-power')
}

function onTestConnection() {
  emit('test-connection')
}
</script>

<template>
  <header class="w-full bg-neutral-800/80 backdrop-blur sticky top-0 z-10">
    <div class="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
      <h1 class="font-black tracking-widest text-xl md:text-2xl">SEDNA</h1>

      <div class="flex items-center gap-3">
        <!-- Selector de modo -->
        <div class="flex items-center gap-2">
          <label for="mode" class="text-sm text-neutral-300">Modo:</label>
          <select
            id="mode"
            :value="mode"
            @change="onChange"
            class="bg-neutral-700 text-white text-sm rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-sky-500"
          >
            <option v-for="m in modes" :key="m.value" :value="m.value">{{ m.label }}</option>
          </select>
        </div>

        <!-- Botón Ver Diagrama -->
        <NuxtLink
          to="/diagrama"
          class="text-sm px-3 py-2 rounded-md font-medium bg-purple-600 hover:bg-purple-500 transition-colors ring-1 ring-neutral-700 flex items-center gap-2"
          title="Ver diagrama de arquitectura del sistema"
        >
          <span class="text-lg">📊</span>
          <span class="hidden md:inline">Diagrama</span>
        </NuxtLink>

        <!-- Botón Encender/Apagar -->
        <button
          @click="onTogglePower"
          class="text-sm px-3 py-2 rounded-md font-medium ring-1 ring-neutral-700 transition-colors"
          :class="poweredOn ? 'bg-emerald-600 hover:bg-emerald-500' : 'bg-rose-600 hover:bg-rose-500'"
          :title="poweredOn ? 'Apagar' : 'Encender'"
        >
          {{ poweredOn ? 'Apagar' : 'Encender' }}
        </button>

        <!-- Botón Test Conexión -->
        <button
          @click="onTestConnection"
          class="text-sm px-3 py-2 rounded-md font-medium bg-sky-600 hover:bg-sky-500 transition-colors ring-1 ring-neutral-700 flex items-center gap-2"
          :disabled="connectionStatus === 'testing'"
          :title="'Probar conexión con el robot'"
        >
          <span v-if="connectionStatus === 'testing'" class="inline-block w-3 h-3 rounded-full border-2 border-white border-t-transparent animate-spin"></span>
          <span v-else class="inline-block w-2 h-2 rounded-full"
                :class="{
                  'bg-neutral-400': connectionStatus === 'idle',
                  'bg-emerald-400': connectionStatus === 'ok',
                  'bg-rose-400': connectionStatus === 'fail',
                }" />
          <span>Test conexión</span>
        </button>
      </div>
    </div>
  </header>
</template>
