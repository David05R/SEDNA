# Backend Robot SEDNA

Sistema de control dual para Robot SEDNA con cambio de modo desde el frontend.

## 🎯 Arquitectura

```
┌─────────────────┐
│    Frontend     │
│  (Nuxt + Vue)   │
└────────┬────────┘
         │ HTTP POST /mode/{short|long}
         ▼
┌─────────────────────────────────┐
│    main_minimal.py              │
│    (FastAPI Backend)            │
└────────┬────────────────────────┘
         │
    ┌────┴────┐
    │         │
┌───▼──┐  ┌──▼──────────┐
│SHORT │  │    LONG     │
│      │  │             │
│test_ │  │motor_       │
│gpio. │  │controller.  │
│py    │  │py           │
│      │  │             │
│RF    │  │WebSocket    │
│Control│  │+ Bluetooth │
└──────┘  └─────────────┘
```

## 📁 Archivos

### Principal
- **`main_minimal.py`** - Backend principal (FastAPI)

### Módulos
- **`motor_controller.py`** - Control de motores BTS7960
- **`ibus_controller.py`** - Lectura de receptor iBus

### Scripts
- **`install-orangepi.sh`** - Instalación automatizada
- **`orangepi-setup.sh`** - Configuración del sistema

## 🚀 Instalación

```bash
# En Orange Pi
cd /home/orangepi/robot-hmi/backend
pip3 install -r requirements.txt
uvicorn main_minimal:app --host 0.0.0.0 --port 5050 --reload
```

## 🎮 Modos

### SHORT - Control RF
- Ejecuta test_gpio.py
- Sin latencia

### LONG - WebSocket
- Control Bluetooth
- Telemetría en tiempo real

## 📡 Endpoints

- GET `/health` - Estado
- POST `/mode/{short|long|idle}` - Cambiar modo
- WS `/ws/control` - WebSocket

Ver `INSTRUCCIONES_SIMPLE.md` para detalles completos.
