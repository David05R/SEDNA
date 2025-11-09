#!/usr/bin/env python3
"""
Módulo de control de motores BTS7960 para Robot SEDNA
Soporta control diferencial con softPWM
"""

import wiringpi
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# ===============================
# Configuración de pines WiringPi
# ===============================
# Motor Izquierdo
R_LPWM = 21
R_RPWM = 22

# Motor Derecho
L_LPWM = 2
L_RPWM = 6

# Pin único de Enable (controla ambos drivers)
EN_MOTORES = 23

# ===============================
# Constantes
# ===============================
PWM_MAX = 1000
DEADZONE = 100


class MotorController:
    """Controlador de motores BTS7960 con PWM diferencial"""

    def __init__(self):
        self.initialized = False
        self.enabled = False

    def setup(self):
        """Inicializa los pines GPIO y PWM"""
        try:
            wiringpi.wiringPiSetup()

            # Pin único de enable
            wiringpi.pinMode(EN_MOTORES, 1)
            wiringpi.digitalWrite(EN_MOTORES, 0)  # Inicialmente apagado

            # Inicializar PWM por software (0–100)
            for pin in [L_LPWM, L_RPWM, R_LPWM, R_RPWM]:
                wiringpi.softPwmCreate(pin, 0, 100)

            self.initialized = True
            logger.info("🔧 Motor controller inicializado")

        except Exception as e:
            logger.error(f"❌ Error inicializando motores: {e}")
            self.initialized = False

    def enable(self):
        """Habilita los motores"""
        if self.initialized:
            wiringpi.digitalWrite(EN_MOTORES, 1)
            self.enabled = True
            logger.info("✅ Motores habilitados")

    def disable(self):
        """Deshabilita los motores"""
        if self.initialized:
            self.stop()
            wiringpi.digitalWrite(EN_MOTORES, 0)
            self.enabled = False
            logger.info("🔴 Motores deshabilitados")

    def move_differential(self, L_pwm: int, R_pwm: int, direction: str):
        """
        Control diferencial de los motores

        Args:
            L_pwm: PWM motor izquierdo (0-1000)
            R_pwm: PWM motor derecho (0-1000)
            direction: "forward", "backward" o "stop"
        """
        if not self.initialized or not self.enabled:
            return

        # Convertir PWM de 0-1000 a 0-100 (duty cycle)
        L_duty = int((L_pwm / 1000) * 100)
        R_duty = int((R_pwm / 1000) * 100)

        # Limitar duty cycle
        L_duty = max(0, min(100, L_duty))
        R_duty = max(0, min(100, R_duty))

        if direction == "forward":
            wiringpi.softPwmWrite(L_LPWM, L_duty)
            wiringpi.softPwmWrite(L_RPWM, 0)
            wiringpi.softPwmWrite(R_LPWM, R_duty)
            wiringpi.softPwmWrite(R_RPWM, 0)
        elif direction == "backward":
            wiringpi.softPwmWrite(L_LPWM, 0)
            wiringpi.softPwmWrite(L_RPWM, L_duty)
            wiringpi.softPwmWrite(R_LPWM, 0)
            wiringpi.softPwmWrite(R_RPWM, R_duty)
        else:
            self.stop()

    def stop(self):
        """Detiene todos los motores"""
        if not self.initialized:
            return

        for pin in [L_LPWM, L_RPWM, R_LPWM, R_RPWM]:
            wiringpi.softPwmWrite(pin, 0)

    def process_websocket_command(self, axis1: int, axis2: int) -> Tuple[int, int, str]:
        """
        Convierte comandos WebSocket (-1000 a 1000) a PWM diferencial

        Args:
            axis1: Adelante/Atrás (-1000 a 1000)
            axis2: Izquierda/Derecha (-1000 a 1000)

        Returns:
            Tuple[left_pwm, right_pwm, direction]
        """
        # Movimiento principal (adelante / atrás)
        if abs(axis1) <= DEADZONE:
            base_pwm = 0
            direction = "stop"
        elif axis1 < -DEADZONE:  # Adelante (negativo)
            base_pwm = int((abs(axis1) - DEADZONE) / (1000 - DEADZONE) * PWM_MAX)
            direction = "forward"
        else:  # Atrás (positivo)
            base_pwm = int((axis1 - DEADZONE) / (1000 - DEADZONE) * PWM_MAX)
            direction = "backward"

        # Dirección diferencial (izq-der)
        if abs(axis2) <= DEADZONE:
            left_pwm = base_pwm
            right_pwm = base_pwm
        else:
            # Normalizar -1 a 1
            diff = axis2 / 1000.0
            diff = max(-1, min(1, diff))

            # Aplicar diferencial
            if diff < 0:  # Izquierda
                left_pwm = int(base_pwm * (1.0 + diff))
                right_pwm = base_pwm
            else:  # Derecha
                left_pwm = base_pwm
                right_pwm = int(base_pwm * (1.0 - diff))

            # Limitar valores
            left_pwm = max(0, min(PWM_MAX, left_pwm))
            right_pwm = max(0, min(PWM_MAX, right_pwm))

        return left_pwm, right_pwm, direction

    def process_ibus_command(self, ch2: int, ch1: int) -> Tuple[int, int, str]:
        """
        Convierte comandos iBus (1000-2000) a PWM diferencial

        Args:
            ch2: Canal 2 - Velocidad (1000-2000)
            ch1: Canal 1 - Dirección (1000-2000)

        Returns:
            Tuple[left_pwm, right_pwm, direction]
        """
        CENTER = 1500

        # Movimiento principal (adelante / atrás)
        if abs(ch2 - CENTER) <= DEADZONE:
            base_pwm = 0
            direction = "stop"
        elif ch2 > CENTER + DEADZONE:
            base_pwm = int(((ch2 - (CENTER + DEADZONE)) / (2000 - (CENTER + DEADZONE))) * PWM_MAX)
            direction = "forward"
        else:
            base_pwm = int((((CENTER - DEADZONE) - ch2) / ((CENTER - DEADZONE) - 1000)) * PWM_MAX)
            direction = "backward"

        # Dirección diferencial (izq-der)
        if abs(ch1 - CENTER) <= DEADZONE:
            left_pwm = base_pwm
            right_pwm = base_pwm
        else:
            diff = (ch1 - CENTER) / 500.0  # Normaliza aprox. -1 a 1
            diff = max(-1, min(1, diff))
            left_pwm = int(base_pwm * (1.0 - diff))
            right_pwm = int(base_pwm * (1.0 + diff))
            left_pwm = max(0, min(PWM_MAX, left_pwm))
            right_pwm = max(0, min(PWM_MAX, right_pwm))

        return left_pwm, right_pwm, direction

    def cleanup(self):
        """Limpia y detiene los motores"""
        logger.info("🧹 Limpiando motor controller")

        # Paso 1: Detener todo movimiento inmediatamente
        self.stop()

        # Paso 2: Liberar explícitamente los pines PWM
        try:
            for pin in [L_LPWM, L_RPWM, R_LPWM, R_RPWM]:
                wiringpi.softPwmWrite(pin, 0)
                wiringpi.softPwmStop(pin)  # Detener PWM por software
            logger.info("✅ PWM detenido")
        except Exception as e:
            logger.debug(f"softPwmStop: {e}")

        # Paso 3: Deshabilitar motores
        self.disable()

        # Paso 4: Resetear pines a INPUT para liberar completamente
        try:
            for pin in [L_LPWM, L_RPWM, R_LPWM, R_RPWM]:
                wiringpi.pinMode(pin, 0)  # INPUT mode
                wiringpi.pullUpDnControl(pin, 0)  # Desactivar pull-up/down

            # Enable también a INPUT
            wiringpi.pinMode(EN_MOTORES, 0)
            logger.info("✅ Pines GPIO liberados completamente")
        except Exception as e:
            logger.error(f"❌ Error liberando pines: {e}")

        # Paso 5: Resetear flags internos
        self.initialized = False
        self.enabled = False
        logger.info("✅ Motor controller completamente limpio")
