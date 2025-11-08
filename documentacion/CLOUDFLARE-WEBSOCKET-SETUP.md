# 🌐 Configuración de WebSocket en Cloudflare para Robot SEDNA

## 📋 Opciones Disponibles

Tienes **3 opciones** para exponer el WebSocket de tu OrangePi a través de `sednarobot.org`:

### ✅ **Opción 1: Cloudflare Tunnel (Recomendado)**
- ✅ Más seguro (no necesitas abrir puertos)
- ✅ Gratis
- ✅ Fácil de configurar
- ✅ SSL/TLS automático
- ✅ Funciona detrás de NAT/Firewall

### ⚡ **Opción 2: Proxy Manual + Port Forwarding**
- ⚠️ Requiere IP pública
- ⚠️ Necesitas abrir puerto en router
- ⚠️ Menos seguro

### 🚀 **Opción 3: Cloudflare Workers (Avanzado)**
- ✅ Escalable
- ⚠️ Más complejo
- ⚠️ Puede tener limitaciones en plan gratuito

---

## 🎯 OPCIÓN 1: Cloudflare Tunnel (Recomendado)

Esta es la **mejor opción** para tu caso. Crea un túnel seguro desde tu OrangePi a Cloudflare.

### Paso 1: Instalar Cloudflared en la OrangePi

Conéctate a tu OrangePi vía SSH y ejecuta:

```bash
# Descargar cloudflared (arquitectura ARM64 para OrangePi)
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64

# Dar permisos de ejecución
chmod +x cloudflared-linux-arm64

# Mover a /usr/local/bin
sudo mv cloudflared-linux-arm64 /usr/local/bin/cloudflared

# Verificar instalación
cloudflared --version
```

### Paso 2: Autenticar con Cloudflare

```bash
cloudflared tunnel login
```

Esto abrirá un navegador (o te dará un link) para autenticar con tu cuenta de Cloudflare. Selecciona el dominio `sednarobot.org`.

### Paso 3: Crear el Tunnel

```bash
# Crear un tunnel llamado "robot-control"
cloudflared tunnel create robot-control

# Esto creará un UUID como: 5a1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d
# Guarda este UUID, lo necesitarás
```

### Paso 4: Crear archivo de configuración

Crea el archivo de configuración del tunnel:

```bash
nano ~/.cloudflared/config.yml
```

Pega este contenido (ajusta el UUID con el que te dio el comando anterior):

```yaml
tunnel: <TU-TUNNEL-UUID-AQUI>
credentials-file: /home/<tu-usuario>/.cloudflared/<TU-TUNNEL-UUID-AQUI>.json

ingress:
  # Ruta para el WebSocket de control
  - hostname: ws.sednarobot.org
    service: ws://localhost:8080
    originRequest:
      noTLSVerify: true

  # Ruta para las cámaras (si quieres exponerlas también)
  - hostname: cam1.sednarobot.org
    service: http://localhost:8081

  - hostname: cam2.sednarobot.org
    service: http://localhost:8082

  - hostname: cam3.sednarobot.org
    service: http://localhost:8083

  # Catch-all rule (debe ser la última)
  - service: http_status:404
```

**Importante:** Cambia `<TU-TUNNEL-UUID-AQUI>` por el UUID real de tu tunnel.

### Paso 5: Crear registros DNS en Cloudflare

Ahora necesitas crear un registro DNS para el WebSocket:

```bash
# Ruta el subdominio ws.sednarobot.org al tunnel
cloudflared tunnel route dns robot-control ws.sednarobot.org
```

### Paso 6: Configurar WebSocket en Cloudflare Dashboard

1. Ve a tu dashboard de Cloudflare: https://dash.cloudflare.com
2. Selecciona el dominio `sednarobot.org`
3. Ve a **Network** (Red)
4. Habilita **WebSockets** (debe estar ON)

### Paso 7: Iniciar el Tunnel

Prueba el tunnel manualmente primero:

```bash
cloudflared tunnel run robot-control
```

Si funciona correctamente, configúralo como servicio para que se inicie automáticamente:

```bash
# Instalar como servicio
sudo cloudflared service install

# Iniciar el servicio
sudo systemctl start cloudflared

# Habilitar para que inicie al boot
sudo systemctl enable cloudflared

# Ver status
sudo systemctl status cloudflared
```

### Paso 8: Actualizar el archivo .env del HMI

Ahora actualiza tu `.env` en el proyecto del HMI:

```bash
NUXT_PUBLIC_ROBOT_WS_URL=wss://ws.sednarobot.org
```

**¡Listo!** Tu WebSocket estará disponible en `wss://ws.sednarobot.org`

---

## ⚡ OPCIÓN 2: Proxy Manual (Si no quieres usar Tunnel)

### Requisitos:
- IP pública estática (o Dynamic DNS)
- Puerto forwarding en tu router
- Nginx en la OrangePi

### Paso 1: Configurar Port Forwarding

En tu router, configura:
- **Puerto externo:** 443 (HTTPS)
- **Puerto interno:** 443
- **IP destino:** IP local de tu OrangePi (ej: 192.168.1.100)
- **Protocolo:** TCP

### Paso 2: Instalar Nginx en OrangePi

```bash
sudo apt update
sudo apt install nginx
```

### Paso 3: Configurar Nginx como Proxy WebSocket

Crea el archivo de configuración:

```bash
sudo nano /etc/nginx/sites-available/robot-ws
```

Contenido:

```nginx
map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}

server {
    listen 443 ssl http2;
    server_name ws.sednarobot.org;

    # Certificados SSL (se configuran después)
    ssl_certificate /etc/letsencrypt/live/ws.sednarobot.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ws.sednarobot.org/privkey.pem;

    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts para WebSocket
        proxy_connect_timeout 7d;
        proxy_send_timeout 7d;
        proxy_read_timeout 7d;
    }
}
```

### Paso 4: Obtener certificado SSL

```bash
# Instalar certbot
sudo apt install certbot python3-certbot-nginx

# Obtener certificado (temporalmente deshabilita Cloudflare proxy)
sudo certbot --nginx -d ws.sednarobot.org
```

### Paso 5: Activar configuración

```bash
sudo ln -s /etc/nginx/sites-available/robot-ws /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Paso 6: Configurar DNS en Cloudflare

1. Ve a **DNS** en Cloudflare dashboard
2. Agrega un registro tipo **A**:
   - **Name:** ws
   - **IPv4 address:** Tu IP pública
   - **Proxy status:** 🟠 DNS only (DESACTIVADO) - Importante!
   - **TTL:** Auto

⚠️ **Importante:** El proxy de Cloudflare (nube naranja) debe estar **DESACTIVADO** para WebSockets si usas esta opción.

---

## 🚀 OPCIÓN 3: Cloudflare Workers (Avanzado)

Esta opción usa Workers para crear un proxy WebSocket. Es más complejo pero muy escalable.

### Paso 1: Crear Worker

1. Ve a **Workers & Pages** en Cloudflare
2. Crea un nuevo Worker llamado `robot-ws`
3. Pega este código:

```javascript
export default {
  async fetch(request, env) {
    const upgradeHeader = request.headers.get('Upgrade');

    if (!upgradeHeader || upgradeHeader !== 'websocket') {
      return new Response('Expected Upgrade: websocket', { status: 426 });
    }

    // URL de tu OrangePi (debe ser accesible desde internet)
    const robotUrl = 'ws://TU-IP-PUBLICA:8080';

    // Crear WebSocket pair
    const [client, server] = Object.values(new WebSocketPair());

    // Conectar al robot
    const robotWs = new WebSocket(robotUrl);

    robotWs.addEventListener('open', () => {
      server.accept();

      // Reenviar mensajes cliente → robot
      server.addEventListener('message', (event) => {
        robotWs.send(event.data);
      });

      // Reenviar mensajes robot → cliente
      robotWs.addEventListener('message', (event) => {
        server.send(event.data);
      });
    });

    return new Response(null, {
      status: 101,
      webSocket: client,
    });
  },
};
```

### Paso 2: Configurar Route

1. En el Worker, ve a **Settings** → **Triggers**
2. Agrega una ruta: `ws.sednarobot.org/*`

---

## 🎯 ¿Cuál opción usar?

| Característica | Tunnel | Proxy Manual | Workers |
|----------------|--------|--------------|---------|
| **Facilidad** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **Seguridad** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Sin IP pública** | ✅ | ❌ | ❌ |
| **Sin Port Forwarding** | ✅ | ❌ | ❌ |
| **SSL automático** | ✅ | ⚠️ Manual | ✅ |
| **Gratis** | ✅ | ✅ | ✅* |

**Recomendación:** Usa **Cloudflare Tunnel** (Opción 1) ✅

---

## 🧪 Probar la Conexión

Una vez configurado, prueba la conexión desde tu navegador:

```javascript
// Abre la consola del navegador (F12) y ejecuta:
const ws = new WebSocket('wss://ws.sednarobot.org');

ws.onopen = () => {
  console.log('✅ Conectado!');
  ws.send(JSON.stringify({ axis1: 0, axis2: 0 }));
};

ws.onmessage = (event) => {
  console.log('📥 Mensaje del robot:', event.data);
};

ws.onerror = (error) => {
  console.error('❌ Error:', error);
};
```

---

## 📝 Checklist de Configuración

### Para Cloudflare Tunnel:

- [ ] cloudflared instalado en OrangePi
- [ ] Tunnel creado y autenticado
- [ ] config.yml configurado correctamente
- [ ] DNS route creado (`cloudflared tunnel route dns`)
- [ ] WebSockets habilitado en Cloudflare dashboard
- [ ] Servicio cloudflared corriendo (`systemctl status cloudflared`)
- [ ] `.env` actualizado con `wss://ws.sednarobot.org`

### Para Proxy Manual:

- [ ] Port forwarding configurado en router (puerto 443)
- [ ] Nginx instalado en OrangePi
- [ ] Certificado SSL obtenido con certbot
- [ ] Configuración Nginx activada
- [ ] DNS A record creado en Cloudflare (proxy DESACTIVADO)
- [ ] `.env` actualizado con `wss://ws.sednarobot.org`

---

## ❓ Troubleshooting

### Error: "WebSocket connection failed"

**Causa:** Cloudflare proxy puede estar bloqueando la conexión

**Solución:**
- Si usas Proxy Manual, asegúrate de que el proxy esté DESACTIVADO (nube gris)
- Si usas Tunnel, verifica que cloudflared esté corriendo

### Error: "Connection refused"

**Causa:** El servidor WebSocket no está corriendo en el puerto correcto

**Solución:**
```bash
# Verifica que tu servidor WebSocket esté corriendo
netstat -tlnp | grep 8080

# O con ss
ss -tlnp | grep 8080
```

### Tunnel conecta pero WebSocket falla

**Causa:** WebSockets puede estar deshabilitado en Cloudflare

**Solución:**
1. Dashboard de Cloudflare → `sednarobot.org`
2. Network → WebSockets → Activar

---

## 🔐 Seguridad Adicional

### Agregar Autenticación

Modifica tu servidor WebSocket para validar un token:

```javascript
// En tu servidor del robot
wss.on('connection', (ws, req) => {
  const url = new URL(req.url, 'ws://base');
  const token = url.searchParams.get('token');

  if (token !== process.env.WS_SECRET_TOKEN) {
    ws.close(1008, 'No autorizado');
    return;
  }

  // Conexión válida...
});
```

Y en el HMI:

```typescript
// app/composables/useRobotControl.ts
const WS_URL = `${config.public.robotWsUrl}?token=${config.public.wsToken}`
```

---

## 📞 Soporte

Si tienes problemas:

1. Verifica logs de cloudflared:
   ```bash
   sudo journalctl -u cloudflared -f
   ```

2. Prueba la conexión local primero:
   ```bash
   wscat -c ws://localhost:8080
   ```

3. Verifica que Cloudflare puede alcanzar tu tunnel en el dashboard:
   - Cloudflare Zero Trust → Access → Tunnels
