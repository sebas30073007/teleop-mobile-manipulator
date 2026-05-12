---
title: "Puesta en marcha"
nav_order: 7
parent: "Documentación"
---

# Puesta en marcha

Tiempo estimado desde cero hasta sistema operativo: **~5 minutos** (mayoría corresponde al arranque de la NUC).

## Alimentación

El sistema usa tres baterías LiPo independientes, una por subsistema de potencia:

| Batería | Celdas | Subsistema alimentado | Nota |
|---|---|---|---|
| LiPo 6S | 6 celdas | Puentes H — plataforma móvil | Alimenta directamente los MOSFETs de tracción |
| LiPo 3S — NUC | 3 celdas | NUC + motor del gripper | El motor DC del gripper (12 V) va en paralelo con la NUC |
| LiPo 3S — manipulador | 3 celdas | Drivers CL57T | Alimenta los tres drivers del manipulador |

Conectar las tres baterías antes de encender la NUC asegura que todos los módulos embebidos y drivers estén energizados desde el inicio.

## Secuencia de arranque

### 1. Conectar las tres baterías

Conectar en cualquier orden. Al energizarse, los módulos ESP32-C3 arrancan automáticamente y quedan en estado `DISARMED` esperando comandos.

### 2. Encender la NUC

Al arrancar, la NUC ejecuta automáticamente el script principal de Python 3.12. Esto levanta el middleware ZMQ, inicializa los canales de streaming de video (RealSense D435i) y LiDAR (RPLiDAR C1), y abre las conexiones seriales con los módulos embebidos (COM4 — Puente H maestro, COM5 — controlador gripper).

No se requiere intervención manual: el sistema llega a estado operativo por sí solo.

### 3. Verificar la IP dinámica de la NUC

La red de la escuela no permite IPs fijas, por lo que la NUC recibe una IP dinámica en cada arranque. La NUC y la PC de debugeo están conectadas a la misma red local (TileSkate); los lentes Meta Quest **no** están en esa red.

Para obtener la IP actual de la NUC desde la PC de debugeo:

```bash
arp -a
```

o, si se conoce el hostname:

```bash
ping <hostname-de-la-NUC>
```

Alternativa más directa: conectar un monitor externo a la NUC al arrancar y leer la IP desde la terminal.

### 4. Ingresar la IP en la aplicación Meta Quest

Al abrir la aplicación en los lentes, el campo de IP del servidor debe apuntarse a la IP dinámica obtenida en el paso anterior. Una vez ingresada, la aplicación establece las conexiones ZMQ y comienza a recibir video, estado del robot y datos de LiDAR.

Si la IP fuera fija este paso desaparecería; es el único punto de fricción en el arranque actual.

### 5. Sistema listo

Con la IP correcta configurada en los lentes, el sistema está operativo: video en vivo, telemetría y control de movimiento disponibles desde la interfaz XR.

{: .warning }
Antes de armar (`ARM`) cualquier controlador, verificar que el área de trabajo del robot esté despejada. Los módulos arrancan en `DISARMED` por diseño, pero el ARM es inmediato una vez enviado el comando.
