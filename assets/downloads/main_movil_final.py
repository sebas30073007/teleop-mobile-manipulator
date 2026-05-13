from machine import Pin, PWM, I2C, UART
import time
import sys

try:
    import uselect
except ImportError:
    uselect = None

# =========================================================
# PINES (segun tu PCB puente H)
# =========================================================
S0_PIN = 1
S1_PIN = 3
S2_PIN = 4
BTN_PIN = 5

IN_0_PIN = 6
IN_1_PIN = 7

SDA_PIN = 8
SCL_PIN = 9

LED_PIN = 10

UART_RX_PIN = 20
UART_TX_PIN = 21

# =========================================================
# MODOS POR DIP (S2 S1 S0)
# Se conserva tu mapa original.
# =========================================================
MODE_TEST       = 0b000
MODE_WIFI       = 0b001   # alias a SERIAL_MASTER en este firmware simplificado
MODE_BLE        = 0b010   # alias a SERIAL_MASTER en este firmware simplificado
MODE_HC05       = 0b011   # alias a SERIAL_MASTER en este firmware simplificado
MODE_I2C_MASTER = 0b100   # MASTER por serial + I2C
MODE_SLAVE1     = 0b101
MODE_SLAVE2     = 0b110
MODE_SLAVE3     = 0b111

MODE_NAMES = {
    MODE_TEST: "TEST",
    MODE_WIFI: "SERIAL_MASTER",
    MODE_BLE: "SERIAL_MASTER",
    MODE_HC05: "SERIAL_MASTER",
    MODE_I2C_MASTER: "SERIAL_MASTER",
    MODE_SLAVE1: "SLAVE1",
    MODE_SLAVE2: "SLAVE2",
    MODE_SLAVE3: "SLAVE3",
}

# Esclavos puente H binarios (mismo protocolo que tu Slave1)
SLAVE_ADDR_MAP = {
    MODE_SLAVE1: 0x08,
    MODE_SLAVE2: 0x09,
    MODE_SLAVE3: 0x0A,
}

# Orquestacion del maestro:
HB_REMOTE_ADDR = 0x08     # puente H esclavo remoto
MANIP_ADDR = 0x0B         # esclavo manipulador de texto ASCII

# =========================================================
# CONFIG GENERAL
# =========================================================
PWM_FREQ = 1000
DEADTIME_US = 300

MAX_CMD_RAW = 255
MAX_SPEED_PCT = 70

RAMP_INTERVAL_MS = 20
RAMP_STEP_PCT = 1

COMM_TIMEOUT_MS = 2500
SLAVE_REFRESH_MS = 80
BTN_DEBOUNCE_MS = 35
BTN_LONG_MS = 1200

TEST_UPDATE_MS = 80
TEST_STEP_RAW = 18

LED_FAULT_TOGGLE_MS = 120
LED_DISARMED_SLOT_MS = 180
LED_DISARMED_CYCLE_MS = 2200
TEST_BLINK_HALF_PERIOD_MS = 1000

SERIAL_BAUD = 115200
USB_PRIORITY_TIMEOUT_MS = 8000

# =========================================================
# PROTOCOLO I2C BINARIO PARA ESCLAVOS PUENTE H
# =========================================================
PKT_PREAMBLE = 0xA5
CMD_STOP   = 0
CMD_TARGET = 1
CMD_TEST   = 2

PKT_FLAG_ARMED = 0x01
PKT_FLAG_FAULT = 0x02
PKT_FLAG_TEST  = 0x04

PKT_LEN = 7

# =========================================================
# ESTADO GLOBAL
# =========================================================
mode_code = MODE_TEST
mode_name = "TEST"

boot_b2 = 0
boot_b1 = 0
boot_b0 = 0

armed = False
fault_latched = False
fault_reason = ""

last_source = "NONE"
control_owner = "NONE"
usb_priority_until_ms = time.ticks_ms()

# Estado motor local
local_cmd_mode = CMD_STOP
local_cmd_raw = 0
local_target_pct = 0
local_current_pct = 0
local_pattern = 0

# Estado esclavo puente H remoto
hb_remote_cmd_mode = CMD_STOP
hb_remote_raw = 0
hb_remote_online = False
hb_remote_online_prev = None
last_hb_send_ms = time.ticks_ms()

# Estado test local
test_running = False
test_raw = 0
test_dir = 1
last_test_ms = time.ticks_ms()

last_ramp_ms = time.ticks_ms()
last_command_ms = time.ticks_ms()
timeout_announced = False

frame_seq = 0
last_manip_tx_ms = time.ticks_ms()

# boton
btn_last_raw = 1
btn_stable = 1
btn_last_change_ms = time.ticks_ms()
btn_press_ms = 0

# serie
usb_poll = None
usb_rx_buffer = ""
serial_uart = None
uart_rx_buffer = ""

# perifericos
s0 = None
s1 = None
s2 = None
btn = None
led = None
pwm_in0 = None
pwm_in1 = None
i2c = None

# esclavo I2C (cuando esta en modo slave1/2/3)
i2c_target = None
i2c_target_supported = False
i2c_target_mem = bytearray(PKT_LEN)
i2c_target_pending = False
i2c_target_last_snapshot = bytes(PKT_LEN)
last_i2c_packet_ms = time.ticks_ms()
last_i2c_seq = None
I2CTargetClass = None

PATTERN_STOP = 0
PATTERN_IN0_PWM = 1
PATTERN_IN1_PWM = 2

MANIP_FIRST_WORDS = (
    "PING", "STATE?", "HOME_ALL", "HOME_CODO", "HOME_MUNECA",
    "BASE_GOTO", "BASE_REL", "CODO_GOTO", "CODO_REL",
    "MUNECA_GOTO", "MUNECA_REL", "POSE"
)

# =========================================================
# HELPERS BASICOS
# =========================================================
def clamp(val, lo, hi):
    if val < lo:
        return lo
    if val > hi:
        return hi
    return val

def xor_checksum(buf):
    c = 0
    for b in buf:
        c ^= b
    return c & 0xFF

def raw_to_pct(raw):
    raw = clamp(int(raw), -MAX_CMD_RAW, MAX_CMD_RAW)
    return int((raw * MAX_SPEED_PCT) / MAX_CMD_RAW)

def percent_to_duty_u16(pct):
    pct = abs(clamp(int(pct), 0, 100))
    return int((pct * 65535) / 100)

def ramp_toward(current, target):
    if current < target:
        current += RAMP_STEP_PCT
        if current > target:
            current = target
    elif current > target:
        current -= RAMP_STEP_PCT
        if current < target:
            current = target
    return current

def mode_blink_count(code):
    return code + 1

def signed16_from_lo_hi(lo, hi):
    v = lo | (hi << 8)
    if v & 0x8000:
        v -= 0x10000
    return v

def is_slave_mode():
    return mode_code in (MODE_SLAVE1, MODE_SLAVE2, MODE_SLAVE3)

def is_master_mode():
    return mode_code in (MODE_WIFI, MODE_BLE, MODE_HC05, MODE_I2C_MASTER)

def read_switches():
    # switch activo conecta a GND -> invertido
    b0 = 0 if s0.value() == 1 else 1
    b1 = 0 if s1.value() == 1 else 1
    b2 = 0 if s2.value() == 1 else 1
    code = (b2 << 2) | (b1 << 1) | b0
    return code, b2, b1, b0

def claim_usb_priority():
    global control_owner, usb_priority_until_ms
    control_owner = "USB"
    usb_priority_until_ms = time.ticks_add(time.ticks_ms(), USB_PRIORITY_TIMEOUT_MS)

def usb_priority_active():
    global control_owner
    if control_owner != "USB":
        return False
    if time.ticks_diff(usb_priority_until_ms, time.ticks_ms()) > 0:
        return True
    control_owner = "NONE"
    return False

def status_text():
    live_code, live_b2, live_b1, live_b0 = read_switches()
    owner = "USB" if usb_priority_active() else control_owner
    extra = ""
    if is_master_mode():
        extra = "|HB={}/{}@{}|MANIP@{}".format(
            hb_remote_cmd_mode, hb_remote_raw, int(hb_remote_online), hex(MANIP_ADDR)
        )
    elif is_slave_mode():
        extra = "|I2C_ADDR={}".format(hex(SLAVE_ADDR_MAP[mode_code]))
    return (
        "MODE={}|DIP_BOOT={}{}{}|DIP_LIVE={}{}{}|ARMED={}|FAULT={}|TEST={}|"
        "SRC={}|OWNER={}|LCMD={}|LRAW={}|LTGT={}|LCUR={}{}".format(
            mode_name,
            boot_b2, boot_b1, boot_b0,
            live_b2, live_b1, live_b0,
            int(armed),
            int(fault_latched),
            int(test_running),
            last_source,
            owner,
            local_cmd_mode,
            local_cmd_raw,
            local_target_pct,
            local_current_pct,
            extra,
        )
    )

def notify(msg):
    print(msg)
    if serial_uart is not None:
        try:
            serial_uart.write(msg + "\n")
        except Exception:
            pass

# =========================================================
# INIT HARDWARE
# =========================================================
def init_common_pins():
    global s0, s1, s2, btn, led, pwm_in0, pwm_in1
    s0 = Pin(S0_PIN, Pin.IN, Pin.PULL_UP)
    s1 = Pin(S1_PIN, Pin.IN, Pin.PULL_UP)
    s2 = Pin(S2_PIN, Pin.IN, Pin.PULL_UP)
    btn = Pin(BTN_PIN, Pin.IN, Pin.PULL_UP)
    led = Pin(LED_PIN, Pin.OUT)

    pwm_in0 = PWM(Pin(IN_0_PIN), freq=PWM_FREQ, duty_u16=0)
    pwm_in1 = PWM(Pin(IN_1_PIN), freq=PWM_FREQ, duty_u16=0)

def init_serial_inputs():
    global usb_poll, serial_uart

    if uselect is not None:
        try:
            usb_poll = uselect.poll()
            usb_poll.register(sys.stdin, uselect.POLLIN)
            print("[SERIAL] USB stdin polling OK")
        except Exception as e:
            usb_poll = None
            print("[SERIAL] USB poll no disponible:", e)

    last_err = None
    for uart_id in (1, 0):
        try:
            serial_uart = UART(uart_id, SERIAL_BAUD, tx=Pin(UART_TX_PIN), rx=Pin(UART_RX_PIN))
            print("[SERIAL] UART OK en id", uart_id)
            return True
        except Exception as e:
            last_err = e

    serial_uart = None
    if last_err is not None:
        print("[SERIAL] UART no disponible:", last_err)
    return False

# =========================================================
# LED
# =========================================================
def update_led():
    now = time.ticks_ms()

    if fault_latched:
        led.value(1 if ((now // LED_FAULT_TOGGLE_MS) % 2) else 0)
        return

    if test_running:
        led.value(1 if ((now // TEST_BLINK_HALF_PERIOD_MS) % 2) else 0)
        return

    if armed:
        led.value(1)
        return

    count = mode_blink_count(mode_code)
    phase = now % LED_DISARMED_CYCLE_MS
    max_window = count * LED_DISARMED_SLOT_MS

    if phase < max_window:
        led.value(1 if (phase % LED_DISARMED_SLOT_MS) < (LED_DISARMED_SLOT_MS // 2) else 0)
    else:
        led.value(0)

# =========================================================
# H-BRIDGE LOCAL SAFE
# =========================================================
def apply_bridge_local_safe(pattern, duty_u16):
    global local_pattern

    duty_u16 = clamp(int(duty_u16), 0, 65535)

    if pattern != local_pattern:
        pwm_in0.duty_u16(0)
        pwm_in1.duty_u16(0)
        local_pattern = PATTERN_STOP
        time.sleep_us(DEADTIME_US)

    if pattern == PATTERN_IN0_PWM:
        pwm_in1.duty_u16(0)
        pwm_in0.duty_u16(duty_u16)
        local_pattern = PATTERN_IN0_PWM
    elif pattern == PATTERN_IN1_PWM:
        pwm_in0.duty_u16(0)
        pwm_in1.duty_u16(duty_u16)
        local_pattern = PATTERN_IN1_PWM
    else:
        pwm_in0.duty_u16(0)
        pwm_in1.duty_u16(0)
        local_pattern = PATTERN_STOP

def apply_motor_local_signed(speed_pct):
    speed_pct = clamp(int(speed_pct), -100, 100)

    if speed_pct == 0:
        apply_bridge_local_safe(PATTERN_STOP, 0)
        return

    duty = percent_to_duty_u16(abs(speed_pct))
    if speed_pct > 0:
        apply_bridge_local_safe(PATTERN_IN0_PWM, duty)
    else:
        apply_bridge_local_safe(PATTERN_IN1_PWM, duty)

# =========================================================
# SAFE / FAULT
# =========================================================
def stop_local_only():
    global local_cmd_mode, local_cmd_raw, local_target_pct, local_current_pct
    global test_running, test_raw, test_dir

    local_cmd_mode = CMD_STOP
    local_cmd_raw = 0
    local_target_pct = 0
    local_current_pct = 0
    test_running = False
    test_raw = 0
    test_dir = 1
    apply_motor_local_signed(0)

def stop_all_hard():
    global hb_remote_cmd_mode, hb_remote_raw
    stop_local_only()
    hb_remote_cmd_mode = CMD_STOP
    hb_remote_raw = 0
    if is_master_mode() and i2c is not None:
        refresh_hb_remote(force=True)

def latch_fault(reason):
    global fault_latched, fault_reason, armed, test_running, last_source
    fault_latched = True
    fault_reason = reason
    armed = False
    test_running = False
    last_source = "FAULT"
    stop_all_hard()
    notify("FAULT:" + reason)

def clear_fault():
    global fault_latched, fault_reason
    fault_latched = False
    fault_reason = ""
    stop_all_hard()
    notify("FAULT_CLEARED")

# =========================================================
# BOTON
# =========================================================
def on_button_short():
    global armed, test_running, last_source
    last_source = "BTN"

    if fault_latched:
        notify("FAULT_LATCHED")
        return

    if armed:
        armed = False
        test_running = False
        stop_all_hard()
        notify("DISARMED")
    else:
        armed = True
        if is_master_mode():
            refresh_hb_remote(force=True)
        notify("ARMED")

def on_button_long():
    global test_running, test_raw, test_dir, armed, last_source, local_cmd_mode, local_cmd_raw
    last_source = "BTN"

    if fault_latched:
        clear_fault()
        return

    if mode_code == MODE_TEST:
        test_running = not test_running
        if test_running:
            armed = True
            test_raw = 0
            test_dir = 1
            local_cmd_mode = CMD_TEST
            local_cmd_raw = 0
            notify("TEST_ON")
        else:
            local_cmd_mode = CMD_STOP
            local_cmd_raw = 0
            notify("TEST_OFF")
    else:
        notify(status_text())

def update_button():
    global btn_last_raw, btn_stable, btn_last_change_ms, btn_press_ms

    raw = btn.value()
    now = time.ticks_ms()

    if raw != btn_last_raw:
        btn_last_raw = raw
        btn_last_change_ms = now

    if time.ticks_diff(now, btn_last_change_ms) < BTN_DEBOUNCE_MS:
        return

    if raw != btn_stable:
        btn_stable = raw
        if btn_stable == 0:
            btn_press_ms = now
        else:
            held_ms = time.ticks_diff(now, btn_press_ms)
            if held_ms >= BTN_LONG_MS:
                on_button_long()
            else:
                on_button_short()

# =========================================================
# PARSING BASICO (motor/local/hb)
# =========================================================
def parse_single_token(token):
    s = token.strip().upper()
    if not s:
        return None, None

    if s == "F":
        return "NODE", (CMD_TARGET, +255)
    elif s == "B":
        return "NODE", (CMD_TARGET, -255)
    elif s == "S":
        return "NODE", (CMD_STOP, 0)
    elif s == "T":
        return "NODE", (CMD_TEST, 0)
    elif s in ("ARM", "DISARM", "STATUS", "CLRFAULT", "RESETFAULT", "FAULTRESET"):
        return "META", s

    try:
        v = int(s)
        v = clamp(v, -MAX_CMD_RAW, MAX_CMD_RAW)
        return "NODE", (CMD_TARGET, v)
    except Exception:
        return None, None

def parse_dual_frame(line):
    # local,hb
    parts = [p.strip() for p in line.split(",") if p.strip() != ""]
    if len(parts) != 2:
        raise ValueError("FRAME_DEBE_TENER_2_TOKENS")

    kind0, val0 = parse_single_token(parts[0])
    kind1, val1 = parse_single_token(parts[1])
    if kind0 != "NODE" or kind1 != "NODE":
        raise ValueError("TOKEN_INVALIDO_EN_FRAME")

    return val0[0], val0[1], val1[0], val1[1]

def require_arm_for_motion():
    if armed:
        return True
    notify("NOT_ARMED")
    return False

# =========================================================
# LOGICA LOCAL
# =========================================================
def set_local_command(cmd_mode, raw_value, source=""):
    global local_cmd_mode, local_cmd_raw
    global last_command_ms, timeout_announced, test_running, last_source

    if fault_latched:
        notify("FAULT_LATCHED")
        return False

    if cmd_mode == CMD_STOP:
        test_running = False
        local_cmd_mode = CMD_STOP
        local_cmd_raw = 0
        last_command_ms = time.ticks_ms()
        timeout_announced = False
        last_source = source
        notify("LOCAL_STOP")
        return True

    if cmd_mode != CMD_STOP and not require_arm_for_motion():
        return False

    if cmd_mode == CMD_TEST:
        test_running = True
        local_cmd_mode = CMD_TEST
        local_cmd_raw = 0
    else:
        test_running = False
        local_cmd_mode = cmd_mode
        local_cmd_raw = clamp(raw_value, -MAX_CMD_RAW, MAX_CMD_RAW)

    last_command_ms = time.ticks_ms()
    timeout_announced = False
    last_source = source
    notify("LOCAL_SET={}".format(local_cmd_raw))
    return True

def update_local_logic():
    global local_target_pct, test_running

    if fault_latched or not armed:
        test_running = False
        local_target_pct = 0
        return

    if local_cmd_mode == CMD_STOP:
        test_running = False
        local_target_pct = 0
    elif local_cmd_mode == CMD_TARGET:
        test_running = False
        local_target_pct = raw_to_pct(local_cmd_raw)
    elif local_cmd_mode == CMD_TEST:
        test_running = True
    else:
        test_running = False
        local_target_pct = 0

def update_test_generator():
    global test_raw, test_dir, local_target_pct, last_test_ms
    now = time.ticks_ms()
    if not test_running:
        return
    if time.ticks_diff(now, last_test_ms) < TEST_UPDATE_MS:
        return
    last_test_ms = now
    test_raw += test_dir * TEST_STEP_RAW
    if test_raw >= MAX_CMD_RAW:
        test_raw = MAX_CMD_RAW
        test_dir = -1
    elif test_raw <= -MAX_CMD_RAW:
        test_raw = -MAX_CMD_RAW
        test_dir = +1
    local_target_pct = raw_to_pct(test_raw)

def update_motor_ramp():
    global local_current_pct, last_ramp_ms
    now = time.ticks_ms()
    if time.ticks_diff(now, last_ramp_ms) < RAMP_INTERVAL_MS:
        return
    last_ramp_ms = now
    local_current_pct = ramp_toward(local_current_pct, local_target_pct)
    apply_motor_local_signed(local_current_pct)

# =========================================================
# I2C MASTER SIDE
# =========================================================
def make_i2c_master():
    last_err = None
    for bus_id in (0, 1):
        try:
            i2c_obj = I2C(bus_id, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=100000)
            print("[I2C] Master OK en bus", bus_id)
            return i2c_obj
        except Exception as e:
            last_err = e
    raise last_err

def ensure_i2c_master():
    global i2c
    if i2c is not None:
        return True
    try:
        i2c = make_i2c_master()
        try:
            devs = i2c.scan()
            print("[I2C] Scan:", [hex(x) for x in devs])
        except Exception as e:
            print("[I2C] Scan error:", e)
        return True
    except Exception as e:
        print("[I2C] Error master:", e)
        return False

def build_packet_flags():
    flags = 0
    if armed:
        flags |= PKT_FLAG_ARMED
    if fault_latched:
        flags |= PKT_FLAG_FAULT
    if test_running:
        flags |= PKT_FLAG_TEST
    return flags & 0xFF

def next_frame_seq():
    global frame_seq
    frame_seq = (frame_seq + 1) & 0xFF
    return frame_seq

def make_packet(cmd_mode, raw_value, seq):
    raw_value = clamp(int(raw_value), -MAX_CMD_RAW, MAX_CMD_RAW)
    lo = raw_value & 0xFF
    hi = (raw_value >> 8) & 0xFF
    flags = build_packet_flags()
    base = bytes([
        PKT_PREAMBLE,
        seq,
        cmd_mode & 0xFF,
        lo,
        hi,
        flags
    ])
    ck = xor_checksum(base)
    return base + bytes([ck])

def send_packet_to_addr(addr, cmd_mode, raw_value, seq, retries=3):
    if i2c is None:
        return False
    pkt = make_packet(cmd_mode, raw_value, seq)
    for _ in range(retries):
        try:
            i2c.writeto(addr, pkt)
            return True
        except Exception:
            time.sleep_ms(3)
    return False

def refresh_hb_remote(force=False):
    global hb_remote_online, hb_remote_online_prev, last_hb_send_ms
    if i2c is None:
        return False
    now = time.ticks_ms()
    if (not force) and time.ticks_diff(now, last_hb_send_ms) < SLAVE_REFRESH_MS:
        return hb_remote_online
    last_hb_send_ms = now
    seq = next_frame_seq()
    ok = send_packet_to_addr(HB_REMOTE_ADDR, hb_remote_cmd_mode, hb_remote_raw, seq, retries=3)
    hb_remote_online = ok
    if hb_remote_online_prev is None or hb_remote_online_prev != ok:
        notify("HB_REMOTE {} @ {}".format("ONLINE" if ok else "OFFLINE", hex(HB_REMOTE_ADDR)))
        hb_remote_online_prev = ok
    return ok

def _decode_manip_reply(buf):
    try:
        if not buf:
            return ""
        if isinstance(buf, bytes):
            raw = buf
        else:
            raw = bytes(buf)
        text = raw.split(b"\x00", 1)[0].decode("utf-8", "ignore").strip()
        return text
    except Exception:
        return ""


def relay_manip_command(cmdline):
    global last_manip_tx_ms
    if not ensure_i2c_master():
        return False, "ERR NO_I2C"

    try:
        payload = cmdline.strip() + "\n"
        i2c.writeto(MANIP_ADDR, payload.encode())
        last_manip_tx_ms = time.ticks_ms()
        time.sleep_ms(15)

        try:
            resp_raw = i2c.readfrom(MANIP_ADDR, 96)
            resp = _decode_manip_reply(resp_raw)
        except Exception as e:
            resp = ""
            notify("MANIP_READ_ERR:{}".format(e))

        if resp:
            return True, resp
        return True, "MANIP_SENT:{}".format(cmdline.strip())

    except Exception as e:
        return False, "ERR MANIP_I2C:{}".format(e)

# =========================================================
# I2C SLAVE SIDE (solo para modos SLAVE1/2/3)
# =========================================================
def i2c_irq_handler(i2c_target_obj):
    global i2c_target_pending, i2c_target_last_snapshot
    try:
        irq_obj = i2c_target_obj.irq()
        flags = irq_obj.flags()
        if hasattr(I2CTargetClass, "IRQ_END_WRITE") and (flags & I2CTargetClass.IRQ_END_WRITE):
            i2c_target_last_snapshot = bytes(i2c_target_mem[:PKT_LEN])
            i2c_target_pending = True
    except Exception:
        pass

def init_i2c_target_for_slave():
    global i2c_target, i2c_target_supported, I2CTargetClass
    try:
        from machine import I2CTarget as I2CTargetImported
        I2CTargetClass = I2CTargetImported
    except Exception:
        notify("[I2C] I2CTarget no disponible en esta build")
        i2c_target_supported = False
        return False

    addr = SLAVE_ADDR_MAP[mode_code]
    last_err = None
    for bus_id in (0, 1):
        try:
            i2c_target = I2CTargetImported(
                bus_id,
                addr,
                mem=i2c_target_mem,
                mem_addrsize=0,
                scl=Pin(SCL_PIN),
                sda=Pin(SDA_PIN)
            )
            try:
                i2c_target.irq(i2c_irq_handler)
            except Exception:
                pass
            i2c_target_supported = True
            notify("[I2C] Target OK en bus {} addr {}".format(bus_id, hex(addr)))
            return True
        except Exception as e:
            last_err = e
    notify("[I2C] Error target: {}".format(last_err))
    i2c_target_supported = False
    return False

def process_i2c_target_packet():
    global i2c_target_pending, last_i2c_packet_ms, last_i2c_seq
    global armed, local_cmd_mode, local_cmd_raw, test_running

    if not i2c_target_pending:
        return

    i2c_target_pending = False
    buf = i2c_target_last_snapshot
    if len(buf) != PKT_LEN:
        return

    if buf[0] != PKT_PREAMBLE:
        return

    if xor_checksum(buf[:6]) != buf[6]:
        return

    seq = buf[1]
    cmd_mode = buf[2]
    raw_value = signed16_from_lo_hi(buf[3], buf[4])
    flags = buf[5]

    last_i2c_packet_ms = time.ticks_ms()
    last_i2c_seq = seq

    # El slave obedece explicitamente el flag ARMED del master.
    armed = bool(flags & PKT_FLAG_ARMED)

    if flags & PKT_FLAG_FAULT:
        local_cmd_mode = CMD_STOP
        local_cmd_raw = 0
        test_running = False
        return

    if cmd_mode == CMD_STOP:
        local_cmd_mode = CMD_STOP
        local_cmd_raw = 0
        test_running = False
    elif cmd_mode == CMD_TEST:
        local_cmd_mode = CMD_TEST
        local_cmd_raw = 0
        test_running = True
    elif cmd_mode == CMD_TARGET:
        local_cmd_mode = CMD_TARGET
        local_cmd_raw = clamp(raw_value, -MAX_CMD_RAW, MAX_CMD_RAW)
        test_running = False
    else:
        local_cmd_mode = CMD_STOP
        local_cmd_raw = 0
        test_running = False

def update_slave_timeout():
    global armed, local_cmd_mode, local_cmd_raw, test_running
    now = time.ticks_ms()
    if time.ticks_diff(now, last_i2c_packet_ms) > COMM_TIMEOUT_MS:
        armed = False
        local_cmd_mode = CMD_STOP
        local_cmd_raw = 0
        test_running = False

# =========================================================
# SERIAL INPUTS
# =========================================================
def poll_usb_lines():
    global usb_rx_buffer
    if usb_poll is None:
        return
    try:
        while usb_poll.poll(0):
            ch = sys.stdin.read(1)
            if not ch:
                break
            if ch == "\r":
                continue
            if ch == "\n":
                line = usb_rx_buffer.strip()
                usb_rx_buffer = ""
                if line:
                    claim_usb_priority()
                    handle_serial_line(line, source="USB")
            else:
                usb_rx_buffer += ch
    except Exception:
        pass

def poll_uart_lines():
    global uart_rx_buffer
    if serial_uart is None:
        return
    try:
        while serial_uart.any():
            data = serial_uart.read(1)
            if not data:
                break
            try:
                ch = data.decode()
            except Exception:
                continue
            if ch == "\r":
                continue
            if ch == "\n":
                line = uart_rx_buffer.strip()
                uart_rx_buffer = ""
                if line:
                    handle_serial_line(line, source="UART")
            else:
                uart_rx_buffer += ch
    except Exception:
        pass

# =========================================================
# SERIAL COMMANDS (maestro)
# =========================================================
def send_hb_command(cmd_mode, raw_value, source="SERIAL"):
    global hb_remote_cmd_mode, hb_remote_raw, last_command_ms, timeout_announced, last_source

    if fault_latched:
        notify("FAULT_LATCHED")
        return False

    if cmd_mode == CMD_STOP:
        hb_remote_cmd_mode = CMD_STOP
        hb_remote_raw = 0
        last_command_ms = time.ticks_ms()
        timeout_announced = False
        last_source = source
        refresh_hb_remote(force=True)
        notify("HB_STOP")
        return True

    if not require_arm_for_motion():
        return False

    hb_remote_cmd_mode = cmd_mode
    hb_remote_raw = clamp(raw_value, -MAX_CMD_RAW, MAX_CMD_RAW)
    last_command_ms = time.ticks_ms()
    timeout_announced = False
    last_source = source
    refresh_hb_remote(force=True)
    notify("HB_SET={}".format(hb_remote_raw))
    return True

def handle_dual_frame(line, source="SERIAL"):
    global last_command_ms, timeout_announced, last_source
    if fault_latched:
        notify("FAULT_LATCHED")
        return
    try:
        l_mode, l_raw, hb_mode, hb_raw = parse_dual_frame(line)
    except Exception as e:
        notify("FRAME_ERROR:{}".format(e))
        return

    frame_needs_arm = (l_mode != CMD_STOP) or (hb_mode != CMD_STOP)
    if frame_needs_arm and not require_arm_for_motion():
        return

    # set local
    if l_mode == CMD_STOP:
        local_ok = set_local_command(CMD_STOP, 0, source)
    else:
        local_ok = set_local_command(l_mode, l_raw, source)

    # set hb remote
    if hb_mode == CMD_STOP:
        hb_ok = send_hb_command(CMD_STOP, 0, source)
    else:
        hb_ok = send_hb_command(hb_mode, hb_raw, source)

    last_command_ms = time.ticks_ms()
    timeout_announced = False
    last_source = source
    notify("FRAME_OK:{}".format(line))
    return local_ok and hb_ok

def handle_serial_line(line, source="SERIAL"):
    global armed, timeout_announced, last_command_ms, last_source

    line = line.strip()
    if not line:
        return
    u = line.upper()

    if "," in line and not u.startswith("MANIP ") and not u.startswith("M "):
        handle_dual_frame(line, source)
        return

    parts = line.split()
    cmd = parts[0].upper()

    if cmd == "PING":
        notify("PONG")
        return

    if cmd in ("STATUS", "STATE", "STATE?"):
        notify(status_text())
        return

    if cmd in ("ARM",):
        armed = True
        refresh_hb_remote(force=True)
        notify("ARMED")
        return

    if cmd in ("DISARM",):
        armed = False
        stop_all_hard()
        notify("DISARMED")
        return

    if cmd in ("CLRFAULT", "RESETFAULT", "FAULTRESET"):
        clear_fault()
        return

    if cmd == "SCAN":
        if ensure_i2c_master():
            try:
                devs = i2c.scan()
                notify("I2C_SCAN:" + ",".join([hex(x) for x in devs]))
            except Exception as e:
                notify("ERR SCAN:{}".format(e))
        return

    if cmd in ("STOPALL", "ALL_STOP"):
        stop_all_hard()
        notify("STOPALL_OK")
        return

    if cmd == "LOCAL":
        if len(parts) < 2:
            notify("ERR LOCAL ARG")
            return
        kind, val = parse_single_token(parts[1])
        if kind != "NODE":
            notify("ERR LOCAL TOKEN")
            return
        set_local_command(val[0], val[1], source)
        return

    if cmd == "HB":
        if len(parts) < 2:
            notify("ERR HB ARG")
            return
        kind, val = parse_single_token(parts[1])
        if kind != "NODE":
            notify("ERR HB TOKEN")
            return
        send_hb_command(val[0], val[1], source)
        return

    if cmd in ("MANIP", "M"):
        if len(parts) < 2:
            notify("ERR MANIP ARG")
            return
        subline = line.split(None, 1)[1]
        ok, msg = relay_manip_command(subline)
        notify(msg)
        return

    # Alias directos al manipulador
    if cmd in MANIP_FIRST_WORDS:
        ok, msg = relay_manip_command(line)
        notify(msg)
        return

    if cmd == "HELP":
        notify("CMDS: PING STATUS ARM DISARM CLRFAULT SCAN STOPALL")
        notify("CMDS: LOCAL <F|B|S|T|raw>")
        notify("CMDS: HB <F|B|S|T|raw>")
        notify("CMDS: <local>,<hb>   e.g. F,B   or   120,-80")
        notify("CMDS: MANIP <manip_cmd>")
        notify("MANIP: HOME_ALL HOME_CODO HOME_MUNECA BASE_GOTO x BASE_REL x CODO_GOTO x CODO_REL x MUNECA_GOTO x MUNECA_REL x POSE b c m")
        return

    notify("ERR UNKNOWN_CMD")

# =========================================================
# TIMEOUTS
# =========================================================
def update_master_timeout():
    global timeout_announced
    now = time.ticks_ms()
    if time.ticks_diff(now, last_command_ms) > COMM_TIMEOUT_MS:
        if local_cmd_mode != CMD_STOP or hb_remote_cmd_mode != CMD_STOP or local_target_pct != 0 or local_current_pct != 0:
            stop_all_hard()
            if not timeout_announced:
                notify("TIMEOUT_STOP")
                timeout_announced = True

# =========================================================
# BOOT Y LOOP
# =========================================================
def boot_mode_setup():
    global mode_code, mode_name, boot_b2, boot_b1, boot_b0
    mode_code, boot_b2, boot_b1, boot_b0 = read_switches()
    mode_name = MODE_NAMES.get(mode_code, "UNKNOWN")
    print("[BOOT] DIP S2S1S0 = {}{}{}".format(boot_b2, boot_b1, boot_b0))
    print("[BOOT] Modo = {}".format(mode_name))

    if is_master_mode():
        init_serial_inputs()
        ensure_i2c_master()
        notify("[READY] MASTER SERIAL + I2C")
        notify(status_text())
    elif is_slave_mode():
        init_i2c_target_for_slave()
        notify("[READY] SLAVE")
        notify(status_text())
    else:
        notify("[READY] TEST")
        notify(status_text())


def main_loop():
    global local_target_pct

    while True:
        update_button()

        if is_master_mode():
            poll_usb_lines()
            poll_uart_lines()
            refresh_hb_remote(force=False)
            update_master_timeout()
        elif is_slave_mode():
            process_i2c_target_packet()
            update_slave_timeout()
        else:
            # test standalone local
            if test_running:
                pass

        update_local_logic()
        update_test_generator()
        update_motor_ramp()
        update_led()
        time.sleep_ms(2)


def main():
    init_common_pins()
    boot_mode_setup()
    main_loop()


main()


