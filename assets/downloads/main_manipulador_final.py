from machine import Pin
from time import sleep_ms, sleep_us
import time
import sys
import uselect

# =====================================================
# ESP32-C3 SuperMini + CL57T
# ESCLAVO I2C + CONSOLA SERIAL DEL MANIPULADOR
#
# CORRECCIÓN IMPORTANTE:
# - SÍ se mantiene la compensación de muñeca cuando se mueve el codo
# - PERO esa compensación ya NO se contabiliza como ángulo lógico de Q2
#
# Modelo correcto:
#   pos_muneca        = ángulo lógico de la muñeca (lo que el usuario ve/comanda)
#   pos_muneca_motor  = posición física acumulada del motor de muñeca
#
# Cuando se mueve el codo:
# - el motor de muñeca se compensa para mantener la orientación
# - pos_muneca_motor cambia
# - pos_muneca NO cambia
#
# Cuando se mueve la muñeca por comando:
# - cambian ambos: pos_muneca y pos_muneca_motor
#
# Además:
# - acepta comandos por I2C
# - acepta comandos por USB serial / stdin
# =====================================================

BTN_PIN = 0
SW1_PIN = 1
LED_PIN = 2
SW2_PIN = 3
SW3_PIN = 4
PUL_MUNECA_PIN = 5
DIR_MUNECA_PIN = 6
PUL_CODO_PIN = 7
SDA_PIN = 8
SCL_PIN = 9
DIR_CODO_PIN = 10
PUL_BASE_PIN = 20
DIR_BASE_PIN = 21

I2C_ADDR = 0x0B
I2C_BUF_LEN = 96

BTN_DEBOUNCE_MS = 35
BTN_LONG_MS = 1200

DIR_A = 1
DIR_B = 0
JOINT_POS = 1
JOINT_NEG = -1

PULSE_JOG_US = 1800
PULSE_HOME_FAST_US = 1800
PULSE_HOME_SLOW_US = 3200
DIR_SETTLE_US = 200

FAST_BLOCK = 8
BACKOFF_STEPS = 220
FINAL_CLEARANCE_STEPS = 120
MAX_SEARCH_CODO = 12000
MAX_SEARCH_MUNECA = 12000
MAX_RELEASE_STEPS = 1500

ENABLE_BASE_RAMP = True
ENABLE_CODO_RAMP = True
ENABLE_MUNECA_RAMP = True

BASE_RAMP_START_US = 2500
BASE_RAMP_CRUISE_US = 1600
BASE_RAMP_END_US = 2500
BASE_ACCEL_STEPS = 1500
BASE_DECEL_STEPS = 1500

BASE_SPLIT_CROSS_ZERO = True
BASE_SPLIT_MIN_TRAVEL_DEG = 60.0
BASE_ZERO_DEG = 0.0

CODO_RAMP_START_US = 2500
CODO_RAMP_CRUISE_US = 1600
CODO_RAMP_END_US = 2500
CODO_ACCEL_STEPS = 1500
CODO_DECEL_STEPS = 1500

MUNECA_RAMP_START_US = 2500
MUNECA_RAMP_CRUISE_US = 1600
MUNECA_RAMP_END_US = 2500
MUNECA_ACCEL_STEPS = 1500
MUNECA_DECEL_STEPS = 1500

# Mantener compensación física
COMP_RATIO = 1.0
COMPENSATE_MUNECA_WITH_CODO = True

BASE_STEPS_PER_REV = 10000
ARM_STEPS_PER_REV = 25000

BASE_DEG_PER_STEP = 360.0 / BASE_STEPS_PER_REV
BASE_STEPS_PER_DEG = BASE_STEPS_PER_REV / 360.0
ARM_DEG_PER_STEP = 360.0 / ARM_STEPS_PER_REV
ARM_STEPS_PER_DEG = ARM_STEPS_PER_REV / 360.0

BASE_MIN_DEG = -80.0
BASE_MAX_DEG = 80.0
CODO_MIN_DEG = 0.0
CODO_MAX_DEG = 136.5
MUNECA_MIN_DEG = -220.0
MUNECA_MAX_DEG = 0.0

SERIAL_POLL_MS = 0

def raw_dir_base(signo_joint):
    return DIR_A if signo_joint == JOINT_POS else DIR_B

def raw_dir_codo(signo_joint):
    return DIR_A if signo_joint == JOINT_POS else DIR_B

def raw_dir_muneca(signo_joint):
    return DIR_B if signo_joint == JOINT_POS else DIR_A

HOME_SIGN_CODO = JOINT_NEG
AWAY_SIGN_CODO = JOINT_POS
HOME_SIGN_MUNECA = JOINT_POS
AWAY_SIGN_MUNECA = JOINT_NEG

pos_base = 0
pos_codo = 0

# Ángulo lógico de Q2 (lo que se reporta al usuario)
pos_muneca = 0

# Posición física acumulada del motor de muñeca
pos_muneca_motor = 0

busy = False

btn_last_raw = 1
btn_stable = 1
btn_last_change_ms = time.ticks_ms()
btn_press_ms = 0

I2CTargetClass = None
i2c_target = None
i2c_target_supported = False
i2c_target_mem = bytearray(I2C_BUF_LEN)
i2c_target_pending = False
i2c_target_last_snapshot = bytes(I2C_BUF_LEN)
last_i2c_cmd_ms = time.ticks_ms()

stdin_poll = None
last_serial_cmd_ms = time.ticks_ms()

DIR_BASE = Pin(DIR_BASE_PIN, Pin.OUT)
PUL_BASE = Pin(PUL_BASE_PIN, Pin.OUT)
DIR_CODO = Pin(DIR_CODO_PIN, Pin.OUT)
PUL_CODO = Pin(PUL_CODO_PIN, Pin.OUT)
DIR_MUNECA = Pin(DIR_MUNECA_PIN, Pin.OUT)
PUL_MUNECA = Pin(PUL_MUNECA_PIN, Pin.OUT)

LED = Pin(LED_PIN, Pin.OUT)
BTN = Pin(BTN_PIN, Pin.IN, Pin.PULL_UP)
SW2 = Pin(SW2_PIN, Pin.IN)
SW3 = Pin(SW3_PIN, Pin.IN)

def set_led(val):
    LED.value(1 if val else 0)

def init_pins():
    PUL_BASE.value(1)
    PUL_CODO.value(1)
    PUL_MUNECA.value(1)
    DIR_BASE.value(DIR_A)
    DIR_CODO.value(DIR_A)
    DIR_MUNECA.value(DIR_A)
    set_led(0)

def switch_active(sw_pin):
    return sw_pin.value() == 0

def switch_active_confirmed(sw_pin, confirm_ms=5):
    if sw_pin.value() == 0:
        sleep_ms(confirm_ms)
        return sw_pin.value() == 0
    return False

def pulse_step(pul_pin, pulse_us):
    pul_pin.value(0)
    sleep_us(pulse_us)
    pul_pin.value(1)
    sleep_us(pulse_us)

def pulse_step_dual(pul1, pul2, pulse_us):
    pul1.value(0)
    pul2.value(0)
    sleep_us(pulse_us)
    pul1.value(1)
    pul2.value(1)
    sleep_us(pulse_us)

def arm_deg_to_steps(deg):
    return int(round(deg * ARM_STEPS_PER_DEG))

def arm_steps_to_deg(steps):
    return steps * ARM_DEG_PER_STEP

def base_deg_to_steps(deg):
    return int(round(deg * BASE_STEPS_PER_DEG))

def base_steps_to_deg(steps):
    return steps * BASE_DEG_PER_STEP

def checar_limite(nombre, target_deg, min_deg, max_deg):
    if min_deg is not None and target_deg < min_deg:
        raise ValueError("{}: {:.3f} menor que limite {:.3f}".format(nombre, target_deg, min_deg))
    if max_deg is not None and target_deg > max_deg:
        raise ValueError("{}: {:.3f} mayor que limite {:.3f}".format(nombre, target_deg, max_deg))

def angulo_actual_base():
    return base_steps_to_deg(pos_base)

def angulo_actual_codo():
    return arm_steps_to_deg(pos_codo)

def angulo_actual_muneca():
    return arm_steps_to_deg(pos_muneca)

def angulo_motor_muneca():
    return arm_steps_to_deg(pos_muneca_motor)

def leer_switches():
    return "SW2={} SW3={}".format(SW2.value(), SW3.value())

def estado_actual_str():
    # Mantengo el formato principal igual para compatibilidad
    return (
        "BASE={:.3f}deg({}) | CODO={:.3f}deg({}) | MUNECA={:.3f}deg({}) | {}"
        .format(
            angulo_actual_base(), pos_base,
            angulo_actual_codo(), pos_codo,
            angulo_actual_muneca(), pos_muneca,
            leer_switches()
        )
    )

def estado_extendido_str():
    return (
        "BASE={:.3f}deg({}) | CODO={:.3f}deg({}) | MUNECA_LOG={:.3f}deg({}) | MUNECA_MOTOR={:.3f}deg({}) | {}"
        .format(
            angulo_actual_base(), pos_base,
            angulo_actual_codo(), pos_codo,
            angulo_actual_muneca(), pos_muneca,
            angulo_motor_muneca(), pos_muneca_motor,
            leer_switches()
        )
    )

def log(msg):
    print(msg)

def lerp_int(a, b, t_num, t_den):
    if t_den <= 0:
        return int(b)
    return int(round(a + ((b - a) * float(t_num) / float(t_den))))

def compute_ramp_pulse_us(step_idx, total_steps, start_us, cruise_us, end_us, accel_steps, decel_steps):
    if total_steps <= 1:
        return int(cruise_us)
    accel_steps = max(0, int(accel_steps))
    decel_steps = max(0, int(decel_steps))
    if accel_steps + decel_steps > total_steps:
        half = total_steps // 2
        accel_steps = half
        decel_steps = total_steps - half
    if accel_steps > 0 and step_idx < accel_steps:
        return lerp_int(start_us, cruise_us, step_idx, accel_steps)
    decel_start = total_steps - decel_steps
    if decel_steps > 0 and step_idx >= decel_start:
        idx = step_idx - decel_start
        return lerp_int(cruise_us, end_us, idx, decel_steps)
    return int(cruise_us)

class MotionAbort(Exception):
    pass

def safety_check_for_axis(axis_name):
    if switch_active_confirmed(SW2, 1):
        raise MotionAbort("{} abortado: SW2 activo".format(axis_name))
    if switch_active_confirmed(SW3, 1):
        raise MotionAbort("{} abortado: SW3 activo".format(axis_name))

def mover_base_joint(signo_joint, pasos, pulse_us=PULSE_JOG_US, safety_stop=True):
    global pos_base
    DIR_BASE.value(raw_dir_base(signo_joint))
    sleep_us(DIR_SETTLE_US)
    for _ in range(pasos):
        if safety_stop:
            safety_check_for_axis("BASE")
        pulse_step(PUL_BASE, pulse_us)
    pos_base = pos_base + pasos if signo_joint == JOINT_POS else pos_base - pasos

def mover_base_joint_ramp(signo_joint, pasos, start_us=BASE_RAMP_START_US, cruise_us=BASE_RAMP_CRUISE_US,
                          end_us=BASE_RAMP_END_US, accel_steps=BASE_ACCEL_STEPS, decel_steps=BASE_DECEL_STEPS,
                          safety_stop=True):
    global pos_base
    if pasos <= 0:
        return
    DIR_BASE.value(raw_dir_base(signo_joint))
    sleep_us(DIR_SETTLE_US)
    for i in range(pasos):
        if safety_stop:
            safety_check_for_axis("BASE")
        current_us = compute_ramp_pulse_us(i, pasos, start_us, cruise_us, end_us, accel_steps, decel_steps)
        pulse_step(PUL_BASE, current_us)
    pos_base = pos_base + pasos if signo_joint == JOINT_POS else pos_base - pasos

def mover_muneca_joint(signo_joint, pasos, pulse_us=PULSE_JOG_US, safety_stop=True):
    global pos_muneca, pos_muneca_motor
    DIR_MUNECA.value(raw_dir_muneca(signo_joint))
    sleep_us(DIR_SETTLE_US)
    for _ in range(pasos):
        if safety_stop:
            safety_check_for_axis("MUNECA")
        pulse_step(PUL_MUNECA, pulse_us)
    if signo_joint == JOINT_POS:
        pos_muneca += pasos
        pos_muneca_motor += pasos
    else:
        pos_muneca -= pasos
        pos_muneca_motor -= pasos

def mover_muneca_joint_ramp(signo_joint, pasos, start_us=MUNECA_RAMP_START_US, cruise_us=MUNECA_RAMP_CRUISE_US,
                            end_us=MUNECA_RAMP_END_US, accel_steps=MUNECA_ACCEL_STEPS,
                            decel_steps=MUNECA_DECEL_STEPS, safety_stop=True):
    global pos_muneca, pos_muneca_motor
    if pasos <= 0:
        return
    DIR_MUNECA.value(raw_dir_muneca(signo_joint))
    sleep_us(DIR_SETTLE_US)
    for i in range(pasos):
        if safety_stop:
            safety_check_for_axis("MUNECA")
        current_us = compute_ramp_pulse_us(i, pasos, start_us, cruise_us, end_us, accel_steps, decel_steps)
        pulse_step(PUL_MUNECA, current_us)
    if signo_joint == JOINT_POS:
        pos_muneca += pasos
        pos_muneca_motor += pasos
    else:
        pos_muneca -= pasos
        pos_muneca_motor -= pasos

# =====================================================
# CODO COMPENSADO:
# - mueve el codo
# - mueve también el motor de muñeca para compensar
# - PERO NO cambia el ángulo lógico de muñeca
# =====================================================
def mover_codo_compensado_joint(signo_joint, pasos, pulse_us=PULSE_JOG_US, safety_stop=True):
    global pos_codo, pos_muneca_motor
    dir_codo = raw_dir_codo(signo_joint)
    dir_muneca = raw_dir_muneca(signo_joint)
    DIR_CODO.value(dir_codo)
    DIR_MUNECA.value(dir_muneca)
    sleep_us(DIR_SETTLE_US)

    pasos_muneca = int(round(pasos * COMP_RATIO))

    if pasos_muneca == pasos:
        for _ in range(pasos):
            if safety_stop:
                safety_check_for_axis("CODO")
            pulse_step_dual(PUL_CODO, PUL_MUNECA, pulse_us)
    else:
        acc = 0.0
        emitted_m = 0
        for _ in range(pasos):
            if safety_stop:
                safety_check_for_axis("CODO")
            PUL_CODO.value(0)
            acc += COMP_RATIO
            step_m = False
            if acc >= 1.0:
                PUL_MUNECA.value(0)
                step_m = True
                acc -= 1.0
                emitted_m += 1
            sleep_us(pulse_us)
            PUL_CODO.value(1)
            if step_m:
                PUL_MUNECA.value(1)
            sleep_us(pulse_us)
            if not step_m:
                PUL_MUNECA.value(1)
        pasos_muneca = emitted_m

    if signo_joint == JOINT_POS:
        pos_codo += pasos
        pos_muneca_motor += pasos_muneca
    else:
        pos_codo -= pasos
        pos_muneca_motor -= pasos_muneca

def mover_codo_compensado_joint_ramp(signo_joint, pasos, start_us=CODO_RAMP_START_US, cruise_us=CODO_RAMP_CRUISE_US,
                                     end_us=CODO_RAMP_END_US, accel_steps=CODO_ACCEL_STEPS,
                                     decel_steps=CODO_DECEL_STEPS, safety_stop=True):
    global pos_codo, pos_muneca_motor
    if pasos <= 0:
        return
    dir_codo = raw_dir_codo(signo_joint)
    dir_muneca = raw_dir_muneca(signo_joint)
    DIR_CODO.value(dir_codo)
    DIR_MUNECA.value(dir_muneca)
    sleep_us(DIR_SETTLE_US)

    acc = 0.0
    emitted_m = 0

    for i in range(pasos):
        if safety_stop:
            safety_check_for_axis("CODO")
        current_us = compute_ramp_pulse_us(i, pasos, start_us, cruise_us, end_us, accel_steps, decel_steps)

        PUL_CODO.value(0)
        acc += COMP_RATIO
        step_m = False
        if acc >= 1.0:
            PUL_MUNECA.value(0)
            step_m = True
            acc -= 1.0
            emitted_m += 1

        sleep_us(current_us)

        PUL_CODO.value(1)
        if step_m:
            PUL_MUNECA.value(1)

        sleep_us(current_us)

        if not step_m:
            PUL_MUNECA.value(1)

    if signo_joint == JOINT_POS:
        pos_codo += pasos
        pos_muneca_motor += emitted_m
    else:
        pos_codo -= pasos
        pos_muneca_motor -= emitted_m

def mover_codo_home(signo_joint, pasos, pulse_us):
    # Durante home de codo, se mantiene compensación física
    mover_codo_compensado_joint(signo_joint, pasos, pulse_us, safety_stop=False)

def mover_muneca_home(signo_joint, pasos, pulse_us):
    mover_muneca_joint(signo_joint, pasos, pulse_us, safety_stop=False)

def mover_base_rel_deg(delta_deg, pulse_us=PULSE_JOG_US, safety_stop=True):
    if delta_deg == 0:
        return
    target_deg = angulo_actual_base() + delta_deg
    checar_limite("BASE", target_deg, BASE_MIN_DEG, BASE_MAX_DEG)
    pasos = abs(base_deg_to_steps(delta_deg))
    signo = JOINT_POS if delta_deg > 0 else JOINT_NEG
    if ENABLE_BASE_RAMP:
        mover_base_joint_ramp(signo, pasos, safety_stop=safety_stop)
    else:
        mover_base_joint(signo, pasos, pulse_us, safety_stop=safety_stop)

def ir_base_a_deg(target_deg, pulse_us=PULSE_JOG_US, safety_stop=True):
    checar_limite("BASE", target_deg, BASE_MIN_DEG, BASE_MAX_DEG)
    current_deg = angulo_actual_base()
    if (BASE_SPLIT_CROSS_ZERO and (current_deg * target_deg < 0) and
        (abs(target_deg - current_deg) >= BASE_SPLIT_MIN_TRAVEL_DEG)):
        mover_base_rel_deg(BASE_ZERO_DEG - current_deg, pulse_us, safety_stop=safety_stop)
        mover_base_rel_deg(target_deg - BASE_ZERO_DEG, pulse_us, safety_stop=safety_stop)
        return
    mover_base_rel_deg(target_deg - current_deg, pulse_us, safety_stop=safety_stop)

def mover_codo_rel_deg(delta_deg, pulse_us=PULSE_JOG_US, safety_stop=True):
    if delta_deg == 0:
        return
    target_deg = angulo_actual_codo() + delta_deg
    checar_limite("CODO", target_deg, CODO_MIN_DEG, CODO_MAX_DEG)
    pasos = abs(arm_deg_to_steps(delta_deg))
    signo = JOINT_POS if delta_deg > 0 else JOINT_NEG
    if ENABLE_CODO_RAMP:
        mover_codo_compensado_joint_ramp(signo, pasos, safety_stop=safety_stop)
    else:
        mover_codo_compensado_joint(signo, pasos, pulse_us, safety_stop=safety_stop)

def ir_codo_a_deg(target_deg, pulse_us=PULSE_JOG_US, safety_stop=True):
    mover_codo_rel_deg(target_deg - angulo_actual_codo(), pulse_us, safety_stop=safety_stop)

def mover_muneca_rel_deg(delta_deg, pulse_us=PULSE_JOG_US, safety_stop=True):
    if delta_deg == 0:
        return
    target_deg = angulo_actual_muneca() + delta_deg
    checar_limite("MUNECA", target_deg, MUNECA_MIN_DEG, MUNECA_MAX_DEG)
    pasos = abs(arm_deg_to_steps(delta_deg))
    signo = JOINT_POS if delta_deg > 0 else JOINT_NEG
    if ENABLE_MUNECA_RAMP:
        mover_muneca_joint_ramp(signo, pasos, safety_stop=safety_stop)
    else:
        mover_muneca_joint(signo, pasos, pulse_us, safety_stop=safety_stop)

def ir_muneca_a_deg(target_deg, pulse_us=PULSE_JOG_US, safety_stop=True):
    mover_muneca_rel_deg(target_deg - angulo_actual_muneca(), pulse_us, safety_stop=safety_stop)

def ir_pose(base_deg=None, codo_deg=None, muneca_deg=None, pulse_us=PULSE_JOG_US, safety_stop=True):
    if base_deg is not None:
        ir_base_a_deg(base_deg, pulse_us, safety_stop=safety_stop)
    if codo_deg is not None:
        ir_codo_a_deg(codo_deg, pulse_us, safety_stop=safety_stop)
    if muneca_deg is not None:
        ir_muneca_a_deg(muneca_deg, pulse_us, safety_stop=safety_stop)

def liberar_switch_si_esta_activo(nombre, move_fn, away_sign, sw_pin, pulse_us, max_steps):
    if not switch_active(sw_pin):
        return True, 0
    log(nombre + ": switch ya activo, liberando...")
    pasos = 0
    while pasos < max_steps:
        if not switch_active_confirmed(sw_pin):
            return True, pasos
        move_fn(away_sign, 1, pulse_us)
        pasos += 1
    return False, pasos

def buscar_switch(nombre, move_fn, home_sign, sw_pin, pulse_us, max_steps, block_steps=1):
    pasos = 0
    while pasos < max_steps:
        if switch_active_confirmed(sw_pin):
            return True, pasos
        n = block_steps
        if pasos + n > max_steps:
            n = max_steps - pasos
        move_fn(home_sign, n, pulse_us)
        pasos += n
    if switch_active_confirmed(sw_pin):
        return True, pasos
    return False, pasos

def home_muneca(reset_pos=True):
    global pos_muneca, pos_muneca_motor
    log("\n=== HOME MUNECA (SW3) ===")
    set_led(1)
    ok, pasos = liberar_switch_si_esta_activo("MUNECA", mover_muneca_home, AWAY_SIGN_MUNECA, SW3,
                                              PULSE_HOME_SLOW_US, MAX_RELEASE_STEPS)
    log("Liberacion inicial muneca: {} pasos".format(pasos))
    if not ok:
        set_led(0)
        log("ERROR: no se pudo liberar SW3")
        return False
    ok, pasos_fast = buscar_switch("MUNECA", mover_muneca_home, HOME_SIGN_MUNECA, SW3,
                                   PULSE_HOME_FAST_US, MAX_SEARCH_MUNECA, FAST_BLOCK)
    log("Busqueda rapida muneca: {} pasos".format(pasos_fast))
    if not ok:
        set_led(0)
        log("ERROR: muneca no encontro SW3")
        return False
    log("Backoff muneca: {} pasos".format(BACKOFF_STEPS))
    mover_muneca_home(AWAY_SIGN_MUNECA, BACKOFF_STEPS, PULSE_HOME_SLOW_US)
    ok, pasos_slow = buscar_switch("MUNECA", mover_muneca_home, HOME_SIGN_MUNECA, SW3,
                                   PULSE_HOME_SLOW_US, BACKOFF_STEPS + 300, 1)
    log("Busqueda fina muneca: {} pasos".format(pasos_slow))
    if not ok:
        set_led(0)
        log("ERROR: muneca no encontro SW3 en busqueda fina")
        return False
    log("Clearance final muneca: {} pasos".format(FINAL_CLEARANCE_STEPS))
    mover_muneca_home(AWAY_SIGN_MUNECA, FINAL_CLEARANCE_STEPS, PULSE_HOME_SLOW_US)
    if reset_pos:
        pos_muneca = -FINAL_CLEARANCE_STEPS
        pos_muneca_motor = -FINAL_CLEARANCE_STEPS
    set_led(0)
    log("HOME MUNECA OK")
    return True

def home_codo(reset_pos=True):
    global pos_codo
    log("\n=== HOME CODO (SW2) + COMPENSACION MUNECA (NO CONTABILIZADA EN Q2) ===")
    set_led(1)
    ok, pasos = liberar_switch_si_esta_activo("CODO", mover_codo_home, AWAY_SIGN_CODO, SW2,
                                              PULSE_HOME_SLOW_US, MAX_RELEASE_STEPS)
    log("Liberacion inicial codo: {} pasos".format(pasos))
    if not ok:
        set_led(0)
        log("ERROR: no se pudo liberar SW2")
        return False
    ok, pasos_fast = buscar_switch("CODO", mover_codo_home, HOME_SIGN_CODO, SW2,
                                   PULSE_HOME_FAST_US, MAX_SEARCH_CODO, FAST_BLOCK)
    log("Busqueda rapida codo: {} pasos".format(pasos_fast))
    if not ok:
        set_led(0)
        log("ERROR: codo no encontro SW2")
        return False
    log("Backoff codo: {} pasos".format(BACKOFF_STEPS))
    mover_codo_home(AWAY_SIGN_CODO, BACKOFF_STEPS, PULSE_HOME_SLOW_US)
    ok, pasos_slow = buscar_switch("CODO", mover_codo_home, HOME_SIGN_CODO, SW2,
                                   PULSE_HOME_SLOW_US, BACKOFF_STEPS + 300, 1)
    log("Busqueda fina codo: {} pasos".format(pasos_slow))
    if not ok:
        set_led(0)
        log("ERROR: codo no encontro SW2 en busqueda fina")
        return False
    log("Clearance final codo: {} pasos".format(FINAL_CLEARANCE_STEPS))
    mover_codo_home(AWAY_SIGN_CODO, FINAL_CLEARANCE_STEPS, PULSE_HOME_SLOW_US)
    if reset_pos:
        pos_codo = FINAL_CLEARANCE_STEPS
    set_led(0)
    log("HOME CODO OK")
    return True

def home_all():
    global pos_codo, pos_muneca
    log("\n==============================")
    log("INICIANDO HOME COMPLETO")
    log("==============================")
    ok = home_codo(reset_pos=True)
    if not ok:
        log("Abortado: fallo en home de codo")
        return False
    sleep_ms(400)
    ok = home_muneca(reset_pos=True)
    if not ok:
        log("Abortado: fallo en home de muneca")
        return False
    log("\nHOME COMPLETO OK")
    log("pos_codo = {} | pos_muneca = {} | pos_muneca_motor = {}".format(pos_codo, pos_muneca, pos_muneca_motor))
    return True

def write_i2c_response(text):
    global i2c_target_last_snapshot
    try:
        if text is None:
            text = ""
        raw = (str(text).strip() + "\n").encode("utf-8", "ignore")
        n = min(len(raw), I2C_BUF_LEN)
        for i in range(I2C_BUF_LEN):
            i2c_target_mem[i] = 0
        for i in range(n):
            i2c_target_mem[i] = raw[i]
        i2c_target_last_snapshot = bytes(i2c_target_mem[:I2C_BUF_LEN])
    except Exception:
        pass

def clear_i2c_target_buffer():
    global i2c_target_pending, i2c_target_last_snapshot
    for i in range(I2C_BUF_LEN):
        i2c_target_mem[i] = 0
    i2c_target_pending = False
    i2c_target_last_snapshot = bytes(I2C_BUF_LEN)

def i2c_irq_handler(i2c_target_obj):
    global i2c_target_pending, i2c_target_last_snapshot
    try:
        irq_obj = i2c_target_obj.irq()
        flags = irq_obj.flags()
        if hasattr(I2CTargetClass, "IRQ_END_WRITE") and (flags & I2CTargetClass.IRQ_END_WRITE):
            i2c_target_last_snapshot = bytes(i2c_target_mem[:I2C_BUF_LEN])
            i2c_target_pending = True
    except Exception:
        pass

def init_i2c_target_for_slave():
    global i2c_target, i2c_target_supported, I2CTargetClass
    try:
        from machine import I2CTarget as I2CTargetImported
        I2CTargetClass = I2CTargetImported
    except Exception:
        log("[I2C] I2CTarget no disponible en esta build")
        i2c_target_supported = False
        return False
    last_err = None
    for bus_id in (0, 1):
        try:
            i2c_target = I2CTargetImported(
                bus_id,
                I2C_ADDR,
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
            clear_i2c_target_buffer()
            log("[I2C] Target OK en bus {} addr {}".format(bus_id, hex(I2C_ADDR)))
            return True
        except Exception as e:
            last_err = e
    log("[I2C] No se pudo iniciar I2CTarget: {}".format(last_err))
    i2c_target_supported = False
    return False

def poll_i2c_target_buffer():
    global i2c_target_pending
    if not i2c_target_supported:
        return None
    if i2c_target_pending:
        i2c_target_pending = False
        return i2c_target_last_snapshot
    snap = bytes(i2c_target_mem[:I2C_BUF_LEN])
    if snap != bytes(I2C_BUF_LEN) and snap != i2c_target_last_snapshot:
        return snap
    return None

def extract_command_text(buf):
    if buf is None:
        return ""
    try:
        raw = bytes(buf)
        end0 = raw.find(b"\x00")
        if end0 >= 0:
            raw = raw[:end0]
        text = raw.decode("utf-8", "ignore")
        text = text.replace("\r", "\n")
        return text.strip()
    except Exception:
        return ""

def _parse_optional_float(token):
    if token.upper() in ("NONE", "NA", "X", "-"):
        return None
    return float(token)

def exec_command(cmdline):
    global busy
    try:
        cmdline = cmdline.strip()
        if not cmdline:
            return "ERR EMPTY"
        parts = cmdline.split()
        cmd = parts[0].upper()
        busy = True

        if cmd == "PING":
            return "PONG"
        if cmd == "STATE?":
            return "OK " + estado_actual_str()
        if cmd == "STATE_EXT?":
            return "OK " + estado_extendido_str()
        if cmd == "HOME_ALL":
            ok = home_all()
            return "OK HOME_ALL" if ok else "ERR HOME_ALL"
        if cmd == "HOME_CODO":
            ok = home_codo(reset_pos=True)
            return "OK HOME_CODO" if ok else "ERR HOME_CODO"
        if cmd == "HOME_MUNECA":
            ok = home_muneca(reset_pos=True)
            return "OK HOME_MUNECA" if ok else "ERR HOME_MUNECA"
        if cmd == "BASE_GOTO":
            target = float(parts[1])
            ir_base_a_deg(target)
            return "OK BASE {:.3f}".format(angulo_actual_base())
        if cmd == "BASE_REL":
            delta = float(parts[1])
            mover_base_rel_deg(delta)
            return "OK BASE {:.3f}".format(angulo_actual_base())
        if cmd == "CODO_GOTO":
            target = float(parts[1])
            ir_codo_a_deg(target)
            return "OK CODO {:.3f}".format(angulo_actual_codo())
        if cmd == "CODO_REL":
            delta = float(parts[1])
            mover_codo_rel_deg(delta)
            return "OK CODO {:.3f}".format(angulo_actual_codo())
        if cmd == "MUNECA_GOTO":
            target = float(parts[1])
            ir_muneca_a_deg(target)
            return "OK MUNECA {:.3f}".format(angulo_actual_muneca())
        if cmd == "MUNECA_REL":
            delta = float(parts[1])
            mover_muneca_rel_deg(delta)
            return "OK MUNECA {:.3f}".format(angulo_actual_muneca())
        if cmd == "POSE":
            if len(parts) < 4:
                return "ERR POSE_ARGS"
            base_deg = _parse_optional_float(parts[1])
            codo_deg = _parse_optional_float(parts[2])
            muneca_deg = _parse_optional_float(parts[3])
            ir_pose(base_deg, codo_deg, muneca_deg)
            return "OK " + estado_actual_str()
        if cmd == "TUNE?":
            return (
                "OK TUNE BASE[{}/{}/{} acc={} dec={}] "
                "CODO[{}/{}/{} acc={} dec={}] "
                "MUNECA[{}/{}/{} acc={} dec={}] "
                "COMP_MUNECA_WITH_CODO={} COMP_RATIO={:.3f}"
                .format(
                    BASE_RAMP_START_US, BASE_RAMP_CRUISE_US, BASE_RAMP_END_US, BASE_ACCEL_STEPS, BASE_DECEL_STEPS,
                    CODO_RAMP_START_US, CODO_RAMP_CRUISE_US, CODO_RAMP_END_US, CODO_ACCEL_STEPS, CODO_DECEL_STEPS,
                    MUNECA_RAMP_START_US, MUNECA_RAMP_CRUISE_US, MUNECA_RAMP_END_US, MUNECA_ACCEL_STEPS, MUNECA_DECEL_STEPS,
                    int(COMPENSATE_MUNECA_WITH_CODO), COMP_RATIO
                )
            )
        if cmd == "HELP" or cmd == "?":
            return "OK CMDS PING STATE? STATE_EXT? HOME_ALL HOME_CODO HOME_MUNECA BASE_GOTO BASE_REL CODO_GOTO CODO_REL MUNECA_GOTO MUNECA_REL POSE TUNE?"
        return "ERR UNKNOWN_CMD"
    except MotionAbort as e:
        return "ABORT " + str(e)
    except Exception as e:
        return "ERR " + str(e)
    finally:
        busy = False

def service_i2c_target_text():
    global last_i2c_cmd_ms
    snap = poll_i2c_target_buffer()
    if snap is None:
        return
    text = extract_command_text(snap)
    clear_i2c_target_buffer()
    if not text:
        return
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        last_i2c_cmd_ms = time.ticks_ms()
        log("[I2C RX] " + line)
        resp = exec_command(line)
        log("[I2C TX] " + resp)
        write_i2c_response(resp)

def init_serial_console():
    global stdin_poll
    try:
        stdin_poll = uselect.poll()
        stdin_poll.register(sys.stdin, uselect.POLLIN)
        log("[SER] USB stdin polling OK")
        return True
    except Exception as e:
        stdin_poll = None
        log("[SER] stdin no disponible: {}".format(e))
        return False

def read_serial_line_nonblocking():
    if stdin_poll is None:
        return None
    try:
        events = stdin_poll.poll(SERIAL_POLL_MS)
        if not events:
            return None
        line = sys.stdin.readline()
        if not line:
            return None
        return line.strip()
    except Exception:
        return None

def service_serial_text():
    global last_serial_cmd_ms
    line = read_serial_line_nonblocking()
    if not line:
        return
    last_serial_cmd_ms = time.ticks_ms()
    log("[SER RX] " + line)
    resp = exec_command(line)
    print(resp)
    try:
        sys.stdout.flush()
    except Exception:
        pass

def on_button_short():
    if busy:
        return
    log("[BTN] HOME_ALL")
    resp = exec_command("HOME_ALL")
    log("[BTN] " + resp)

def on_button_long():
    log("[BTN] STATE")
    log(estado_extendido_str())

def update_button():
    global btn_last_raw, btn_stable, btn_last_change_ms, btn_press_ms
    raw = BTN.value()
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

def main():
    init_pins()
    log("\n=== MANIPULADOR I2C + SERIAL (COMPENSACION Q2 SIN CONTABILIZARLA) ===")
    log("[BOOT] BTN=GPIO{} SW2=GPIO{} SW3=GPIO{} SDA=GPIO{} SCL=GPIO{}".format(
        BTN_PIN, SW2_PIN, SW3_PIN, SDA_PIN, SCL_PIN
    ))
    log("[BOOT] Estado inicial: " + estado_extendido_str())
    log("[BOOT] COMPENSATE_MUNECA_WITH_CODO={} COMP_RATIO={}".format(int(COMPENSATE_MUNECA_WITH_CODO), COMP_RATIO))
    write_i2c_response("BOOT " + estado_actual_str())

    ok_i2c = init_i2c_target_for_slave()
    if not ok_i2c:
        log("[BOOT] I2C target no disponible")
    else:
        log("[READY] Comandos por I2C: PING, STATE?, STATE_EXT?, HOME_ALL, HOME_CODO, HOME_MUNECA,")
        log("[READY] BASE_GOTO <deg>, BASE_REL <deg>, CODO_GOTO <deg>, CODO_REL <deg>,")
        log("[READY] MUNECA_GOTO <deg>, MUNECA_REL <deg>, POSE <base|NA> <codo|NA> <muneca|NA>, TUNE?")

    ok_ser = init_serial_console()
    if ok_ser:
        log("[READY] Comandos por SERIAL: PING, STATE?, STATE_EXT?, HOME_ALL, HOME_CODO, HOME_MUNECA,")
        log("[READY] BASE_GOTO <deg>, BASE_REL <deg>, CODO_GOTO <deg>, CODO_REL <deg>,")
        log("[READY] MUNECA_GOTO <deg>, MUNECA_REL <deg>, POSE <base|NA> <codo|NA> <muneca|NA>, TUNE?, HELP")

    while True:
        update_button()
        service_i2c_target_text()
        service_serial_text()
        sleep_ms(5)

main()
