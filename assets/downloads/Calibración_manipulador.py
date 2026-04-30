from machine import Pin
from time import sleep_ms, sleep_us

# =====================================================
# ESP32-C3 SuperMini + CL57T
# MicroPython para Thonny
# Pulso activo en LOW
#
# Motor 1 -> Hombro   (sin home)
# Motor 2 -> Codo     (home con SW2)
# Motor 3 -> Muñeca   (home con SW3)
#
# IMPORTANTE:
# Cuando se mueve el CODO, la MUNECA acompaña
# para mantener la congruencia mecánica del sistema
# por poleas.
# =====================================================

# ---------- Pines ----------
DIR_HOMBRO = Pin(21, Pin.OUT)   # dir1
PUL_HOMBRO = Pin(20, Pin.OUT)   # pul1

DIR_CODO   = Pin(10, Pin.OUT)   # dir2
PUL_CODO   = Pin(7, Pin.OUT)    # pul2

DIR_MUNECA = Pin(6, Pin.OUT)    # dir3
PUL_MUNECA = Pin(5, Pin.OUT)    # pul3

LED_TEST = Pin(2, Pin.OUT)

# ---------- Finales de carrera ----------
SW2 = Pin(3, Pin.IN)   # Codo / primer eslabón
SW3 = Pin(4, Pin.IN)   # Muñeca / segundo eslabón

# ---------- Direcciones crudas ----------
DIR_A = 1
DIR_B = 0

# =====================================================
# CONVENCION DE SIGNO ARTICULAR
# =====================================================
JOINT_POS = 1
JOINT_NEG = -1

# =====================================================
# MAPEO RAW SEGUN TUS PRUEBAS
# =====================================================
# CODO:
#   A = positivo
#   B = negativo
def raw_dir_codo(signo_joint):
    return DIR_A if signo_joint == JOINT_POS else DIR_B

# MUNECA:
#   A = negativo
#   B = positivo
def raw_dir_muneca(signo_joint):
    return DIR_B if signo_joint == JOINT_POS else DIR_A

# =====================================================
# HOME EN ESPACIO ARTICULAR
# =====================================================
# CODO: para ir a SW2 debe ir en negativo
HOME_SIGN_CODO = JOINT_NEG
AWAY_SIGN_CODO = JOINT_POS

# MUNECA: para ir a SW3 debe ir en positivo
HOME_SIGN_MUNECA = JOINT_POS
AWAY_SIGN_MUNECA = JOINT_NEG

# =====================================================
# PARAMETROS
# =====================================================
PULSE_JOG_US       = 1800
PULSE_HOME_FAST_US = 1800
PULSE_HOME_SLOW_US = 3200

DIR_SETTLE_US = 200

JOG_STEPS = 100
FAST_BLOCK = 8

BACKOFF_STEPS = 220
FINAL_CLEARANCE_STEPS = 120

MAX_SEARCH_CODO = 12000
MAX_SEARCH_MUNECA = 12000
MAX_RELEASE_STEPS = 1500

# Relacion de compensacion muñeca/codo
# 1.0 = 1 paso de muñeca por 1 paso de codo
COMP_RATIO = 1.0

# =====================================================
# POSICION SOFTWARE (en espacio articular)
# =====================================================
pos_hombro = 0
pos_codo = 0
pos_muneca = 0

# =====================================================
# UTILS BASICOS
# =====================================================

# =====================================================
# ANGULOS Y MOVIMIENTOS EN GRADOS
# Switch = 0°
# =====================================================

STEPS_PER_REV_JOINT = 25000
DEG_PER_STEP = 360.0 / STEPS_PER_REV_JOINT
STEPS_PER_DEG = STEPS_PER_REV_JOINT / 360.0

# Límites opcionales de software
# Pon números si ya conoces tus rangos
CODO_MIN_DEG = None
CODO_MAX_DEG = None

MUNECA_MIN_DEG = None
MUNECA_MAX_DEG = None


def deg_to_steps(deg):
    return int(round(deg * STEPS_PER_DEG))


def steps_to_deg(steps):
    return steps * DEG_PER_STEP


def angulo_actual_codo():
    return steps_to_deg(pos_codo)


def angulo_actual_muneca():
    return steps_to_deg(pos_muneca)


def imprimir_angulos():
    print("CODO  :", angulo_actual_codo(), "deg | pasos =", pos_codo)
    print("MUNECA:", angulo_actual_muneca(), "deg | pasos =", pos_muneca)


def checar_limite(nombre, target_deg, min_deg, max_deg):
    if min_deg is not None and target_deg < min_deg:
        raise ValueError("{}: objetivo {:.3f}° menor que limite {:.3f}°".format(
            nombre, target_deg, min_deg))

    if max_deg is not None and target_deg > max_deg:
        raise ValueError("{}: objetivo {:.3f}° mayor que limite {:.3f}°".format(
            nombre, target_deg, max_deg))


def mover_codo_rel_deg(delta_deg, pulse_us=PULSE_JOG_US):
    """
    Mueve el codo delta_deg.
    IMPORTANTE: esta funcion SI compensa la muñeca.
    """
    global pos_codo

    if delta_deg == 0:
        return

    pasos = abs(deg_to_steps(delta_deg))
    signo = JOINT_POS if delta_deg > 0 else JOINT_NEG

    # revisar limite objetivo del codo
    target_deg = angulo_actual_codo() + delta_deg
    checar_limite("CODO", target_deg, CODO_MIN_DEG, CODO_MAX_DEG)

    mover_codo_compensado_joint(signo, pasos, pulse_us)


def mover_muneca_rel_deg(delta_deg, pulse_us=PULSE_JOG_US):
    """
    Mueve solo la muñeca delta_deg.
    """
    global pos_muneca

    if delta_deg == 0:
        return

    pasos = abs(deg_to_steps(delta_deg))
    signo = JOINT_POS if delta_deg > 0 else JOINT_NEG

    # revisar limite objetivo de muñeca
    target_deg = angulo_actual_muneca() + delta_deg
    checar_limite("MUNECA", target_deg, MUNECA_MIN_DEG, MUNECA_MAX_DEG)

    mover_muneca_joint(signo, pasos, pulse_us)


def ir_codo_a_deg(target_deg, pulse_us=PULSE_JOG_US):
    """
    Lleva el codo a un ángulo absoluto.
    Switch SW2 = 0°.
    IMPORTANTE: al mover el codo, la muñeca acompaña automáticamente.
    """
    actual = angulo_actual_codo()
    delta = target_deg - actual
    mover_codo_rel_deg(delta, pulse_us)


def ir_muneca_a_deg(target_deg, pulse_us=PULSE_JOG_US):
    """
    Lleva la muñeca a un ángulo absoluto.
    Switch SW3 = 0°.
    """
    actual = angulo_actual_muneca()
    delta = target_deg - actual
    mover_muneca_rel_deg(delta, pulse_us)


def ir_pose(codo_deg=None, muneca_deg=None, pulse_us=PULSE_JOG_US):
    """
    Lleva ambos joints a una pose final.

    Orden recomendado:
    1) mover codo
    2) corregir muñeca

    Esto porque mover el codo arrastra/compensa la muñeca.
    """
    if codo_deg is not None:
        ir_codo_a_deg(codo_deg, pulse_us)

    if muneca_deg is not None:
        ir_muneca_a_deg(muneca_deg, pulse_us)


def cero_logico():
    """
    Solo imprime dónde está el cero real de referencia:
    el switch es 0°.
    """
    print("Referencia:")
    print("  SW2 = 0° del CODO")
    print("  SW3 = 0° de la MUNECA")


def estado_actual():
    leer_switches()
    imprimir_angulos()


def init_pins():
    PUL_HOMBRO.value(1)
    PUL_CODO.value(1)
    PUL_MUNECA.value(1)

    DIR_HOMBRO.value(DIR_A)
    DIR_CODO.value(DIR_A)
    DIR_MUNECA.value(DIR_A)

    LED_TEST.value(0)

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

# =====================================================
# MOVIMIENTO DE MUNECA SOLA (espacio articular)
# =====================================================

def mover_muneca_joint(signo_joint, pasos, pulse_us=PULSE_JOG_US):
    global pos_muneca

    DIR_MUNECA.value(raw_dir_muneca(signo_joint))
    sleep_us(DIR_SETTLE_US)

    for _ in range(pasos):
        pulse_step(PUL_MUNECA, pulse_us)

    if signo_joint == JOINT_POS:
        pos_muneca += pasos
    else:
        pos_muneca -= pasos

# =====================================================
# MOVIMIENTO DE CODO + COMPENSACION DE MUNECA
# =====================================================
# Cuando el codo se mueve, la muñeca acompaña con el
# mismo signo articular para mantener congruencia.
# =====================================================

def mover_codo_compensado_joint(signo_joint, pasos, pulse_us=PULSE_JOG_US):
    global pos_codo, pos_muneca

    dir_codo = raw_dir_codo(signo_joint)
    dir_muneca = raw_dir_muneca(signo_joint)

    DIR_CODO.value(dir_codo)
    DIR_MUNECA.value(dir_muneca)
    sleep_us(DIR_SETTLE_US)

    # Si luego quieres otra razón distinta a 1:1,
    # aquí se puede cambiar por un acumulador.
    pasos_muneca = int(round(pasos * COMP_RATIO))

    # Caso 1: ratio 1:1 exacto
    if pasos_muneca == pasos:
        for _ in range(pasos):
            pulse_step_dual(PUL_CODO, PUL_MUNECA, pulse_us)
    else:
        # Caso general simple: acumulador
        acc = 0.0
        for _ in range(pasos):
            # paso de codo siempre
            PUL_CODO.value(0)

            acc += COMP_RATIO
            step_m = False
            if acc >= 1.0:
                PUL_MUNECA.value(0)
                step_m = True
                acc -= 1.0

            sleep_us(pulse_us)

            PUL_CODO.value(1)
            if step_m:
                PUL_MUNECA.value(1)

            sleep_us(pulse_us)

            # Si no hubo paso de muñeca, asegurar HIGH
            if not step_m:
                PUL_MUNECA.value(1)

    if signo_joint == JOINT_POS:
        pos_codo += pasos
        pos_muneca += pasos_muneca
    else:
        pos_codo -= pasos
        pos_muneca -= pasos_muneca

# =====================================================
# JOGS
# =====================================================

def leer_switches():
    print("SW2 =", SW2.value(), "| SW3 =", SW3.value())

def codo_jog_home(pasos=JOG_STEPS):
    print("CODO -> hacia SW2 (con compensacion de muñeca)")
    mover_codo_compensado_joint(HOME_SIGN_CODO, pasos)

def codo_jog_away(pasos=JOG_STEPS):
    print("CODO -> alejandose de SW2 (con compensacion de muñeca)")
    mover_codo_compensado_joint(AWAY_SIGN_CODO, pasos)

def muneca_jog_home(pasos=JOG_STEPS):
    print("MUNECA -> hacia SW3")
    mover_muneca_joint(HOME_SIGN_MUNECA, pasos)

def muneca_jog_away(pasos=JOG_STEPS):
    print("MUNECA -> alejandose de SW3")
    mover_muneca_joint(AWAY_SIGN_MUNECA, pasos)

# =====================================================
# HOMING GENERICO
# move_fn(signo_joint, pasos, pulse_us)
# =====================================================

def liberar_switch_si_esta_activo(nombre, move_fn, away_sign, sw_pin, pulse_us, max_steps):
    if not switch_active(sw_pin):
        return True, 0

    print(nombre, ": switch ya activo, liberando...")
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

# =====================================================
# HOME MUNECA
# =====================================================

def home_muneca(reset_pos=True):
    global pos_muneca

    print("\n=== HOME MUNECA (SW3) ===")
    LED_TEST.value(1)

    ok, pasos = liberar_switch_si_esta_activo(
        "MUNECA",
        mover_muneca_joint,
        AWAY_SIGN_MUNECA,
        SW3,
        PULSE_HOME_SLOW_US,
        MAX_RELEASE_STEPS
    )
    print("Liberacion inicial muñeca:", pasos, "pasos")

    if not ok:
        LED_TEST.value(0)
        print("ERROR: no se pudo liberar SW3")
        return False

    ok, pasos_fast = buscar_switch(
        "MUNECA",
        mover_muneca_joint,
        HOME_SIGN_MUNECA,
        SW3,
        PULSE_HOME_FAST_US,
        MAX_SEARCH_MUNECA,
        FAST_BLOCK
    )
    print("Busqueda rapida muñeca:", pasos_fast, "pasos")

    if not ok:
        LED_TEST.value(0)
        print("ERROR: muñeca no encontro SW3")
        return False

    print("Backoff muñeca:", BACKOFF_STEPS, "pasos")
    mover_muneca_joint(AWAY_SIGN_MUNECA, BACKOFF_STEPS, PULSE_HOME_SLOW_US)

    ok, pasos_slow = buscar_switch(
        "MUNECA",
        mover_muneca_joint,
        HOME_SIGN_MUNECA,
        SW3,
        PULSE_HOME_SLOW_US,
        BACKOFF_STEPS + 300,
        1
    )
    print("Busqueda fina muñeca:", pasos_slow, "pasos")

    if not ok:
        LED_TEST.value(0)
        print("ERROR: muñeca no encontro SW3 en busqueda fina")
        return False

    print("Clearance final muñeca:", FINAL_CLEARANCE_STEPS, "pasos")
    mover_muneca_joint(AWAY_SIGN_MUNECA, FINAL_CLEARANCE_STEPS, PULSE_HOME_SLOW_US)

    #if reset_pos:
        #pos_muneca = 0
        
    if reset_pos:
        pos_muneca = -FINAL_CLEARANCE_STEPS

    LED_TEST.value(0)
    print("HOME MUNECA OK")
    return True

# =====================================================
# HOME CODO CON COMPENSACION DE MUNECA
# =====================================================

def home_codo(reset_pos=True):
    global pos_codo

    print("\n=== HOME CODO (SW2) + COMPENSACION MUNECA ===")
    LED_TEST.value(1)

    ok, pasos = liberar_switch_si_esta_activo(
        "CODO",
        mover_codo_compensado_joint,
        AWAY_SIGN_CODO,
        SW2,
        PULSE_HOME_SLOW_US,
        MAX_RELEASE_STEPS
    )
    print("Liberacion inicial codo:", pasos, "pasos")

    if not ok:
        LED_TEST.value(0)
        print("ERROR: no se pudo liberar SW2")
        return False

    ok, pasos_fast = buscar_switch(
        "CODO",
        mover_codo_compensado_joint,
        HOME_SIGN_CODO,
        SW2,
        PULSE_HOME_FAST_US,
        MAX_SEARCH_CODO,
        FAST_BLOCK
    )
    print("Busqueda rapida codo:", pasos_fast, "pasos")

    if not ok:
        LED_TEST.value(0)
        print("ERROR: codo no encontro SW2")
        return False

    print("Backoff codo:", BACKOFF_STEPS, "pasos")
    mover_codo_compensado_joint(AWAY_SIGN_CODO, BACKOFF_STEPS, PULSE_HOME_SLOW_US)

    ok, pasos_slow = buscar_switch(
        "CODO",
        mover_codo_compensado_joint,
        HOME_SIGN_CODO,
        SW2,
        PULSE_HOME_SLOW_US,
        BACKOFF_STEPS + 300,
        1
    )
    print("Busqueda fina codo:", pasos_slow, "pasos")

    if not ok:
        LED_TEST.value(0)
        print("ERROR: codo no encontro SW2 en busqueda fina")
        return False

    print("Clearance final codo:", FINAL_CLEARANCE_STEPS, "pasos")
    mover_codo_compensado_joint(AWAY_SIGN_CODO, FINAL_CLEARANCE_STEPS, PULSE_HOME_SLOW_US)

    #if reset_pos:
        #os_codo = 0
    if reset_pos:
        pos_codo = FINAL_CLEARANCE_STEPS

    LED_TEST.value(0)
    print("HOME CODO OK")
    return True

# =====================================================
# HOME COMPLETO RECOMENDADO
# =====================================================

def home_all():
    global pos_codo, pos_muneca

    print("\n==============================")
    print("INICIANDO HOME COMPLETO")
    print("==============================")

    # 1) Home inicial de muñeca
    ok = home_muneca(reset_pos=True)
    if not ok:
        print("Abortado: fallo en home inicial de muñeca")
        return False

    sleep_ms(400)

    # 2) Home de codo compensando muñeca
    ok = home_codo(reset_pos=True)
    if not ok:
        print("Abortado: fallo en home de codo")
        return False

    sleep_ms(400)

    # 3) Re-home de muñeca porque se movio durante home_codo
    ok = home_muneca(reset_pos=True)
    if not ok:
        print("Abortado: fallo en home final de muñeca")
        return False

    print("\nHOME COMPLETO OK")
    print("pos_codo =", pos_codo, "| pos_muneca =", pos_muneca)
    return True

# =====================================================
# INIT
# =====================================================
init_pins()

print("Listo.")
print("Funciones:")
print("  leer_switches()")
print("  codo_jog_home()")
print("  codo_jog_away()")
print("  muneca_jog_home()")
print("  muneca_jog_away()")
print("  home_codo()")
print("  home_muneca()")
print("  home_all()")

home_all()
estado_actual()
#ir_codo_a_deg(136, 500)
#ir_muneca_a_deg(-150,500) paralelo al primer eslabon
ir_muneca_a_deg(-220,500)
ir_codo_a_deg(146, 500)
