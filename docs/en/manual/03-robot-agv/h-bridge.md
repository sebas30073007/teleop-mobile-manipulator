---
title: "H-Bridge"
nav_order: 1
parent: "Embedded Systems"
---

# H-Bridge Module with ESP32-C3

**Custom-designed** DC motor control board, based on a discrete H-bridge topology with optical isolation and an embedded microcontroller.

[⬇ Download Datasheet (PDF, 1.5 MB)]({{ "/assets/downloads/datasheet_puente_h_esp32c3.pdf" | relative_url }}){: .btn .btn-outline }
[⬇ KiCad Project (ZIP, 5.6 MB)]({{ "/assets/downloads/puente_h_kicad.zip" | relative_url }}){: .btn .btn-outline }

---

## Requirements

The motor driver had to:

- Control 12–24 V DC motors, ~4 A continuous current
- Support multiple communication modes (I²C, WiFi, BLE, UART)
- Chain into a master–slave architecture (daisy-chain I²C)
- Boot into a safe state (`DISARMED`) to prevent unwanted motion
- Be compact and replicable with catalog components

## Circuit design

### Overview

| Field | Value |
|---|---|
| Power supply | 12 V to 24 V DC nominal |
| Desired continuous current | 4 A to 5 A |
| Max. peak current | up to 8 A |
| Microcontroller | ESP32-C3 SuperMini |
| Logic/power isolation | 4N25 optocouplers |
| High-side MOSFETs | IRF9540N (P-channel, 117 mΩ) |
| Low-side MOSFETs | IRF540N (N-channel, 44 mΩ) |
| Control modes | Test, WiFi, BLE, HC-05 (UART), I²C master/slave |

### Functional blocks
![H-bridge schematic diagram]({{ "/assets/img/puente_h_esquema.jpg" | relative_url }})
1. **Power stage** — H-bridge with IRF540N (N) and IRF9540N (P) MOSFETs
2. **Control isolation** — 4N25 optocouplers separating the logic from the switching circuit
3. **Embedded control** — ESP32-C3 manages communication modes, command logic, and states
4. **Expansion interface** — I²C input and output connectors for master–slave architecture
5. **Protection and indication** — Input fuse, filtering capacitor, status LEDs, local button

### H-bridge functional table

{: .warning }
The state `PWM_0 = 1` and `PWM_1 = 1` simultaneously is **forbidden**: it causes a short circuit between the power rails.

| PWM_0 | PWM_1 | State | Description |
|---|---|---|---|
| 0 | 0 | Free / disabled | Both paths off |
| 1 | 0 | Turn A | Activates diagonal A; combinable with PWM |
| 0 | 1 | Turn B | Activates diagonal B; combinable with PWM |
| 1 | 1 | **FORBIDDEN** | Short-circuit risk |


## PCB

The PCB design was done in **KiCad** following the flow: schematic → two-layer layout → Gerber export for manufacturing at JLCPCB.

[⬇ Manufacturing Gerbers (ZIP)]({{ "/assets/downloads/puente_h_gerbers.zip" | relative_url }}){: .btn .btn-outline }

### Schematic

![H-Bridge schematic]({{ "/assets/img/Esquematico PuenteH.png" | relative_url }})

The schematic captures all electrical connections of the design: ESP32-C3 SuperMini, 4N25 optocouplers for logic/power isolation, IRF540N (N-channel) and IRF9540N (P-channel) MOSFETs forming the four bridge branches, power and I²C connectors, and protection elements.

### PCB layout — 2 layers

![2-layer PCB — H-Bridge]({{ "/assets/img/PCB 2 layers PuenteH.png" | relative_url }})

The two-layer routing separates the power planes — traces sized wide enough for continuous currents up to 8 A — from the microcontroller's logic signals and the optocouplers. This separation reduces coupling between the switching stage and the control logic.

### Manufacturing

![JLCPCB manufacturing view — H-Bridge]({{ "/assets/img/Manofactura JLCPCB PuenteH.png" | relative_url }})

The manufacturing view is the render JLCPCB generates from the Gerbers before confirming the order, followed by the assembled board with all components hand-soldered.

### Installation on the robot

![H-Bridge module installed in the robot structure]({{ "/assets/img/Puente H e instalación.png" | relative_url }})

The image shows the H-Bridge module and its installation inside the manipulator structure. The PCB layout concentrates control and power on a single compact board to ease integration within the robot. The right-hand image shows how both H-Bridge modules ended up housed inside the metal structure that raises the manipulator above the mobile platform, taking advantage of existing space without additional external enclosures. This placement keeps the wiring contained within the robot's body, resulting in a cleaner, more organized integration.



### ESP32-C3 pin assignment

| Signal | GPIO | Function |
|---|---|---|
| `PWM_0` | GPIO6 | Command output — H-bridge diagonal A |
| `PWM_1` | GPIO7 | Command output — H-bridge diagonal B |
| `SDA` | GPIO8 | I²C bus data |
| `SCL` | GPIO9 | I²C bus clock |
| `LED` | GPIO10 | User / debug LED |
| `RX` / `TX` | GPIO20 / GPIO21 | UART for HC-05 module |
| `S0`, `S1`, `S2` | GPIO1, GPIO3, GPIO4 | DIP switch reading |
| `BTN` | GPIO5 | Local button (internal pull-up) |

### External connectors

| Connector | Pins | Description |
|---|---|---|
| Power input | 2 | Main 12–24 V DC input |
| Motor output | 2 | H-bridge terminals to the load |
| `Data_in` I²C | 4 | +5V, SDA, SCL, GND — receives the bus from the master |
| `Data_out` I²C | 4 | Bus replica to chain the next module |
| HC-05 header | 6 | +5V, GND, RX, TX — for classic Bluetooth or UART debug |
| USB-C (ESP32-C3) | — | Programming, digital power, and priority debug |

### Operating modes (DIP switch)

The DIP switch state is read **only at power-up** and sets the operating mode.

| SW3 | SW2 | SW1 | Mode | Description |
|---|---|---|---|---|
| 0 | 0 | 0 | Local test | Internal validation; routine triggered by button |
| 0 | 0 | 1 | WiFi | Receives commands over wireless network |
| 0 | 1 | 0 | BLE | Bluetooth Low Energy |
| 0 | 1 | 1 | HC-05 | Classic Bluetooth over external UART |
| 1 | 0 | 0 | I²C Master | Master node in distributed architecture |
| 1 | 0 | 1 | I²C Slave 1 | Slave 1 (reserved address) |
| 1 | 1 | 0 | I²C Slave 2 | Slave 2 (reserved address) |
| 1 | 1 | 1 | I²C Slave 3 | Slave 3 (reserved address) |

## Firmware

The firmware runs on **MicroPython** on the ESP32-C3. It accepts commands both over USB-C (priority channel, always active) and over the medium selected with the DIP switch. The full source code is available for download:

[⬇ main_movil_final.py]({{ "/assets/downloads/main_movil_final.py" | relative_url }}){: .btn .btn-outline }

### State machine

```
  BOOT
   │  reads DIP switch (once only)
   ▼
DISARMED ──── explicit ARM or long button press ────► ARMED
   ▲                                              │
   └─── 2,500 ms timeout with no command ────────┘
   │
FAULT ◄─── short circuit / checksum error
```

The motor output stays disabled in `DISARMED`. ARM requires an explicit command, which prevents accidental motion on power-up or reconnection.

### LED indicators

| State | LED behavior |
|---|---|
| `DISARMED` | Burst of N flashes every 2.2 s (N = DIP code + 1) |
| `ARMED` | LED steady on |
| Test running | Slow 0.5 Hz blink (1 s ON / 1 s OFF) |
| Latched fault | Continuous fast blink |

### Control commands

| Command | Action |
|---|---|
| `F` | Forward |
| `B` | Backward |
| `L` | Left |
| `R` | Right |
| `S` | Stop |
| `T` | Enable test mode |
| `-255` to `+255` | Direct numeric setpoint (saturates at ±70% duty) |

Dual commands (master controlling the local motor + the remote motor simultaneously) are sent as `"F,B"` — the `parse_dual_frame()` parser splits the local motor setpoint from the remote slave's.

### Binary I²C protocol — 7-byte frames

In master/slave modes, all commands to the H-Bridge travel as fixed-length binary packets. The master builds the frame and sends it; the slaves validate it before executing.

```python
# Packet structure (PKT_LEN = 7 bytes)
PKT_PREAMBLE = 0xA5   # byte 0 — fixed start marker

CMD_STOP   = 0        # byte 2 — CMD_MODE: motor stopped
CMD_TARGET = 1        #           go to setpoint
CMD_TEST   = 2        #           enable internal test routine

PKT_FLAG_ARMED = 0x01 # byte 5 — FLAGS (bitmask)
PKT_FLAG_FAULT = 0x02
PKT_FLAG_TEST  = 0x04
# byte 6 — XOR checksum of bytes 0-5
```

| Byte | Field | Description |
|---|---|---|
| 0 | `PREAMBLE` | Always `0xA5` — sync marker |
| 1 | `SEQ` | Sequence number 0–255 for duplicate detection |
| 2 | `CMD_MODE` | `0` STOP, `1` TARGET, `2` TEST |
| 3–4 | `LO`, `HI` | Signed setpoint as little-endian `int16` |
| 5 | `FLAGS` | Bitmask: `ARMED (0x01)`, `FAULT (0x02)`, `TEST (0x04)` |
| 6 | `CHECKSUM` | XOR of bytes 0–5 |

{: .warning }
If the checksum doesn't match, the packet is silently dropped and the motor remains in its last state. A move is never executed on corrupted data.

### Deadtime and switching protection

Switching both H-bridge diagonals simultaneously causes a short circuit between the power rails. The `apply_bridge_local_safe()` function imposes a dead time before activating the new diagonal:

```python
DEADTIME_US = 300   # 300 µs wait between diagonal changes

# When changing direction:
#   1. Turn off both PWM outputs
#   2. Wait DEADTIME_US
#   3. Activate the new diagonal
```

### Acceleration ramps

No speed change is instantaneous. Duty cycle rises or falls 1% every 20 ms until the setpoint is reached:

```python
RAMP_INTERVAL_MS = 20   # ramp tick every 20 ms
RAMP_STEP_PCT    = 1    # max increment per tick: 1% duty
MAX_SPEED_PCT    = 70   # maximum speed = 70% duty cycle
```

The minimum time to go from 0% to top speed is 70 × 20 ms = **1.4 s**. This limits inrush currents and mechanical stress on the DC motors.

## Validation

See H-Bridge tests in [Testing and Calibration]({{ "/docs/en/manual/03-robot-agv/testing-calibration" | relative_url }}).
