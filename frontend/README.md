# 🎨 Robot SEDNA - Frontend

Interfaz web para control y monitoreo remoto del Robot SEDNA, construida con Nuxt 4 y Vue 3.

## 🚀 Inicio Rápido

### 1. Instalación

```bash
npm install
```

### 2. Configuración

```bash
cp .env.example .env
```

Edita `.env` y configura la URL del WebSocket:

```bash
# Desarrollo local
NUXT_PUBLIC_ROBOT_WS_URL=ws://localhost:8080/ws/control

# Producción
NUXT_PUBLIC_ROBOT_WS_URL=wss://ws.sednarobot.org/ws/control
```

### 3. Desarrollo

```bash
npm run dev
```

Abre http://localhost:3000/visor

### 4. Producción

```bash
npm run build
npm run preview
```

## 📁 Estructura

```
frontend/
├── app/
│   ├── pages/
│   │   └── visor.vue          # Página principal del HMI
│   ├── components/
│   │   └── visor/
│   │       ├── ModeLong.vue   # Modo control remoto
│   │       ├── ModeShort.vue  # Modo corto alcance
│   │       ├── ModeSurvey.vue # Modo mapeo
│   │       ├── HeaderBar.vue  # Navegación
│   │       └── GpsMap.vue     # Componente de mapa
│   ├── composables/
│   │   └── useRobotControl.ts # Lógica WebSocket
│   └── assets/
│       └── css/main.css       # Estilos globales
├── public/                    # Archivos estáticos
├── nuxt.config.ts            # Configuración de Nuxt
└── package.json              # Dependencias
```

## 🎮 Modos de Operación

### 1. Mode Short (Corto Alcance)
- 3 cámaras lado a lado
- Telemetría completa
- Mapa GPS
- Estado del robot

### 2. Mode Long (Control Remoto)
- Vista principal con HUD
- Mini-mapa
- Brújula
- Control con gamepad
- Estado de conexión WebSocket

### 3. Mode Survey (Mapeo)
- Vista principal + panel lateral
- Visualización de ruta
- Sensores

## 🛠️ Tecnologías

- **Framework**: Nuxt 4.0.3
- **UI Library**: Vue 3.5.18
- **Styling**: Tailwind CSS 4.1.12
- **Components**: Nuxt UI 3.3.2, Vuetify 3.9.5
- **Maps**: Leaflet 1.9.4 + Vue-Leaflet
- **Icons**: Material Design Icons

## 🎮 Control con Gamepad

El sistema usa la Gamepad API del navegador:

```typescript
// Detectar gamepad
navigator.getGamepads()

// Capturar ejes
const axis1 = gamepad.axes[3]  // Joystick derecho Y
const axis2 = gamepad.axes[2]  // Joystick derecho X
```

## 📡 WebSocket

El composable `useRobotControl.ts` maneja la comunicación:

```typescript
const { isConnected, connect, disconnect, sendControlCommand } = useRobotControl()

// Conectar
connect()

// Enviar comando
sendControlCommand(axis1, axis2)

// Desconectar
disconnect()
```

## 🎨 Personalización

### Cambiar colores

Edita `app/assets/css/main.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

### Agregar nuevo modo

1. Crea componente en `app/components/visor/ModeNuevo.vue`
2. Agrégalo en `HeaderBar.vue`
3. Impórtalo en `visor.vue`

## 📦 Build

```bash
# Desarrollo
npm run dev

# Build de producción
npm run build

# Preview de producción
npm run preview

# Generar sitio estático
npm run generate
```

## 🔧 Variables de Entorno

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `NUXT_PUBLIC_ROBOT_WS_URL` | URL del WebSocket | `ws://localhost:8080/ws/control` |

## 📚 Recursos

- [Nuxt 4 Docs](https://nuxt.com)
- [Vue 3 Docs](https://vuejs.org)
- [Tailwind CSS](https://tailwindcss.com)
- [Leaflet](https://leafletjs.com)

## 🐛 Debugging

### Consola del navegador (F12)

Verás logs de:
- Conexión/desconexión WebSocket
- Detección de gamepad
- Comandos enviados
- Errores

### Vue DevTools

Instala la extensión para ver:
- Estado de componentes
- Props y eventos
- Performance

## 📝 Notas

- Las cámaras usan `<img>` tags para streams MJPEG (mejor rendimiento)
- El WebSocket se reconecta automáticamente
- La zona muerta del joystick es de 0.1 (10%)
- Los valores se escalan de -1..1 a -1000..1000

---

Ver [README principal](../README.md) para documentación completa del proyecto.
