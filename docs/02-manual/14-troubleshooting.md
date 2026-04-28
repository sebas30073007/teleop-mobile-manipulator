---
title: "Troubleshooting"
nav_order: 14
parent: "Manual de réplica académica"
---

# Troubleshooting

## Fallas comunes

| Caso | Síntoma | Causas probables | Qué revisar | Información faltante para diagnóstico preciso |
|---|---|---|---|---|
| No hay comunicación ZMQ | No llegan datos a XR | Red no válida, servicio no iniciado, puertos no disponibles | Estado del backend, red local, puertos documentados | Comandos de verificación de red/puertos |
| XR no recibe datos | Paneles vacíos o sin actualización | Suscripción inactiva, endpoint incorrecto | Configuración de endpoint, estado de topics | Tabla oficial de endpoints por entorno |
| Robot no se mueve | Comando recibido sin acción física | Puente de control incompleto, firmware no ejecutando | Estado de ESP32-C3, alimentación, enlace de control | Logs de control embebido |
| Un motor no responde | Movimiento parcial | Módulo embebido o conexión física | Cableado, módulo, señales de salida | Diagrama eléctrico completo |
| ESP32-C3 no ejecuta firmware | Sin respuesta del módulo | Firmware ausente o despliegue incorrecto | Método de carga y arranque | Procedimiento de flasheo documentado |
| Computadora no detecta dispositivo | Sensor/control no visible | Conexión física o driver | Puerto físico, enlace USB, estado del módulo | Checklist de reconocimiento por dispositivo |
| Movimiento físico no coincide con virtual | Acción inconsistente XR/robot | Mapeo parcial o falta de calibración | Configuración de control y referencias espaciales | Proceso formal de calibración |
| Respuesta irregular o retraso | Control inestable | Carga de sistema, red o sincronización | Estado de red y consumo de recursos | Métricas formales de rendimiento |

> Pendiente por documentar
>
> Actualmente esta información no está disponible en el repositorio.
>
> Para completar esta sección se necesita:
> - Procedimientos de diagnóstico con comandos concretos por subsistema.
> - Umbrales de referencia para detectar falla real vs variación normal.
> - Registro histórico de fallas y resolución.
>
> Esta información es necesaria porque permite:
> - Resolver incidencias de forma sistemática y replicable en prácticas académicas.
