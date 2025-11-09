# 🤖 Robot SEDNA - Sistema de Control Dual

Sistema de interfaz web para control y monitoreo del robot SEDNA, con dos modos de operación: control RF de corto alcance y control remoto WebSocket con telemetría en tiempo real.

## 🎯 Arquitectura

```
┌─────────────────────────────┐
│       Frontend              │
│    (Nuxt 4 + Vue 3)         │
│  https://sednarobot.org     │
└──────────┬──────────────────┘
           │ POST /mode/{short|long|idle}
           │ WS /ws/control
           ▼
┌─────────────────────────────┐
│   main_minimal.py           │
│   (FastAPI Backend)         │
│   Orange Pi - Port 5050     │
│                             │
│  ┌──────────────────────┐  │
│  │  ESP32 Reader        │  │
│  │  - RPM encoders      │  │
│  │  - Voltaje batería   │  │
│  └──────────────────────┘  │
│                             │
│  ┌──────────────────────┐  │
│  │  Modo LONG           │  │
│  │  WebSocket + Gamepad │  │
│  └──────────────────────┘  │
│                             │
│  ┌──────────────────────┐  │
│  │  Modo SHORT          │  │
│  │  iBus integrado      │  │
│  └──────────────────────┘  │
└─────────────────────────────┘
```

## 📁 Estructura del Proyecto

```
SEDNA/
├── backend/
│   ├── main_minimal.py         ← Backend principal FastAPI
│   ├── motor_controller.py     ← Control motores BTS7960
│   ├── ibus_controller.py      ← Lectura receptor iBus
│   ├── esp32_reader.py         ← Telemetría ESP32
│   ├── fix-esp32-connection.sh ← Diagnóstico ESP32
│   ├── requirements.txt
│   └── README.md
│
├── frontend/
│   ├── app/                    ← Código Vue/Nuxt
│   │   ├── components/visor/  ← Componentes de interfaz
│   │   ├── composables/       ← useRobotControl.ts
│   │   └── pages/             ← Páginas (visor.vue)
│   ├── package.json
│   └── README.md
│
├── documentacion/
│   ├── CLOUDFLARE-WEBSOCKET-SETUP.md
│   └── INSTALACION-ORANGEPI.md
│
├── MEJORAS_VELOCIDAD.md       ← Optimizaciones telemetría
└── README.md                  ← Este archivo
```

## ✨ Características

### Dos Modos de Control

**🔷 Modo SHORT (Corto Alcance)**
- Control RF vía receptor FlySky iBus
- Sin latencia, respuesta instantánea
- Loop iBus integrado en `main_minimal.py`
- Telemetría en tiempo real (500ms)
- Ideal para operación en campo cercano

**🔷 Modo LONG (Remoto)**
- Control WebSocket + Gamepad Bluetooth
- Telemetría bidireccional (500ms)
- Streams de 3 cámaras MJPEG optimizadas
- GPS y navegación con mapa
- Ideal para operación remota

### Telemetría Completa
- 🔋 Batería: Porcentaje y voltaje (11V-14.6V)
- ⚡ RPM: 2 motores con encoders KY-040
- 🗺️ GPS: Coordenadas en tiempo real
- 📊 Estado: Operacional, modo, velocidad

### Interfaz Web
- 📹 3 streams de cámaras con baja latencia
- 🗺️ Mapas GPS interactivos (Leaflet)
- 📊 HUD con telemetría en tiempo real
- 🎮 Control con gamepad Bluetooth (API nativa)
- 📱 Diseño responsive y optimizado

## 🚀 Inicio Rápido

### 1. Backend (Orange Pi)

```bash
cd backend

# Instalar dependencias
pip3 install -r requirements.txt

# Iniciar servidor
uvicorn main_minimal:app --host 0.0.0.0 --port 5050 --reload
```

El backend estará en:
- API: http://orangepi-ip:5050
- WebSocket: ws://orangepi-ip:5050/ws/control
- Docs: http://orangepi-ip:5050/docs

### 2. Frontend

```bash
cd frontend

# Instalar dependencias
npm install

# Configurar variables de entorno
cp .env.example .env
# Edita .env y configura las URLs del backend

# Iniciar desarrollo
npm run dev
```

El frontend estará en: http://localhost:3000

### 3. Usar el Sistema

1. Abre http://localhost:3000/visor
2. Selecciona el modo:
   - **SHORT**: Control RF (iBus)
   - **LONG**: Control remoto con gamepad
3. En modo LONG:
   - Conecta un gamepad Bluetooth
   - Haz clic en "Conectar al Robot"
   - Mueve el joystick derecho para controlar

## 🎮 Modos de Operación

### Modo SHORT
- Loop iBus integrado directamente en `main_minimal.py`
- Comparte la misma instancia de `motor_controller`
- Sin procesos externos, sin conflictos de GPIO
- Telemetría activa via WebSocket (500ms)

### Modo LONG
- Control via WebSocket con gamepad Bluetooth
- Telemetría bidireccional (500ms)
- Mapeo de ejes: Joystick derecho Y (axis1) y X (axis2)
- Rango: -1000 a 1000

### Modo IDLE
- Motores detenidos
- Telemetría activa
- Esperando comandos

## 📡 API Endpoints

### HTTP
- `GET /health` - Estado del robot y telemetría completa
- `GET /status` - Estado detallado del sistema
- `GET /ping` - Test de latencia
- `POST /mode/{idle|short|long}` - Cambiar modo de operación

### WebSocket
- `WS /ws/control` - Control y telemetría en tiempo real

**Cliente → Servidor:**
```json
{
  "axis1": -850,  // Adelante/Atrás (-1000 a 1000)
  "axis2": 300    // Izquierda/Derecha (-1000 a 1000)
}
```

**Servidor → Cliente (cada 500ms):**
```json
{
  "type": "telemetry",
  "robot_state": {
    "battery": 82,
    "battery_voltage": 12.45,
    "rpm_motor1": 120.5,
    "rpm_motor2": 118.3,
    "gps": {"lat": 10.342586, "lng": -75.492847},
    "speed": 0,
    "operational": true,
    "remote_control": false,
    "mode": "idle"
  }
}
```

## 🔌 Hardware - ESP32

### Componentes
- ESP32 DevKit
- 2x Encoder KY-040 (motores)
- Módulo FZ0430 (sensor de voltaje)

### Conexiones
- **Encoders KY-040**
  - Motor 1: GPIO 34 (CLK), GPIO 35 (DT)
  - Motor 2: GPIO 32 (CLK), GPIO 33 (DT)
- **Sensor FZ0430**
  - GPIO 36 (ADC1_CH0)
  - VIN+ → Batería +
  - VIN- → Batería -
- **USB a Orange Pi**: `/dev/ttyUSB0` @ 115200 baud

### Formato Serial
```
RPM Motor 1: 120.50 | RPM Motor 2: 118.30 | Bat V: 12.456 V
```

### Rango de batería
- Mínimo: 11.0V (0%)
- Máximo: 14.6V (100%)

## 🛠️ Stack Tecnológico

### Frontend
- **Framework**: Nuxt 4 + Vue 3 (Composition API)
- **UI**: Tailwind CSS 4
- **Mapas**: Leaflet + Vue-Leaflet
- **Control**: Gamepad API (nativa del navegador)
- **Comunicación**: WebSocket + Fetch API

### Backend
- **Framework**: FastAPI 0.115+
- **Server**: Uvicorn (ASGI)
- **WebSocket**: Nativo con FastAPI
- **GPIO**: WiringPi
- **Serial**: pyserial (iBus + ESP32)
- **Async**: asyncio

### Hardware
- **SBC**: Orange Pi 5 Plus
- **Motores**: BTS7960 (doble driver)
- **Telemetría**: ESP32 + KY-040 + FZ0430
- **RF**: FlySky FS-i6 + receptor iBus

## 📈 Optimizaciones de Velocidad

Ver `MEJORAS_VELOCIDAD.md` para detalles completos.

**Cambios aplicados:**
- WebSocket telemetry: 2s → **500ms** (4x más rápido)
- ESP32 read loop: **100ms**
- HTTP polling: Solo cuando WebSocket desconectado
- Frontend: Auto-conecta WebSocket en ambos modos
- Latencia percibida: **0.5 segundos** (antes 2-5s)

## 📚 Documentación Detallada

| Documento | Descripción |
|-----------|-------------|
| [backend/README.md](./backend/README.md) | Arquitectura completa del backend |
| [frontend/README.md](./frontend/README.md) | Documentación del frontend |
| [MEJORAS_VELOCIDAD.md](./MEJORAS_VELOCIDAD.md) | Optimizaciones de telemetría |
| [CLOUDFLARE-WEBSOCKET-SETUP.md](./documentacion/CLOUDFLARE-WEBSOCKET-SETUP.md) | Túnel Cloudflare |
| [INSTALACION-ORANGEPI.md](./documentacion/INSTALACION-ORANGEPI.md) | Setup Orange Pi |

## 🌐 Despliegue en Producción

### Backend en Orange Pi

```bash
cd backend
chmod +x install-orangepi.sh
./install-orangepi.sh

# Ver logs
sudo journalctl -u sedna-backend -f
```

### Frontend

```bash
cd frontend
npm run build
npm run preview
```

### Cloudflare Tunnel (Recomendado)

Para acceso remoto seguro, configura un túnel Cloudflare siguiendo la guía en `documentacion/CLOUDFLARE-WEBSOCKET-SETUP.md`.

## 🔧 Troubleshooting

### ESP32 no conecta

```bash
cd backend
chmod +x fix-esp32-connection.sh
./fix-esp32-connection.sh
```

### WebSocket no se conecta
- Verifica que el backend esté corriendo: `curl http://localhost:5050/health`
- Verifica la URL en `.env` del frontend
- Revisa la consola del navegador (F12) → Network → WS

### Gamepad no se detecta
- Conecta el control Bluetooth ANTES de abrir el navegador
- Presiona algún botón después de conectar
- Verifica en DevTools que `navigator.getGamepads()` retorne un array

### Telemetría lenta
- Abre DevTools Console
- Busca mensajes `📡 WebSocket telemetry recibida:`
- Deberías ver updates cada ~500ms
- Si ves `🔄 Polling HTTP`, WebSocket no está conectado

## 🧪 Testing

### Backend

```bash
# Health check
curl http://localhost:5050/health | python3 -m json.tool

# Cambiar modo
curl -X POST http://localhost:5050/mode/short
curl -X POST http://localhost:5050/mode/long

# Test latencia
curl http://localhost:5050/ping

# WebSocket test
npm install -g wscat
wscat -c ws://localhost:5050/ws/control
```

### Frontend

1. Abre http://localhost:3000/visor
2. Abre DevTools (F12) → Console
3. Conecta un gamepad y verifica detección
4. Cambia entre modos y verifica transiciones
5. Observa logs de WebSocket telemetry

## 🔒 Seguridad

- ✅ WSS (WebSocket Secure) en producción via Cloudflare
- ✅ Cloudflare Tunnel (sin exponer puertos)
- ✅ CORS configurado
- ⚠️ Implementar autenticación para producción
- ⚠️ Agregar kill switch de emergencia

## 🚧 Desarrollo Futuro

- [ ] Autenticación con tokens JWT
- [ ] Grabación de telemetría y misiones
- [ ] Modo autónomo con waypoints GPS
- [ ] Dashboard administrativo
- [ ] Alertas y notificaciones
- [ ] Análisis de datos recolectados

## 📞 Soporte

**Backend:**
```bash
sudo journalctl -u sedna-backend -f
```

**Frontend:**
- Consola del navegador (F12)
- Terminal donde corre `npm run dev`

**ESP32:**
```bash
sudo screen /dev/ttyUSB0 115200  # Ctrl+A, K para salir
```

---

**Robot SEDNA** - Sistema de limpieza de playas automatizado 🤖🏖️

**Versión:** 2.0 | **Fecha:** 2025-11-09 | **Estado:** ✅ Producción
