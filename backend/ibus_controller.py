#!/usr/bin/env python3
"""
Módulo de control iBus para Robot SEDNA
Lectura de receptor RF FlySky
"""

import serial
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

# ===============================
# Configuración iBus
# ===============================
IBUS_PORT = "/dev/ttyS0"
IBUS_BAUDRATE = 115200


class IBusController:
    """Controlador de receptor iBus (FlySky)"""

    def __init__(self, port: str = IBUS_PORT, baudrate: int = IBUS_BAUDRATE):
        self.port = port
        self.baudrate = baudrate
        self.ser: Optional[serial.Serial] = None
        self.buffer = bytearray()
        self.last_channels: Optional[List[int]] = None
        self.is_active = False

    def connect(self) -> bool:
        """Conecta al puerto serie del receptor iBus"""
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=0)
            self.ser.reset_input_buffer()
            logger.info(f"📡 iBus conectado en {self.port} @ {self.baudrate}bps")
            return True
        except Exception as e:
            logger.error(f"❌ Error conectando iBus: {e}")
            self.ser = None
            return False

    def disconnect(self):
        """Desconecta el puerto serie"""
        if self.ser:
            self.ser.close()
            self.ser = None
            logger.info("🔴 iBus desconectado")

    def read_frame(self) -> Optional[bytes]:
        """
        Lee una trama iBus válida del buffer

        Returns:
            bytes: Trama de 32 bytes si es válida, None si no hay datos o es inválida
        """
        if not self.ser or not self.ser.is_open:
            return None

        # Leer datos disponibles
        data = self.ser.read(self.ser.in_waiting or 1)
        self.buffer.extend(data)

        # Buscar inicio de trama
        while len(self.buffer) >= 32:
            # Verificar header (0x20 0x40)
            if self.buffer[0] != 0x20 or self.buffer[1] != 0x40:
                self.buffer.pop(0)
                continue

            # Extraer frame completo
            frame = self.buffer[:32]
            self.buffer = self.buffer[32:]

            # Verificar checksum
            received_checksum = frame[30] | (frame[31] << 8)
            checksum = 0xFFFF - sum(frame[:-2]) & 0xFFFF

            if received_checksum == checksum:
                self.is_active = True
                return bytes(frame)
            else:
                logger.debug("⚠️ Checksum iBus inválido")

        return None

    def parse_channels(self, frame: bytes) -> List[int]:
        """
        Decodifica los canales del frame iBus

        Args:
            frame: Trama de 32 bytes validada

        Returns:
            List[int]: Lista de 6 canales (valores 1000-2000)
        """
        return [
            frame[2] | (frame[3] << 8),
            frame[4] | (frame[5] << 8),
            frame[6] | (frame[7] << 8),
            frame[8] | (frame[9] << 8),
            frame[10] | (frame[11] << 8),
            frame[12] | (frame[13] << 8)
        ]

    def get_channels(self) -> Optional[List[int]]:
        """
        Lee los canales actuales del receptor

        Returns:
            List[int]: Lista de canales o None si no hay señal
        """
        frame = self.read_frame()
        if frame:
            self.last_channels = self.parse_channels(frame)
            return self.last_channels
        return None

    def has_signal(self) -> bool:
        """
        Verifica si hay señal activa del control RF

        Returns:
            bool: True si hay señal activa
        """
        return self.is_active

    def reset_activity(self):
        """Resetea el flag de actividad"""
        self.is_active = False
