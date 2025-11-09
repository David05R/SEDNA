import { ref, onBeforeUnmount } from 'vue'

export interface RobotControlData {
  axis1: number // -1000 a 1000 (adelante/atrás)
  axis2: number // -1000 a 1000 (izquierda/derecha)
}

export interface RobotState {
  battery: number // 0-100
  battery_voltage: number // Voltaje real de batería
  rpm_motor1: number // RPM encoder motor 1
  rpm_motor2: number // RPM encoder motor 2
  gps: {
    lat: number
    lng: number
  }
  speed: number
  operational?: boolean // Robot funcionando (GPS, sensores)
  remote_control?: boolean // Control remoto activo (WebSocket)
  mode?: string // Modo actual: 'idle' | 'short' | 'long'
  // Mantener 'connected' para compatibilidad con backends antiguos
  connected?: boolean
}

export interface RobotHealthResponse {
  status: string
  timestamp: string
  robot_state: RobotState
}

export const useRobotControl = () => {
  const ws = ref<WebSocket | null>(null)
  const isConnected = ref(false)
  const connectionStatus = ref<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected')
  const lastError = ref<string>('')

  // Estado del robot recibido desde el WebSocket
  const robotState = ref<RobotState>({
    battery: 0,
    battery_voltage: 0.0,
    rpm_motor1: 0.0,
    rpm_motor2: 0.0,
    gps: {
      lat: 10.342586,
      lng: -75.492847
    },
    speed: 0,
    operational: false,
    remote_control: false,
    mode: 'idle',
    connected: false
  })

  // URL del WebSocket y API desde variables de entorno
  const config = useRuntimeConfig()
  const WS_URL = config.public.robotWsUrl || 'wss://ws.sednarobot.org/ws/control'
  const API_URL = 'https://ws.sednarobot.org'

  // Intervalo para polling del estado del robot
  let healthPollInterval: ReturnType<typeof setInterval> | null = null

  /**
   * Conecta al WebSocket del robot
   */
  const connect = () => {
    if (ws.value?.readyState === WebSocket.OPEN) {
      console.log('WebSocket ya está conectado')
      return
    }

    try {
      connectionStatus.value = 'connecting'
      ws.value = new WebSocket(WS_URL)

      ws.value.onopen = () => {
        console.log('WebSocket conectado al robot')
        isConnected.value = true
        connectionStatus.value = 'connected'
        lastError.value = ''

        // Detener polling HTTP cuando WebSocket se conecta
        stopHealthPolling()
        console.log('🛑 Polling HTTP detenido (usando WebSocket)')
      }

      ws.value.onclose = () => {
        console.log('WebSocket desconectado')
        isConnected.value = false
        connectionStatus.value = 'disconnected'

        // Reiniciar polling HTTP cuando WebSocket se cierra
        startHealthPolling()
        console.log('🔄 Polling HTTP reiniciado (WebSocket cerrado)')
      }

      ws.value.onerror = (error) => {
        console.error('Error en WebSocket:', error)
        connectionStatus.value = 'error'
        lastError.value = 'Error de conexión con el robot'
      }

      ws.value.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)

          // Log para debug (temporal)
          if (data.type === 'telemetry') {
            console.log('📡 WebSocket telemetry recibida:', {
              battery: data.robot_state?.battery,
              voltage: data.robot_state?.battery_voltage,
              rpm1: data.robot_state?.rpm_motor1,
              rpm2: data.robot_state?.rpm_motor2,
              timestamp: new Date().toLocaleTimeString()
            })
          }

          // Si es telemetría del WebSocket, actualizar estado
          if (data.type === 'telemetry' && data.robot_state) {
            robotState.value = {
              battery: data.robot_state.battery || 0,
              battery_voltage: data.robot_state.battery_voltage || 0.0,
              rpm_motor1: data.robot_state.rpm_motor1 || 0.0,
              rpm_motor2: data.robot_state.rpm_motor2 || 0.0,
              gps: data.robot_state.gps || robotState.value.gps,
              speed: data.robot_state.speed || 0,
              operational: data.robot_state.operational ?? true,
              remote_control: data.robot_state.remote_control ?? false,
              mode: data.robot_state.mode || 'idle',
              connected: data.robot_state.connected ?? false
            }
          }
          // Si el mensaje contiene robot_state directamente (compatibilidad)
          else if (data.robot_state) {
            robotState.value = {
              battery: data.robot_state.battery || 0,
              battery_voltage: data.robot_state.battery_voltage || 0.0,
              rpm_motor1: data.robot_state.rpm_motor1 || 0.0,
              rpm_motor2: data.robot_state.rpm_motor2 || 0.0,
              gps: data.robot_state.gps || robotState.value.gps,
              speed: data.robot_state.speed || 0,
              operational: data.robot_state.operational ?? true,
              remote_control: data.robot_state.remote_control ?? false,
              mode: data.robot_state.mode || 'idle',
              connected: data.robot_state.connected || false
            }
          }
        } catch (error) {
          console.error('Error al parsear mensaje del robot:', error)
        }
      }
    } catch (error) {
      console.error('Error al conectar WebSocket:', error)
      connectionStatus.value = 'error'
      lastError.value = 'No se pudo conectar al robot'
    }
  }

  /**
   * Desconecta el WebSocket
   */
  const disconnect = () => {
    if (ws.value) {
      ws.value.close()
      ws.value = null
      isConnected.value = false
      connectionStatus.value = 'disconnected'
    }

    // Reiniciar polling HTTP cuando WebSocket se desconecta
    startHealthPolling()
    console.log('🔄 Polling HTTP reiniciado (WebSocket desconectado)')
  }

  /**
   * Obtiene el estado del robot desde la API /health
   */
  const fetchRobotHealth = async () => {
    try {
      const response = await fetch(`${API_URL}/health`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data: RobotHealthResponse = await response.json()

      // Actualizar el estado del robot
      if (data.robot_state) {
        robotState.value = {
          battery: data.robot_state.battery || 0,
          battery_voltage: data.robot_state.battery_voltage || 0.0,
          rpm_motor1: data.robot_state.rpm_motor1 || 0.0,
          rpm_motor2: data.robot_state.rpm_motor2 || 0.0,
          gps: data.robot_state.gps || robotState.value.gps,
          speed: data.robot_state.speed || 0,
          operational: data.robot_state.operational ?? data.robot_state.connected ?? false,
          remote_control: data.robot_state.remote_control ?? false,
          mode: data.robot_state.mode || 'idle',
          connected: data.robot_state.connected ?? false
        }
      }
    } catch (error) {
      console.error('Error al obtener estado del robot:', error)
    }
  }

  /**
   * Inicia el polling del estado del robot cada 5 segundos
   * SOLO se usa cuando WebSocket NO está conectado
   */
  const startHealthPolling = () => {
    // No iniciar polling si WebSocket está conectado
    if (isConnected.value) {
      console.log('🚫 No se inicia HTTP polling: WebSocket ya conectado')
      return
    }

    // Detener polling anterior si existe
    stopHealthPolling()

    console.log('🔄 Iniciando HTTP polling (WebSocket no disponible)')

    // Obtener el estado inmediatamente
    fetchRobotHealth()

    // Configurar polling cada 5 segundos (reducido para evitar interferencia)
    healthPollInterval = setInterval(() => {
      // Detener polling si WebSocket se conecta
      if (isConnected.value) {
        console.log('🛑 HTTP polling detenido: WebSocket conectado')
        stopHealthPolling()
        return
      }
      fetchRobotHealth()
    }, 1000)  // Cambiado de 1000ms a 5000ms
  }

  /**
   * Detiene el polling del estado del robot
   */
  const stopHealthPolling = () => {
    if (healthPollInterval) {
      clearInterval(healthPollInterval)
      healthPollInterval = null
    }
  }

  /**
   * Transforma valores del gamepad (-1 a 1) a valores del robot (-1000 a 1000)
   * @param gamepadValue Valor del eje del gamepad (-1.0 a 1.0)
   * @returns Valor transformado para el robot (-1000 a 1000)
   */
  const transformAxis = (gamepadValue: number): number => {
    // Zona muerta para evitar drift (valores muy pequeños se consideran 0)
    const DEAD_ZONE = 0.1
    if (Math.abs(gamepadValue) < DEAD_ZONE) {
      return 0
    }

    // Escalar de -1..1 a -1000..1000
    return Math.round(gamepadValue * 1000)
  }

  /**
   * Envía comandos de control al robot
   * @param axis1Raw Eje 1 del gamepad (joystick derecho Y) - adelante/atrás
   * @param axis2Raw Eje 2 del gamepad (joystick derecho X) - izquierda/derecha
   */
  const sendControlCommand = (axis1Raw: number, axis2Raw: number) => {
    if (!isConnected.value || !ws.value || ws.value.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket no está conectado, no se puede enviar comando')
      return
    }

    const controlData: RobotControlData = {
      axis1: transformAxis(axis1Raw),
      axis2: transformAxis(axis2Raw),
    }

    try {
      ws.value.send(JSON.stringify(controlData))
    } catch (error) {
      console.error('Error al enviar comando:', error)
    }
  }

  /**
   * Limpia recursos al desmontar el componente
   */
  onBeforeUnmount(() => {
    disconnect()
    stopHealthPolling()
  })

  // Iniciar el polling del estado del robot automáticamente
  startHealthPolling()

  /**
   * Cambia el modo del robot (idle, short, long)
   */
  const setRobotMode = async (mode: 'idle' | 'short' | 'long'): Promise<boolean> => {
    try {
      const response = await fetch(`${API_URL}/mode/${mode}`, {
        method: 'POST',
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data = await response.json()
      console.log(`✅ Modo cambiado a: ${mode}`, data)
      return true
    } catch (error) {
      console.error(`❌ Error cambiando modo a ${mode}:`, error)
      return false
    }
  }

  /**
   * Test de ping/latencia al servidor
   */
  const testConnection = async (): Promise<{ success: boolean; latency: number; error?: string }> => {
    const startTime = performance.now()
    try {
      const response = await fetch(`${API_URL}/ping`, {
        method: 'GET',
        cache: 'no-cache',
      })
      const endTime = performance.now()
      const latency = Math.round(endTime - startTime)

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      await response.json() // Parsear respuesta

      return {
        success: true,
        latency,
      }
    } catch (error) {
      const endTime = performance.now()
      const latency = Math.round(endTime - startTime)

      return {
        success: false,
        latency,
        error: error instanceof Error ? error.message : 'Error desconocido',
      }
    }
  }

  return {
    isConnected,
    connectionStatus,
    lastError,
    robotState,
    connect,
    disconnect,
    sendControlCommand,
    transformAxis,
    fetchRobotHealth,
    startHealthPolling,
    stopHealthPolling,
    testConnection,
    setRobotMode,
  }
}
