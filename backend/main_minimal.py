#!/usr/bin/env python3
"""
Backend Minimalista para Robot SEDNA
- Modo SHORT: Ejecuta test_gpio.py
- Modo LONG: Usa WebSocket + motor_controller

Ejecución:
    uvicorn main_minimal:app --host 0.0.0.0 --port 5050 --reload
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import asyncio
import subprocess
import signal
from datetime import datetime
import logging
import serial

# Importar módulos de control
from motor_controller import MotorController
from ibus_controller import IBusController
from esp32_reader import ESP32Reader

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="Robot SEDNA API Minimal",
    description="SHORT: Ejecuta test_gpio.py | LONG: WebSocket",
    version="3.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================
# CONFIGURACIÓN GPS
# ==========================
GPS_PORT = '/dev/ttyS6'
GPS_BAUD = 9600

try:
    gps = serial.Serial(GPS_PORT, baudrate=GPS_BAUD, timeout=1)
    logger.info(f"📡 GPS inicializado en {GPS_PORT} @ {GPS_BAUD}bps")
except Exception as e:
    gps = None
    logger.warning(f"⚠️ No se pudo inicializar el GPS: {e}")


def parse_GPRMC(sentence: str) -> Optional[tuple]:
    """Parsea tramas $GPRMC"""
    parts = sentence.split(',')
    if len(parts) < 7 or parts[2] != 'A':
        return None

    lat_raw, lat_dir, lon_raw, lon_dir = parts[3], parts[4], parts[5], parts[6]

    def nmea_to_decimal(raw: str, direction: str) -> Optional[float]:
        if not raw or raw == '0':
            return None
        try:
            if direction in ['N', 'S']:
                deg = int(raw[:2])
                minutes = float(raw[2:])
            else:
                deg = int(raw[:3])
                minutes = float(raw[3:])
            dec = deg + minutes / 60.0
            if direction in ['S', 'W']:
                dec *= -1
            return round(dec, 6)
        except Exception:
            return None

    lat = nmea_to_decimal(lat_raw, lat_dir)
    lon = nmea_to_decimal(lon_raw, lon_dir)
    if lat is None or lon is None:
        return None
    return lat, lon


async def gps_reader_task():
    """Tarea de lectura GPS"""
    global gps
    if gps is None:
        manager.robot_state["operational"] = False
        return

    manager.robot_state["operational"] = True

    while True:
        try:
            raw = await asyncio.to_thread(gps.readline)
            if not raw:
                await asyncio.sleep(0.2)
                continue

            line = raw.decode('ascii', errors='ignore').strip()
            if line.startswith('$GPRMC'):
                parsed = parse_GPRMC(line)
                if parsed:
                    lat, lon = parsed
                    manager.robot_state['gps']['lat'] = lat
                    manager.robot_state['gps']['lng'] = lon

            await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"❌ Error GPS: {e}")
            await asyncio.sleep(1)


# ==========================
# MINIMAL MANAGER
# ==========================
class MinimalManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.robot_state = {
            "battery": 0,  # Actualizado desde ESP32
            "battery_voltage": 0.0,  # Voltaje real
            "rpm_motor1": 0.0,  # RPM encoder 1
            "rpm_motor2": 0.0,  # RPM encoder 2
            "gps": {"lat": None, "lng": None},
            "speed": 0,
            "operational": False,
            "remote_control": False,
            "mode": "idle",
        }

        # Modo actual
        self.current_mode = "idle"

        # Controlador de motores (compartido entre LONG y SHORT)
        self.motor_controller = None
        self.motor_controller_initialized = False

        # Controlador iBus para modo SHORT
        self.ibus_controller = None
        self.ibus_task = None  # Task asyncio para loop iBus

        # Lector de ESP32 (encoders + batería)
        self.esp32_reader = None
        self.esp32_task = None  # Task asyncio para lectura ESP32

    async def set_mode_async(self, mode: str):
        """Cambia el modo de operación (versión async)"""
        if mode == self.current_mode:
            logger.info(f"⚠️ Ya estamos en modo {mode}")
            return

        logger.info(f"🔄 Cambiando modo: {self.current_mode} → {mode}")

        # Detener loop iBus si está activo
        await self.stop_ibus_loop()

        # Gestión del motor_controller
        if mode == "idle":
            # IDLE: Limpiar todo
            logger.info("🧹 Limpiando para modo IDLE...")
            self.cleanup_motor_controller()
            if self.ibus_controller:
                self.ibus_controller.disconnect()
                self.ibus_controller = None
        else:
            # SHORT o LONG: Asegurar que motor_controller existe
            if not self.motor_controller_initialized:
                self.init_motor_controller()

        # Actualizar modo
        self.current_mode = mode
        self.robot_state["mode"] = mode
        self.robot_state["speed"] = 0

        # Iniciar según el modo
        if mode == "short":
            logger.info("📡 Modo SHORT: Iniciando loop iBus interno")
            await self.start_ibus_loop()
        elif mode == "long":
            logger.info("🌐 Modo LONG: Control WebSocket activo")
            # WebSocket ya está manejado, solo asegurar motores habilitados
            if self.motor_controller:
                self.motor_controller.enable()
        else:
            logger.info("⏸️ Modo IDLE: Todo detenido")

        logger.info(f"✅ Modo {mode} activado")

    def set_mode(self, mode: str):
        """Wrapper síncrono para set_mode"""
        # Crear una tarea async
        asyncio.create_task(self.set_mode_async(mode))

    async def start_ibus_loop(self):
        """Inicia el loop de control iBus (modo SHORT)"""
        if self.ibus_task is not None:
            logger.warning("⚠️ Loop iBus ya está activo")
            return

        # Crear controlador iBus si no existe
        if self.ibus_controller is None:
            self.ibus_controller = IBusController()

        # Conectar
        if not self.ibus_controller.connect():
            logger.error("❌ No se pudo conectar al receptor iBus")
            return

        # Crear task para el loop
        self.ibus_task = asyncio.create_task(self.ibus_control_loop())
        logger.info("✅ Loop iBus iniciado")

    async def stop_ibus_loop(self):
        """Detiene el loop de control iBus"""
        if self.ibus_task is None:
            return

        logger.info("🛑 Deteniendo loop iBus...")

        # Cancelar task
        self.ibus_task.cancel()

        try:
            await self.ibus_task
        except asyncio.CancelledError:
            pass

        self.ibus_task = None
        logger.info("✅ Loop iBus detenido")

    async def ibus_control_loop(self):
        """Loop principal de control iBus"""
        logger.info("🎮 Loop iBus activo - esperando comandos del control RF")

        try:
            while True:
                # Leer canales
                channels = await asyncio.to_thread(self.ibus_controller.get_channels)

                if channels and len(channels) >= 2:
                    ch1 = channels[0]  # Dirección
                    ch2 = channels[1]  # Velocidad

                    # Convertir a PWM usando el método del motor_controller
                    L_pwm, R_pwm, direction = self.motor_controller.process_ibus_command(ch2, ch1)

                    # Mover motores
                    self.motor_controller.move_differential(L_pwm, R_pwm, direction)

                    # Actualizar velocidad en robot_state
                    self.robot_state["speed"] = max(L_pwm, R_pwm)

                # Pequeña pausa para no saturar CPU
                await asyncio.sleep(0.001)

        except asyncio.CancelledError:
            logger.info("ℹ️ Loop iBus cancelado")
            # Detener motores al cancelar
            if self.motor_controller:
                self.motor_controller.stop()
            raise
        except Exception as e:
            logger.error(f"❌ Error en loop iBus: {e}")
            # Detener motores en caso de error
            if self.motor_controller:
                self.motor_controller.stop()

    def init_motor_controller(self):
        """Inicializa el motor controller (solo para modo LONG)"""
        if self.motor_controller_initialized:
            return

        try:
            logger.info("🔧 Inicializando motor controller...")
            self.motor_controller = MotorController()
            self.motor_controller.setup()
            self.motor_controller.enable()
            self.motor_controller_initialized = True
            logger.info("✅ Motor controller listo")
        except Exception as e:
            logger.error(f"❌ Error inicializando motor controller: {e}")
            self.motor_controller = None
            self.motor_controller_initialized = False

    def cleanup_motor_controller(self):
        """Limpia el motor controller"""
        if not self.motor_controller_initialized or self.motor_controller is None:
            return

        try:
            logger.info("🧹 Limpiando motor controller...")
            self.motor_controller.stop()
            self.motor_controller.disable()
            self.motor_controller.cleanup()
            self.motor_controller = None
            self.motor_controller_initialized = False
            logger.info("✅ Motor controller limpiado")
        except Exception as e:
            logger.error(f"❌ Error limpiando motor controller: {e}")

    def process_websocket_command(self, axis1: int, axis2: int):
        """Procesa comandos WebSocket (solo en modo long)"""
        if self.current_mode != "long":
            return

        if not self.motor_controller_initialized or self.motor_controller is None:
            logger.warning("⚠️ Motor controller no inicializado")
            return

        # Convertir a PWM
        L_pwm, R_pwm, direction = self.motor_controller.process_websocket_command(axis1, axis2)

        # Ejecutar movimiento
        self.motor_controller.move_differential(L_pwm, R_pwm, direction)

        # Actualizar velocidad
        self.robot_state["speed"] = max(L_pwm, R_pwm)

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.robot_state["remote_control"] = len(self.active_connections) > 0
        logger.info(f"✅ Cliente WS conectado. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        try:
            self.active_connections.remove(websocket)
        except ValueError:
            pass
        self.robot_state["remote_control"] = len(self.active_connections) > 0
        logger.info(f"🔴 Cliente WS desconectado. Total: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def start_esp32_reader(self):
        """Inicia la lectura de la ESP32"""
        if self.esp32_task is not None:
            logger.warning("⚠️ ESP32 reader ya está activo")
            return

        # Crear lector si no existe
        if self.esp32_reader is None:
            self.esp32_reader = ESP32Reader()

        # Conectar
        if not self.esp32_reader.connect():
            logger.error("❌ No se pudo conectar a la ESP32")
            return

        # Crear task para lectura continua
        self.esp32_task = asyncio.create_task(self.esp32_read_loop())
        logger.info("✅ ESP32 reader iniciado")

    async def stop_esp32_reader(self):
        """Detiene la lectura de la ESP32"""
        if self.esp32_task is None:
            return

        logger.info("🛑 Deteniendo ESP32 reader...")

        # Cancelar task
        self.esp32_task.cancel()

        try:
            await self.esp32_task
        except asyncio.CancelledError:
            pass

        self.esp32_task = None
        logger.info("✅ ESP32 reader detenido")

    async def esp32_read_loop(self):
        """Loop de lectura de ESP32"""
        logger.info("📡 ESP32 read loop activo")

        try:
            while True:
                # Leer datos de ESP32
                updated = await asyncio.to_thread(self.esp32_reader.update)

                if updated:
                    # Obtener telemetría
                    data = self.esp32_reader.get_telemetry()

                    # Actualizar robot_state
                    self.robot_state["rpm_motor1"] = data["rpm_motor1"]
                    self.robot_state["rpm_motor2"] = data["rpm_motor2"]
                    self.robot_state["battery_voltage"] = data["battery_voltage"]
                    self.robot_state["battery"] = self.esp32_reader.get_battery_percentage()

                # Leer cada 100ms
                await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            logger.info("ℹ️ ESP32 read loop cancelado")
            raise
        except Exception as e:
            logger.error(f"❌ Error en ESP32 read loop: {e}")

    def cleanup(self):
        """Limpia recursos"""
        logger.info("🧹 Limpiando recursos")

        # Detener loop iBus si está activo
        if self.ibus_task:
            self.ibus_task.cancel()

        # Detener ESP32 reader
        if self.esp32_task:
            self.esp32_task.cancel()

        # Desconectar iBus
        if self.ibus_controller:
            self.ibus_controller.disconnect()

        # Desconectar ESP32
        if self.esp32_reader:
            self.esp32_reader.disconnect()

        # Limpiar motor controller
        self.cleanup_motor_controller()


manager = MinimalManager()


# ==========================
# ENDPOINTS HTTP
# ==========================
@app.get("/")
async def root():
    return {
        "name": "Robot SEDNA API Minimal",
        "version": "3.0.0",
        "status": "online",
        "mode": manager.current_mode,
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "robot_state": manager.robot_state,
    }


@app.get("/ping")
async def ping():
    return {
        "pong": True,
        "timestamp": datetime.now().isoformat(),
        "server_time_ms": int(datetime.now().timestamp() * 1000),
    }


@app.post("/mode/{mode}")
async def set_mode(mode: str):
    """Cambia el modo (idle, short, long)"""
    if mode not in ["idle", "short", "long"]:
        return {"error": "Modo inválido"}

    manager.set_mode(mode)

    return {
        "success": True,
        "mode": manager.current_mode,
    }


@app.get("/status")
async def get_status():
    return {
        "timestamp": datetime.now().isoformat(),
        "robot": manager.robot_state,
        "current_mode": manager.current_mode,
        "ibus_loop_active": manager.ibus_task is not None,
        "motor_controller_initialized": manager.motor_controller_initialized,
        "ibus_connected": manager.ibus_controller is not None and manager.ibus_controller.ser is not None,
    }


# ==========================
# WEBSOCKET
# ==========================
@app.websocket("/ws/control")
async def websocket_control(websocket: WebSocket):
    await manager.connect(websocket)

    await manager.send_personal_message({
        "type": "welcome",
        "message": "Conectado al Robot SEDNA",
        "timestamp": datetime.now().isoformat(),
        "robot_state": manager.robot_state,
    }, websocket)

    # Telemetría
    async def send_telemetry():
        try:
            while True:
                # Enviar telemetría completa por WebSocket
                await manager.send_personal_message({
                    "type": "telemetry",
                    "robot_state": {
                        "battery": manager.robot_state["battery"],
                        "battery_voltage": manager.robot_state["battery_voltage"],
                        "rpm_motor1": manager.robot_state["rpm_motor1"],
                        "rpm_motor2": manager.robot_state["rpm_motor2"],
                        "gps": manager.robot_state["gps"],
                        "speed": manager.robot_state["speed"],
                        "mode": manager.robot_state["mode"],
                        "operational": manager.robot_state["operational"],
                        "remote_control": manager.robot_state["remote_control"],
                    },
                    "timestamp": datetime.now().isoformat(),
                }, websocket)
                await asyncio.sleep(0.5)  # Cada 500ms para telemetría más rápida
        except Exception:
            pass

    telemetry_task = asyncio.create_task(send_telemetry())

    try:
        while True:
            data = await websocket.receive_json()
            axis1 = data.get("axis1", 0)
            axis2 = data.get("axis2", 0)

            manager.process_websocket_command(axis1, axis2)

            await manager.send_personal_message({
                "type": "ack",
                "status": "ok",
                "mode": manager.current_mode,
                "timestamp": datetime.now().isoformat(),
            }, websocket)

    except WebSocketDisconnect:
        logger.info("Cliente WS desconectado")
    except Exception as e:
        logger.error(f"❌ Error WS: {e}")
    finally:
        telemetry_task.cancel()
        manager.disconnect(websocket)


# ==========================
# EVENTOS
# ==========================
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Robot SEDNA API Minimal iniciada")
    logger.info("📡 Modo SHORT: Loop iBus interno")
    logger.info("📡 Modo LONG: WebSocket + motor_controller")

    # Iniciar GPS reader
    if gps is not None:
        asyncio.create_task(gps_reader_task())

    # Iniciar ESP32 reader (encoders + batería)
    await manager.start_esp32_reader()


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Cerrando API")
    manager.cleanup()
    if gps:
        try:
            gps.close()
        except:
            pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main_minimal:app", host="0.0.0.0", port=5050, reload=True)
