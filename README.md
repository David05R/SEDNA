# 🤖 Robot SEDNA - Sistema de Control Dual

Sistema de interfaz web para control y monitoreo del robot SEDNA, con dos modos de operación: control RF de corto alcance y control remoto WebSocket.

## 🎯 Arquitectura

```
┌─────────────────────────────┐
│       Frontend              │
│    (Nuxt 4 + Vue 3)         │
│  http://localhost:3000      │
└──────────┬──────────────────┘
           │ POST /mode/{short|long|idle}
           │ WS /ws/control
           ▼
┌─────────────────────────────┐
│   main_minimal.py           │
│   (FastAPI Backend)         │
│   Orange Pi - Port 5050     │
└──────────┬──────────────────┘
           │
      ┌────┴────┐
      │         │
┌─────▼──┐  ┌──▼─────────┐
│ SHORT  │  │   LONG     │
│        │  │            │
│test_   │  │motor_      │
│gpio.py │  │controller  │
│        │  │.py         │
│        │  │            │
│RF      │  │WebSocket   │
│Control │  │+ Bluetooth │
│(iBus)  │  │Gamepad     │
└────────┘  └────────────┘
```

## 📁 Estructura del Proyecto

```
robot-hmi/
├── backend/
│   ├── main_minimal.py         ← BACKEND PRINCIPAL
│   ├── motor_controller.py     ← Control de motores BTS7960
│   ├── ibus_controller.py      ← Lectura de receptor iBus
│   ├── test_gpio.py           ← Control RF directo (modo SHORT)
│   ├── requirements.txt
│   ├── install-orangepi.sh
│   ├── orangepi-setup.sh
│   └── README.md
│
├── frontend/
│   ├── app/                    ← Código fuente Vue/Nuxt
│   ├── package.json
│   └── README.md
│
├── documentacion/
│   ├── CLOUDFLARE-WEBSOCKET-SETUP.md
│   └── INSTALACION-ORANGEPI.md
│
└── README.md                   ← Este archivo
```

## ✨ Características

### Dos Modos de Control

**🔷 Modo SHORT (Corto Alcance)**
- Control vía RF usando receptor FlySky iBus
- Sin latencia, respuesta instantánea
- Ejecuta `test_gpio.py` como proceso independiente
- Ideal para operación en campo cercano

**🔷 Modo LONG (Remoto)**
- Control vía WebSocket + Bluetooth gamepad
- Telemetría en tiempo real
- Streams de cámaras MJPEG
- GPS y navegación
- Ideal para operación remota

### Interfaz Web
- 📹 3 streams de cámaras optimizados
- 🗺️ Mapas GPS en tiempo real
- 📊 Telemetría (batería, velocidad, estado)
- 🎮 Control con gamepad Bluetooth
- 📱 Diseño responsive

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
   - **SHORT**: Para control RF (iBus)
   - **LONG**: Para control remoto con gamepad Bluetooth
3. En modo LONG:
   - Conecta un gamepad Bluetooth
   - Haz clic en "Conectar al Robot"
   - Mueve el joystick derecho para controlar

## 🎮 Modos de Operación

### Modo SHORT
El frontend envía `POST /mode/short` al backend, que:
1. Detiene cualquier control WebSocket activo
2. Libera pines GPIO si estaban en uso
3. Ejecuta `test_gpio.py` como subproceso con sudo
4. `test_gpio.py` lee directamente del receptor iBus y controla motores

### Modo LONG
El frontend envía `POST /mode/long` al backend, que:
1. Detiene cualquier proceso de `test_gpio.py`
2. Inicializa `motor_controller.py` bajo demanda
3. Acepta comandos vía WebSocket desde el gamepad
4. Envía telemetría cada 2 segundos

### Modo IDLE
Detiene ambos modos de control.

## 📡 Protocolo de Comunicación

### Cambio de Modo (HTTP)

```bash
# Activar modo SHORT
POST /mode/short

# Activar modo LONG
POST /mode/long

# Modo IDLE
POST /mode/idle
```

### Control WebSocket (Modo LONG)

Cliente → Servidor:
```json
{
  "axis1": -850,  // Adelante/Atrás (-1000 a 1000)
  "axis2": 300    // Izquierda/Derecha (-1000 a 1000)
}
```

Servidor → Cliente (Telemetría):
```json
{
  "type": "robot_state",
  "battery": 58,
  "gps": {"lat": 10.377, "lng": -75.465},
  "speed": 85.0,
  "mode": "long",
  "operational": true,
  "remote_control": true
}
```

### Estado del Sistema (HTTP)

```bash
GET /health
```

Respuesta:
```json
{
  "status": "healthy",
  "battery": 58,
  "gps": {"lat": 10.377, "lng": -75.465},
  "speed": 85.0,
  "operational": true,
  "remote_control": true,
  "mode": "long"
}
```

## 🛠️ Stack Tecnológico

### Frontend
- Framework: Nuxt 4 + Vue 3
- UI: Tailwind CSS 4, Nuxt UI
- Mapas: Leaflet + Vue-Leaflet
- Control: Gamepad API
- Comunicación: WebSocket, Fetch API

### Backend
- Framework: FastAPI 0.115+
- Server: Uvicorn (ASGI)
- WebSocket: Nativo con FastAPI
- GPIO: WiringPi (motor_controller.py)
- Serial: pyserial (ibus_controller.py)
- Async: asyncio

## 📚 Documentación Detallada

| Documento | Descripción |
|-----------|-------------|
| [backend/README.md](./backend/README.md) | Arquitectura del backend y modos |
| [backend/INSTRUCCIONES_SIMPLE.md](./backend/INSTRUCCIONES_SIMPLE.md) | Instrucciones de uso |
| [frontend/README.md](./frontend/README.md) | Documentación del frontend |
| [CLOUDFLARE-WEBSOCKET-SETUP.md](./documentacion/CLOUDFLARE-WEBSOCKET-SETUP.md) | Configurar Cloudflare Tunnel |
| [INSTALACION-ORANGEPI.md](./documentacion/INSTALACION-ORANGEPI.md) | Instalación en Orange Pi |

## 🌐 Despliegue en Producción

### Backend en Orange Pi

Usando el script automático:
```bash
cd backend
chmod +x install-orangepi.sh
./install-orangepi.sh
```

O manualmente:
```bash
sudo systemctl start robot-api
sudo systemctl enable robot-api
```

Ver logs:
```bash
sudo journalctl -u robot-api -f
```

### Frontend

Build de producción:
```bash
cd frontend
npm run build
npm run preview
```

### Cloudflare Tunnel (Opcional)

Para acceso remoto seguro, configura un túnel Cloudflare siguiendo la guía en `documentacion/CLOUDFLARE-WEBSOCKET-SETUP.md`.

## 🧪 Testing

### Probar Backend

```bash
# Health check
curl http://localhost:5050/health

# Cambiar a modo SHORT
curl -X POST http://localhost:5050/mode/short

# Cambiar a modo LONG
curl -X POST http://localhost:5050/mode/long

# Probar WebSocket
npm install -g wscat
wscat -c ws://localhost:5050/ws/control
```

### Probar Frontend

1. Abre http://localhost:3000/visor
2. Abre DevTools (F12) para ver logs
3. Conecta un gamepad y verifica la detección
4. Cambia entre modos SHORT y LONG

## ⚠️ Notas Importantes

### Cambio de Modo LONG → SHORT
Cuando se cambia de modo LONG a SHORT:
1. El backend espera 1 segundo antes de iniciar `test_gpio.py`
2. Ejecuta `pkill -9 -f test_gpio.py` para eliminar procesos residuales
3. `motor_controller.py` libera completamente los pines GPIO

Esto evita conflictos de GPIO entre ambos modos.

### Polling HTTP
- Cuando el WebSocket está conectado (modo LONG), el polling HTTP se detiene automáticamente
- El polling se reinicia cuando el WebSocket se desconecta
- Intervalo de polling: 5 segundos

## 🔒 Seguridad

- ✅ Usa WSS (WebSocket Secure) en producción
- ✅ Cloudflare Tunnel para conexión segura sin abrir puertos
- ✅ CORS configurado correctamente
- ⚠️ Considera agregar autenticación para producción
- ⚠️ Implementar kill switch de emergencia

## ❓ Troubleshooting

### El modo SHORT se traba al volver de LONG
- El backend ahora incluye un delay de 1s y cleanup agresivo de GPIO
- Verifica logs: `sudo journalctl -u robot-api -f`

### WebSocket no se conecta
- Verifica que el backend esté corriendo en puerto 5050
- Verifica la URL en `.env` del frontend
- Revisa la consola del navegador (F12)

### El gamepad no se detecta
- Conecta el control Bluetooth ANTES de abrir el navegador
- Presiona algún botón después de conectar
- Verifica en http://localhost:3000/visor que aparezca el indicador de gamepad

## 📞 Soporte

**Backend:**
- Ver logs: `sudo journalctl -u robot-api -f`
- Docs interactivas: http://localhost:5050/docs

**Frontend:**
- Consola del navegador: F12
- Logs de Nuxt en terminal donde corre `npm run dev`

---

**Robot SEDNA** - Sistema de limpieza de playas automatizado 🤖🏖️
