#!/usr/bin/env python3
"""
Módulo de lectura de ESP32 para Robot SEDNA
Lee RPM de encoders y voltaje de batería via Serial
"""

import serial
import re
import logging
from typing import Optional, Dict
import time

logger = logging.getLogger(__name__)

# ===============================
# Configuración Serial ESP32
# ===============================
ESP32_PORT = "/dev/ttyUSB0"  # Ajustar según tu configuración
ESP32_BAUDRATE = 115200


class ESP32Reader:
    """Lector de telemetría desde ESP32 (encoders + voltaje)"""

    def __init__(self, port: str = ESP32_PORT, baudrate: int = ESP32_BAUDRATE):
        self.port = port
        self.baudrate = baudrate
        self.ser: Optional[serial.Serial] = None
        self.is_connected = False

        # Últimos valores leídos
        self.rpm_motor1 = 0.0
        self.rpm_motor2 = 0.0
        self.battery_voltage = 0.0

        # Patrón regex para parsear la línea de la ESP32
        # Formato esperado: "RPM Motor 1: 120.50 | RPM Motor 2: 118.30 | Bat V: 12.456 V"
        self.pattern = re.compile(
            r"RPM Motor 1:\s*([\d.]+)\s*\|\s*RPM Motor 2:\s*([\d.]+)\s*\|\s*Bat V:\s*([\d.]+)\s*V"
        )

    def connect(self) -> bool:
        """Conecta al puerto serial de la ESP32"""
        try:
            self.ser = serial.Serial(
                self.port,
                self.baudrate,
                timeout=1,
                write_timeout=1
            )
            # Esperar un poco para que se estabilice la conexión
            time.sleep(0.5)
            self.ser.reset_input_buffer()
            self.is_connected = True
            logger.info(f"📡 ESP32 conectada en {self.port} @ {self.baudrate}bps")
            return True
        except Exception as e:
            logger.error(f"❌ Error conectando ESP32: {e}")
            self.ser = None
            self.is_connected = False
            return False

    def disconnect(self):
        """Desconecta el puerto serial"""
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
                logger.info("🔴 ESP32 desconectada")
            except Exception as e:
                logger.error(f"❌ Error desconectando ESP32: {e}")

        self.ser = None
        self.is_connected = False

    def read_line(self) -> Optional[str]:
        """Lee una línea del serial"""
        if not self.ser or not self.ser.is_open:
            return None

        try:
            if self.ser.in_waiting > 0:
                line = self.ser.readline()
                return line.decode('utf-8', errors='ignore').strip()
        except Exception as e:
            logger.debug(f"Error leyendo línea: {e}")

        return None

    def parse_data(self, line: str) -> bool:
        """
        Parsea una línea de datos de la ESP32

        Args:
            line: Línea con formato "RPM Motor 1: X.X | RPM Motor 2: Y.Y | Bat V: Z.Z V"

        Returns:
            True si se parseó correctamente, False si no
        """
        if not line:
            return False

        match = self.pattern.search(line)
        if match:
            try:
                self.rpm_motor1 = float(match.group(1))
                self.rpm_motor2 = float(match.group(2))
                self.battery_voltage = float(match.group(3))
                return True
            except ValueError as e:
                logger.debug(f"Error parseando valores: {e}")
                return False

        return False

    def update(self) -> bool:
        """
        Lee y actualiza los valores de la ESP32

        Returns:
            True si se leyeron nuevos datos, False si no
        """
        line = self.read_line()
        if line:
            if self.parse_data(line):
                logger.debug(f"ESP32: RPM1={self.rpm_motor1:.2f} RPM2={self.rpm_motor2:.2f} BAT={self.battery_voltage:.2f}V")
                return True

        return False

    def get_telemetry(self) -> Dict[str, float]:
        """
        Obtiene los últimos valores de telemetría

        Returns:
            Diccionario con rpm_motor1, rpm_motor2, battery_voltage
        """
        return {
            "rpm_motor1": round(self.rpm_motor1, 2),
            "rpm_motor2": round(self.rpm_motor2, 2),
            "battery_voltage": round(self.battery_voltage, 3),
            "connected": self.is_connected
        }

    def get_battery_percentage(self, min_voltage: float = 11.0, max_voltage: float = 14.6) -> int:
        """
        Calcula el porcentaje de batería basado en voltaje

        Args:
            min_voltage: Voltaje mínimo (0%) - Default 11.0V
            max_voltage: Voltaje máximo (100%) - Default 14.6V

        Returns:
            Porcentaje de batería (0-100)
        """
        if self.battery_voltage <= min_voltage:
            return 0
        if self.battery_voltage >= max_voltage:
            return 100

        percentage = ((self.battery_voltage - min_voltage) / (max_voltage - min_voltage)) * 100
        return int(round(percentage))


# ===============================
# Función de test standalone
# ===============================
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    reader = ESP32Reader()

    if not reader.connect():
        print("No se pudo conectar a la ESP32")
        exit(1)

    print("Leyendo datos de ESP32 (Ctrl+C para salir)...")
    print("-" * 60)

    try:
        while True:
            if reader.update():
                data = reader.get_telemetry()
                battery_pct = reader.get_battery_percentage()

                print(f"RPM Motor 1: {data['rpm_motor1']:6.2f} | "
                      f"RPM Motor 2: {data['rpm_motor2']:6.2f} | "
                      f"Batería: {data['battery_voltage']:5.2f}V ({battery_pct}%)")

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\nDeteniendo...")
    finally:
        reader.disconnect()
        print("✅ Desconectado correctamente")
