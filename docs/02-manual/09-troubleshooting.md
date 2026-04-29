---
title: "Troubleshooting"
nav_order: 9
parent: "Documentación"
---

# Troubleshooting

## Fallas comunes

| Caso | Síntoma | Causas probables | Qué revisar |
|---|---|---|---|
| No hay comunicación ZMQ | No llegan datos a XR | Red no válida, servicio no iniciado, puertos no disponibles | Estado del backend, red local, puertos documentados |
| XR no recibe datos | Paneles vacíos o sin actualización | Suscripción inactiva, endpoint incorrecto | Configuración de endpoint, estado de topics |
| Robot no se mueve | Comando recibido sin acción física | Puente de control incompleto, firmware no ejecutando | Estado de ESP32-C3, alimentación, enlace de control |
| Un motor no responde | Movimiento parcial | Módulo embebido o conexión física | Cableado, módulo, señales de salida |
| ESP32-C3 no ejecuta firmware | Sin respuesta del módulo | Firmware ausente o despliegue incorrecto | Método de carga y arranque |
| Computadora no detecta dispositivo | Sensor/control no visible | Conexión física o driver | Puerto físico, enlace USB, estado del módulo |
| Movimiento físico no coincide con virtual | Acción inconsistente | Mapeo parcial o falta de calibración | Configuración de control y referencias espaciales |
| Respuesta irregular o retraso | Control inestable | Carga de sistema, red o sincronización | Estado de red y consumo de recursos |

> **Pendiente:** Agregar procedimientos de diagnóstico con comandos concretos por subsistema y registro histórico de fallas resueltas.
