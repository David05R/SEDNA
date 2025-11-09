#!/bin/bash
# Script para diagnosticar y arreglar conexión ESP32

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  Diagnóstico y Fix - Conexión ESP32                          ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 1. Detectar puerto
echo -e "${YELLOW}1. Detectando puerto USB...${NC}"
PORT=$(ls /dev/ttyUSB* 2>/dev/null | head -n 1)
if [ -z "$PORT" ]; then
    echo -e "${RED}❌ No se encontró puerto /dev/ttyUSB*${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Puerto detectado: $PORT${NC}"
echo ""

# 2. Verificar procesos usando el puerto
echo -e "${YELLOW}2. Verificando procesos en el puerto...${NC}"
USING=$(lsof $PORT 2>/dev/null)
if [ -n "$USING" ]; then
    echo -e "${RED}⚠️ El puerto está siendo usado:${NC}"
    echo "$USING"
    echo ""
    echo -e "${YELLOW}Cerrando procesos...${NC}"
    sudo pkill -9 screen
    sleep 1
    echo -e "${GREEN}✅ Procesos cerrados${NC}"
else
    echo -e "${GREEN}✅ Puerto libre${NC}"
fi
echo ""

# 3. Verificar permisos
echo -e "${YELLOW}3. Verificando permisos...${NC}"
CURRENT_USER=$(whoami)
if groups | grep -q dialout; then
    echo -e "${GREEN}✅ Usuario $CURRENT_USER está en grupo dialout${NC}"
else
    echo -e "${RED}❌ Usuario NO está en grupo dialout${NC}"
    echo "Ejecutando: sudo usermod -a -G dialout $CURRENT_USER"
    sudo usermod -a -G dialout $CURRENT_USER
    echo -e "${YELLOW}⚠️ Debes cerrar sesión y volver a entrar para que tome efecto${NC}"
fi
echo ""

# 4. Dar permisos temporales
echo -e "${YELLOW}4. Dando permisos temporales...${NC}"
sudo chmod 666 $PORT
echo -e "${GREEN}✅ Permisos ajustados${NC}"
echo ""

# 5. Verificar lectura
echo -e "${YELLOW}5. Probando lectura del puerto (3 segundos)...${NC}"
timeout 3s cat $PORT 2>/dev/null | head -n 2
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Se pueden leer datos correctamente${NC}"
else
    echo -e "${RED}❌ No se pueden leer datos${NC}"
    echo "Verifica que la ESP32 esté flasheada correctamente"
fi
echo ""

# 6. Actualizar esp32_reader.py
echo -e "${YELLOW}6. Actualizando esp32_reader.py con puerto correcto...${NC}"
BACKEND_DIR="/home/orangepi/robot-hmi/backend"
ESP32_FILE="$BACKEND_DIR/esp32_reader.py"

if [ -f "$ESP32_FILE" ]; then
    # Hacer backup
    cp "$ESP32_FILE" "$ESP32_FILE.backup"

    # Actualizar puerto
    sed -i "s|ESP32_PORT = \"/dev/tty[^\"]*\"|ESP32_PORT = \"$PORT\"|g" "$ESP32_FILE"

    echo -e "${GREEN}✅ esp32_reader.py actualizado${NC}"
    echo "   Puerto configurado: $PORT"

    # Mostrar la línea actualizada
    grep "ESP32_PORT" "$ESP32_FILE" | head -n 1
else
    echo -e "${RED}❌ No se encontró $ESP32_FILE${NC}"
    echo "   Debes copiar el archivo primero"
fi
echo ""

# 7. Probar módulo Python
echo -e "${YELLOW}7. Probando módulo esp32_reader.py (5 segundos)...${NC}"
cd $BACKEND_DIR
timeout 5s python3 esp32_reader.py 2>&1 | tail -n 10
echo ""

# 8. Reiniciar backend
echo -e "${YELLOW}8. Reiniciando backend...${NC}"
sudo systemctl restart sedna-backend
sleep 2

if systemctl is-active --quiet sedna-backend; then
    echo -e "${GREEN}✅ Backend reiniciado correctamente${NC}"
else
    echo -e "${RED}❌ Backend no está corriendo${NC}"
    echo "Ver logs: journalctl -u sedna-backend -n 50"
    exit 1
fi
echo ""

# 9. Verificar logs
echo -e "${YELLOW}9. Verificando logs del backend (últimos 10)...${NC}"
journalctl -u sedna-backend -n 10 --no-pager | grep -A 2 -B 2 ESP32
echo ""

# 10. Probar endpoint
echo -e "${YELLOW}10. Probando endpoint /health...${NC}"
sleep 1
RESPONSE=$(curl -s http://localhost:5050/health)
VOLTAGE=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['robot_state']['battery_voltage'])" 2>/dev/null)

if [ "$VOLTAGE" != "0.0" ] && [ -n "$VOLTAGE" ]; then
    echo -e "${GREEN}✅ ESP32 está enviando datos correctamente${NC}"
    echo "   Voltaje: ${VOLTAGE}V"
else
    echo -e "${RED}❌ ESP32 no está enviando datos${NC}"
    echo "   Respuesta: $RESPONSE"
fi
echo ""

# Resumen
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  RESUMEN                                                      ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "Puerto configurado: $PORT"
echo "Backend: sedna-backend"
echo ""
echo "Si aún no funciona:"
echo "  1. Verifica logs: journalctl -u sedna-backend -f"
echo "  2. Verifica lectura: cat $PORT"
echo "  3. Reinicia Orange Pi: sudo reboot"
echo ""
