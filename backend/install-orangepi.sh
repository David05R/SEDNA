#!/bin/bash
###############################################################################
# Script de instalación del Backend en OrangePi - Robot SEDNA
# Para usar con Cloudflare Tunnel ya configurado
###############################################################################

set -e

echo "🤖 Instalación del Backend FastAPI - Robot SEDNA"
echo "================================================="
echo ""

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

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
# 1. Verificar Python
###############################################################################
print_step "Verificando Python..."

if ! command -v python3 &> /dev/null; then
    print_warning "Python3 no encontrado. Instalando..."
    sudo apt update
    sudo apt install -y python3 python3-pip python3-venv
fi

PYTHON_VERSION=$(python3 --version)
print_success "Python instalado: $PYTHON_VERSION"

###############################################################################
# 2. Crear directorio del proyecto
###############################################################################
INSTALL_DIR="$HOME/robot-sedna"

if [ -d "$INSTALL_DIR" ]; then
    print_warning "El directorio $INSTALL_DIR ya existe"
    read -p "¿Deseas sobrescribir? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Instalación cancelada"
        exit 1
    fi
    rm -rf "$INSTALL_DIR"
fi

print_step "Creando directorio $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"
print_success "Directorio creado"

###############################################################################
# 3. Copiar archivos
###############################################################################
print_step "Copiando archivos del backend..."

# Verificar que estamos en el directorio correcto
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cp "$SCRIPT_DIR/main.py" .
cp "$SCRIPT_DIR/requirements.txt" .

if [ -f "$SCRIPT_DIR/.env.example" ]; then
    cp "$SCRIPT_DIR/.env.example" .env
fi

print_success "Archivos copiados"

###############################################################################
# 4. Crear entorno virtual
###############################################################################
print_step "Creando entorno virtual..."

python3 -m venv venv
source venv/bin/activate

print_success "Entorno virtual creado"

###############################################################################
# 5. Instalar dependencias
###############################################################################
print_step "Instalando dependencias de Python..."

pip install --upgrade pip
pip install -r requirements.txt

print_success "Dependencias instaladas"

###############################################################################
# 6. Crear servicio systemd
###############################################################################
print_step "Creando servicio systemd..."

sudo tee /etc/systemd/system/robot-api.service > /dev/null << EOF
[Unit]
Description=Robot SEDNA FastAPI Backend
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin"
ExecStart=$INSTALL_DIR/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
print_success "Servicio systemd creado"

###############################################################################
# 7. Probar el servidor
###############################################################################
print_step "Probando el servidor..."

# Iniciar en background para probar
$INSTALL_DIR/venv/bin/python main.py &
SERVER_PID=$!

# Esperar un poco
sleep 3

# Probar endpoint
if curl -s http://localhost:8080/health > /dev/null; then
    print_success "Servidor funcionando correctamente"
else
    print_warning "No se pudo conectar al servidor"
fi

# Detener servidor de prueba
kill $SERVER_PID 2>/dev/null || true

###############################################################################
# 8. Mostrar resumen
###############################################################################
echo ""
echo "======================================================="
echo -e "${GREEN}✅ Instalación completada${NC}"
echo "======================================================="
echo ""
echo "📂 Instalado en: $INSTALL_DIR"
echo ""
echo "🚀 Para iniciar el servidor:"
echo "   sudo systemctl start robot-api"
echo ""
echo "🔄 Para habilitar inicio automático:"
echo "   sudo systemctl enable robot-api"
echo ""
echo "📊 Ver logs:"
echo "   sudo journalctl -u robot-api -f"
echo ""
echo "⚙️  Ver estado:"
echo "   sudo systemctl status robot-api"
echo ""
echo "🌐 El servidor escuchará en:"
echo "   - Local: http://localhost:8080"
echo "   - Cloudflare: wss://ws.sednarobot.org"
echo ""
echo "📖 Documentación API:"
echo "   http://localhost:8080/docs"
echo ""
echo "🔌 WebSocket endpoint:"
echo "   ws://localhost:8080/ws/control (local)"
echo "   wss://ws.sednarobot.org/ws/control (Cloudflare)"
echo ""
print_warning "Asegúrate de que Cloudflare Tunnel esté corriendo:"
echo "   sudo systemctl status cloudflared"
echo ""
