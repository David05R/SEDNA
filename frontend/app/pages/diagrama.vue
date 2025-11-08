<template>
  <div class="min-h-screen bg-white text-gray-900">
    <!-- Header con botones de acción -->
    <div class="no-print sticky top-0 z-50 bg-slate-900 text-white border-b border-slate-700">
      <div class="container mx-auto px-6 py-3 flex items-center justify-between">
        <h1 class="text-lg font-bold">Documentación Técnica - Robot SEDNA</h1>
        <div class="flex gap-3">
          <button
            @click="exportToPDF"
            class="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm font-medium transition-colors"
          >
            📄 Exportar PDF
          </button>
          <button
            @click="print"
            class="px-4 py-2 bg-green-600 hover:bg-green-700 rounded text-sm font-medium transition-colors"
          >
            🖨️ Imprimir
          </button>
          <NuxtLink
            to="/visor"
            class="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded text-sm font-medium transition-colors"
          >
            ← Volver
          </NuxtLink>
        </div>
      </div>
    </div>

    <!-- Documento técnico -->
    <div id="technical-document" class="document-container">
      <!-- Header del documento -->
      <header class="document-header">
        <div class="flex items-start justify-between mb-6">
          <div>
            <h1 class="text-3xl font-bold text-gray-900 mb-1">Robot SEDNA</h1>
            <h2 class="text-xl text-gray-600">Arquitectura del Sistema de Control Dual</h2>
          </div>
          <div class="text-right text-sm text-gray-600">
            <div class="font-bold text-gray-900">Documento Técnico</div>
            <div>Versión 1.0</div>
            <div>{{ new Date().toLocaleDateString('es-ES', { year: 'numeric', month: 'long', day: 'numeric' }) }}</div>
          </div>
        </div>
        <div class="border-t-4 border-cyan-600 mb-6"></div>
      </header>

      <!-- Contenido principal en 2 columnas -->
      <div class="grid grid-cols-2 gap-6">

        <!-- COLUMNA IZQUIERDA -->
        <div class="space-y-5">

          <!-- 1. Resumen Ejecutivo -->
          <section class="section">
            <h3 class="section-title">1. Resumen Ejecutivo</h3>
            <p class="text-sm leading-relaxed text-gray-700">
              Sistema de control dual para robot autónomo de limpieza de playas que opera en dos modos:
              <strong>SHORT</strong> (control RF de corto alcance con latencia mínima) y
              <strong>LONG</strong> (control remoto vía WebSocket con telemetría bidireccional).
              Implementado con arquitectura minimal que ejecuta procesos exclusivos según el modo activo,
              evitando interferencias y conflictos de GPIO.
            </p>
          </section>

          <!-- 2. Arquitectura del Sistema -->
          <section class="section">
            <h3 class="section-title">2. Arquitectura del Sistema</h3>

            <div class="architecture-diagram">
              <div class="arch-layer">
                <div class="arch-box purple">
                  <div class="arch-label">Frontend (Nuxt 4 + Vue 3)</div>
                  <div class="arch-desc">Puerto 3000 • Gamepad API • WebSocket Client</div>
                </div>
              </div>

              <div class="arch-arrow">↓ HTTP/WebSocket</div>

              <div class="arch-layer">
                <div class="arch-box cyan">
                  <div class="arch-label">Backend (FastAPI)</div>
                  <div class="arch-desc">main_minimal.py • Puerto 5050 • Orange Pi</div>
                </div>
              </div>

              <div class="arch-arrow">↓ Gestión de Modos</div>

              <div class="arch-layer grid grid-cols-2 gap-2">
                <div class="arch-box orange">
                  <div class="arch-label-sm">Modo SHORT</div>
                  <div class="arch-desc-sm">test_gpio.py<br>iBus RF Control</div>
                </div>
                <div class="arch-box green">
                  <div class="arch-label-sm">Modo LONG</div>
                  <div class="arch-desc-sm">motor_controller.py<br>WebSocket Control</div>
                </div>
              </div>

              <div class="arch-arrow">↓ GPIO PWM</div>

              <div class="arch-layer">
                <div class="arch-box emerald">
                  <div class="arch-label">Hardware</div>
                  <div class="arch-desc">Motores BTS7960 • GPS NEO6MV3 • Cámaras MJPEG</div>
                </div>
              </div>
            </div>
          </section>

          <!-- 3. Stack Tecnológico -->
          <section class="section">
            <h3 class="section-title">3. Stack Tecnológico</h3>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <div class="tech-category">Frontend</div>
                <ul class="tech-list">
                  <li>Nuxt 4, Vue 3</li>
                  <li>Tailwind CSS 4</li>
                  <li>Leaflet (mapas)</li>
                  <li>Gamepad API</li>
                </ul>
              </div>
              <div>
                <div class="tech-category">Backend</div>
                <ul class="tech-list">
                  <li>FastAPI 0.115+</li>
                  <li>Uvicorn (ASGI)</li>
                  <li>WiringPi (GPIO)</li>
                  <li>pyserial (iBus)</li>
                </ul>
              </div>
            </div>
          </section>

          <!-- 4. Flujo de Cambio de Modo -->
          <section class="section">
            <h3 class="section-title">4. Flujo de Cambio de Modo</h3>
            <div class="flow-diagram text-xs">
              <div class="flow-step">
                <div class="flow-box bg-purple-100 border-purple-400">1. Usuario selecciona modo en Frontend</div>
                <div class="flow-connector">↓</div>
                <div class="flow-box bg-yellow-50 border-yellow-400">
                  <code class="text-xs">POST /mode/{'{short|long|idle}'}</code>
                </div>
                <div class="flow-connector">↓</div>
                <div class="flow-box bg-cyan-100 border-cyan-400">2. Backend: set_mode_async(mode)</div>
                <div class="flow-connector">↓ Decisión</div>
              </div>

              <div class="grid grid-cols-3 gap-2 text-xs">
                <div class="flow-box bg-orange-50 border-orange-400">
                  <strong>SHORT</strong><br>
                  • Cleanup GPIO<br>
                  • sleep(1s)<br>
                  • pkill test_gpio<br>
                  • Ejecutar test_gpio.py
                </div>
                <div class="flow-box bg-green-50 border-green-400">
                  <strong>LONG</strong><br>
                  • Stop test_gpio<br>
                  • Cleanup GPIO<br>
                  • Init motor_controller<br>
                  • Escuchar WebSocket
                </div>
                <div class="flow-box bg-gray-100 border-gray-400">
                  <strong>IDLE</strong><br>
                  • Stop test_gpio<br>
                  • Cleanup motor_ctrl<br>
                  • Liberar recursos<br>
                  • Sistema en reposo
                </div>
              </div>
            </div>
          </section>

          <!-- 5. Modo SHORT -->
          <section class="section">
            <h3 class="section-title">5. Modo SHORT (Control RF)</h3>
            <div class="mode-flow">
              <div class="flow-horizontal">
                <div class="flow-node">Receptor<br>FlySky</div>
                <span>→</span>
                <div class="flow-node">iBus<br>/dev/ttyS1</div>
                <span>→</span>
                <div class="flow-node">test_gpio.py</div>
                <span>→</span>
                <div class="flow-node">GPIO PWM</div>
                <span>→</span>
                <div class="flow-node">Motores<br>BTS7960</div>
              </div>
            </div>
            <div class="characteristics">
              <strong>Características:</strong> Latencia mínima (&lt;5ms), proceso independiente con sudo,
              sin intermediarios WebSocket, alcance ~100m, ideal para operación en campo cercano.
            </div>
          </section>

        </div>

        <!-- COLUMNA DERECHA -->
        <div class="space-y-5">

          <!-- 6. Modo LONG -->
          <section class="section">
            <h3 class="section-title">6. Modo LONG (Control Remoto)</h3>
            <div class="mode-flow">
              <div class="flow-horizontal">
                <div class="flow-node-sm">Gamepad<br>BT</div>
                <span>→</span>
                <div class="flow-node-sm">Frontend</div>
                <span class="text-xs">WS⇄</span>
                <div class="flow-node-sm">Backend</div>
                <span>→</span>
                <div class="flow-node-sm">motor_ctrl</div>
                <span>→</span>
                <div class="flow-node-sm">Motores</div>
              </div>
            </div>
            <div class="characteristics">
              <strong>Características:</strong> Control remoto ilimitado (requiere internet), telemetría bidireccional,
              ~60 FPS de comandos, delay ~50-100ms, motor_controller inicializado bajo demanda.
            </div>
            <div class="mt-2 p-2 bg-green-50 border border-green-300 rounded text-xs">
              <strong>Telemetría (cada 2s):</strong> Batería, GPS (lat/lng), velocidad, modo, estado operacional,
              conexión de control remoto.
            </div>
          </section>

          <!-- 7. Protocolos de Comunicación -->
          <section class="section">
            <h3 class="section-title">7. Protocolos de Comunicación</h3>
            <table class="protocol-table">
              <thead>
                <tr>
                  <th>Protocolo</th>
                  <th>Endpoint</th>
                  <th>Frecuencia</th>
                  <th>Propósito</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><code>HTTP POST</code></td>
                  <td><code>/mode/{'{mode}'}</code></td>
                  <td>On demand</td>
                  <td>Cambiar modo</td>
                </tr>
                <tr>
                  <td><code>HTTP GET</code></td>
                  <td><code>/health</code></td>
                  <td>5s (si WS off)</td>
                  <td>Estado del sistema</td>
                </tr>
                <tr>
                  <td><code>WebSocket</code></td>
                  <td><code>/ws/control</code></td>
                  <td>~60 FPS</td>
                  <td>Control real-time</td>
                </tr>
                <tr>
                  <td><code>Serial iBus</code></td>
                  <td><code>/dev/ttyS1</code></td>
                  <td>~100 Hz</td>
                  <td>Control RF</td>
                </tr>
                <tr>
                  <td><code>GPIO PWM</code></td>
                  <td>Pins físicos</td>
                  <td>Continuo</td>
                  <td>Señales motores</td>
                </tr>
              </tbody>
            </table>
          </section>

          <!-- 8. Polling HTTP Inteligente -->
          <section class="section">
            <h3 class="section-title">8. Polling HTTP Inteligente</h3>
            <div class="grid grid-cols-2 gap-2 text-xs">
              <div class="p-2 bg-blue-50 border border-blue-300 rounded">
                <strong class="text-blue-700">WebSocket OFF:</strong><br>
                GET /health cada 5 segundos para actualizar estado en UI (batería, GPS, velocidad, modo).
              </div>
              <div class="p-2 bg-green-50 border border-green-300 rounded">
                <strong class="text-green-700">WebSocket ON:</strong><br>
                Polling HTTP detenido. Telemetría recibida por WebSocket. Reduce carga del servidor.
              </div>
            </div>
          </section>

          <!-- 9. Arquitectura de Archivos -->
          <section class="section">
            <h3 class="section-title">9. Arquitectura de Archivos</h3>
            <div class="grid grid-cols-2 gap-3 text-xs">
              <div>
                <div class="file-category">Backend (Orange Pi)</div>
                <ul class="file-list">
                  <li><code>main_minimal.py</code> - FastAPI app, WS handler</li>
                  <li><code>test_gpio.py</code> - Control RF modo SHORT</li>
                  <li><code>motor_controller.py</code> - Control motores LONG</li>
                  <li><code>ibus_controller.py</code> - Lectura iBus serial</li>
                </ul>
              </div>
              <div>
                <div class="file-category">Frontend (Nuxt)</div>
                <ul class="file-list">
                  <li><code>useRobotControl.ts</code> - Composable WS/HTTP</li>
                  <li><code>visor.vue</code> - Página principal, tabs</li>
                  <li><code>ModeShort.vue</code> - Interfaz modo SHORT</li>
                  <li><code>ModeLong.vue</code> - Interfaz modo LONG</li>
                </ul>
              </div>
            </div>
          </section>

          <!-- 10. Decisiones Técnicas Clave -->
          <section class="section">
            <h3 class="section-title">10. Decisiones Técnicas Clave</h3>
            <ul class="decision-list">
              <li>
                <strong>Arquitectura minimal:</strong> Control explícito desde frontend, sin detección automática
                ni sistemas de prioridad que causen interferencias.
              </li>
              <li>
                <strong>Procesos exclusivos:</strong> Solo un modo activo a la vez. test_gpio.py como subproceso
                independiente en SHORT; motor_controller.py en LONG.
              </li>
              <li>
                <strong>GPIO cleanup agresivo:</strong> Delay de 1s + pkill + softPwmStop() + pinMode(0) al cambiar
                LONG→SHORT previene conflictos de hardware.
              </li>
              <li>
                <strong>Inicialización bajo demanda:</strong> motor_controller solo se inicializa cuando modo LONG
                se activa, reduciendo uso de recursos.
              </li>
              <li>
                <strong>Polling inteligente:</strong> HTTP polling se detiene automáticamente cuando WebSocket conecta,
                eliminando latencia y reduciendo carga del servidor.
              </li>
            </ul>
          </section>

          <!-- 11. Formato de Mensajes -->
          <section class="section">
            <h3 class="section-title">11. Formato de Mensajes JSON</h3>
            <div class="space-y-2">
              <div>
                <div class="json-label">Cliente → Servidor (Control):</div>
                <pre class="json-code">{"axis1": -850, "axis2": 300}</pre>
                <div class="json-desc">axis1: Adelante/Atrás (-1000 a 1000) • axis2: Izq/Der (-1000 a 1000)</div>
              </div>
              <div>
                <div class="json-label">Servidor → Cliente (Telemetría):</div>
                <pre class="json-code">{
  "type": "robot_state",
  "battery": 58,
  "gps": {"lat": 10.377, "lng": -75.465},
  "speed": 85.0,
  "mode": "long",
  "operational": true,
  "remote_control": true
}</pre>
              </div>
            </div>
          </section>

        </div>
      </div>

      <!-- Footer -->
      <footer class="document-footer">
        <div class="border-t-2 border-gray-300 pt-3 mt-6">
          <div class="flex items-center justify-between text-xs text-gray-600">
            <div>
              <strong>Robot SEDNA</strong> - Sistema de Control Dual •
              Backend: main_minimal.py (FastAPI) • Frontend: Nuxt 4 + Vue 3
            </div>
            <div>
              Documento generado: {{ new Date().toLocaleString('es-ES') }}
            </div>
          </div>
        </div>
      </footer>

    </div>
  </div>
</template>

<script setup lang="ts">
function print() {
  window.print()
}

function exportToPDF() {
  // El usuario puede usar Ctrl+P y "Guardar como PDF" o usar la función print
  window.print()
}
</script>

<style scoped>
/* ============================================
   ESTILOS PARA PANTALLA
   ============================================ */

.document-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 3rem;
  background: white;
  min-height: 100vh;
}

.document-header {
  margin-bottom: 1.5rem;
}

.section {
  background: white;
  page-break-inside: avoid;
}

.section-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: #0e7490;
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 2px solid #e5e7eb;
  padding-bottom: 0.25rem;
}

/* Architecture Diagram */
.architecture-diagram {
  font-size: 0.75rem;
}

.arch-layer {
  margin-bottom: 0.5rem;
}

.arch-box {
  padding: 0.5rem;
  border-radius: 0.375rem;
  border: 2px solid;
  text-align: center;
}

.arch-box.purple {
  background: #f3e8ff;
  border-color: #a78bfa;
}

.arch-box.cyan {
  background: #cffafe;
  border-color: #22d3ee;
}

.arch-box.orange {
  background: #ffedd5;
  border-color: #fb923c;
}

.arch-box.green {
  background: #d1fae5;
  border-color: #34d399;
}

.arch-box.emerald {
  background: #d1fae5;
  border-color: #10b981;
}

.arch-label {
  font-weight: 700;
  font-size: 0.75rem;
  margin-bottom: 0.125rem;
}

.arch-label-sm {
  font-weight: 700;
  font-size: 0.7rem;
  margin-bottom: 0.125rem;
}

.arch-desc {
  font-size: 0.65rem;
  color: #4b5563;
}

.arch-desc-sm {
  font-size: 0.6rem;
  color: #4b5563;
  line-height: 1.3;
}

.arch-arrow {
  text-align: center;
  font-weight: 600;
  color: #6b7280;
  font-size: 0.7rem;
  margin: 0.25rem 0;
}

/* Tech Stack */
.tech-category {
  font-weight: 700;
  font-size: 0.75rem;
  color: #374151;
  margin-bottom: 0.25rem;
}

.tech-list {
  list-style: none;
  padding: 0;
  font-size: 0.7rem;
  color: #6b7280;
  line-height: 1.4;
}

.tech-list li::before {
  content: "• ";
  color: #0e7490;
  font-weight: bold;
}

/* Flow Diagram */
.flow-diagram {
  font-size: 0.7rem;
}

.flow-step {
  margin-bottom: 0.5rem;
}

.flow-box {
  padding: 0.4rem 0.5rem;
  border-radius: 0.25rem;
  border: 1.5px solid;
  text-align: center;
  margin-bottom: 0.25rem;
}

.flow-connector {
  text-align: center;
  font-weight: 600;
  color: #6b7280;
  font-size: 0.7rem;
  margin: 0.15rem 0;
}

/* Mode Flow */
.mode-flow {
  margin: 0.5rem 0;
}

.flow-horizontal {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.3rem;
  font-size: 0.65rem;
  text-align: center;
}

.flow-node {
  background: #f3f4f6;
  border: 1.5px solid #d1d5db;
  border-radius: 0.25rem;
  padding: 0.3rem 0.4rem;
  flex: 1;
  font-size: 0.65rem;
  line-height: 1.2;
}

.flow-node-sm {
  background: #f3f4f6;
  border: 1.5px solid #d1d5db;
  border-radius: 0.25rem;
  padding: 0.25rem 0.3rem;
  flex: 1;
  font-size: 0.6rem;
  line-height: 1.2;
}

.characteristics {
  margin-top: 0.5rem;
  padding: 0.4rem;
  background: #f9fafb;
  border-left: 3px solid #0e7490;
  font-size: 0.7rem;
  line-height: 1.4;
  color: #374151;
}

/* Protocol Table */
.protocol-table {
  width: 100%;
  font-size: 0.7rem;
  border-collapse: collapse;
  margin-top: 0.5rem;
}

.protocol-table th {
  background: #f3f4f6;
  padding: 0.3rem 0.4rem;
  text-align: left;
  font-weight: 600;
  border: 1px solid #d1d5db;
  font-size: 0.65rem;
}

.protocol-table td {
  padding: 0.25rem 0.4rem;
  border: 1px solid #e5e7eb;
  font-size: 0.65rem;
}

.protocol-table code {
  background: #f3f4f6;
  padding: 0.1rem 0.3rem;
  border-radius: 0.15rem;
  font-size: 0.6rem;
}

/* File Architecture */
.file-category {
  font-weight: 700;
  font-size: 0.7rem;
  color: #374151;
  margin-bottom: 0.25rem;
  background: #f3f4f6;
  padding: 0.25rem 0.4rem;
  border-radius: 0.25rem;
}

.file-list {
  list-style: none;
  padding: 0;
  font-size: 0.65rem;
  line-height: 1.5;
  color: #4b5563;
}

.file-list li {
  margin-bottom: 0.15rem;
}

.file-list code {
  background: #fef3c7;
  padding: 0.1rem 0.3rem;
  border-radius: 0.15rem;
  font-weight: 600;
  font-size: 0.6rem;
}

/* Decision List */
.decision-list {
  list-style: none;
  padding: 0;
  font-size: 0.7rem;
  line-height: 1.5;
  color: #374151;
}

.decision-list li {
  margin-bottom: 0.4rem;
  padding-left: 0.8rem;
  position: relative;
}

.decision-list li::before {
  content: "→";
  position: absolute;
  left: 0;
  color: #0e7490;
  font-weight: bold;
}

/* JSON Examples */
.json-label {
  font-weight: 600;
  font-size: 0.7rem;
  color: #374151;
  margin-bottom: 0.15rem;
}

.json-code {
  background: #1f2937;
  color: #10b981;
  padding: 0.4rem;
  border-radius: 0.25rem;
  font-size: 0.6rem;
  line-height: 1.4;
  overflow-x: auto;
  font-family: 'Courier New', monospace;
}

.json-desc {
  font-size: 0.65rem;
  color: #6b7280;
  margin-top: 0.15rem;
}

.document-footer {
  margin-top: 2rem;
}

/* ============================================
   ESTILOS PARA IMPRESIÓN
   ============================================ */

@media print {
  @page {
    size: A4;
    margin: 1.5cm 1.5cm 1.5cm 1.5cm;
  }

  body {
    background: white !important;
  }

  .no-print {
    display: none !important;
  }

  .document-container {
    max-width: 100%;
    padding: 0;
    margin: 0;
  }

  .section {
    page-break-inside: avoid;
  }

  .section-title {
    page-break-after: avoid;
  }

  /* Ajustar tamaños de fuente para impresión */
  .section-title {
    font-size: 10pt;
  }

  p, li, td, .characteristics {
    font-size: 8pt;
    line-height: 1.3;
  }

  .tech-list, .file-list, .decision-list {
    font-size: 7.5pt;
  }

  .protocol-table {
    font-size: 7pt;
  }

  .json-code {
    font-size: 6.5pt;
  }

  .flow-box, .flow-node, .arch-box {
    font-size: 7pt;
  }

  /* Forzar salto de página después de columna 1 si es necesario */
  .grid.grid-cols-2 {
    display: block;
  }

  .grid.grid-cols-2 > div:first-child {
    page-break-after: always;
  }
}

/* Ocultar el botón de acciones en pantalla pequeña */
@media (max-width: 768px) {
  .document-container {
    padding: 1rem;
  }
}
</style>
