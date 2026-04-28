---
title: "Pendientes por documentar"
nav_order: 4
parent: "Validación y pruebas"
---

# Pendientes por documentar para réplica académica

Esta sección concentra lo que aún falta para convertir el repositorio en un manual de réplica académica completo.

## Información ya confirmada

- Arquitectura de comunicación: **ZeroMQ (ZMQ)**.
- Firmware de ESP32-C3: **MicroPython**.
- Backend NUC: **Python 3.12**.
- XR: **Meta XR SDK 83.0**.
- Sistema operativo del entorno principal: **pendiente de especificar en la documentación final**.
- Prioridad documental: **réplica académica**.

## Información faltante y necesaria para redactar el manual final

### 1) Entorno de ejecución (host y NUC)

**Falta por documentar:**
- Sistema operativo exacto de la NUC y de la máquina de desarrollo.
- Método de instalación de dependencias (ej. `pip`, `venv`, instaladores de fabricante).
- Versiones de librerías clave (ZMQ/NetMQ, visión, drivers de sensores).

**Información que necesito del autor:**
- Nombre + versión del sistema operativo usado en NUC.
- Lista de comandos reales que usas para instalar y ejecutar backend.
- Archivo o lista de dependencias Python (si existe).

### 2) Firmware ESP32-C3 (MicroPython)

**Falta por documentar:**
- Estructura del código fuente actual (archivos principales y flujo de arranque).
- Proceso de flasheo y despliegue.
- Parámetros configurables (pines, baudrate, modos, límites de velocidad).

**Información que necesito del autor:**
- Código o árbol de archivos MicroPython de cada ESP32-C3.
- Comandos exactos de carga/flasheo que usas.
- Script o procedimiento de prueba rápida posterior al flasheo.

### 3) Configuración de red y puertos

**Falta por documentar:**
- Esquema de red reproducible (IPs fijas/dinámicas, SSID, segmentación).
- Manejo de reconexión en caso de pérdida de enlace.

**Información que necesito del autor:**
- IP objetivo de NUC y forma de descubrirla.
- Requisitos de red (misma subred, router dedicado, etc.).
- Comportamiento esperado cuando se cae la conexión.

### 4) Integración de hardware

**Falta por documentar:**
- BOM completo y alternativas de componentes.
- Esquema eléctrico integral (no solo módulo puente H).
- Procedimiento mecánico y eléctrico de armado paso a paso.

**Información que necesito del autor:**
- Lista mínima de componentes obligatorios para réplica funcional.
- Diagrama de conexiones final del sistema completo.
- Fotos o secuencia de armado con orden recomendado.

### 5) Calibración y validación técnica

**Falta por documentar:**
- Procedimiento de calibración (sensores, actuadores, centros de articulación).
- Método de medición de desempeño (latencia, estabilidad, tasa de error).
- Protocolo de pruebas con criterios de aprobación/rechazo.

**Información que necesito del autor:**
- Cómo verificas hoy que “funciona bien”.
- Qué métricas sí observas aunque no estén instrumentadas formalmente.
- Tabla de resultados reales ya obtenidos (aunque sea preliminar).

### 6) Seguridad operativa

**Falta por documentar:**
- Protocolo mínimo de seguridad para operación en laboratorio.
- Procedimiento de paro seguro y recuperación tras fallo.

**Información que necesito del autor:**
- Qué haces actualmente para detener el robot ante fallas.
- Distancias/zonas de operación y supervisión durante pruebas.
- Reglas operativas que sigues de forma práctica.

## Criterio editorial para “pendiente por documentar”

Mientras no exista evidencia verificable en repositorio, cada punto faltante se marcará explícitamente como:

> **Pendiente por documentar**: este dato es necesario para réplica académica y aún no está disponible.

Cuando compartas la información, esta página servirá como checklist de cierre hasta completar el manual final.
