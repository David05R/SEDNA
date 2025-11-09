# Backend Robot SEDNA

Sistema de control dual para Robot SEDNA con telemetría en tiempo real.

## 🎯 Arquitectura

```
┌─────────────────┐
│    Frontend     │
│  (Nuxt + Vue)   │
└────────┬────────┘
         │ HTTP POST /mode/{short|long|idle}
         │ WebSocket /ws/control
         ▼
┌─────────────────────────────────┐
│    main_minimal.py              │
│    (FastAPI Backend)            │
│                                 │
│  ┌──────────────────────────┐  │
│  │  Modo LONG (WebSocket)   │  │
│  │  - Control remoto        │  │
│  │  - Gamepad Bluetooth     │  │
│  └──────────────────────────┘  │
│                                 │
│  ┌──────────────────────────┐  │
│  │  Modo SHORT (RF)         │  │
│  │  - Control iBus          │  │
│  │  - Sin latencia          │  │
│  └──────────────────────────┘  │
│                                 │
│  ┌──────────────────────────┐  │
│  │  ESP32 Reader            │  │
│  │  - RPM encoders          │  │
│  │  - Voltaje batería       │  │
│  └──────────────────────────┘  │
└─────────────────────────────────┘
```

## 📁 Archivos

### Principal
- **`main_minimal.py`** - Backend FastAPI principal con control dual integrado

### Módulos
- **`motor_controller.py`** - Control de motores BTS7960 con PWM
- **`ibus_controller.py`** - Lectura de receptor iBus (modo SHORT)
- **`esp32_reader.py`** - Lectura de telemetría desde ESP32

### Scripts
- **`install-orangepi.sh`** - Instalación automatizada en Orange Pi
- **`orangepi-setup.sh`** - Configuración del sistema
- **`fix-esp32-connection.sh`** - Diagnóstico y fix de conexión ESP32

## 🚀 Instalación

```bash
# En Orange Pi
cd /home/orangepi/SEDNA/backend
pip3 install -r requirements.txt
uvicorn main_minimal:app --host 0.0.0.0 --port 5050 --reload
```

## 🎮 Modos de Operación

### IDLE - Standby
- Motores detenidos
- Telemetría activa
- Esperando comandos

### SHORT - Control RF Local
- Control via receptor iBus (RF 2.4GHz)
- Loop iBus integrado en `main_minimal.py`
- Sin latencia
- Telemetría en tiempo real

### LONG - Control Remoto WebSocket
- Control via WebSocket + Gamepad Bluetooth
- Telemetría bidireccional
- Latencia ~500ms

## 📡 Endpoints

### HTTP
- `GET /health` - Estado del robot y telemetría
- `GET /status` - Estado detallado del sistema
- `GET /ping` - Test de latencia
- `POST /mode/{idle|short|long}` - Cambiar modo de operación

### WebSocket
- `WS /ws/control` - Control y telemetría en tiempo real
  - Envío: `{"axis1": -1000..1000, "axis2": -1000..1000}`
  - Recepción: `{"type": "telemetry", "robot_state": {...}}`

## 📊 Telemetría (robot_state)

```json
{
  "battery": 82,           // Porcentaje 0-100
  "battery_voltage": 12.45, // Voltaje real (V)
  "rpm_motor1": 120.5,      // RPM encoder motor 1
  "rpm_motor2": 118.3,      // RPM encoder motor 2
  "gps": {
    "lat": 10.342586,
    "lng": -75.492847
  },
  "speed": 0,               // PWM actual de motores
  "operational": true,      // Robot funcionando
  "remote_control": false,  // Control remoto activo
  "mode": "idle"            // Modo actual
}
```

## 🔌 Hardware - ESP32

### Conexiones
- **Encoders KY-040**
  - Motor 1: GPIO 34 (CLK), GPIO 35 (DT)
  - Motor 2: GPIO 32 (CLK), GPIO 33 (DT)
- **Sensor voltaje FZ0430**
  - GPIO 36 (ADC1_CH0)
  - VIN+ → Batería +
  - VIN- → Batería -
- **USB a Orange Pi**: `/dev/ttyUSB0` @ 115200 baud

### Formato Serial
```
RPM Motor 1: 120.50 | RPM Motor 2: 118.30 | Bat V: 12.456 V
```

### Rango de batería
- **Mínimo**: 11.0V (0%)
- **Máximo**: 14.6V (100%)

## 🔧 Troubleshooting

### ESP32 no conecta

```bash
# Diagnosticar y reparar automáticamente
cd /home/orangepi/SEDNA/backend
chmod +x fix-esp32-connection.sh
./fix-esp32-connection.sh
```

### Verificar telemetría

```bash
# Ver datos directos de ESP32
sudo screen /dev/ttyUSB0 115200

# Ver endpoint
curl http://localhost:5050/health | python3 -m json.tool
```

### Logs del backend

```bash
# Si está corriendo como servicio
journalctl -u sedna-backend -f

# Si está corriendo manual
# Los logs aparecen en la terminal
```

## 📈 Optimizaciones de Velocidad

- **WebSocket telemetry**: Cada 500ms (antes 2s)
- **ESP32 read loop**: Cada 100ms
- **HTTP polling**: Solo cuando WebSocket no está conectado
- **Frontend updates**: Tiempo real via WebSocket

Ver `MEJORAS_VELOCIDAD.md` en la raíz del proyecto para más detalles.

## 🔄 Cambio de Modos

El backend maneja transiciones limpias entre modos:

```
IDLE → SHORT: Inicia loop iBus integrado
SHORT → LONG: Detiene iBus, inicia WebSocket
LONG → SHORT: Limpia WebSocket, reinicia iBus
ANY → IDLE: Detiene todo, motores a 0
```

## 📚 Documentación

Ver `/documentacion` en la raíz del proyecto para:
- Instalación completa en Orange Pi
- Configuración de Cloudflare Tunnel para WebSocket
- Diagramas de arquitectura

---

**Versión:** 2.0
**Fecha:** 2025-11-09
**Estado:** ✅ Producción
