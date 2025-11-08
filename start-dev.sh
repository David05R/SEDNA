#!/bin/bash
###############################################################################
# Script de inicio rápido para desarrollo - Robot SEDNA
# Inicia backend y frontend simultáneamente
###############################################################################

echo "🤖 Iniciando Robot SEDNA - Modo Desarrollo"
echo "=========================================="
echo ""

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Función para limpiar procesos al salir
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Deteniendo servicios...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}✅ Servicios detenidos${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Verificar que estamos en el directorio correcto
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo -e "${YELLOW}❌ Error: Ejecuta este script desde la raíz del proyecto${NC}"
    exit 1
fi

###############################################################################
# 1. Iniciar Backend
###############################################################################
echo -e "${BLUE}📡 Iniciando Backend (FastAPI)...${NC}"

cd backend

# Verificar si existe entorno virtual
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  No se encontró entorno virtual. Creando...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Iniciar backend en background
python main.py > ../backend.log 2>&1 &
BACKEND_PID=$!

echo -e "${GREEN}✅ Backend iniciado (PID: $BACKEND_PID)${NC}"
echo -e "   📍 API: http://localhost:8080"
echo -e "   📡 WebSocket: ws://localhost:8080/ws/control"
echo -e "   📖 Docs: http://localhost:8080/docs"
echo ""

cd ..

###############################################################################
# 2. Iniciar Frontend
###############################################################################
echo -e "${BLUE}🎨 Iniciando Frontend (Nuxt)...${NC}"

cd frontend

# Verificar node_modules
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠️  No se encontró node_modules. Instalando...${NC}"
    npm install
fi

# Iniciar frontend en background
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!

echo -e "${GREEN}✅ Frontend iniciado (PID: $FRONTEND_PID)${NC}"
echo -e "   🌐 URL: http://localhost:3000"
echo -e "   🎮 HMI: http://localhost:3000/visor"
echo ""

cd ..

###############################################################################
# 3. Mostrar información
###############################################################################
echo "=========================================="
echo -e "${GREEN}🚀 Robot SEDNA está listo!${NC}"
echo "=========================================="
echo ""
echo "📋 Servicios:"
echo "   Backend:  http://localhost:8080"
echo "   Frontend: http://localhost:3000"
echo ""
echo "📝 Logs:"
echo "   Backend:  tail -f backend.log"
echo "   Frontend: tail -f frontend.log"
echo ""
echo "🎮 Para usar:"
echo "   1. Abre http://localhost:3000/visor"
echo "   2. Conecta tu gamepad Bluetooth"
echo "   3. Cambia al modo 'long'"
echo "   4. Haz clic en 'Conectar al Robot'"
echo ""
echo -e "${YELLOW}Presiona Ctrl+C para detener todos los servicios${NC}"
echo ""

# Esperar indefinidamente
wait
