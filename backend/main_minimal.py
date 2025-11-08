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

# Importar módulo de control de motores (solo para WebSocket)
from motor_controller import MotorController

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
            "battery": 58,
            "gps": {"lat": None, "lng": None},
            "speed": 0,
            "operational": False,
            "remote_control": False,
            "mode": "idle",
        }

        # Modo actual
        self.current_mode = "idle"

        # Proceso de test_gpio.py
        self.gpio_process = None

        # Controlador de motores (solo para modo LONG, inicializado bajo demanda)
        self.motor_controller = None
        self.motor_controller_initialized = False

    async def set_mode_async(self, mode: str):
        """Cambia el modo de operación (versión async)"""
        if mode == self.current_mode:
            logger.info(f"⚠️ Ya estamos en modo {mode}")
            return

        logger.info(f"🔄 Cambiando modo: {self.current_mode} → {mode}")

        # Detener todo primero
        self.stop_gpio_process()
        self.cleanup_motor_controller()

        # IMPORTANTE: Esperar a que GPIO se libere completamente
        if self.current_mode == "long" and mode == "short":
            logger.info("⏳ Esperando 1s para liberar GPIO completamente...")
            await asyncio.sleep(1.0)  # Aumentado a 1 segundo

            # Reset adicional: matar cualquier proceso python residual
            try:
                logger.info("🔧 Limpiando procesos Python residuales...")
                # Solo matar procesos test_gpio.py específicamente
                subprocess.run(['sudo', 'pkill', '-9', '-f', 'test_gpio.py'],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
            except Exception as e:
                logger.debug(f"pkill: {e}")

        # Actualizar modo
        self.current_mode = mode
        self.robot_state["mode"] = mode
        self.robot_state["speed"] = 0

        # Iniciar según el modo
        if mode == "short":
            logger.info("📡 Modo SHORT: Iniciando test_gpio.py (control RF)")
            self.start_gpio_process()
        elif mode == "long":
            logger.info("🌐 Modo LONG: Iniciando motor_controller (WebSocket)")
            self.init_motor_controller()
        else:
            logger.info("⏸️ Modo IDLE: Todo detenido")

        logger.info(f"✅ Modo {mode} activado")

    def set_mode(self, mode: str):
        """Wrapper síncrono para set_mode"""
        # Crear una tarea async
        asyncio.create_task(self.set_mode_async(mode))

    def start_gpio_process(self):
        """Inicia test_gpio.py como proceso separado"""
        if self.gpio_process is not None:
            logger.warning("⚠️ test_gpio.py ya está corriendo")
            return

        try:
            # Ejecutar test_gpio.py con sudo
            logger.info("🚀 Iniciando test_gpio.py...")
            self.gpio_process = subprocess.Popen(
                ['sudo', 'python3', '/home/orangepi/robot-hmi/backend/test_gpio.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=lambda: signal.signal(signal.SIGINT, signal.SIG_IGN)
            )
            logger.info(f"✅ test_gpio.py iniciado (PID: {self.gpio_process.pid})")

        except Exception as e:
            logger.error(f"❌ Error iniciando test_gpio.py: {e}")
            self.gpio_process = None

    def stop_gpio_process(self):
        """Detiene el proceso test_gpio.py"""
        if self.gpio_process is None:
            return

        try:
            logger.info(f"🛑 Deteniendo test_gpio.py (PID: {self.gpio_process.pid})...")

            # Enviar SIGTERM
            self.gpio_process.terminate()

            # Esperar hasta 2 segundos
            try:
                self.gpio_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                # Si no se detuvo, forzar con SIGKILL
                logger.warning("⚠️ Proceso no respondió a SIGTERM, enviando SIGKILL")
                self.gpio_process.kill()
                self.gpio_process.wait()

            logger.info("✅ test_gpio.py detenido")
            self.gpio_process = None

        except Exception as e:
            logger.error(f"❌ Error deteniendo test_gpio.py: {e}")
            self.gpio_process = None

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

    def cleanup(self):
        """Limpia recursos"""
        logger.info("🧹 Limpiando recursos")
        self.stop_gpio_process()
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
        "gpio_running": manager.gpio_process is not None,
        "gpio_pid": manager.gpio_process.pid if manager.gpio_process else None,
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
                        "gps": manager.robot_state["gps"],
                        "speed": manager.robot_state["speed"],
                        "mode": manager.robot_state["mode"],
                        "operational": manager.robot_state["operational"],
                        "remote_control": manager.robot_state["remote_control"],
                    },
                    "timestamp": datetime.now().isoformat(),
                }, websocket)
                await asyncio.sleep(2)  # Cada 2 segundos
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
    logger.info("📡 Modo SHORT: Ejecuta test_gpio.py")
    logger.info("📡 Modo LONG: WebSocket + motor_controller")

    if gps is not None:
        asyncio.create_task(gps_reader_task())


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
