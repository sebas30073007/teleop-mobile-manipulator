---
title: "Puente H"
nav_order: 1
parent: "Robot AGV"
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

![PCB recién soldada]({{ "/assets/img/Puente H e instalación.png" | relative_url }})

La imagen muestra el módulo puente H diseñado para el proyecto y su instalación dentro de la estructura del manipulador. La distribución de la PCB busca concentrar los elementos principales de control y potencia en una sola placa compacta, reduciendo el espacio necesario para el sistema electrónico y facilitando su integración dentro del robot.En la imagen de la derecha se observa cómo ambos módulos puente H fueron colocados dentro de la estructura metálica que eleva el manipulador sobre la plataforma móvil. Esta decisión permite aprovechar un espacio que ya formaba parte de la estructura mecánica, evitando agregar cajas externas o soportes adicionales.Además de optimizar el espacio disponible, esta ubicación ayuda a disminuir el ruido visual del prototipo, ya que gran parte del cableado y de la electrónica queda contenida dentro del cuerpo del robot. De esta forma, la integración final se ve más limpia, compacta y ordenada, manteniendo los módulos cerca de los actuadores que controlan.



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

El firmware (MicroPython) acepta comandos tanto por USB-C (canal prioritario siempre activo) como por el medio configurado (WiFi/BLE/HC-05/I²C).

### Máquina de estados

`DISARMED` → `ARMED` → ejecución de comandos

La salida al motor permanece deshabilitada en `DISARMED` hasta habilitación explícita.

### Indicadores LED

| Estado | Comportamiento del LED |
|---|---|
| `DISARMED` | Destellos con patrón del modo DIP configurado |
| `ARMED` | LED fijo encendido |
| Prueba en ejecución | Parpadeo lento a 0.5 Hz (1s ON / 1s OFF) |
| Falla | Parpadeo rápido |

### Comandos de control

| Comando | Acción |
|---|---|
| `F` | Adelante (forward) |
| `B` | Atrás (backward) |
| `L` | Izquierda |
| `R` | Derecha |
| `S` | Detener |
| `T` | Modo prueba |
| `-255` a `+255` | Consigna numérica de velocidad (con saturación automática) |

Todos los comandos se ejecutan mediante **rampas de aceleración** — ningún cambio de velocidad es instantáneo.

> **Pendiente:** Publicar el código fuente MicroPython completo (archivo `.py` de arranque y módulos de máquina de estados).

## Validación

Ver pruebas del puente H en [Pruebas y calibración]({{ "/docs/02-manual/03-robot-agv/pruebas" | relative_url }}).
