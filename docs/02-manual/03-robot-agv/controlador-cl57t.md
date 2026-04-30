---
title: "Controlador de drivers (CL57T)"
nav_order: 2
parent: "Sistemas embebidos"
---

# Controlador de drivers (CL57T)

Placa de diseño propio basada en **ESP32-C3** que genera las señales de paso para los tres drivers de motor del manipulador. Cada driver es un **CL57T** (cerrado-lazo, compatible con NEMA17).

![Controlador]({{ "/assets/img/Controlador.png" | relative_url }})

## Requisitos

- Controlar 3 ejes del manipulador (articulaciones + hombro) de forma independiente
- Generar señales **PUL / DIR / ENABLE** hacia cada driver CL57T
- Soportar finales de carrera para rutinas de calibración y búsqueda de cero
- Recibir comandos de posición desde la NUC vía I2C (a través del Puente H maestro)

## Diseño

### Drivers CL57T

El CL57T es un driver de paso cerrado (servo-stepper) que acepta señales digitales de pulso y dirección. Opera en modo de lazo cerrado usando el encoder del motor para corregir pérdida de pasos.

| Parámetro | Valor |
|---|---|
| Motor compatible | NEMA17 |
| Tipo de lazo | Cerrado (encoder incremental) |
| Señales de control | PUL, DIR, ENABLE (lógica 5V) |
| Corriente máx. | Configurable por DIP en driver |

### Placa controladora

La placa genera las señales para los tres CL57T y gestiona las entradas digitales de los finales de carrera:

| Función | Descripción |
|---|---|
| Salidas PUL/DIR/ENABLE | Una terna por cada eje (×3) |
| Entradas digitales | Finales de carrera para calibración |
| Botón físico | Rutina de búsqueda de cero activable localmente |
| Comunicación | I2C esclavo — recibe comandos del Puente H maestro |

## Resolución y rangos por eje

| Eje | Pasos / vuelta | Rango lógico | Pasos / grado | Función |
|---|---|---|---|---|
| BASE | 10 000 | −80° a +80° | 27.78 | Rotación horizontal de la base |
| CODO | 25 000 | 0° a 136.5° | 69.44 | Articulación del codo |
| MUÑECA | 25 000 | −220° a 0° | 69.44 | Orientación de la muñeca |

La resolución aumentada en codo y muñeca (25 000 pasos/vuelta) incluye la reducción de la transmisión HTD3M más el reductor planetario 10:1.

## Firmware

[⬇ main_manipulador_final.py]({{ "/assets/downloads/main_manipulador_final.py" | relative_url }}){: .btn .btn-outline }

### Asignación de pines ESP32-C3

| Señal | GPIO | Función |
|---|---|---|
| `PUL_BASE` | GPIO20 | Pulso de paso — base |
| `DIR_BASE` | GPIO21 | Dirección — base |
| `PUL_CODO` | GPIO7 | Pulso de paso — codo |
| `DIR_CODO` | GPIO10 | Dirección — codo |
| `PUL_MUNECA` | GPIO5 | Pulso de paso — muñeca |
| `DIR_MUNECA` | GPIO6 | Dirección — muñeca |
| `SW2` | GPIO3 | Final de carrera codo |
| `SW3` | GPIO4 | Final de carrera muñeca |
| `SDA` / `SCL` | GPIO8 / GPIO9 | Bus I²C esclavo (addr `0x0B`) |
| `BTN` | GPIO0 | Botón local (homing sin NUC) |
| `LED` | GPIO2 | Indicador de estado |

## Implementación

Los comandos de posición viajan desde la NUC por el serial del Puente H maestro (USB → COM4), y el maestro los reenvía a esta placa por el bus I²C. La placa ejecuta la interpolación de pasos localmente, sin que la NUC tenga que gestionar señales en tiempo real.

### Flujo de comando de eje

```
Meta Quest (XR)
    │ ZMQ cmd (manip_cmd)
    ▼
NUC (Python 3.12)
    │ Serial COM4
    ▼
Puente H maestro (ESP32-C3)
    │ I²C addr 0x0B (texto ASCII)
    ▼
Controlador CL57T (ESP32-C3)
    │ PUL / DIR / ENABLE
    ▼
Driver CL57T × 3
    │
    ▼
NEMA17 + reductor planetario × 3 (articulaciones del manipulador)
```

### Protocolo ASCII por I²C (esclavo `0x0B`)

El maestro escribe texto ASCII terminado en `\n` al buffer I²C; el controlador coloca la respuesta en los 96 bytes del buffer de lectura. Todos los comandos bloquean hasta que el movimiento termina (sincrónico).

| Comando | Argumento | Respuesta | Descripción |
|---|---|---|---|
| `PING` | — | `PONG` | Verificar que el esclavo responde |
| `STATE?` | — | `OK busy=0 sw2=0 sw3=0 calibrated=1 base=0.00 codo=45.00 muneca=-90.00` | Estado completo |
| `HOME_ALL` | — | `OK HOME_ALL` / `ERR HOME_ALL` | Homing de codo + muñeca |
| `HOME_CODO` | — | `OK HOME_CODO` | Homing solo codo |
| `HOME_MUNECA` | — | `OK HOME_MUNECA` | Homing solo muñeca |
| `BASE_GOTO` | `grados` | `OK BASE 45.000` | Posición absoluta base |
| `BASE_REL` | `delta_grados` | `OK BASE -10.000` | Posición relativa base |
| `CODO_GOTO` | `grados` | `OK CODO 90.000` | Posición absoluta codo |
| `CODO_REL` | `delta_grados` | `OK CODO 5.000` | Posición relativa codo |
| `MUNECA_GOTO` | `grados` | `OK MUNECA -45.000` | Posición absoluta muñeca |
| `MUNECA_REL` | `delta_grados` | `OK MUNECA -10.000` | Posición relativa muñeca |
| `POSE` | `base codo muneca` | `OK POSE base codo muneca` | Los 3 ejes en secuencia |

Núcleo del parser (simplificado):

```python
def exec_command(cmdline):
    parts = cmdline.strip().split()
    cmd   = parts[0].upper()

    if cmd == "PING":        return "PONG"
    if cmd == "STATE?":      return "OK " + estado_actual_str()
    if cmd == "HOME_ALL":    return "OK HOME_ALL" if home_all() else "ERR HOME_ALL"
    if cmd == "BASE_GOTO":   ir_base_a_deg(float(parts[1]));   return "OK BASE ..."
    if cmd == "CODO_GOTO":   ir_codo_a_deg(float(parts[1]));   return "OK CODO ..."
    if cmd == "MUNECA_GOTO": ir_muneca_a_deg(float(parts[1])); return "OK MUNECA ..."
    if cmd == "POSE":
        ir_base_a_deg(float(parts[1]))    # base: sin efecto sobre muñeca
        ir_codo_a_deg(float(parts[2]))    # codo: arrastra compensación de muñeca
        ir_muneca_a_deg(float(parts[3]))  # muñeca: se ajusta sobre la compensación
        return "OK POSE ..."
```

### Rutina de homing — algoritmo de 4 fases

Cada vez que se enciende el robot, es necesario ejecutar `HOME_ALL` para establecer la posición cero de codo y muñeca. La base no tiene final de carrera y arranca desde donde esté.

```
Fase 1 — Búsqueda rápida:  avanza hacia el switch a 1 800 µs/paso
                            hasta que SW2/SW3 se activa
Fase 2 — Backoff:          retrocede 220 pasos a 3 200 µs/paso
Fase 3 — Búsqueda fina:    avanza de nuevo a 3 200 µs/paso
                            (menor velocidad = mayor precisión de reproducción)
Fase 4 — Clearance final:  retrocede 120 pasos → posición cero reproducible
```

```python
# Ejemplo: homing del codo (muñeca sigue el mismo patrón con SW3)
mover_codo_home(AWAY_SIGN_CODO, BACKOFF_STEPS, PULSE_HOME_SLOW_US)      # 220 pasos atrás
ok, _ = buscar_switch("CODO", mover_codo_home, HOME_SIGN_CODO, SW2,
                       PULSE_HOME_SLOW_US, BACKOFF_STEPS + 300, 1)      # búsqueda fina
mover_codo_home(AWAY_SIGN_CODO, FINAL_CLEARANCE_STEPS, PULSE_HOME_SLOW_US)  # 120 pasos
pos_codo = FINAL_CLEARANCE_STEPS                                         # cero lógico
```

El botón físico (GPIO0, pulsación larga) ejecuta `HOME_ALL` sin necesidad de la NUC — útil durante desarrollo o recuperación de error.

### Finales de carrera

Los finales de carrera definen los puntos de referencia (cero) de cada articulación.

![Final de carrera — articulación superior — base del manipulador]({{ "/assets/img/Finales de carrera.png" | relative_url }})

La lectura del switch aplica un debounce de 5 ms con doble confirmación para evitar falsas activaciones por vibración mecánica:

```python
def switch_active_confirmed(sw_pin, confirm_ms=5):
    if sw_pin.value() == 0:       # activo bajo
        sleep_ms(confirm_ms)
        return sw_pin.value() == 0
    return False
```

### Compensación mecánica de muñeca

La transmisión de correa HTD3M entre el codo y la muñeca acopla físicamente ambos ejes: cuando el codo gira, la muñeca gira con él aunque no se haya enviado un comando. El firmware corrige esto emitiendo pulsos de compensación al motor de muñeca en paralelo con los del codo, manteniendo el ángulo lógico (`pos_muneca`) estable:

```python
# Dos variables independientes para la muñeca:
# pos_muneca       = ángulo lógico (lo que el usuario ve y comanda)
# pos_muneca_motor = posición física acumulada del motor

# Durante mover_codo():
#   → pos_muneca_motor cambia (se emiten COMP_RATIO pasos de compensación)
#   → pos_muneca NO cambia

# Durante MUNECA_GOTO:
#   → cambian ambas variables

COMPENSATE_MUNECA_WITH_CODO = True
COMP_RATIO = 1.0    # 1 paso de codo → 1 paso de compensación en muñeca
```

### Rampas de velocidad (perfil trapezoidal)

Los 3 ejes usan rampas independientes para evitar pérdida de pasos al arrancar y vibración al frenar:

```python
# Configuración idéntica para BASE, CODO y MUÑECA
*_RAMP_START_US  = 2500   # velocidad inicial (pulso largo = lento)
*_RAMP_CRUISE_US = 1600   # velocidad de crucero
*_RAMP_END_US    = 2500   # velocidad de frenado
*_ACCEL_STEPS    = 1500   # pasos en rampa de aceleración
*_DECEL_STEPS    = 1500   # pasos en rampa de deceleración
```

Perfil: aceleración lineal → crucero → deceleración lineal.

### Estado publicado hacia la NUC

La placa reporta estado en respuesta a `STATE?`:

| Campo | Descripción |
|---|---|
| `busy` | `1` si algún eje está en movimiento |
| `sw2`, `sw3` | Estado actual de los finales de carrera |
| `calibrated` | `1` si se completó al menos un `HOME_ALL` |
| `base`, `codo`, `muneca` | Ángulos lógicos actuales en grados |

## Validación

| Prueba | Resultado |
|---|---|
| Movimiento de articulaciones (estático) | ✅ Rangos alcanzados, sin pérdida de pasos detectada |
| Rutina de búsqueda de cero | ✅ Funcional con finales de carrera |
| Control remoto desde interfaz XR | ⏳ Pendiente integración completa |

Ver evidencia en [Pruebas y calibración]({{ "/docs/02-manual/03-robot-agv/pruebas" | relative_url }}).
