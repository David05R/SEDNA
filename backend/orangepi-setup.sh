#!/bin/bash
###############################################################################
# Script de instalación para OrangePi - Robot SEDNA
# Este script configura todo lo necesario para el servidor WebSocket
###############################################################################

set -e  # Salir si hay algún error

echo "🤖 Instalación del servidor WebSocket para Robot SEDNA"
echo "======================================================="
echo ""

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir con color
print_step() {
    echo -e "${BLUE}[PASO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

###############################################################################
# 1. Actualizar sistema
###############################################################################
print_step "Actualizando sistema..."
sudo apt update
sudo apt upgrade -y
print_success "Sistema actualizado"

###############################################################################
# 2. Instalar Python3 y pip
###############################################################################
print_step "Instalando Python3 y dependencias..."
sudo apt install -y python3 python3-pip python3-venv
print_success "Python3 instalado: $(python3 --version)"

###############################################################################
# 3. Instalar dependencias de Python para WebSocket
###############################################################################
print_step "Instalando bibliotecas de Python..."
pip3 install websockets asyncio --user
print_success "Bibliotecas de Python instaladas"

###############################################################################
# 4. Instalar Cloudflare Tunnel (cloudflared)
###############################################################################
print_step "Instalando Cloudflare Tunnel..."

# Detectar arquitectura
ARCH=$(uname -m)
if [ "$ARCH" = "aarch64" ]; then
    CLOUDFLARED_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
elif [ "$ARCH" = "armv7l" ]; then
    CLOUDFLARED_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm"
else
    print_warning "Arquitectura no soportada: $ARCH"
    CLOUDFLARED_URL=""
fi

if [ -n "$CLOUDFLARED_URL" ]; then
    wget -O cloudflared $CLOUDFLARED_URL
    chmod +x cloudflared
    sudo mv cloudflared /usr/local/bin/
    print_success "Cloudflared instalado: $(cloudflared --version)"
else
    print_warning "Cloudflared no se pudo instalar automáticamente"
fi

###############################################################################
# 5. Crear directorio para el proyecto
###############################################################################
print_step "Creando directorio del proyecto..."
ROBOT_DIR="$HOME/robot-sedna"
mkdir -p "$ROBOT_DIR"
cd "$ROBOT_DIR"
print_success "Directorio creado: $ROBOT_DIR"

###############################################################################
# 6. Descargar servidor WebSocket de ejemplo
###############################################################################
print_step "Creando servidor WebSocket de ejemplo..."

cat > "$ROBOT_DIR/robot-server.py" << 'EOF'
#!/usr/bin/env python3
"""
Servidor WebSocket para Robot SEDNA
"""
import asyncio
import json
import websockets
from datetime import datetime

PORT = 8080
connected_clients = set()

def process_control_command(axis1, axis2):
    DEAD_ZONE = 100

    if abs(axis1) < DEAD_ZONE and abs(axis2) < DEAD_ZONE:
        return "🛑 DETENIDO"
    elif abs(axis1) > abs(axis2):
        if axis1 < -DEAD_ZONE:
            return f"⬆️  ADELANTE ({abs(axis1)/10:.1f}%)"
        else:
            return f"⬇️  ATRÁS ({abs(axis1)/10:.1f}%)"
    else:
        if axis2 < -DEAD_ZONE:
            return f"⬅️  IZQUIERDA ({abs(axis2)/10:.1f}%)"
        else:
            return f"➡️  DERECHA ({abs(axis2)/10:.1f}%)"

async def handle_client(websocket, path):
    client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
    print(f"✅ Cliente conectado: {client_id}")
    connected_clients.add(websocket)

    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                axis1 = data.get("axis1", 0)
                axis2 = data.get("axis2", 0)
                movement = process_control_command(axis1, axis2)

                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"📥 [{timestamp}] axis1={axis1:5d}, axis2={axis2:5d} → {movement}")

            except json.JSONDecodeError:
                print(f"⚠️  Mensaje inválido: {message}")
    except websockets.exceptions.ConnectionClosed:
        print(f"🔴 Cliente desconectado: {client_id}")
    finally:
        connected_clients.remove(websocket)
        print("🛑 Deteniendo robot")

async def main():
    print(f"\n🤖 Servidor WebSocket del Robot SEDNA")
    print(f"📡 Escuchando en: ws://0.0.0.0:{PORT}\n")

    async with websockets.serve(handle_client, "0.0.0.0", PORT):
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Servidor detenido")
EOF

chmod +x "$ROBOT_DIR/robot-server.py"
print_success "Servidor creado: $ROBOT_DIR/robot-server.py"

###############################################################################
# 7. Crear servicio systemd
###############################################################################
print_step "Creando servicio systemd..."

sudo tee /etc/systemd/system/robot-ws.service > /dev/null << EOF
[Unit]
Description=Robot SEDNA WebSocket Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$ROBOT_DIR
ExecStart=/usr/bin/python3 $ROBOT_DIR/robot-server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
print_success "Servicio systemd creado: robot-ws.service"

###############################################################################
# 8. Mostrar resumen
###############################################################################
echo ""
echo "======================================================="
echo -e "${GREEN}✅ Instalación completada${NC}"
echo "======================================================="
echo ""
echo "📝 Próximos pasos:"
echo ""
echo "1️⃣  Configurar Cloudflare Tunnel:"
echo "   cloudflared tunnel login"
echo "   cloudflared tunnel create robot-control"
echo ""
echo "2️⃣  Iniciar el servidor WebSocket:"
echo "   sudo systemctl start robot-ws"
echo "   sudo systemctl enable robot-ws"
echo ""
echo "3️⃣  Ver logs del servidor:"
echo "   sudo journalctl -u robot-ws -f"
echo ""
echo "4️⃣  Probar localmente:"
echo "   python3 $ROBOT_DIR/robot-server.py"
echo ""
echo "📂 Archivos instalados en: $ROBOT_DIR"
echo ""
print_warning "No olvides configurar el tunnel con las instrucciones en CLOUDFLARE-WEBSOCKET-SETUP.md"
echo ""
