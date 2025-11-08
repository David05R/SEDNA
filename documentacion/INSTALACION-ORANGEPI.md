# 🍊 Instalación en OrangePi - Robot SEDNA

## 🎯 Lo que ya tienes configurado

✅ Cloudflare Tunnel funcionando
✅ Dominio: `ws.sednarobot.org`
✅ Frontend apuntando a `wss://ws.sednarobot.org/ws/control`

## 🚀 Lo que necesitas hacer ahora

Instalar el **backend FastAPI** en la OrangePi para que escuche en `localhost:8080`.

---

## 📋 Opción 1: Script Automático (Recomendado)

### 1. Copia los archivos del backend a la OrangePi

Desde tu PC:

```bash
# Opción A: Usando SCP
scp -r backend/* usuario@ip-orangepi:/home/usuario/

# Opción B: Usando USB o red compartida
# Copia la carpeta 'backend' a la OrangePi
```

### 2. En la OrangePi, ejecuta el script de instalación

```bash
ssh usuario@ip-orangepi

cd /home/usuario/
chmod +x install-orangepi.sh
./install-orangepi.sh
```

El script hará TODO automáticamente:
- ✅ Instalar dependencias
- ✅ Crear entorno virtual
- ✅ Configurar servicio systemd
- ✅ Probar el servidor

### 3. Iniciar el servicio

```bash
# Iniciar
sudo systemctl start robot-api

# Habilitar para que inicie automáticamente
sudo systemctl enable robot-api

# Ver estado
sudo systemctl status robot-api

# Ver logs en tiempo real
sudo journalctl -u robot-api -f
```

---

## 📋 Opción 2: Instalación Manual

Si prefieres hacerlo paso a paso:

### 1. Crear directorio

```bash
mkdir -p ~/robot-sedna
cd ~/robot-sedna
```

### 2. Copiar archivos

Copia `main.py` y `requirements.txt` a este directorio.

### 3. Instalar Python y dependencias

```bash
# Instalar Python si no lo tienes
sudo apt update
sudo apt install -y python3 python3-pip python3-venv

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 4. Probar el servidor

```bash
# Iniciar servidor
python main.py
```

Deberías ver:
```
🤖 Iniciando servidor FastAPI para Robot SEDNA
📍 URL: http://0.0.0.0:8080
📡 WebSocket: ws://0.0.0.0:8080/ws/control
📖 Docs: http://0.0.0.0:8080/docs
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080
```

### 5. Probar desde la misma OrangePi

Abre otra terminal:

```bash
curl http://localhost:8080/health
```

Deberías ver:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-26T...",
  "robot_state": {...}
}
```

### 6. Crear servicio systemd

```bash
sudo nano /etc/systemd/system/robot-api.service
```

Pega:

```ini
[Unit]
Description=Robot SEDNA FastAPI Backend
After=network.target

[Service]
Type=simple
User=tu-usuario
WorkingDirectory=/home/tu-usuario/robot-sedna
Environment="PATH=/home/tu-usuario/robot-sedna/venv/bin"
ExecStart=/home/tu-usuario/robot-sedna/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**⚠️ Importante:** Reemplaza `tu-usuario` con tu nombre de usuario real.

```bash
# Recargar systemd
sudo systemctl daemon-reload

# Habilitar e iniciar
sudo systemctl enable robot-api
sudo systemctl start robot-api

# Ver estado
sudo systemctl status robot-api
```

---

## 🧪 Verificar que todo funciona

### 1. Backend local en OrangePi

```bash
curl http://localhost:8080/health
```

✅ Debe responder con JSON.

### 2. Cloudflare Tunnel

```bash
# Verificar que el tunnel esté corriendo
sudo systemctl status cloudflared
```

✅ Debe estar "active (running)".

### 3. Desde internet (tu PC)

```bash
curl https://ws.sednarobot.org/health
```

✅ Debe responder igual que el local.

### 4. WebSocket desde el navegador

Abre consola del navegador (F12) y ejecuta:

```javascript
const ws = new WebSocket('wss://ws.sednarobot.org/ws/control');

ws.onopen = () => {
  console.log('✅ Conectado a ws.sednarobot.org!');
  ws.send(JSON.stringify({ axis1: 0, axis2: 0 }));
};

ws.onmessage = (event) => {
  console.log('📥 Respuesta del robot:', JSON.parse(event.data));
};

ws.onerror = (error) => {
  console.error('❌ Error:', error);
};
```

---

## 🔧 Configuración de Cloudflare Tunnel

Tu `~/.cloudflared/config.yml` debe verse así:

```yaml
tunnel: <TU-UUID-DEL-TUNNEL>
credentials-file: /home/usuario/.cloudflared/<TU-UUID>.json

ingress:
  # WebSocket del backend
  - hostname: ws.sednarobot.org
    service: ws://localhost:8080
    originRequest:
      noTLSVerify: true

  # Cámaras (si las tienes configuradas)
  - hostname: cam1.sednarobot.org
    service: http://localhost:8081

  - hostname: cam2.sednarobot.org
    service: http://localhost:8082

  - hostname: cam3.sednarobot.org
    service: http://localhost:8083

  # Catch-all
  - service: http_status:404
```

**Nota:** El servicio es `ws://localhost:8080` (SIN `/ws/control`), porque FastAPI maneja las rutas internamente.

---

## 📊 Resumen de Puertos

| Servicio | Puerto | URL |
|----------|--------|-----|
| Backend FastAPI | 8080 | http://localhost:8080 |
| Cámara 1 (opcional) | 8081 | http://localhost:8081 |
| Cámara 2 (opcional) | 8082 | http://localhost:8082 |
| Cámara 3 (opcional) | 8083 | http://localhost:8083 |

**A través de Cloudflare:**
- Backend: `wss://ws.sednarobot.org/ws/control`
- Cámaras: `https://cam1.sednarobot.org`, etc.

---

## 🛠️ Comandos Útiles

### Ver logs del backend:
```bash
sudo journalctl -u robot-api -f
```

### Reiniciar backend:
```bash
sudo systemctl restart robot-api
```

### Detener backend:
```bash
sudo systemctl stop robot-api
```

### Ver estado de Cloudflare Tunnel:
```bash
sudo systemctl status cloudflared
sudo journalctl -u cloudflared -f
```

### Probar WebSocket localmente:
```bash
# Instalar wscat
npm install -g wscat

# Probar
wscat -c ws://localhost:8080/ws/control
```

---

## 🐛 Troubleshooting

### ❌ Error: "Connection refused"

**Problema:** El backend no está corriendo.

**Solución:**
```bash
sudo systemctl status robot-api
sudo systemctl start robot-api
```

### ❌ Error: "502 Bad Gateway" desde Cloudflare

**Problema:** Cloudflare no puede conectar al backend local.

**Solución:**
1. Verifica que el backend esté corriendo: `curl http://localhost:8080/health`
2. Verifica que cloudflared esté corriendo: `sudo systemctl status cloudflared`
3. Revisa los logs: `sudo journalctl -u cloudflared -f`

### ❌ El WebSocket se conecta pero no responde

**Problema:** La ruta del WebSocket está mal.

**Solución:**
Verifica que tu `.env` en el frontend tenga:
```bash
NUXT_PUBLIC_ROBOT_WS_URL=wss://ws.sednarobot.org/ws/control
```

### ❌ "ModuleNotFoundError: No module named 'fastapi'"

**Problema:** El entorno virtual no está activado o las dependencias no están instaladas.

**Solución:**
```bash
cd ~/robot-sedna
source venv/bin/activate
pip install -r requirements.txt
```

---

## 🎯 Checklist Final

Antes de probar desde el frontend:

- [ ] Backend instalado en OrangePi
- [ ] Servicio `robot-api` corriendo (`systemctl status robot-api`)
- [ ] Cloudflare Tunnel corriendo (`systemctl status cloudflared`)
- [ ] `curl http://localhost:8080/health` responde OK
- [ ] `curl https://ws.sednarobot.org/health` responde OK desde internet
- [ ] Frontend `.env` tiene `wss://ws.sednarobot.org/ws/control`

---

## 🚀 Siguiente Paso

Una vez que todo esté funcionando:

1. Abre el frontend: http://localhost:3000/visor (desde tu PC)
2. Conecta tu gamepad Bluetooth
3. Cambia al modo "long"
4. Haz clic en "Conectar al Robot"
5. ¡Mueve el joystick!

Deberías ver los comandos llegando a la OrangePi:

```bash
# En los logs del backend
sudo journalctl -u robot-api -f

# Verás:
📥 Comando: axis1= -850, axis2=    0 → ⬆️  ADELANTE (85.0%)
```

---

¿Necesitas ayuda con algún paso? 🤖
