---
title: "Controlador del gripper"
nav_order: 3
parent: "Sistemas embebidos"
---

# Controlador del gripper

Firmware MicroPython sobre **ESP32-C3 SuperMini** que controla el motor del gripper por posición en milímetros. A diferencia de los otros controladores, este módulo **no tiene PCB dedicada**: el ESP32-C3 se conecta directamente al driver TB6612FNG en protoboard y se comunica con la NUC por USB-CDC (COM5) mediante comandos ASCII.

[⬇ main_gripper_final.py]({{ "/assets/downloads/main_gripper_final.py" | relative_url }}){: .btn .btn-outline }

---

## Hardware

| Componente | Descripción |
|---|---|
| Microcontrolador | ESP32-C3 SuperMini |
| Driver de motor | TB6612FNG (dual, solo canal A usado) |
| Motor | Pololu con encoder de cuadratura (reductor 100:1) |
| Recorrido total | 80 mm |
| Comunicación con NUC | USB-CDC serial 115200 baud (COM5) |
| Montaje | Protoboard — sin PCB dedicada |

## Asignación de pines

| Señal | GPIO | Función |
|---|---|---|
| `ENC_A` | GPIO3 | Encoder canal A (IRQ en ambos flancos) |
| `ENC_B` | GPIO4 | Encoder canal B (IRQ en ambos flancos) |
| `STBY` | GPIO5 | Standby TB6612 (alto = activo) |
| `AIN1` | GPIO6 | Dirección bit 1 |
| `AIN2` | GPIO7 | Dirección bit 2 |
| `PWMA` | GPIO10 | PWM de velocidad a 20 kHz |

## Encoder de cuadratura

El encoder cuadratura de 2 canales del motor Pololu es la única fuente de retroalimentación de posición. La clase `QuadratureEncoder` lo procesa en tiempo real por interrupciones, usando una tabla de transición para decodificación phase-correct con resolución ±1 count:

```python
class QuadratureEncoder:
    _TRANSITION_TABLE = (
        0, -1,  1,  0,
        1,  0,  0, -1,
       -1,  0,  0,  1,
        0,  1, -1,  0,
    )

    def _irq(self, pin):
        state = (self.pin_a.value() << 1) | self.pin_b.value()
        transition = (self.prev_state << 2) | state
        delta = self._TRANSITION_TABLE[transition] * DIR_SIGN
        if delta:
            self.count += delta
        self.prev_state = state

    def read(self):
        irq = disable_irq()   # lectura atómica: evita condición de carrera con el IRQ
        c = self.count
        enable_irq(irq)
        return c
```

## Driver TB6612FNG

La clase `TB6612Motor` abstrae las señales de control del TB6612:

```python
class TB6612Motor:
    def open_raw(self, pct):  # AIN1=1, AIN2=0, PWM=pct% → abre el gripper
    def close_raw(self, pct): # AIN1=0, AIN2=1, PWM=pct% → cierra el gripper
    def brake(self):          # AIN1=1, AIN2=1, PWM=0    → freno activo (hold)
    def stop(self):           # AIN1=0, AIN2=0, PWM=0    → coasting (sin freno)
```

El freno activo (`brake`) se usa siempre al llegar a la posición destino para mantener la pinza en posición sin consumo continuo de corriente.

## Comandos USB serial

La NUC envía líneas de texto por COM5 a 115200 baud; el gripper responde con líneas de estado. Todos los comandos son no bloqueantes: el motor arranca y el bucle de control sigue corriendo en segundo plano.

| Comando | Argumento | Descripción | Ejemplo |
|---|---|---|---|
| `m <mm>` | posición en mm | Ir a posición absoluta | `m 40` |
| `o <mm>` | delta mm | Abrir _delta_ mm desde posición actual | `o 5` |
| `c <mm>` | delta mm | Cerrar _delta_ mm desde posición actual | `c 5` |
| `to` | — | Ir a completamente abierto (OPEN_COUNT) | `to` |
| `tc` | — | Ir a completamente cerrado (CLOSED_COUNT) | `tc` |
| `s` | — | Stop suave (brake + stop) | `s` |
| `b` | — | Brake activo inmediato | `b` |
| `p` | — | Publicar estado machine-readable | `p` |
| `ph` | — | Publicar estado human-readable | `ph` |
| `sc` | — | Guardar posición actual como CERRADO | `sc` |
| `so` | — | Guardar posición actual como ABIERTO | `so` |
| `z` | — | Reset encoder a 0 | `z` |
| `save` | — | Guardar estado en JSON | `save` |
| `load` | — | Cargar estado desde JSON | `load` |

## Control de posición — flujo `goto_mm_async`

```
1. mm_to_count(mm)
      convierte mm a encoder counts: count = mm / TRAVEL_MM × (OPEN_COUNT - CLOSED_COUNT)

2. ¿|target - current| ≤ TOL_COUNTS (35)?
      sí → brake + stop, ya está en posición

3. motion_active = True
      el bucle principal llama control_update() cada 8 ms

4. control_update() genera el perfil de velocidad y detecta stall:
      BOOST (12 ms)  →  rampa accel (30% del recorrido)
      →  crucero  →  rampa decel (55% del recorrido)

5. Detección de stall:
      si encoder no cambió en 500 ms → fuerza stop + guarda estado
```

## Perfil de movimiento

El perfil de velocidad usa `smoothstep01(x) = x²(3 − 2x)` para transiciones suaves entre fases, combinado con un boost de arranque para vencer la inercia estática:

```python
DUTY_MIN    = 10   # % mínimo para vencer la inercia
DUTY_CRUISE = 50   # % de crucero nominal
DUTY_BOOST  = 40   # % extra en los primeros BOOST_MS ms de arranque
BOOST_MS    = 12   # duración del boost inicial

ACCEL_FRAC  = 0.30  # 30 % del recorrido total en aceleración
DECEL_FRAC  = 0.55  # 55 % del recorrido total en desaceleración
```

La función de transición `smoothstep01` elimina los escalones de aceleración que causan saltos mecánicos o rebote en el mecanismo de piñón-cremallera.

## Detección de stall

Si el encoder no registra cambio durante `STALL_MS = 500` ms mientras el motor está activo, el firmware asume que el gripper golpeó un obstáculo o límite mecánico y detiene el motor de forma segura:

```python
if time.ticks_diff(now, last_motion_change_ms) > STALL_MS:
    print("GRIPPER_EVENT stall")
    motor.brake()
    motor.stop()
    motion_active = False
    save_state("stall")  # guarda la posición del stall para diagnóstico
```

## Formato de estado publicado

El gripper publica su estado en cada tick de control (cada 250 ms) o inmediatamente tras un comando:

```
GRIPPER_STATE mm=40.000 count=-14285 target_mm=40.000 target_count=-14285 busy=0 calibrated=1 open_count=-28570 closed_count=0
```

| Campo | Descripción |
|---|---|
| `mm` | Posición actual en mm (−1.0 si no calibrado) |
| `count` | Cuenta del encoder |
| `target_mm` / `target_count` | Consigna activa |
| `busy` | `1` si el motor está en movimiento |
| `calibrated` | `1` si OPEN_COUNT y CLOSED_COUNT están guardados |
| `open_count` / `closed_count` | Endpoints de calibración |

La NUC parsea esta línea con regex y la publica como `gripper_state` en el tópico ZMQ del puerto :5001.

## Calibración y persistencia

La calibración mapea los extremos físicos del gripper a counts de encoder. El procedimiento es:

1. Mover manualmente (o con pulsos cortos `po`/`pc`) hasta la posición **abierta máxima**
2. Enviar `so` → guarda `OPEN_COUNT`
3. Mover hasta la posición **cerrada máxima**
4. Enviar `sc` → guarda `CLOSED_COUNT`

Los valores se almacenan en `gripper_state.json` con escritura atómica para evitar corrupción si se interrumpe el proceso:

```python
def atomic_json_write(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        ujson.dump(data, f)   # escribe al archivo temporal primero
    uos.remove(path)          # elimina el archivo anterior
    uos.rename(tmp, path)     # renombra el temporal → atomicidad garantizada
```

Al arrancar, `load_state()` restaura automáticamente los endpoints de calibración. Si el archivo no existe o está corrupto, el gripper arranca en modo no calibrado (`calibrated=0`) y los comandos de posición quedan bloqueados hasta que se ejecute la calibración.

## Validación

| Prueba | Resultado |
|---|---|
| Movimiento absoluto `m 0` a `m 80` | ✅ Recorrido completo sin pérdida |
| Stall en obstáculo | ✅ Para en 500 ms, no daña el gripper |
| Persistencia tras reinicio | ✅ Calibración recuperada de JSON |
| Control remoto desde NUC (COM5) | ✅ Latencia < 50 ms |

Ver evidencia en [Pruebas y calibración]({{ "/docs/02-manual/03-robot-agv/pruebas" | relative_url }}).
