---
title: "Puente H"
nav_order: 1
parent: "Sistemas embebidos"
---

# Módulo Puente H con ESP32-C3

Tarjeta de control de motor DC de **diseño propio**, basada en topología de puente H discreto con aislamiento óptico y microcontrolador embebido.

[⬇ Descargar Datasheet (PDF, 1.5 MB)]({{ "/assets/downloads/datasheet_puente_h_esp32c3.pdf" | relative_url }}){: .btn .btn-outline }
[⬇ Proyecto KiCad (ZIP, 5.6 MB)]({{ "/assets/downloads/puente_h_kicad.zip" | relative_url }}){: .btn .btn-outline }

---

## Requisitos

El driver de motor debía:

- Controlar motores DC de 12–24 V, corriente continua ~4 A
- Soportar modos de comunicación múltiples (I²C, WiFi, BLE, UART)
- Encadenarse en arquitectura maestro–esclavo (daisy chain I²C)
- Arrancar en estado seguro (`DISARMED`) para evitar movimientos no deseados
- Ser compacto y replicable con componentes de catálogo

## Diseño del circuito

### Descripción general

| Campo | Valor |
|---|---|
| Alimentación de potencia | 12 V a 24 V DC nominal |
| Corriente continua deseada | 4 A a 5 A |
| Corriente pico máx. | hasta 8 A |
| Microcontrolador | ESP32-C3 SuperMini |
| Aislamiento lógica/potencia | Optoacopladores 4N25 |
| MOSFETs alto lado | IRF9540N (canal P, 117 mΩ) |
| MOSFETs bajo lado | IRF540N (canal N, 44 mΩ) |
| Modos de control | Test, WiFi, BLE, HC-05 (UART), I²C maestro/esclavo |

### Bloques funcionales
![Esquema del puente H]({{ "/assets/img/puente_h_esquema.jpg" | relative_url }})
1. **Etapa de potencia** — Puente H con MOSFETs IRF540N (N) e IRF9540N (P)
2. **Aislamiento de control** — Optoacopladores 4N25 que separan la lógica del circuito de conmutación
3. **Control embebido** — ESP32-C3 administra modos de comunicación, lógica de mando y estados
4. **Interfaz de expansión** — Conectores I²C de entrada y salida para arquitectura maestro–esclavo
5. **Protección e indicación** — Fusible de entrada, capacitor de filtrado, LEDs de estado, botón local

### Tabla funcional del puente H

{: .warning }
El estado `PWM_0 = 1` y `PWM_1 = 1` simultáneamente está **prohibido**: provoca cortocircuito entre rieles de potencia.

| PWM_0 | PWM_1 | Estado | Descripción |
|---|---|---|---|
| 0 | 0 | Libre / deshabilitado | Ambos caminos apagados |
| 1 | 0 | Giro A | Activa diagonal A; combinable con PWM |
| 0 | 1 | Giro B | Activa diagonal B; combinable con PWM |
| 1 | 1 | **PROHIBIDO** | Riesgo de cortocircuito |


## PCB

El diseño de la PCB se realizó en **KiCad** siguiendo el flujo: esquemático → layout de dos capas → exportación de Gerbers para fabricación en JLCPCB.

[⬇ Gerbers para fabricación (ZIP)]({{ "/assets/downloads/puente_h_gerbers.zip" | relative_url }}){: .btn .btn-outline }

### Esquemático

![Esquemático del Puente H]({{ "/assets/img/Esquematico PuenteH.png" | relative_url }})

El esquemático captura todas las conexiones eléctricas del diseño: ESP32-C3 SuperMini, optoacopladores 4N25 para el aislamiento lógica/potencia, MOSFETs IRF540N (canal N) e IRF9540N (canal P) que forman las cuatro ramas del puente, conectores de potencia e I²C, y elementos de protección.

### Layout PCB — 2 capas

![PCB 2 capas — Puente H]({{ "/assets/img/PCB 2 layers PuenteH.png" | relative_url }})

El ruteo en dos capas separa los planos de potencia —pistas anchas dimensionadas para corrientes continuas de hasta 8 A— de las señales lógicas del microcontrolador y los optoacopladores. Esta separación reduce el acoplamiento entre la etapa de conmutación y la lógica de control.

### Fabricación

![Vista de manufactura JLCPCB — Puente H]({{ "/assets/img/Manofactura JLCPCB PuenteH.png" | relative_url }})

La vista de manufactura es el render que genera JLCPCB a partir de los Gerbers antes de confirmar la orden, seguido de la placa ya ensamblada con todos sus componentes soldados manualmente.

### Instalación en el robot

![Módulo Puente H instalado en la estructura del robot]({{ "/assets/img/Puente H e instalación.png" | relative_url }})

La imagen muestra el módulo puente H y su instalación dentro de la estructura del manipulador. La distribución de la PCB concentra control y potencia en una sola placa compacta para facilitar la integración dentro del robot. En la imagen de la derecha se observa cómo ambos módulos Puente H quedaron alojados dentro de la estructura metálica que eleva el manipulador sobre la plataforma móvil, aprovechando espacio ya existente sin cajas externas adicionales. Esta ubicación mantiene el cableado contenido dentro del cuerpo del robot, logrando una integración más limpia y ordenada.



### Asignación de pines ESP32-C3

| Señal | GPIO | Función |
|---|---|---|
| `PWM_0` | GPIO6 | Salida de mando — diagonal A del puente H |
| `PWM_1` | GPIO7 | Salida de mando — diagonal B del puente H |
| `SDA` | GPIO8 | Datos del bus I²C |
| `SCL` | GPIO9 | Reloj del bus I²C |
| `LED` | GPIO10 | LED de usuario / depuración |
| `RX` / `TX` | GPIO20 / GPIO21 | UART para módulo HC-05 |
| `S0`, `S1`, `S2` | GPIO1, GPIO3, GPIO4 | Lectura del DIP switch |
| `BTN` | GPIO5 | Botón local (pull-up interno) |

### Conectores externos

| Conector | Pines | Descripción |
|---|---|---|
| Entrada de potencia | 2 | Entrada principal de 12–24 V DC |
| Salida al motor | 2 | Terminales del puente H hacia la carga |
| `Data_in` I²C | 4 | +5V, SDA, SCL, GND — recibe el bus desde el maestro |
| `Data_out` I²C | 4 | Réplica del bus para encadenar el siguiente módulo |
| Header HC-05 | 6 | +5V, GND, RX, TX — para Bluetooth clásico o debug UART |
| USB-C (ESP32-C3) | — | Programación, alimentación digital y debug prioritario |

### Modos de operación (DIP switch)

El estado del DIP switch se lee **únicamente al encender** y fija el modo de operación.

| SW3 | SW2 | SW1 | Modo | Descripción |
|---|---|---|---|---|
| 0 | 0 | 0 | Prueba local | Validación interna; rutina activable por botón |
| 0 | 0 | 1 | WiFi | Recibe comandos por red inalámbrica |
| 0 | 1 | 0 | BLE | Bluetooth Low Energy |
| 0 | 1 | 1 | HC-05 | Bluetooth clásico por UART externo |
| 1 | 0 | 0 | I²C Maestro | Nodo maestro en arquitectura distribuida |
| 1 | 0 | 1 | I²C Slave 1 | Esclavo 1 (dirección reservada) |
| 1 | 1 | 0 | I²C Slave 2 | Esclavo 2 (dirección reservada) |
| 1 | 1 | 1 | I²C Slave 3 | Esclavo 3 (dirección reservada) |

## Firmware

El firmware corre en **MicroPython** sobre el ESP32-C3. Acepta comandos tanto por USB-C (canal prioritario siempre activo) como por el medio seleccionado con el DIP switch. El código fuente completo está disponible para descarga:

[⬇ main_movil_final.py]({{ "/assets/downloads/main_movil_final.py" | relative_url }}){: .btn .btn-outline }

### Máquina de estados

```
  BOOT
   │  lee DIP switch (solo una vez)
   ▼
DISARMED ──── ARM explícito o botón largo ────► ARMED
   ▲                                              │
   └─── timeout 2 500 ms sin comando ────────────┘
   │
FAULT ◄─── cortocircuito / error de checksum
```

La salida al motor permanece deshabilitada en `DISARMED`. El ARM requiere un comando explícito, lo que impide que movimientos accidentales ocurran al encender o reconectar.

### Indicadores LED

| Estado | Comportamiento del LED |
|---|---|
| `DISARMED` | Ráfaga de N destellos cada 2.2 s (N = código DIP + 1) |
| `ARMED` | LED fijo encendido |
| Prueba en ejecución | Parpadeo lento 0.5 Hz (1 s ON / 1 s OFF) |
| Falla latched | Parpadeo rápido continuo |

### Comandos de control

| Comando | Acción |
|---|---|
| `F` | Adelante (forward) |
| `B` | Atrás (backward) |
| `L` | Izquierda |
| `R` | Derecha |
| `S` | Detener |
| `T` | Activar modo prueba |
| `-255` a `+255` | Consigna numérica directa (se satura a ±70 % de duty) |

Los comandos duales (maestro que controla motor local + motor remoto simultáneamente) se envían como `"F,B"` — el parser `parse_dual_frame()` separa la consigna del motor local de la del esclavo remoto.

### Protocolo I²C binario — tramas de 7 bytes

En los modos maestro/esclavo todos los comandos al Puente H viajan como paquetes binarios de longitud fija. El maestro construye la trama y la envía; los esclavos la validan antes de ejecutar.

```python
# Estructura del paquete (PKT_LEN = 7 bytes)
PKT_PREAMBLE = 0xA5   # byte 0 — marca de inicio fija

CMD_STOP   = 0        # byte 2 — CMD_MODE: motor parado
CMD_TARGET = 1        #           ir a consigna
CMD_TEST   = 2        #           activar rutina de prueba interna

PKT_FLAG_ARMED = 0x01 # byte 5 — FLAGS (bitmask)
PKT_FLAG_FAULT = 0x02
PKT_FLAG_TEST  = 0x04
# byte 6 — XOR checksum de bytes 0-5
```

| Byte | Campo | Descripción |
|---|---|---|
| 0 | `PREAMBLE` | Siempre `0xA5` — marca de sincronía |
| 1 | `SEQ` | Número de secuencia 0–255 para detección de duplicados |
| 2 | `CMD_MODE` | `0` STOP, `1` TARGET, `2` TEST |
| 3–4 | `LO`, `HI` | Consigna con signo como `int16` little-endian |
| 5 | `FLAGS` | Bitmask: `ARMED (0x01)`, `FAULT (0x02)`, `TEST (0x04)` |
| 6 | `CHECKSUM` | XOR de los bytes 0–5 |

{: .warning }
Si el checksum no coincide, el paquete se descarta silenciosamente y el motor permanece en su último estado. Nunca se ejecuta un movimiento con datos corruptos.

### Deadtime y protección de conmutación

Conmutar ambas diagonales del puente H simultáneamente provoca cortocircuito entre rieles de potencia. La función `apply_bridge_local_safe()` impone un tiempo muerto antes de activar la diagonal nueva:

```python
DEADTIME_US = 300   # 300 µs de espera entre cambios de diagonal

# Al cambiar de dirección:
#   1. Apagar ambas salidas PWM
#   2. Esperar DEADTIME_US
#   3. Activar la nueva diagonal
```

### Rampas de aceleración

Ningún cambio de velocidad es instantáneo. El duty cycle sube o baja 1 % cada 20 ms hasta alcanzar la consigna:

```python
RAMP_INTERVAL_MS = 20   # tick de rampa cada 20 ms
RAMP_STEP_PCT    = 1    # incremento máximo por tick: 1 % de duty
MAX_SPEED_PCT    = 70   # velocidad máxima = 70 % de duty cycle
```

El tiempo mínimo para pasar de 0 % a velocidad máxima es 70 × 20 ms = **1.4 s**. Esto limita las corrientes de arranque y el estrés mecánico en los motores DC.

## Validación

Ver pruebas del puente H en [Pruebas y calibración]({{ "/docs/02-manual/03-robot-agv/pruebas" | relative_url }}).
