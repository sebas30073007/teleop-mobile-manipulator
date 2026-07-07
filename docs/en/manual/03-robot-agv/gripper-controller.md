---
title: "Gripper Controller"
nav_order: 3
parent: "Embedded Systems"
---

# Gripper Controller

MicroPython firmware on **ESP32-C3 SuperMini** that controls the gripper motor by position in millimeters. Unlike the other controllers, this module **has no dedicated PCB**: the ESP32-C3 connects directly to the TB6612FNG driver on a protoboard and communicates with the NUC over USB-CDC (COM5) using ASCII commands.

[⬇ main_gripper_final.py]({{ "/assets/downloads/main_gripper_final.py" | relative_url }}){: .btn .btn-outline }

---

## Hardware

| Component | Description |
|---|---|
| Microcontroller | ESP32-C3 SuperMini |
| Motor driver | TB6612FNG (dual, only channel A used) |
| Motor | Pololu with quadrature encoder (100:1 gearbox) |
| Total travel | 80 mm |
| Communication with NUC | USB-CDC serial 115200 baud (COM5) |
| Mounting | Protoboard — no dedicated PCB |

## Pin assignment

| Signal | GPIO | Function |
|---|---|---|
| `ENC_A` | GPIO3 | Encoder channel A (IRQ on both edges) |
| `ENC_B` | GPIO4 | Encoder channel B (IRQ on both edges) |
| `STBY` | GPIO5 | TB6612 standby (high = active) |
| `AIN1` | GPIO6 | Direction bit 1 |
| `AIN2` | GPIO7 | Direction bit 2 |
| `PWMA` | GPIO10 | 20 kHz speed PWM |

## Quadrature encoder

The Pololu motor's 2-channel quadrature encoder is the only source of position feedback. The `QuadratureEncoder` class processes it in real time via interrupts, using a transition table for phase-correct decoding with ±1 count resolution:

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
        irq = disable_irq()   # atomic read: avoids race condition with the IRQ
        c = self.count
        enable_irq(irq)
        return c
```

## TB6612FNG driver

The `TB6612Motor` class abstracts the TB6612 control signals:

```python
class TB6612Motor:
    def open_raw(self, pct):  # AIN1=1, AIN2=0, PWM=pct% → opens the gripper
    def close_raw(self, pct): # AIN1=0, AIN2=1, PWM=pct% → closes the gripper
    def brake(self):          # AIN1=1, AIN2=1, PWM=0    → active brake (hold)
    def stop(self):           # AIN1=0, AIN2=0, PWM=0    → coasting (no brake)
```

The active brake (`brake`) is always used upon reaching the target position to hold the gripper in place without continuous current draw.

## USB serial commands

The NUC sends text lines over COM5 at 115200 baud; the gripper responds with status lines. All commands are non-blocking: the motor starts and the control loop keeps running in the background.

| Command | Argument | Description | Example |
|---|---|---|---|
| `m <mm>` | position in mm | Go to absolute position | `m 40` |
| `o <mm>` | delta mm | Open _delta_ mm from current position | `o 5` |
| `c <mm>` | delta mm | Close _delta_ mm from current position | `c 5` |
| `to` | — | Go to fully open (OPEN_COUNT) | `to` |
| `tc` | — | Go to fully closed (CLOSED_COUNT) | `tc` |
| `s` | — | Soft stop (brake + stop) | `s` |
| `b` | — | Immediate active brake | `b` |
| `p` | — | Publish machine-readable status | `p` |
| `ph` | — | Publish human-readable status | `ph` |
| `sc` | — | Save current position as CLOSED | `sc` |
| `so` | — | Save current position as OPEN | `so` |
| `z` | — | Reset encoder to 0 | `z` |
| `save` | — | Save state to JSON | `save` |
| `load` | — | Load state from JSON | `load` |

## Position control — `goto_mm_async` flow

```
1. mm_to_count(mm)
      converts mm to encoder counts: count = mm / TRAVEL_MM × (OPEN_COUNT - CLOSED_COUNT)

2. |target - current| ≤ TOL_COUNTS (35)?
      yes → brake + stop, already in position

3. motion_active = True
      the main loop calls control_update() every 8 ms

4. control_update() generates the speed profile and detects stall:
      BOOST (12 ms)  →  accel ramp (30% of travel)
      →  cruise  →  decel ramp (55% of travel)

5. Stall detection:
      if the encoder hasn't changed in 500 ms → forces stop + saves state
```

## Motion profile

The speed profile uses `smoothstep01(x) = x²(3 − 2x)` for smooth transitions between phases, combined with a startup boost to overcome static inertia:

```python
DUTY_MIN    = 10   # minimum % to overcome inertia
DUTY_CRUISE = 50   # nominal cruise %
DUTY_BOOST  = 40   # extra % during the first BOOST_MS ms of startup
BOOST_MS    = 12   # duration of the initial boost

ACCEL_FRAC  = 0.30  # 30% of total travel in acceleration
DECEL_FRAC  = 0.55  # 55% of total travel in deceleration
```

The `smoothstep01` transition function eliminates the acceleration steps that cause mechanical jumps or bounce in the rack-and-pinion mechanism.

## Stall detection

If the encoder registers no change for `STALL_MS = 500` ms while the motor is active, the firmware assumes the gripper hit an obstacle or mechanical limit and safely stops the motor:

```python
if time.ticks_diff(now, last_motion_change_ms) > STALL_MS:
    print("GRIPPER_EVENT stall")
    motor.brake()
    motor.stop()
    motion_active = False
    save_state("stall")  # saves the stall position for diagnostics
```

## Published status format

The gripper publishes its status on each control tick (every 250 ms) or immediately after a command:

```
GRIPPER_STATE mm=40.000 count=-14285 target_mm=40.000 target_count=-14285 busy=0 calibrated=1 open_count=-28570 closed_count=0
```

| Field | Description |
|---|---|
| `mm` | Current position in mm (−1.0 if not calibrated) |
| `count` | Encoder count |
| `target_mm` / `target_count` | Active setpoint |
| `busy` | `1` if the motor is moving |
| `calibrated` | `1` if OPEN_COUNT and CLOSED_COUNT are stored |
| `open_count` / `closed_count` | Calibration endpoints |

The NUC parses this line with a regex and publishes it as `gripper_state` on the ZMQ topic on port :5001.

## Calibration and persistence

Calibration maps the gripper's physical extremes to encoder counts. The procedure is:

1. Manually move (or with short `po`/`pc` pulses) to the **maximum open** position
2. Send `so` → saves `OPEN_COUNT`
3. Move to the **maximum closed** position
4. Send `sc` → saves `CLOSED_COUNT`

Values are stored in `gripper_state.json` with atomic writes to prevent corruption if the process is interrupted:

```python
def atomic_json_write(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        ujson.dump(data, f)   # write to the temp file first
    uos.remove(path)          # remove the previous file
    uos.rename(tmp, path)     # rename temp → atomicity guaranteed
```

On startup, `load_state()` automatically restores the calibration endpoints. If the file doesn't exist or is corrupted, the gripper starts in uncalibrated mode (`calibrated=0`) and position commands remain blocked until calibration is run.

## Validation

| Test | Result |
|---|---|
| Absolute move `m 0` to `m 80` | ✅ Full travel with no loss |
| Stall on obstacle | ✅ Stops within 500 ms, no damage to the gripper |
| Persistence after restart | ✅ Calibration recovered from JSON |
| Remote control from NUC (COM5) | ✅ Latency < 50 ms |

See evidence in [Testing and Calibration]({{ "/docs/en/manual/03-robot-agv/testing-calibration" | relative_url }}).
