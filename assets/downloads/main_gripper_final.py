from machine import Pin, PWM, disable_irq, enable_irq
import time
import micropython
import ujson
import uos
import sys
import uselect

micropython.alloc_emergency_exception_buf(100)

# =========================================================
# PINES
# =========================================================
PIN_ENC_A = 3
PIN_ENC_B = 4

PIN_STBY = 5
PIN_AIN1 = 6
PIN_AIN2 = 7
PIN_PWMA = 10

# =========================================================
# AJUSTES DEL GRIPPER / MOTOR / PERFIL
# =========================================================
DIR_SIGN = 1
TRAVEL_MM = 80.0
STATE_FILE = "gripper_state.json"

PWM_FREQ = 20000
UPDATE_MS = 8
BRAKE_MS = 8
STALL_MS = 500
TOL_COUNTS = 35

# Perfil suave
DUTY_MIN = 10
DUTY_CRUISE = 50
DUTY_BOOST = 40
BOOST_MS = 12
ACCEL_FRAC = 0.30
DECEL_FRAC = 0.55
MIN_ACCEL_COUNTS = 400
MIN_DECEL_COUNTS = 1400

# Pulsos manuales
PULSE_SMALL_DUTY = 24
PULSE_SMALL_MS = 65
PULSE_BIG_DUTY = 36
PULSE_BIG_MS = 120

AUTO_SAVE_AFTER_COMMAND = True
STATE_PUBLISH_MS = 250

OPEN_COUNT = None
CLOSED_COUNT = None

# =========================================================
# UTILIDADES
# =========================================================
def clamp(x, lo, hi):
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x


def smoothstep01(x):
    x = clamp(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def atomic_json_write(path, data):
    tmp = path + ".tmp"
    try:
        try:
            uos.remove(tmp)
        except:
            pass
        with open(tmp, "w") as f:
            ujson.dump(data, f)
            try:
                f.flush()
            except:
                pass
        try:
            uos.remove(path)
        except:
            pass
        uos.rename(tmp, path)
    except Exception as e:
        print("No se pudo guardar", path, ":", e)


# =========================================================
# ENCODER CUADRATURA
# =========================================================
class QuadratureEncoder:
    _TRANSITION_TABLE = (
        0, -1,  1,  0,
        1,  0,  0, -1,
       -1,  0,  0,  1,
        0,  1, -1,  0,
    )

    def __init__(self, pin_a, pin_b):
        self.pin_a = Pin(pin_a, Pin.IN, Pin.PULL_UP)
        self.pin_b = Pin(pin_b, Pin.IN, Pin.PULL_UP)
        self.count = 0
        self.last_dir = 0
        self.prev_state = (self.pin_a.value() << 1) | self.pin_b.value()

        self.pin_a.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self._irq)
        self.pin_b.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self._irq)

    def _irq(self, pin):
        state = (self.pin_a.value() << 1) | self.pin_b.value()
        transition = (self.prev_state << 2) | state
        delta = self._TRANSITION_TABLE[transition] * DIR_SIGN
        if delta:
            self.count += delta
            self.last_dir = 1 if delta > 0 else -1
        self.prev_state = state

    def read(self):
        irq = disable_irq()
        c = self.count
        enable_irq(irq)
        return c

    def set_count(self, value):
        irq = disable_irq()
        self.count = int(value)
        enable_irq(irq)

    def reset(self):
        self.set_count(0)


# =========================================================
# DRIVER TB6612FNG
# =========================================================
class TB6612Motor:
    def __init__(self, stby, ain1, ain2, pwma, pwm_freq=PWM_FREQ):
        self.stby = Pin(stby, Pin.OUT)
        self.ain1 = Pin(ain1, Pin.OUT)
        self.ain2 = Pin(ain2, Pin.OUT)
        self.pwm = PWM(Pin(pwma), freq=pwm_freq)
        self.pwm.duty_u16(0)
        self.stby.value(1)
        self.stop()

    def _set_duty_percent(self, pct):
        pct = int(clamp(pct, 0, 100))
        duty = int((pct / 100.0) * 65535)
        self.pwm.duty_u16(duty)

    def open_raw(self, pct):
        self.stby.value(1)
        self.ain1.value(1)
        self.ain2.value(0)
        self._set_duty_percent(pct)

    def close_raw(self, pct):
        self.stby.value(1)
        self.ain1.value(0)
        self.ain2.value(1)
        self._set_duty_percent(pct)

    def drive(self, direction, pct):
        if direction == "OPEN":
            self.open_raw(pct)
        else:
            self.close_raw(pct)

    def stop(self):
        self.ain1.value(0)
        self.ain2.value(0)
        self._set_duty_percent(0)

    def brake(self):
        self.ain1.value(1)
        self.ain2.value(1)
        self._set_duty_percent(0)

    def pulse(self, direction, peak_pct, total_ms, shaped=True):
        peak_pct = int(clamp(peak_pct, 0, 100))
        total_ms = max(1, int(total_ms))

        if not shaped or total_ms < 30:
            self.drive(direction, peak_pct)
            time.sleep_ms(total_ms)
            self.brake()
            time.sleep_ms(BRAKE_MS)
            self.stop()
            return

        t0 = time.ticks_ms()
        while True:
            now = time.ticks_ms()
            elapsed = time.ticks_diff(now, t0)
            if elapsed >= total_ms:
                break

            x = elapsed / float(total_ms)
            if x < 0.25:
                g = smoothstep01(x / 0.25)
            elif x > 0.75:
                g = smoothstep01((1.0 - x) / 0.25)
            else:
                g = 1.0

            pct = DUTY_MIN + (peak_pct - DUTY_MIN) * g
            pct = int(clamp(pct, DUTY_MIN, peak_pct))
            self.drive(direction, pct)
            time.sleep_ms(6)

        self.brake()
        time.sleep_ms(BRAKE_MS)
        self.stop()


enc = QuadratureEncoder(PIN_ENC_A, PIN_ENC_B)
motor = TB6612Motor(PIN_STBY, PIN_AIN1, PIN_AIN2, PIN_PWMA, pwm_freq=PWM_FREQ)

# =========================================================
# ESTADO / PERSISTENCIA
# =========================================================
def load_state():
    global OPEN_COUNT, CLOSED_COUNT
    try:
        with open(STATE_FILE, "r") as f:
            data = ujson.load(f)
        OPEN_COUNT = data.get("open_count", None)
        CLOSED_COUNT = data.get("closed_count", None)
        pos_count = data.get("pos_count", 0)
        enc.set_count(pos_count)
        print("Estado cargado:")
        print("  pos_count    =", pos_count)
        print("  CLOSED_COUNT =", CLOSED_COUNT)
        print("  OPEN_COUNT   =", OPEN_COUNT)
    except:
        print("No hay estado guardado. Iniciando desde cero.")


def save_state(reason=""):
    data = {
        "pos_count": enc.read(),
        "open_count": OPEN_COUNT,
        "closed_count": CLOSED_COUNT,
        "travel_mm": TRAVEL_MM,
        "reason": reason,
        "saved_ms": time.ticks_ms(),
    }
    atomic_json_write(STATE_FILE, data)


def counts_span():
    if OPEN_COUNT is None or CLOSED_COUNT is None:
        return None
    return OPEN_COUNT - CLOSED_COUNT


def counts_per_mm():
    span = counts_span()
    if span is None or TRAVEL_MM == 0:
        return None
    return abs(span) / TRAVEL_MM


def count_to_mm(count):
    if OPEN_COUNT is None or CLOSED_COUNT is None:
        return None
    span = OPEN_COUNT - CLOSED_COUNT
    if span == 0:
        return None
    return (count - CLOSED_COUNT) * (TRAVEL_MM / span)


def mm_to_count(mm):
    if OPEN_COUNT is None or CLOSED_COUNT is None:
        return None
    mm = clamp(float(mm), 0.0, TRAVEL_MM)
    return int(round(CLOSED_COUNT + (OPEN_COUNT - CLOSED_COUNT) * (mm / TRAVEL_MM)))


def opening_increases_count():
    if OPEN_COUNT is None or CLOSED_COUNT is None:
        return False
    return OPEN_COUNT > CLOSED_COUNT


def direction_for_target(cur, target):
    if OPEN_COUNT is not None and CLOSED_COUNT is not None:
        if opening_increases_count():
            return "OPEN" if target > cur else "CLOSE"
        return "CLOSE" if target > cur else "OPEN"
    return "OPEN" if target < cur else "CLOSE"


def print_status_human():
    print("\n====== ESTADO ======")
    cur = enc.read()
    print("Encoder actual :", cur)
    mm = count_to_mm(cur)
    if mm is not None:
        print("Apertura aprox :", round(mm, 2), "mm")
    else:
        print("Apertura aprox : sin calibracion")
    print("CLOSED_COUNT   :", CLOSED_COUNT)
    print("OPEN_COUNT     :", OPEN_COUNT)
    cpm = counts_per_mm()
    if cpm is not None:
        print("Counts/mm      :", round(cpm, 3))
    if OPEN_COUNT is not None and CLOSED_COUNT is not None:
        print("RECORRIDO TOTAL:", abs(OPEN_COUNT - CLOSED_COUNT), "counts")
        print("RECORRIDO REAL :", TRAVEL_MM, "mm")
        print("OPEN aumenta?  :", "SI" if opening_increases_count() else "NO")
    print("PWM_FREQ       :", PWM_FREQ, "Hz")
    print("DUTY_MIN       :", DUTY_MIN, "%")
    print("DUTY_CRUISE    :", DUTY_CRUISE, "%")
    print("DUTY_BOOST     :", DUTY_BOOST, "%")
    print("====================\n")


# =========================================================
# CONTROL NO BLOQUEANTE / ULTIMO TARGET GANA
# =========================================================
motion_active = False
target_count = None
motion_start_count = 0
motion_start_ms = time.ticks_ms()
last_motion_pos = 0
last_motion_change_ms = time.ticks_ms()
last_direction = None
last_state_publish_ms = 0
last_cmd_text = ""


def profile_duty(total_counts, remaining_counts):
    if total_counts <= 0:
        return DUTY_MIN

    travelled = total_counts - remaining_counts
    accel_counts = max(int(total_counts * ACCEL_FRAC), MIN_ACCEL_COUNTS)
    decel_counts = max(int(total_counts * DECEL_FRAC), MIN_DECEL_COUNTS)

    accel_gain = smoothstep01(travelled / float(accel_counts))
    decel_gain = smoothstep01(remaining_counts / float(decel_counts))

    duty_up = DUTY_MIN + (DUTY_CRUISE - DUTY_MIN) * accel_gain
    duty_down = DUTY_MIN + (DUTY_CRUISE - DUTY_MIN) * decel_gain
    duty = min(duty_up, duty_down)

    if total_counts < 1000:
        duty = max(duty, DUTY_MIN + 4)

    return int(clamp(round(duty), DUTY_MIN, DUTY_CRUISE))


def is_calibrated():
    return OPEN_COUNT is not None and CLOSED_COUNT is not None and OPEN_COUNT != CLOSED_COUNT


def current_mm_safe():
    mm = count_to_mm(enc.read())
    return 0.0 if mm is None else float(mm)


def target_mm_safe():
    if target_count is None:
        return current_mm_safe()
    mm = count_to_mm(target_count)
    return current_mm_safe() if mm is None else float(mm)


def emit_state(force=False):
    global last_state_publish_ms
    now = time.ticks_ms()
    if (not force) and time.ticks_diff(now, last_state_publish_ms) < STATE_PUBLISH_MS:
        return
    last_state_publish_ms = now

    cur = enc.read()
    mm = count_to_mm(cur)
    if mm is None:
        mm = -1.0
    tmm = target_mm_safe()
    tcount = cur if target_count is None else int(target_count)
    cal = 1 if is_calibrated() else 0
    busy = 1 if motion_active else 0

    print(
        "GRIPPER_STATE mm={:.3f} count={} target_mm={:.3f} target_count={} busy={} calibrated={} open_count={} closed_count={}".format(
            float(mm), int(cur), float(tmm), int(tcount), busy, cal,
            OPEN_COUNT if OPEN_COUNT is not None else -1,
            CLOSED_COUNT if CLOSED_COUNT is not None else -1,
        )
    )


def stop_motion(save_reason=""):
    global motion_active, target_count, last_direction
    motor.stop()
    motion_active = False
    target_count = enc.read()
    last_direction = None
    if AUTO_SAVE_AFTER_COMMAND and save_reason:
        save_state(save_reason)
    emit_state(force=True)


def set_target_count(new_target, reason="set_target"):
    global motion_active, target_count, motion_start_count, motion_start_ms
    global last_motion_pos, last_motion_change_ms, last_direction

    cur = enc.read()
    target = int(new_target)
    target_count = target
    motion_start_count = cur
    motion_start_ms = time.ticks_ms()
    last_motion_pos = cur
    last_motion_change_ms = motion_start_ms
    last_direction = None

    if abs(target - cur) <= TOL_COUNTS:
        motion_active = False
        motor.brake()
        time.sleep_ms(BRAKE_MS)
        motor.stop()
        if AUTO_SAVE_AFTER_COMMAND:
            save_state(reason)
        emit_state(force=True)
        return True

    motion_active = True
    emit_state(force=True)
    return True


def goto_mm_async(mm, reason="m"):
    target = mm_to_count(mm)
    if target is None:
        print("ERR falta_calibracion")
        return False
    return set_target_count(target, reason=reason)


def move_relative_mm_async(delta_mm, reason="rel"):
    cur_mm = count_to_mm(enc.read())
    if cur_mm is None:
        print("ERR falta_calibracion")
        return False
    target_mm = clamp(cur_mm + delta_mm, 0.0, TRAVEL_MM)
    return goto_mm_async(target_mm, reason=reason)


def control_update():
    global motion_active, last_motion_pos, last_motion_change_ms, last_direction

    if not motion_active or target_count is None:
        return

    now = time.ticks_ms()
    cur = enc.read()
    remaining = abs(target_count - cur)

    if cur != last_motion_pos:
        last_motion_pos = cur
        last_motion_change_ms = now

    if remaining <= TOL_COUNTS:
        motor.brake()
        time.sleep_ms(BRAKE_MS)
        motor.stop()
        motion_active = False
        if AUTO_SAVE_AFTER_COMMAND:
            save_state(last_cmd_text if last_cmd_text else "target_reached")
        emit_state(force=True)
        return

    total = abs(target_count - motion_start_count)
    if total <= 0:
        total = remaining

    direction = direction_for_target(cur, target_count)

    if last_direction is not None and direction != last_direction:
        motor.brake()
        time.sleep_ms(BRAKE_MS)
    last_direction = direction

    duty = profile_duty(total, remaining)
    if time.ticks_diff(now, motion_start_ms) < BOOST_MS:
        duty = max(duty, DUTY_BOOST)

    motor.drive(direction, duty)

    if time.ticks_diff(now, last_motion_change_ms) > STALL_MS:
        print("GRIPPER_EVENT stall")
        motor.brake()
        time.sleep_ms(BRAKE_MS)
        motor.stop()
        motion_active = False
        if AUTO_SAVE_AFTER_COMMAND:
            save_state("stall")
        emit_state(force=True)


# =========================================================
# CONSOLA / USB SERIAL NO BLOQUEANTE
# =========================================================
stdin_poll = uselect.poll()
stdin_poll.register(sys.stdin, uselect.POLLIN)


def read_command_line_nonblocking():
    try:
        events = stdin_poll.poll(0)
        if not events:
            return None
        line = sys.stdin.readline()
        if not line:
            return None
        return line.strip()
    except Exception:
        return None


def print_help():
    print("\nControl de gripper asincrono listo.")
    print("Comandos:")
    print("  m 40    -> ir a 40 mm (ultimo target sobreescribe el anterior)")
    print("  o 5     -> abrir 5 mm")
    print("  c 5     -> cerrar 5 mm")
    print("  tc      -> ir a cerrado completo")
    print("  to      -> ir a abierto completo")
    print("  s       -> stop")
    print("  b       -> brake")
    print("  p       -> estado maquina-readable")
    print("  ph      -> estado humano")
    print("  sc      -> guardar posicion actual como CERRADO")
    print("  so      -> guardar posicion actual como ABIERTO")
    print("  z       -> reset encoder a 0")
    print("  save    -> guardar estado")
    print("  load    -> cargar estado")
    print("  po/poo  -> pulso abrir")
    print("  pc/pcc  -> pulso cerrar")
    print("  cfg     -> guia tuning\n")


def handle_command(cmd):
    global OPEN_COUNT, CLOSED_COUNT, last_cmd_text

    if not cmd:
        return

    last_cmd_text = cmd
    parts = cmd.lower().split()
    head = parts[0]

    try:
        if head in ("?", "help"):
            print_help()
            return

        if head in ("p", "state?", "status"):
            emit_state(force=True)
            return

        if head == "ph":
            print_status_human()
            return

        if head == "save":
            save_state("manual_save")
            emit_state(force=True)
            return

        if head == "load":
            load_state()
            emit_state(force=True)
            return

        if head == "z":
            enc.reset()
            if AUTO_SAVE_AFTER_COMMAND:
                save_state("z")
            emit_state(force=True)
            return

        if head == "sc":
            CLOSED_COUNT = enc.read()
            if AUTO_SAVE_AFTER_COMMAND:
                save_state("sc")
            emit_state(force=True)
            return

        if head == "so":
            OPEN_COUNT = enc.read()
            if AUTO_SAVE_AFTER_COMMAND:
                save_state("so")
            emit_state(force=True)
            return

        if head == "cfg":
            print("GUIA RAPIDA DE TUNING")
            print("- Si sigue lento: sube DUTY_CRUISE")
            print("- Si no arranca fácil: sube DUTY_BOOST")
            print("- Si golpea al final: baja DUTY_MIN o sube DECEL_FRAC")
            print("- Si vibra mucho: sube UPDATE_MS")
            print("- Si se calienta: baja DUTY_CRUISE y/o BOOST_MS")
            return

        if head == "s":
            stop_motion("s")
            return

        if head == "b":
            motor.brake()
            time.sleep_ms(BRAKE_MS)
            stop_motion("b")
            return

        if head == "po":
            motor.pulse("OPEN", PULSE_SMALL_DUTY, PULSE_SMALL_MS, shaped=True)
            if AUTO_SAVE_AFTER_COMMAND:
                save_state("po")
            emit_state(force=True)
            return

        if head == "poo":
            motor.pulse("OPEN", PULSE_BIG_DUTY, PULSE_BIG_MS, shaped=True)
            if AUTO_SAVE_AFTER_COMMAND:
                save_state("poo")
            emit_state(force=True)
            return

        if head == "pc":
            motor.pulse("CLOSE", PULSE_SMALL_DUTY, PULSE_SMALL_MS, shaped=True)
            if AUTO_SAVE_AFTER_COMMAND:
                save_state("pc")
            emit_state(force=True)
            return

        if head == "pcc":
            motor.pulse("CLOSE", PULSE_BIG_DUTY, PULSE_BIG_MS, shaped=True)
            if AUTO_SAVE_AFTER_COMMAND:
                save_state("pcc")
            emit_state(force=True)
            return

        if head == "tc":
            if CLOSED_COUNT is None:
                print("ERR no_closed_count")
                return
            set_target_count(CLOSED_COUNT, reason="tc")
            return

        if head == "to":
            if OPEN_COUNT is None:
                print("ERR no_open_count")
                return
            set_target_count(OPEN_COUNT, reason="to")
            return

        if head == "m" and len(parts) == 2:
            mm = float(parts[1])
            goto_mm_async(mm, reason=cmd)
            return

        if head == "o" and len(parts) == 2:
            mm = float(parts[1])
            move_relative_mm_async(+mm, reason=cmd)
            return

        if head == "c" and len(parts) == 2:
            mm = float(parts[1])
            move_relative_mm_async(-mm, reason=cmd)
            return

        print("ERR comando_no_valido")
    except Exception as e:
        motor.stop()
        print("ERR", e)
        emit_state(force=True)


# =========================================================
# ARRANQUE
# =========================================================
load_state()
print_help()
emit_state(force=True)

while True:
    line = read_command_line_nonblocking()
    if line is not None:
        handle_command(line)
    control_update()
    emit_state(force=False)
    time.sleep_ms(UPDATE_MS)

