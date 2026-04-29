import asyncio
import json
import math
import queue
import signal
import struct
import threading
import time
import re
from collections import deque
from dataclasses import dataclass, asdict
from typing import Any, Deque, Dict, List, Optional, Set, Tuple

import cv2
import numpy as np
import pyrealsense2 as rs
import zmq
from ultralytics import YOLO

try:
    import serial
except Exception:
    serial = None

try:
    from scanner import RPLidar
except Exception:
    from rplidarc1.scanner import RPLidar


# ============================================================
# NUC MASTER SERVER | CAMERA MODES + LIDAR GRID + WALLS MODE
# ------------------------------------------------------------
# Camera modes:
#   - normal
#   - pose
#   - segment
#   - off
#
# Lidar modes:
#   - detail
#   - medium
#   - panorama
#   - off
#
# Walls immersive mode:
#   - disabled by default
#   - when enabled, the NUC derives simplified wall segments from
#     the same RPLidar C1 stream and publishes:
#       * walls_snapshot (binary)
#       * walls_delta    (binary)
#       * walls_status   (json via PORT_SENSORS)
#
# Points immersive mode:
#   - disabled by default
#   - when enabled, the NUC publishes local-frame lidar points
#     referenced to the lidar origin:
#       * lidar_points_snapshot (binary)
#       * lidar_points_frame    (binary)
#       * points_status         (json via PORT_SENSORS)
#
# ZMQ ports:
#   - PORT_VIDEO   : JPG stream of the active camera mode
#   - PORT_SENSORS : stat / cam_info / vision / lidar_grid / mode_ack / error / walls_status
#   - PORT_CMD     : incoming commands from Unity
#   - PORT_WALLS   : binary walls stream for immersive scene
# ============================================================

# ============================================================
# CONFIG
# ============================================================
PORT_SENSORS = 5001
PORT_VIDEO = 5555
PORT_CMD = 5002
PORT_WALLS = 5007

# Serial bridge to ESP32-C3 master bridge
SERIAL_MASTER_PORT = "COM4"
SERIAL_MASTER_BAUD = 115200
SERIAL_MASTER_TIMEOUT_S = 0.02
SERIAL_RECONNECT_DELAY_S = 1.0

# Serial bridge to gripper ESP32-C3
GRIPPER_SERIAL_PORT = "COM5"  # ajusta segun tu PC/NUC
GRIPPER_SERIAL_BAUD = 115200
GRIPPER_SERIAL_TIMEOUT_S = 0.02
GRIPPER_RECONNECT_DELAY_S = 1.0
GRIPPER_QUERY_HZ = 4.0
GRIPPER_COMMAND_HZ = 20.0

LIDAR_PORT = "COM3"
LIDAR_BAUD = 460800

COLOR_W = 640
COLOR_H = 480
DEPTH_W = 640
DEPTH_H = 480
COLOR_FPS = 30
DEPTH_FPS = 30

JPEG_QUALITY = 85
VIDEO_TOPIC_RGB = b"video_rgb"

MAX_RANGE_MM = 6000
MIN_QUALITY = 0
LIDAR_GRID_HZ = 12.0
LIDAR_STALE_S = 0.35
LIDAR_YAW_DEG = 0.0

STAT_PUBLISH_HZ = 2.0
VISION_PUBLISH_HZ = 10.0
CMD_HEARTBEAT_TIMEOUT = 2.0

ZMQ_SNDHWM_VIDEO = 2
ZMQ_SNDHWM_SENSORS = 300
ZMQ_SNDHWM_WALLS = 50

POINTS_PUBLISH_HZ = 8.0
POINTS_WINDOW_SECONDS = 0.35
POINTS_MAX_BUFFER = 20000
MAX_POINTS_IN_PACKET = 12000

# Drive control bridge (Unity -> NUC -> serial master bridge)
DRIVE_SERIAL_HZ = 15.0
DRIVE_CMD_TIMEOUT_S = 0.35
DRIVE_DEADZONE = 0.08
DRIVE_MAX_RAW = 255
LOCAL_MOTOR_IS_LEFT = True
MANIP_STATE_QUERY_HZ = 4.0

VALID_CAMERA_MODES = {"normal", "pose", "segment", "off"}
VALID_LIDAR_MODES = {"detail", "medium", "panorama", "off"}

LIDAR_MODES: Dict[str, Dict[str, float]] = {
    "detail": {"cell_m": 0.01, "radius_m": 1.0, "grid_size": 200},
    "medium": {"cell_m": 0.01, "radius_m": 2.0, "grid_size": 400},
    "panorama": {"cell_m": 0.01, "radius_m": 3.0, "grid_size": 600},
}

# Vision
POSE_MODEL_PATH = "yolov8n-pose.pt"
SEG_MODEL_PATH = "yolo26n-seg.pt"
VISION_DEVICE = "cpu"
VISION_IMGSZ = 640
VISION_CONF_TH = 0.70
POSE_KEYPOINT_CONF_TH = 0.20
TARGET_CLASS_IDS_SEG: Optional[set] = None
MIN_MASK_PIXELS = 200
DEPTH_SAMPLE_RADIUS = 10
MAX_VALID_DEPTH_MM = 2500.0
LEFT_HIP = 11
RIGHT_HIP = 12

# Walls pipeline
WALLS_PROCESS_HZ = 1.0
WALLS_WINDOW_SECONDS = 4.0
WALLS_MAX_POINTS_BUFFER = 150000
WALLS_RESOLUTION_M = 0.10
WALLS_GRID_MARGIN_M = 0.50
WALLS_MIN_COMPONENT_AREA_PX = 80

WALLS_DILATE_KERNEL = 3
WALLS_DILATE_ITER = 1
WALLS_CLOSE_KERNEL = 5
WALLS_CLOSE_ITER = 2
WALLS_OPEN_KERNEL = 2
WALLS_OPEN_ITER = 1

WALLS_SIMPLIFY_EPS_PX = 4.0
WALLS_MIN_POLYLINE_LEN_PX = 8
WALLS_ANGLE_TOL_DEG = 15
WALLS_MIN_SEG_LEN_PX = 3
WALLS_SNAP_DIST_PX = 3
WALLS_EXTEND_MAX_PX = 4
WALLS_ORTHO_ANGLE_TOL_DEG = 15

MAX_WALLS_ADDS_PER_PACKET = 1200
MAX_WALLS_REMS_PER_PACKET = 1200
MAX_WALLS_SEGMENTS_IN_SNAPSHOT = 30000

# Binary protocol
WALLS_SNAPSHOT_MAGIC = b"WSNP"
WALLS_DELTA_MAGIC = b"WDEL"
POINTS_SNAPSHOT_MAGIC = b"LPSN"
POINTS_FRAME_MAGIC = b"LPFR"
WALLS_VERSION = 1
POINTS_VERSION = 1
MM_PER_M = 1000

# Depth calibration
intel_mm = np.array([
    160, 170, 180, 190, 200, 210, 220, 230, 240, 250, 260, 270, 280, 290, 300,
    310, 320, 330, 340, 350, 360, 370, 380, 390, 400, 500, 600, 700, 800, 900, 1000
], dtype=float)

real_mm = np.array([
    160, 170, 181, 191, 202, 212, 223, 234, 245, 255, 265, 275, 287, 299, 310,
    321, 333, 343, 355, 366, 376, 387, 397, 409, 422, 535, 653, 771, 894, 1024, 1151
], dtype=float)


@dataclass
class SharedState:
    start_ts: float
    camera_ok: bool = False
    lidar_ok: bool = False
    walls_ok: bool = False
    points_ok: bool = False
    cmd_link_ok: bool = False
    last_camera_ts: float = 0.0
    last_lidar_ts: float = 0.0
    last_walls_ts: float = 0.0
    last_points_ts: float = 0.0
    last_cmd_ts: float = 0.0
    depth_scale: float = 0.0
    dropped_video_frames: int = 0
    dropped_sensor_msgs: int = 0
    dropped_walls_msgs: int = 0
    active_camera_mode: str = "normal"
    active_lidar_mode: str = "off"
    walls_enabled: bool = False
    points_enabled: bool = False
    walls_seq: int = 0
    points_seq: int = 0
    walls_snapshot_pending: bool = False
    points_snapshot_pending: bool = False
    pose_model_ready: bool = False
    seg_model_ready: bool = False
    master_serial_ok: bool = False
    last_serial_tx_ts: float = 0.0
    last_serial_rx_ts: float = 0.0
    drive_enabled: bool = False
    manip_enabled: bool = False
    base_enabled: bool = False
    last_drive_cmd_ts: float = 0.0
    last_manip_cmd_ts: float = 0.0
    manip_state_valid: bool = False
    manip_busy: bool = False
    manip_sw2: int = -1
    manip_sw3: int = -1
    actual_base_deg: float = 0.0
    actual_codo_deg: float = 0.0
    actual_muneca_deg: float = 0.0
    last_manip_state_ts: float = 0.0
    gripper_serial_ok: bool = False
    gripper_state_valid: bool = False
    gripper_busy: bool = False
    gripper_calibrated: bool = False
    gripper_mm: float = 0.0
    gripper_target_mm: float = 0.0
    gripper_count: int = 0
    last_gripper_state_ts: float = 0.0
    last_gripper_cmd_ts: float = 0.0

    def snapshot(self) -> Dict[str, Any]:
        now = time.time()
        cmd_ok = self.cmd_link_ok
        if self.last_cmd_ts > 0:
            cmd_ok = (now - self.last_cmd_ts) <= CMD_HEARTBEAT_TIMEOUT
        return {
            **asdict(self),
            "cmd_link_ok": cmd_ok,
            "uptime_s": round(now - self.start_ts, 3),
            "ts": round(now, 3),
        }


state = SharedState(start_ts=time.time())
state_lock = threading.Lock()
running = True

sensor_queue: "queue.Queue[List[bytes]]" = queue.Queue(maxsize=512)
video_queue: "queue.Queue[List[bytes]]" = queue.Queue(maxsize=8)
walls_queue: "queue.Queue[List[bytes]]" = queue.Queue(maxsize=64)
serial_cmd_queue: "queue.Queue[str]" = queue.Queue(maxsize=256)
gripper_cmd_queue: "queue.Queue[str]" = queue.Queue(maxsize=64)

# Latest continuous drive target from Unity
drive_cmd_lock = threading.Lock()
drive_enabled = False
drive_v = 0.0
drive_w = 0.0
drive_last_rx_ts = 0.0

# Latest gripper target / serial bridge
gripper_cmd_lock = threading.Lock()
gripper_target_line: Optional[str] = None
gripper_target_dirty = False


def safe_put(q: queue.Queue, item: List[bytes], kind: str) -> None:
    try:
        q.put_nowait(item)
    except queue.Full:
        with state_lock:
            if kind == "video":
                state.dropped_video_frames += 1
            elif kind == "walls":
                state.dropped_walls_msgs += 1
            else:
                state.dropped_sensor_msgs += 1


def publish_sensor(topic: str, data: Dict[str, Any]) -> None:
    payload = json.dumps(data, separators=(",", ":")).encode("utf-8")
    safe_put(sensor_queue, [topic.encode("utf-8"), payload], kind="sensor")


def publish_video(topic: bytes, buffer: bytes) -> None:
    safe_put(video_queue, [topic, buffer], kind="video")


def publish_walls(topic: bytes, payload: bytes) -> None:
    safe_put(walls_queue, [topic, payload], kind="walls")


def publish_points(topic: bytes, payload: bytes) -> None:
    safe_put(walls_queue, [topic, payload], kind="walls")


MANIP_STATE_RE = re.compile(
    r"BASE=(?P<base>-?\d+(?:\.\d+)?)deg\([^)]*\)\s*\|\s*"
    r"CODO=(?P<codo>-?\d+(?:\.\d+)?)deg\([^)]*\)\s*\|\s*"
    r"MUNECA=(?P<muneca>-?\d+(?:\.\d+)?)deg\([^)]*\).*?SW2=(?P<sw2>[-01])\s+SW3=(?P<sw3>[-01])",
    re.IGNORECASE,
)

GRIPPER_STATE_RE = re.compile(
    r"GRIPPER_STATE\s+mm=(?P<mm>-?\d+(?:\.\d+)?)\s+count=(?P<count>-?\d+)\s+"
    r"target_mm=(?P<target_mm>-?\d+(?:\.\d+)?)\s+target_count=(?P<target_count>-?\d+)\s+"
    r"busy=(?P<busy>[01])\s+calibrated=(?P<cal>[01])",
    re.IGNORECASE,
)


def maybe_extract_manip_state(line: str) -> Optional[Dict[str, Any]]:
    if not line:
        return None
    m = MANIP_STATE_RE.search(line)
    if not m:
        return None
    try:
        return {
            "base_deg": float(m.group("base")),
            "codo_deg": float(m.group("codo")),
            "muneca_deg": float(m.group("muneca")),
            "sw2": int(m.group("sw2")),
            "sw3": int(m.group("sw3")),
            "busy": False,
            "source_line": line,
            "ts": round(time.time(), 3),
        }
    except Exception:
        return None


def apply_manip_state_payload(payload: Dict[str, Any]) -> None:
    now = time.time()
    with state_lock:
        state.manip_state_valid = True
        state.actual_base_deg = float(payload.get("base_deg", 0.0))
        state.actual_codo_deg = float(payload.get("codo_deg", 0.0))
        state.actual_muneca_deg = float(payload.get("muneca_deg", 0.0))
        state.manip_sw2 = int(payload.get("sw2", -1))
        state.manip_sw3 = int(payload.get("sw3", -1))
        state.manip_busy = bool(payload.get("busy", False))
        state.last_manip_state_ts = now
        state.last_serial_rx_ts = now
    publish_sensor("manip_state", payload)


def maybe_extract_gripper_state(line: str) -> Optional[Dict[str, Any]]:
    if not line:
        return None
    m = GRIPPER_STATE_RE.search(line)
    if not m:
        return None
    try:
        return {
            "ts": round(time.time(), 3),
            "mm": float(m.group("mm")),
            "count": int(m.group("count")),
            "target_mm": float(m.group("target_mm")),
            "target_count": int(m.group("target_count")),
            "busy": bool(int(m.group("busy"))),
            "calibrated": bool(int(m.group("cal"))),
            "source_line": line,
        }
    except Exception:
        return None


def apply_gripper_state_payload(payload: Dict[str, Any]) -> None:
    now = time.time()
    with state_lock:
        state.gripper_state_valid = True
        state.gripper_mm = float(payload.get("mm", 0.0))
        state.gripper_target_mm = float(payload.get("target_mm", 0.0))
        state.gripper_count = int(payload.get("count", 0))
        state.gripper_busy = bool(payload.get("busy", False))
        state.gripper_calibrated = bool(payload.get("calibrated", False))
        state.last_gripper_state_ts = now
    publish_sensor("gripper_state", payload)


def set_latest_gripper_target(mm: Any) -> bool:
    try:
        line = f"m {float(mm):.3f}"
    except Exception:
        return False
    global gripper_target_line, gripper_target_dirty
    with gripper_cmd_lock:
        gripper_target_line = line
        gripper_target_dirty = True
    with state_lock:
        state.last_gripper_cmd_ts = time.time()
    return True


def enqueue_gripper_command(line: str) -> None:
    if not line:
        return
    try:
        gripper_cmd_queue.put_nowait(line.strip())
    except queue.Full:
        try:
            gripper_cmd_queue.get_nowait()
        except Exception:
            pass
        try:
            gripper_cmd_queue.put_nowait(line.strip())
        except Exception:
            pass


def get_active_modes() -> Tuple[str, str, bool, bool]:
    with state_lock:
        return state.active_camera_mode, state.active_lidar_mode, state.walls_enabled, state.points_enabled


def set_active_modes(
    camera_mode: Optional[str] = None,
    lidar_mode: Optional[str] = None,
    walls_enabled: Optional[bool] = None,
    points_enabled: Optional[bool] = None,
    request_snapshot: bool = False,
    request_points_snapshot: bool = False,
) -> Dict[str, Any]:
    changed = False
    with state_lock:
        if camera_mode is not None and camera_mode in VALID_CAMERA_MODES and state.active_camera_mode != camera_mode:
            state.active_camera_mode = camera_mode
            changed = True
        if lidar_mode is not None and lidar_mode in VALID_LIDAR_MODES and state.active_lidar_mode != lidar_mode:
            state.active_lidar_mode = lidar_mode
            changed = True
        if walls_enabled is not None and state.walls_enabled != walls_enabled:
            state.walls_enabled = walls_enabled
            changed = True
            if walls_enabled:
                state.walls_snapshot_pending = True
        if points_enabled is not None and state.points_enabled != points_enabled:
            state.points_enabled = points_enabled
            changed = True
            if points_enabled:
                state.points_snapshot_pending = True
        if request_snapshot:
            state.walls_snapshot_pending = True
        if request_points_snapshot:
            state.points_snapshot_pending = True
        snap = state.snapshot()
    if changed or request_snapshot or request_points_snapshot:
        publish_sensor("mode_ack", snap)
    return snap


def signal_handler(sig, frame):
    global running
    print("\n[MAIN] Señal de salida recibida, cerrando...")
    running = False


# ------------------------- CONTROL BRIDGE -------------------------
def clamp_unit(v: float) -> float:
    return max(-1.0, min(1.0, float(v)))


def apply_deadzone(v: float, dz: float = DRIVE_DEADZONE) -> float:
    v = clamp_unit(v)
    if abs(v) < dz:
        return 0.0
    return v


def format_drive_tokens(left_raw: int, right_raw: int) -> str:
    def tok(val: int) -> str:
        val = int(max(-DRIVE_MAX_RAW, min(DRIVE_MAX_RAW, val)))
        return "S" if val == 0 else str(val)

    if LOCAL_MOTOR_IS_LEFT:
        local_tok = tok(left_raw)
        hb_tok = tok(right_raw)
    else:
        local_tok = tok(right_raw)
        hb_tok = tok(left_raw)
    return f"{local_tok},{hb_tok}"


def mix_unicycle_to_dual_raw(v_cmd: float, w_cmd: float) -> Tuple[int, int]:
    v = apply_deadzone(v_cmd)
    w = apply_deadzone(w_cmd)

    left = max(-1.0, min(1.0, v - w))
    right = max(-1.0, min(1.0, v + w))

    left_raw = int(round(left * DRIVE_MAX_RAW))
    right_raw = int(round(right * DRIVE_MAX_RAW))
    return left_raw, right_raw


def enqueue_serial_command(line: str) -> None:
    if not line:
        return
    try:
        serial_cmd_queue.put_nowait(line.strip())
    except queue.Full:
        try:
            serial_cmd_queue.get_nowait()
        except Exception:
            pass
        try:
            serial_cmd_queue.put_nowait(line.strip())
        except Exception:
            pass


def update_drive_target(enabled: Optional[bool] = None, v_cmd: Optional[float] = None, w_cmd: Optional[float] = None) -> None:
    global drive_enabled, drive_v, drive_w, drive_last_rx_ts
    now = time.time()
    with drive_cmd_lock:
        if enabled is not None:
            drive_enabled = bool(enabled)
        if v_cmd is not None:
            drive_v = clamp_unit(v_cmd)
        if w_cmd is not None:
            drive_w = clamp_unit(w_cmd)
        drive_last_rx_ts = now
    with state_lock:
        state.drive_enabled = drive_enabled
        state.last_drive_cmd_ts = now


def queue_manip_pose(q: List[Any]) -> bool:
    if len(q) < 3:
        return False
    vals = []
    for x in q[:3]:
        if x is None:
            vals.append("NA")
        else:
            vals.append(f"{float(x):.3f}")
    enqueue_serial_command(f"POSE {vals[0]} {vals[1]} {vals[2]}")
    with state_lock:
        state.last_manip_cmd_ts = time.time()
    return True


def queue_base_goto(q_base: Any) -> bool:
    if q_base is None:
        return False
    enqueue_serial_command(f"BASE_GOTO {float(q_base):.3f}")
    with state_lock:
        state.last_manip_cmd_ts = time.time()
    return True


def handle_control_command(payload: Any) -> bool:
    handled = False

    if not isinstance(payload, dict):
        return False

    cmd_type = str(payload.get("type", "")).lower().strip()

    if cmd_type == "set_control_enable":
        drive_flag = bool(payload.get("drive_enabled", False)) if "drive_enabled" in payload else None
        manip_flag = bool(payload.get("manip_enabled", False)) if "manip_enabled" in payload else None
        base_flag = bool(payload.get("base_enabled", False)) if "base_enabled" in payload else None
        with state_lock:
            if drive_flag is not None:
                state.drive_enabled = drive_flag
            if manip_flag is not None:
                state.manip_enabled = manip_flag
            if base_flag is not None:
                state.base_enabled = base_flag
        if drive_flag is not None:
            if drive_flag:
                enqueue_serial_command("ARM")
                update_drive_target(enabled=True)
            else:
                update_drive_target(enabled=False, v_cmd=0.0, w_cmd=0.0)
                enqueue_serial_command("STOPALL")
                enqueue_serial_command("DISARM")
        handled = True

    elif cmd_type == "master_arm":
        enqueue_serial_command("ARM")
        handled = True

    elif cmd_type == "master_disarm":
        enqueue_serial_command("DISARM")
        handled = True

    elif cmd_type in {"stop_all", "all_stop"}:
        enqueue_serial_command("STOPALL")
        update_drive_target(enabled=False, v_cmd=0.0, w_cmd=0.0)
        handled = True

    elif cmd_type == "drive_cmd":
        enabled = bool(payload.get("enabled", True))
        v_cmd = float(payload.get("v", payload.get("vx", 0.0)))
        w_cmd = float(payload.get("w", payload.get("wz", 0.0)))
        update_drive_target(enabled=enabled, v_cmd=v_cmd, w_cmd=w_cmd)
        handled = True

    elif cmd_type == "drive_direct":
        left = int(payload.get("left", 0))
        right = int(payload.get("right", 0))
        enqueue_serial_command(format_drive_tokens(left, right))
        with state_lock:
            state.last_drive_cmd_ts = time.time()
        handled = True

    elif cmd_type == "manip_cmd":
        q = payload.get("q", [])
        handled = queue_manip_pose(q)

    elif cmd_type == "base_joint_cmd":
        handled = queue_base_goto(payload.get("q_base", payload.get("q", None)))

    elif cmd_type == "manip_home":
        enqueue_serial_command("HOME_ALL")
        with state_lock:
            state.last_manip_cmd_ts = time.time()
        handled = True

    elif cmd_type == "manip_ascii":
        line = str(payload.get("line", "")).strip()
        if line:
            enqueue_serial_command(line)
            with state_lock:
                state.last_manip_cmd_ts = time.time()
            handled = True

    elif cmd_type == "gripper_cmd":
        mm = payload.get("opening_mm", payload.get("mm", payload.get("value", None)))
        handled = set_latest_gripper_target(mm)

    elif cmd_type == "gripper_ascii":
        line = str(payload.get("line", "")).strip()
        if line:
            if re.match(r"^m\s+-?\d+(?:\.\d+)?$", line, re.IGNORECASE):
                try:
                    handled = set_latest_gripper_target(float(line.split()[1]))
                except Exception:
                    handled = False
            else:
                enqueue_gripper_command(line)
                with state_lock:
                    state.last_gripper_cmd_ts = time.time()
                handled = True

    elif cmd_type == "gripper_stop":
        enqueue_gripper_command("s")
        with state_lock:
            state.last_gripper_cmd_ts = time.time()
        handled = True

    return handled


def serial_master_thread():
    if serial is None:
        print("[SERIAL] pyserial no disponible; puente serial deshabilitado")
        return

    ser = None
    last_connect_try = 0.0
    drive_period = 1.0 / DRIVE_SERIAL_HZ
    manip_query_period = 1.0 / MANIP_STATE_QUERY_HZ
    last_drive_tx = 0.0
    last_manip_query_tx = 0.0
    drive_stop_sent = False

    while running:
        now = time.time()

        if ser is None:
            if now - last_connect_try < SERIAL_RECONNECT_DELAY_S:
                time.sleep(0.05)
                continue
            last_connect_try = now
            try:
                ser = serial.Serial(SERIAL_MASTER_PORT, SERIAL_MASTER_BAUD, timeout=SERIAL_MASTER_TIMEOUT_S)
                with state_lock:
                    state.master_serial_ok = True
                print(f"[SERIAL] Master bridge conectado en {SERIAL_MASTER_PORT} @ {SERIAL_MASTER_BAUD}")
            except Exception as e:
                with state_lock:
                    state.master_serial_ok = False
                print(f"[SERIAL] No se pudo abrir {SERIAL_MASTER_PORT}: {e}")
                ser = None
                time.sleep(0.2)
                continue

        try:
            try:
                while ser.in_waiting:
                    line = ser.readline().decode("utf-8", errors="ignore").strip()
                    if not line:
                        continue
                    with state_lock:
                        state.last_serial_rx_ts = time.time()
                    print(f"[SERIAL RX] {line}")
                    payload = maybe_extract_manip_state(line)
                    if payload is not None:
                        apply_manip_state_payload(payload)
            except Exception:
                pass

            with drive_cmd_lock:
                cur_enabled = drive_enabled
                cur_v = drive_v
                cur_w = drive_w
                cur_last = drive_last_rx_ts

            if cur_enabled and (now - cur_last) <= DRIVE_CMD_TIMEOUT_S:
                if (now - last_drive_tx) >= drive_period:
                    left_raw, right_raw = mix_unicycle_to_dual_raw(cur_v, cur_w)
                    line = format_drive_tokens(left_raw, right_raw)
                    ser.write((line + "\n").encode("utf-8"))
                    last_drive_tx = now
                    drive_stop_sent = False
                    with state_lock:
                        state.last_serial_tx_ts = now
                        state.master_serial_ok = True
            else:
                if not drive_stop_sent:
                    ser.write(b"S,S\n")
                    drive_stop_sent = True
                    last_drive_tx = now
                    with state_lock:
                        state.last_serial_tx_ts = now
                        state.master_serial_ok = True

            try:
                line = serial_cmd_queue.get_nowait()
                if line:
                    ser.write((line + "\n").encode("utf-8"))
                    with state_lock:
                        state.last_serial_tx_ts = time.time()
                        state.master_serial_ok = True
                    print(f"[SERIAL TX] {line}")
            except queue.Empty:
                pass

            with state_lock:
                wants_manip_feedback = state.manip_enabled or state.base_enabled or state.manip_state_valid

            if wants_manip_feedback and (now - last_manip_query_tx) >= manip_query_period:
                ser.write(b"M STATE?\n")
                last_manip_query_tx = now
                with state_lock:
                    state.last_serial_tx_ts = now
                    state.master_serial_ok = True

            time.sleep(0.005)

        except Exception as e:
            print(f"[SERIAL] Error de enlace: {e}")
            with state_lock:
                state.master_serial_ok = False
            try:
                ser.close()
            except Exception:
                pass
            ser = None
            time.sleep(0.2)

    if ser is not None:
        try:
            ser.close()
        except Exception:
            pass


def serial_gripper_thread():
    if serial is None:
        print("[GRIPPER] pyserial no disponible; puente serial de gripper deshabilitado")
        return
    global gripper_target_line, gripper_target_dirty
    ser = None
    last_connect_try = 0.0
    query_period = 1.0 / GRIPPER_QUERY_HZ
    tx_period = 1.0 / GRIPPER_COMMAND_HZ
    last_query_tx = 0.0
    last_target_tx = 0.0

    while running:
        now = time.time()

        if ser is None:
            if now - last_connect_try < GRIPPER_RECONNECT_DELAY_S:
                time.sleep(0.05)
                continue
            last_connect_try = now
            try:
                ser = serial.Serial(GRIPPER_SERIAL_PORT, GRIPPER_SERIAL_BAUD, timeout=GRIPPER_SERIAL_TIMEOUT_S)
                ser.reset_input_buffer()
                ser.reset_output_buffer()
                with state_lock:
                    state.gripper_serial_ok = True
                print(f"[GRIPPER] Conectado en {GRIPPER_SERIAL_PORT} @ {GRIPPER_SERIAL_BAUD}")
            except Exception as e:
                with state_lock:
                    state.gripper_serial_ok = False
                print(f"[GRIPPER] No se pudo abrir {GRIPPER_SERIAL_PORT}: {e}")
                ser = None
                time.sleep(0.2)
                continue

        try:
            try:
                while ser.in_waiting:
                    line = ser.readline().decode("utf-8", errors="ignore").strip()
                    if not line:
                        continue
                    print(f"[GRIPPER RX] {line}")
                    payload = maybe_extract_gripper_state(line)
                    if payload is not None:
                        apply_gripper_state_payload(payload)
            except Exception:
                pass

            # latest target wins
            with gripper_cmd_lock:
                line = gripper_target_line
                dirty = gripper_target_dirty
                if dirty:
                    gripper_target_dirty = False
            if line and dirty and (now - last_target_tx) >= tx_period:
                ser.write((line + "\n").encode("utf-8"))
                last_target_tx = now
                with state_lock:
                    state.last_gripper_cmd_ts = now
                    state.gripper_serial_ok = True
                print(f"[GRIPPER TX] {line}")

            try:
                line2 = gripper_cmd_queue.get_nowait()
                if line2:
                    ser.write((line2 + "\n").encode("utf-8"))
                    with state_lock:
                        state.last_gripper_cmd_ts = time.time()
                        state.gripper_serial_ok = True
                    print(f"[GRIPPER TX] {line2}")
            except queue.Empty:
                pass

            if (now - last_query_tx) >= query_period:
                ser.write(b"p\n")
                last_query_tx = now
                with state_lock:
                    state.gripper_serial_ok = True

            time.sleep(0.005)

        except Exception as e:
            print(f"[GRIPPER] Error de enlace: {e}")
            with state_lock:
                state.gripper_serial_ok = False
            try:
                ser.close()
            except Exception:
                pass
            ser = None
            time.sleep(0.2)

    if ser is not None:
        try:
            ser.close()
        except Exception:
            pass


# ------------------------- LIDAR GRID -------------------------
def deg_to_local_xy_mm(angle_deg: float, dist_mm: float) -> Tuple[float, float]:
    a = math.radians(angle_deg + LIDAR_YAW_DEG)
    x_mm = dist_mm * math.cos(a)
    y_mm = dist_mm * math.sin(a)
    return x_mm, y_mm


def build_lidar_grid(dist_bins: List[int], ts_bins: List[float], mode_name: str, now: float) -> Dict[str, Any]:
    profile = LIDAR_MODES[mode_name]
    cell_m = float(profile["cell_m"])
    radius_m = float(profile["radius_m"])
    grid_size = int(profile["grid_size"])

    occupancy = [0] * (grid_size * grid_size)
    hit_count = 0

    for ang in range(360):
        age = now - ts_bins[ang]
        d_mm = dist_bins[ang]
        if age > LIDAR_STALE_S or d_mm <= 0:
            continue

        d_m = d_mm / 1000.0
        if d_m > radius_m:
            continue

        x_mm, y_mm = deg_to_local_xy_mm(float(ang), float(d_mm))
        x_m = x_mm / 1000.0
        y_m = y_mm / 1000.0

        col = int((x_m + radius_m) / cell_m)
        row = int((radius_m - y_m) / cell_m)

        if 0 <= row < grid_size and 0 <= col < grid_size:
            idx = row * grid_size + col
            if occupancy[idx] == 0:
                occupancy[idx] = 1
                hit_count += 1

    return {
        "ts": round(now, 3),
        "mode": mode_name,
        "grid_size": grid_size,
        "cell_size_m": cell_m,
        "radius_m": radius_m,
        "hits": hit_count,
        "occupancy": occupancy,
    }


# ------------------------- DEPTH / VISION -------------------------
def correct_mm(d_intel_mm: float) -> float:
    d = float(np.clip(d_intel_mm, intel_mm.min(), intel_mm.max()))
    return float(np.interp(d, intel_mm, real_mm))


def build_circle_mask(r: int) -> np.ndarray:
    y, x = np.ogrid[-r:r + 1, -r:r + 1]
    return (x * x + y * y) <= (r * r)


def corrected_depth_m_from_mm(mean_mm: float, max_mm: float = MAX_VALID_DEPTH_MM) -> Optional[float]:
    if mean_mm <= 0 or mean_mm > max_mm:
        return None
    return correct_mm(mean_mm) / 1000.0


def median_depth_raw_in_circle(depth_z16: np.ndarray, cx: int, cy: int, r: int, circle_mask: np.ndarray) -> Tuple[Optional[float], int]:
    h, w = depth_z16.shape
    x1, x2 = cx - r, cx + r
    y1, y2 = cy - r, cy + r
    if x1 < 0 or y1 < 0 or x2 >= w or y2 >= h:
        return None, 0
    patch = depth_z16[y1:y2 + 1, x1:x2 + 1]
    vals = patch[circle_mask]
    vals = vals[vals > 0]
    if vals.size == 0:
        return None, 0
    return float(np.median(vals)), int(vals.size)


def get_corrected_depth_m_at_point(
    depth_z16: np.ndarray,
    u: int,
    v: int,
    r: int,
    circle_mask: np.ndarray,
    depth_scale: float,
) -> Tuple[Optional[float], int]:
    median_raw, n = median_depth_raw_in_circle(depth_z16, u, v, r, circle_mask)
    if median_raw is None:
        return None, 0
    median_mm = median_raw * depth_scale * 1000.0
    z_m = corrected_depth_m_from_mm(median_mm)
    return z_m, n


def get_corrected_depth_m_from_mask(depth_z16: np.ndarray, mask_bool: np.ndarray, depth_scale: float) -> Tuple[Optional[float], int]:
    valid = mask_bool & (depth_z16 > 0)
    vals = depth_z16[valid]
    if vals.size == 0:
        return None, 0
    median_raw = float(np.median(vals))
    median_mm = median_raw * depth_scale * 1000.0
    z_m = corrected_depth_m_from_mm(median_mm)
    return z_m, int(vals.size)


def bbox_center_xyxy(xyxy: Tuple[float, float, float, float]) -> Tuple[int, int]:
    x1, y1, x2, y2 = xyxy
    return int((x1 + x2) / 2.0), int((y1 + y2) / 2.0)


def get_mid_hip_keypoint_for_index(result, person_idx: int) -> Optional[Tuple[int, int]]:
    if result.keypoints is None:
        return None
    kxy = result.keypoints.xy
    if kxy is None or len(kxy) <= person_idx:
        return None

    pts = kxy[person_idx].cpu().numpy()
    if pts.shape[0] <= max(LEFT_HIP, RIGHT_HIP):
        return None

    kconf = getattr(result.keypoints, "conf", None)
    if kconf is not None and len(kconf) > person_idx:
        confs = kconf[person_idx].cpu().numpy()
        if confs[LEFT_HIP] < POSE_KEYPOINT_CONF_TH or confs[RIGHT_HIP] < POSE_KEYPOINT_CONF_TH:
            return None

    u = int((pts[LEFT_HIP, 0] + pts[RIGHT_HIP, 0]) / 2.0)
    v = int((pts[LEFT_HIP, 1] + pts[RIGHT_HIP, 1]) / 2.0)
    return u, v


def find_pose_targets(result, depth_z16: np.ndarray, depth_scale: float, circle_mask: np.ndarray) -> List[Dict[str, Any]]:
    targets: List[Dict[str, Any]] = []
    if result.boxes is None or len(result.boxes) == 0:
        return targets

    for i, box in enumerate(result.boxes):
        conf = float(box.conf.item())
        if conf < VISION_CONF_TH:
            continue

        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().tolist()
        point = get_mid_hip_keypoint_for_index(result, i)
        point_source = "mid_hip"
        if point is None:
            point = bbox_center_xyxy((x1, y1, x2, y2))
            point_source = "bbox_center"

        u, v = point
        z_m, n_samples = get_corrected_depth_m_at_point(depth_z16, u, v, DEPTH_SAMPLE_RADIUS, circle_mask, depth_scale)

        targets.append({
            "index": i,
            "label": "person",
            "conf": conf,
            "bbox": [int(x1), int(y1), int(x2), int(y2)],
            "u": int(u),
            "v": int(v),
            "point_source": point_source,
            "distance_m": z_m,
            "samples": n_samples,
        })

    return targets


def find_segment_targets(result, depth_z16: np.ndarray, depth_scale: float, circle_mask: np.ndarray) -> List[Dict[str, Any]]:
    targets: List[Dict[str, Any]] = []
    if result.boxes is None or len(result.boxes) == 0:
        return targets

    masks_data = None
    if result.masks is not None:
        masks_data = result.masks.data.cpu().numpy()

    h, w = depth_z16.shape[:2]
    for i, box in enumerate(result.boxes):
        conf = float(box.conf.item())
        if conf < VISION_CONF_TH:
            continue

        cls_id = int(box.cls.item())
        if TARGET_CLASS_IDS_SEG is not None and cls_id not in TARGET_CLASS_IDS_SEG:
            continue

        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().tolist()
        cx, cy = bbox_center_xyxy((x1, y1, x2, y2))
        class_name = result.names.get(cls_id, str(cls_id))

        z_m: Optional[float] = None
        n_samples = 0
        mask_bool = None
        centroid_source = "bbox_center"

        if masks_data is not None and i < len(masks_data):
            mask = cv2.resize(masks_data[i], (w, h), interpolation=cv2.INTER_NEAREST)
            mask_bool = mask > 0.5
            if int(mask_bool.sum()) >= MIN_MASK_PIXELS:
                M = cv2.moments(mask_bool.astype(np.uint8))
                if M["m00"] > 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    centroid_source = "mask_centroid"
                z_m, n_samples = get_corrected_depth_m_from_mask(depth_z16, mask_bool, depth_scale)

        if z_m is None:
            z_m, n_samples = get_corrected_depth_m_at_point(depth_z16, cx, cy, DEPTH_SAMPLE_RADIUS, circle_mask, depth_scale)
            centroid_source = f"{centroid_source}_fallback_circle"

        targets.append({
            "index": i,
            "label": class_name,
            "class_id": cls_id,
            "conf": conf,
            "bbox": [int(x1), int(y1), int(x2), int(y2)],
            "u": int(cx),
            "v": int(cy),
            "point_source": centroid_source,
            "distance_m": z_m,
            "samples": n_samples,
            "has_mask": mask_bool is not None,
            "mask": mask_bool,
        })

    return targets


def pick_best_target(targets: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    valid = [t for t in targets if t.get("distance_m") is not None]
    if valid:
        return min(valid, key=lambda t: float(t["distance_m"]))
    if targets:
        return max(targets, key=lambda t: float(t.get("conf", 0.0)))
    return None


def sanitize_target_for_json(target: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if target is None:
        return None
    clean = dict(target)
    clean.pop("mask", None)
    return clean


def draw_pose_overlay(annotated: np.ndarray, selected: Optional[Dict[str, Any]]) -> np.ndarray:
    if selected is None:
        return annotated
    u, v = int(selected["u"]), int(selected["v"])
    cv2.circle(annotated, (u, v), 6, (0, 255, 255), -1)
    cv2.circle(annotated, (u, v), DEPTH_SAMPLE_RADIUS, (0, 255, 255), 2)
    label = f"person {selected['conf']:.2f}"
    if selected.get("distance_m") is not None:
        label += f" | Z={selected['distance_m']:.2f}m"
    cv2.putText(annotated, label, (max(10, u - 80), max(25, v - 12)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2, cv2.LINE_AA)
    return annotated


def draw_segment_overlay(annotated: np.ndarray, selected: Optional[Dict[str, Any]]) -> np.ndarray:
    if selected is None:
        return annotated
    u, v = int(selected["u"]), int(selected["v"])
    cv2.circle(annotated, (u, v), 6, (0, 255, 255), -1)
    if selected.get("mask") is not None:
        mask_u8 = selected["mask"].astype(np.uint8) * 255
        contours, _ = cv2.findContours(mask_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(annotated, contours, -1, (0, 255, 255), 2)
    else:
        cv2.circle(annotated, (u, v), DEPTH_SAMPLE_RADIUS, (0, 255, 255), 2)
    label = f"{selected['label']} {selected['conf']:.2f}"
    if selected.get("distance_m") is not None:
        label += f" | Z={selected['distance_m']:.2f}m"
    cv2.putText(annotated, label, (max(10, u - 80), max(25, v - 12)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2, cv2.LINE_AA)
    return annotated


class VisionModelRegistry:
    def __init__(self):
        self.pose_model: Optional[YOLO] = None
        self.seg_model: Optional[YOLO] = None

    def get_pose(self) -> YOLO:
        if self.pose_model is None:
            print(f"[VISION] Cargando modelo pose: {POSE_MODEL_PATH}")
            self.pose_model = YOLO(POSE_MODEL_PATH)
            with state_lock:
                state.pose_model_ready = True
        return self.pose_model

    def get_segment(self) -> YOLO:
        if self.seg_model is None:
            print(f"[VISION] Cargando modelo segment: {SEG_MODEL_PATH}")
            self.seg_model = YOLO(SEG_MODEL_PATH)
            with state_lock:
                state.seg_model_ready = True
        return self.seg_model


# ------------------------- WALLS PIPELINE -------------------------
def build_occupancy_grid(points_xy_m: np.ndarray, resolution_m: float, margin_m: float):
    min_xy = points_xy_m.min(axis=0)
    max_xy = points_xy_m.max(axis=0)

    min_x, min_y = float(min_xy[0] - margin_m), float(min_xy[1] - margin_m)
    max_x, max_y = float(max_xy[0] + margin_m), float(max_xy[1] + margin_m)

    width = int(math.ceil((max_x - min_x) / resolution_m))
    height = int(math.ceil((max_y - min_y) / resolution_m))
    width = max(width, 1)
    height = max(height, 1)

    grid = np.zeros((height, width), dtype=np.uint8)

    ix = ((points_xy_m[:, 0] - min_x) / resolution_m).astype(np.int32)
    iy = ((points_xy_m[:, 1] - min_y) / resolution_m).astype(np.int32)

    valid = (ix >= 0) & (ix < width) & (iy >= 0) & (iy < height)
    ix = ix[valid]
    iy = iy[valid]

    iy_img = (height - 1) - iy
    grid[iy_img, ix] = 255

    origin = (min_x, min_y)
    return grid, origin, width, height


def clean_grid(grid: np.ndarray):
    g = grid.copy()

    if WALLS_DILATE_ITER and WALLS_DILATE_KERNEL:
        k = cv2.getStructuringElement(cv2.MORPH_RECT, (WALLS_DILATE_KERNEL, WALLS_DILATE_KERNEL))
        g = cv2.dilate(g, k, iterations=WALLS_DILATE_ITER)

    if WALLS_CLOSE_KERNEL and WALLS_CLOSE_ITER:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (WALLS_CLOSE_KERNEL, WALLS_CLOSE_KERNEL))
        g = cv2.morphologyEx(g, cv2.MORPH_CLOSE, k, iterations=WALLS_CLOSE_ITER)

    if WALLS_OPEN_KERNEL and WALLS_OPEN_ITER:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (WALLS_OPEN_KERNEL, WALLS_OPEN_KERNEL))
        g = cv2.morphologyEx(g, cv2.MORPH_OPEN, k, iterations=WALLS_OPEN_ITER)

    return g


def remove_small_components(binary_img: np.ndarray, min_area_px: int):
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary_img, connectivity=8)
    out = binary_img.copy()
    for label in range(1, num_labels):
        if stats[label, cv2.CC_STAT_AREA] < min_area_px:
            out[labels == label] = 0
    return out


def skeletonize(binary_img: np.ndarray):
    if hasattr(cv2, "ximgproc") and hasattr(cv2.ximgproc, "thinning"):
        return cv2.ximgproc.thinning(binary_img)
    return None


def neighbors8(y, x, h, w):
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy == 0 and dx == 0:
                continue
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w:
                yield ny, nx


def skeleton_to_polylines_safe(skel: np.ndarray, max_steps_factor=10):
    h, w = skel.shape
    on = skel > 0

    deg = np.zeros((h, w), dtype=np.uint8)
    ys, xs = np.where(on)
    for y, x in zip(ys, xs):
        c = 0
        for ny, nx in neighbors8(y, x, h, w):
            if on[ny, nx]:
                c += 1
        deg[y, x] = c

    nodes = set(zip(*np.where((deg == 1) | (deg >= 3))))
    visited_edges = set()
    visited_pixels_global = set()
    polylines = []

    def mark_edge(a, b):
        visited_edges.add((a, b))
        visited_edges.add((b, a))

    max_steps = max(200, int(max_steps_factor * max(1, int(on.sum()))))

    for node in nodes:
        y0, x0 = node
        for ny, nx in neighbors8(y0, x0, h, w):
            if not on[ny, nx]:
                continue
            a = node
            b = (ny, nx)
            if (a, b) in visited_edges:
                continue

            path = [a]
            prev = a
            cur = b
            local_visited = {a}
            steps = 0

            while True:
                steps += 1
                if steps > max_steps:
                    break

                path.append(cur)
                local_visited.add(cur)

                if cur in nodes and cur != node:
                    break

                y, x = cur
                nbrs = []
                for nny, nnx in neighbors8(y, x, h, w):
                    if on[nny, nnx] and (nny, nnx) != prev:
                        nbrs.append((nny, nnx))
                if not nbrs:
                    break

                nxt = None
                for cand in nbrs:
                    if cand not in local_visited:
                        nxt = cand
                        break
                if nxt is None:
                    break

                prev, cur = cur, nxt

            for i in range(len(path) - 1):
                mark_edge(path[i], path[i + 1])
                visited_pixels_global.add(path[i])
            visited_pixels_global.add(path[-1])

            if len(path) >= WALLS_MIN_POLYLINE_LEN_PX:
                polylines.append([(p[1], p[0]) for p in path])

    ys2, xs2 = np.where(on)
    for y, x in zip(ys2, xs2):
        start = (y, x)
        if start in visited_pixels_global or start in nodes:
            continue

        path = [start]
        visited_local = {start}
        prev = None
        cur = start
        steps = 0

        while True:
            steps += 1
            if steps > max_steps:
                break

            y0, x0 = cur
            nbrs = []
            for ny, nx in neighbors8(y0, x0, h, w):
                if on[ny, nx] and (ny, nx) != prev:
                    nbrs.append((ny, nx))
            if not nbrs:
                break

            nxt = nbrs[0]
            prev, cur = cur, nxt

            if cur == start or cur in visited_local:
                break

            visited_local.add(cur)
            path.append(cur)

        for p in path:
            visited_pixels_global.add(p)

        if len(path) >= WALLS_MIN_POLYLINE_LEN_PX:
            polylines.append([(p[1], p[0]) for p in path])

    return polylines


def simplify_polyline(poly, eps_px):
    cnt = np.array(poly, dtype=np.int32).reshape((-1, 1, 2))
    approx = cv2.approxPolyDP(cnt, eps_px, False)
    return [(int(p[0][0]), int(p[0][1])) for p in approx]


def polyline_to_colinear_segments(poly, angle_tol_deg=15, min_len_px=3):
    if len(poly) < 2:
        return []

    def seg_angle(p, q):
        return math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))

    def manhattan_len(p, q):
        return abs(q[0] - p[0]) + abs(q[1] - p[1])

    segs = []
    start = poly[0]
    prev = poly[0]
    prev_ang = None

    for i in range(1, len(poly)):
        cur = poly[i]
        ang = seg_angle(prev, cur)

        if prev_ang is None:
            prev_ang = ang
            prev = cur
            continue

        diff = (ang - prev_ang + 180) % 360 - 180
        if abs(diff) > angle_tol_deg:
            if manhattan_len(start, prev) >= min_len_px:
                segs.append((start[0], start[1], prev[0], prev[1]))
            start = prev
            prev_ang = ang
        prev = cur

    if manhattan_len(start, prev) >= min_len_px:
        segs.append((start[0], start[1], prev[0], prev[1]))

    return segs


def snap_segment_endpoints(segments, snap_dist_px=3):
    if not segments:
        return segments

    pts = []
    for i, (x1, y1, x2, y2) in enumerate(segments):
        pts.append((i, 0, x1, y1))
        pts.append((i, 1, x2, y2))

    pts_np = np.array([(p[2], p[3]) for p in pts], dtype=np.int32)
    used = np.zeros(len(pts), dtype=bool)
    clusters = []

    for i in range(len(pts)):
        if used[i]:
            continue
        pi = pts_np[i]
        d2 = np.sum((pts_np - pi) ** 2, axis=1)
        idxs = np.where(d2 <= snap_dist_px * snap_dist_px)[0]
        used[idxs] = True
        cpts = pts_np[idxs]
        cx = int(round(cpts[:, 0].mean()))
        cy = int(round(cpts[:, 1].mean()))
        clusters.append((idxs, cx, cy))

    segs = [list(s) for s in segments]
    for idxs, cx, cy in clusters:
        for j in idxs:
            seg_i, which, _, _ = pts[j]
            if which == 0:
                segs[seg_i][0], segs[seg_i][1] = cx, cy
            else:
                segs[seg_i][2], segs[seg_i][3] = cx, cy

    return [tuple(s) for s in segs]


def extend_perpendicular_corners(segments, max_extend_px=4, angle_tol_deg=15):
    if not segments:
        return segments

    def seg_dir(x1, y1, x2, y2):
        ang = math.degrees(math.atan2(y2 - y1, x2 - x1))
        return (ang + 180) % 180

    segs = [list(s) for s in segments]
    n = len(segs)

    for i in range(n):
        x1, y1, x2, y2 = segs[i]
        ang_i = seg_dir(x1, y1, x2, y2)
        is_h = min(abs(ang_i - 0), abs(ang_i - 180)) < angle_tol_deg
        is_v = abs(ang_i - 90) < angle_tol_deg
        if not (is_h or is_v):
            continue

        ends_i = [(x1, y1), (x2, y2)]
        for j in range(n):
            if i == j:
                continue
            a1, b1, a2, b2 = segs[j]
            ang_j = seg_dir(a1, b1, a2, b2)
            is_hj = min(abs(ang_j - 0), abs(ang_j - 180)) < angle_tol_deg
            is_vj = abs(ang_j - 90) < angle_tol_deg
            if not (is_hj or is_vj):
                continue
            if not ((is_h and is_vj) or (is_v and is_hj)):
                continue

            ends_j = [(a1, b1), (a2, b2)]
            for ei in range(2):
                for ej in range(2):
                    px, py = ends_i[ei]
                    qx, qy = ends_j[ej]
                    if (px - qx) ** 2 + (py - qy) ** 2 > (max_extend_px * max_extend_px):
                        continue

                    if is_h and is_vj:
                        ix, iy = qx, py
                    elif is_v and is_hj:
                        ix, iy = px, qy
                    else:
                        continue

                    if ei == 0:
                        segs[i][0], segs[i][1] = ix, iy
                    else:
                        segs[i][2], segs[i][3] = ix, iy

                    if ej == 0:
                        segs[j][0], segs[j][1] = ix, iy
                    else:
                        segs[j][2], segs[j][3] = ix, iy

    return [tuple(s) for s in segs]


def pixel_to_world_m(x_pix, y_pix, origin, resolution_m, height):
    x_m = origin[0] + (x_pix + 0.5) * resolution_m
    y_cell = (height - 1 - y_pix) + 0.5
    y_m = origin[1] + y_cell * resolution_m
    return float(x_m), float(y_m)


def normalize_key(x1, y1, x2, y2):
    if (x2, y2) < (x1, y1):
        return (x2, y2, x1, y1)
    return (x1, y1, x2, y2)


def seg_m_to_key_mm(x1, y1, x2, y2):
    x1i = int(round(x1 * MM_PER_M))
    y1i = int(round(y1 * MM_PER_M))
    x2i = int(round(x2 * MM_PER_M))
    y2i = int(round(y2 * MM_PER_M))
    return normalize_key(x1i, y1i, x2i, y2i)


def segments_from_grid(cleaned_grid: np.ndarray) -> List[Tuple[int, int, int, int]]:
    skel = skeletonize(cleaned_grid)
    if skel is not None:
        polylines = skeleton_to_polylines_safe(skel)
        polylines_s = [simplify_polyline(p, WALLS_SIMPLIFY_EPS_PX) for p in polylines]
        segments_pix = []
        for poly in polylines_s:
            segments_pix.extend(polyline_to_colinear_segments(poly, WALLS_ANGLE_TOL_DEG, WALLS_MIN_SEG_LEN_PX))
        segments_pix = snap_segment_endpoints(segments_pix, WALLS_SNAP_DIST_PX)
        segments_pix = extend_perpendicular_corners(segments_pix, WALLS_EXTEND_MAX_PX, WALLS_ORTHO_ANGLE_TOL_DEG)
        return segments_pix

    lines = cv2.HoughLinesP(
        cleaned_grid,
        rho=1,
        theta=np.pi / 180.0,
        threshold=20,
        minLineLength=max(8, WALLS_MIN_SEG_LEN_PX),
        maxLineGap=5,
    )
    if lines is None:
        return []
    segs = []
    for line in lines:
        x1, y1, x2, y2 = [int(v) for v in line[0]]
        segs.append((x1, y1, x2, y2))
    segs = snap_segment_endpoints(segs, WALLS_SNAP_DIST_PX)
    segs = extend_perpendicular_corners(segs, WALLS_EXTEND_MAX_PX, WALLS_ORTHO_ANGLE_TOL_DEG)
    return segs


def build_walls_segment_keys(points_xy_m: np.ndarray) -> Tuple[Set[Tuple[int, int, int, int]], Dict[str, Any]]:
    grid_raw, origin, w, h = build_occupancy_grid(points_xy_m, WALLS_RESOLUTION_M, WALLS_GRID_MARGIN_M)
    grid_clean = remove_small_components(clean_grid(grid_raw), WALLS_MIN_COMPONENT_AREA_PX)
    segments_pix = segments_from_grid(grid_clean)

    keys: Set[Tuple[int, int, int, int]] = set()
    for (x1, y1, x2, y2) in segments_pix:
        wx1, wy1 = pixel_to_world_m(x1, y1, origin, WALLS_RESOLUTION_M, h)
        wx2, wy2 = pixel_to_world_m(x2, y2, origin, WALLS_RESOLUTION_M, h)
        keys.add(seg_m_to_key_mm(wx1, wy1, wx2, wy2))

    meta = {
        "origin_m": [round(float(origin[0]), 3), round(float(origin[1]), 3)],
        "grid_w": int(w),
        "grid_h": int(h),
        "resolution_m": WALLS_RESOLUTION_M,
        "segment_count": len(keys),
    }
    return keys, meta


def encode_walls_snapshot(seq: int, keys: List[Tuple[int, int, int, int]]) -> bytes:
    n = min(len(keys), MAX_WALLS_SEGMENTS_IN_SNAPSHOT)
    header = struct.pack("<4sB I I", WALLS_SNAPSHOT_MAGIC, WALLS_VERSION, seq, n)
    body = bytearray()
    for k in keys[:n]:
        body += struct.pack("<iiii", *k)
    return header + body


def encode_walls_delta(seq: int, adds_keys: List[Tuple[int, int, int, int]], rems_keys: List[Tuple[int, int, int, int]]) -> bytes:
    n_add = min(len(adds_keys), MAX_WALLS_ADDS_PER_PACKET)
    n_rem = min(len(rems_keys), MAX_WALLS_REMS_PER_PACKET)
    header = struct.pack("<4sB I H H", WALLS_DELTA_MAGIC, WALLS_VERSION, seq, n_add, n_rem)
    body = bytearray()
    for k in adds_keys[:n_add]:
        body += struct.pack("<iiii", *k)
    for k in rems_keys[:n_rem]:
        body += struct.pack("<iiii", *k)
    return header + body


def quantize_points_to_mm(points_xy_m: np.ndarray) -> List[Tuple[int, int]]:
    if points_xy_m.size == 0:
        return []

    pts_mm = np.rint(points_xy_m * MM_PER_M).astype(np.int32)
    unique = np.unique(pts_mm, axis=0)
    return [(int(p[0]), int(p[1])) for p in unique[:MAX_POINTS_IN_PACKET]]


def encode_points_packet(magic: bytes, seq: int, points_mm: List[Tuple[int, int]]) -> bytes:
    n = min(len(points_mm), MAX_POINTS_IN_PACKET)
    header = struct.pack("<4sB I I", magic, POINTS_VERSION, seq, n)
    body = bytearray()
    for x_mm, y_mm in points_mm[:n]:
        body += struct.pack("<ii", x_mm, y_mm)
    return header + body


# ------------------------- COMMAND PARSING -------------------------
def parse_command(topic: str, raw: str) -> Tuple[Optional[str], Optional[str], Optional[bool], Optional[bool], bool, bool, Dict[str, Any]]:
    camera_mode = None
    lidar_mode = None
    walls_enabled = None
    points_enabled = None
    request_walls_snapshot = False
    request_points_snapshot = False
    meta: Dict[str, Any] = {"topic": topic, "raw": raw}

    try:
        payload = json.loads(raw)
    except Exception:
        payload = raw.strip()

    if isinstance(payload, dict):
        cmd_type = str(payload.get("type", "")).lower().strip()

        if "camera_mode" in payload:
            candidate = str(payload.get("camera_mode", "")).lower().strip()
            if candidate in VALID_CAMERA_MODES:
                camera_mode = candidate

        if "video_mode" in payload:
            candidate = str(payload.get("video_mode", "")).lower().strip()
            if candidate == "rgb":
                camera_mode = "normal"
            elif candidate == "off":
                camera_mode = "off"
            elif candidate in VALID_CAMERA_MODES:
                camera_mode = candidate

        if "lidar_mode" in payload:
            candidate = str(payload.get("lidar_mode", "")).lower().strip()
            if candidate in VALID_LIDAR_MODES:
                lidar_mode = candidate

        if "walls_enabled" in payload:
            walls_enabled = bool(payload.get("walls_enabled"))

        if "points_enabled" in payload:
            points_enabled = bool(payload.get("points_enabled"))

        if cmd_type == "set_camera_mode":
            candidate = str(payload.get("mode", "")).lower().strip()
            if candidate in VALID_CAMERA_MODES:
                camera_mode = candidate

        if cmd_type == "set_video_mode":
            candidate = str(payload.get("mode", "")).lower().strip()
            if candidate == "rgb":
                camera_mode = "normal"
            elif candidate == "off":
                camera_mode = "off"
            elif candidate in VALID_CAMERA_MODES:
                camera_mode = candidate

        if cmd_type == "set_lidar_mode":
            candidate = str(payload.get("mode", "")).lower().strip()
            if candidate in VALID_LIDAR_MODES:
                lidar_mode = candidate

        if cmd_type == "set_walls_mode":
            walls_enabled = bool(payload.get("enabled", payload.get("mode", True)))

        if cmd_type == "set_points_mode":
            points_enabled = bool(payload.get("enabled", payload.get("mode", True)))

        if cmd_type == "set_lidar_3d_mode":
            candidate = str(payload.get("mode", "")).lower().strip()
            if candidate == "off":
                walls_enabled = False
                points_enabled = False
            elif candidate == "walls":
                walls_enabled = True
                points_enabled = False
                request_walls_snapshot = True
            elif candidate == "points":
                walls_enabled = False
                points_enabled = True
                request_points_snapshot = True
            elif candidate == "both":
                walls_enabled = True
                points_enabled = True
                request_walls_snapshot = True
                request_points_snapshot = True

        if cmd_type == "request_walls_snapshot":
            request_walls_snapshot = True

        if cmd_type == "request_points_snapshot":
            request_points_snapshot = True

        if cmd_type == "enter_scene":
            scene_name = str(payload.get("scene", "")).lower().strip()
            if scene_name == "walls":
                walls_enabled = True
                request_walls_snapshot = True
            elif scene_name in {"mr", "mr_view", "lidar3d"}:
                request_walls_snapshot = True
                request_points_snapshot = True

        if cmd_type == "exit_scene":
            scene_name = str(payload.get("scene", "")).lower().strip()
            if scene_name == "walls":
                walls_enabled = False
            elif scene_name in {"mr", "mr_view", "lidar3d"}:
                walls_enabled = False
                points_enabled = False

        meta["parsed"] = payload
        return camera_mode, lidar_mode, walls_enabled, points_enabled, request_walls_snapshot, request_points_snapshot, meta

    if isinstance(payload, str):
        text = payload.lower().strip()
        if text in VALID_CAMERA_MODES:
            camera_mode = text
        elif text in VALID_LIDAR_MODES:
            lidar_mode = text
        elif text == "rgb":
            camera_mode = "normal"
        elif text.startswith("camera:"):
            candidate = text.split(":", 1)[1].strip()
            if candidate in VALID_CAMERA_MODES:
                camera_mode = candidate
        elif text.startswith("video:"):
            candidate = text.split(":", 1)[1].strip()
            if candidate == "rgb":
                camera_mode = "normal"
            elif candidate == "off":
                camera_mode = "off"
            elif candidate in VALID_CAMERA_MODES:
                camera_mode = candidate
        elif text.startswith("lidar:"):
            candidate = text.split(":", 1)[1].strip()
            if candidate in VALID_LIDAR_MODES:
                lidar_mode = candidate
        elif text.startswith("walls:"):
            candidate = text.split(":", 1)[1].strip()
            if candidate in {"on", "true", "1", "enable", "enabled"}:
                walls_enabled = True
            elif candidate in {"off", "false", "0", "disable", "disabled"}:
                walls_enabled = False
        elif text.startswith("points:"):
            candidate = text.split(":", 1)[1].strip()
            if candidate in {"on", "true", "1", "enable", "enabled"}:
                points_enabled = True
            elif candidate in {"off", "false", "0", "disable", "disabled"}:
                points_enabled = False
        elif text.startswith("lidar3d:"):
            candidate = text.split(":", 1)[1].strip()
            if candidate == "off":
                walls_enabled = False
                points_enabled = False
            elif candidate == "walls":
                walls_enabled = True
                points_enabled = False
                request_walls_snapshot = True
            elif candidate == "points":
                walls_enabled = False
                points_enabled = True
                request_points_snapshot = True
            elif candidate == "both":
                walls_enabled = True
                points_enabled = True
                request_walls_snapshot = True
                request_points_snapshot = True
        elif text == "request_walls_snapshot":
            request_walls_snapshot = True
        elif text == "request_points_snapshot":
            request_points_snapshot = True

    return camera_mode, lidar_mode, walls_enabled, points_enabled, request_walls_snapshot, request_points_snapshot, meta

    if isinstance(payload, str):
        text = payload.lower().strip()
        if text in VALID_CAMERA_MODES:
            camera_mode = text
        elif text in VALID_LIDAR_MODES:
            lidar_mode = text
        elif text == "rgb":
            camera_mode = "normal"
        elif text.startswith("camera:"):
            candidate = text.split(":", 1)[1].strip()
            if candidate in VALID_CAMERA_MODES:
                camera_mode = candidate
        elif text.startswith("video:"):
            candidate = text.split(":", 1)[1].strip()
            if candidate == "rgb":
                camera_mode = "normal"
            elif candidate == "off":
                camera_mode = "off"
            elif candidate in VALID_CAMERA_MODES:
                camera_mode = candidate
        elif text.startswith("lidar:"):
            candidate = text.split(":", 1)[1].strip()
            if candidate in VALID_LIDAR_MODES:
                lidar_mode = candidate
        elif text.startswith("walls:"):
            candidate = text.split(":", 1)[1].strip()
            if candidate in {"on", "true", "1", "enable", "enabled"}:
                walls_enabled = True
            elif candidate in {"off", "false", "0", "disable", "disabled"}:
                walls_enabled = False
        elif text == "request_walls_snapshot":
            request_walls_snapshot = True

    return camera_mode, lidar_mode, walls_enabled, request_walls_snapshot, meta


# ------------------------- PUB THREADS -------------------------
def sensor_pub_thread(context: zmq.Context):
    socket = context.socket(zmq.PUB)
    socket.setsockopt(zmq.SNDHWM, ZMQ_SNDHWM_SENSORS)
    socket.bind(f"tcp://*:{PORT_SENSORS}")
    print(f"[ZMQ] Sensores PUB en tcp://*:{PORT_SENSORS}")

    while running or not sensor_queue.empty():
        try:
            msg = sensor_queue.get(timeout=0.1)
            socket.send_multipart(msg)
        except queue.Empty:
            continue
        except Exception as e:
            print(f"[ZMQ][SENSORS] Error enviando: {e}")
            time.sleep(0.05)

    socket.close(linger=0)


def video_pub_thread(context: zmq.Context):
    socket = context.socket(zmq.PUB)
    socket.setsockopt(zmq.SNDHWM, ZMQ_SNDHWM_VIDEO)
    socket.bind(f"tcp://*:{PORT_VIDEO}")
    print(f"[ZMQ] Video PUB en tcp://*:{PORT_VIDEO}")

    while running or not video_queue.empty():
        try:
            msg = video_queue.get(timeout=0.1)
            socket.send_multipart(msg)
        except queue.Empty:
            continue
        except Exception as e:
            print(f"[ZMQ][VIDEO] Error enviando: {e}")
            time.sleep(0.05)

    socket.close(linger=0)


def walls_pub_thread(context: zmq.Context):
    socket = context.socket(zmq.PUB)
    socket.setsockopt(zmq.SNDHWM, ZMQ_SNDHWM_WALLS)
    socket.bind(f"tcp://*:{PORT_WALLS}")
    print(f"[ZMQ] Walls PUB en tcp://*:{PORT_WALLS}")

    while running or not walls_queue.empty():
        try:
            msg = walls_queue.get(timeout=0.1)
            socket.send_multipart(msg)
        except queue.Empty:
            continue
        except Exception as e:
            print(f"[ZMQ][WALLS] Error enviando: {e}")
            time.sleep(0.05)

    socket.close(linger=0)


def command_listener_thread(context: zmq.Context):
    socket = context.socket(zmq.SUB)
    socket.bind(f"tcp://*:{PORT_CMD}")
    socket.setsockopt(zmq.SUBSCRIBE, b"")
    print(f"[ZMQ] Comandos SUB en tcp://*:{PORT_CMD}")

    while running:
        try:
            frames = socket.recv_multipart(flags=zmq.NOBLOCK)
            if len(frames) >= 2:
                topic = frames[0].decode("utf-8", errors="ignore")
                raw = frames[1].decode("utf-8", errors="ignore")

                try:
                    payload = json.loads(raw)
                except Exception:
                    payload = raw.strip()

                camera_mode, lidar_mode, walls_enabled, points_enabled, request_walls_snapshot, request_points_snapshot, _ = parse_command(topic, raw)
                control_handled = handle_control_command(payload)

                with state_lock:
                    state.last_cmd_ts = time.time()
                    state.cmd_link_ok = True

                snap = set_active_modes(
                    camera_mode=camera_mode,
                    lidar_mode=lidar_mode,
                    walls_enabled=walls_enabled,
                    points_enabled=points_enabled,
                    request_snapshot=request_walls_snapshot,
                    request_points_snapshot=request_points_snapshot,
                )
                print(
                    "[CMD] topic={} raw={} -> camera={} lidar={} walls={} points={} ctrl={}".format(
                        topic,
                        raw,
                        snap["active_camera_mode"],
                        snap["active_lidar_mode"],
                        snap["walls_enabled"],
                        snap["points_enabled"],
                        control_handled,
                    )
                )
        except zmq.Again:
            time.sleep(0.005)
        except Exception as e:
            print(f"[CMD] Error: {e}")
            time.sleep(0.05)

    socket.close(linger=0)


def status_thread():
    period = 1.0 / STAT_PUBLISH_HZ
    while running:
        with state_lock:
            snap = state.snapshot()
        publish_sensor("stat", snap)
        time.sleep(period)


# ------------------------- CAMERA THREAD -------------------------
def camera_thread():
    print("[CAM] Inicializando RealSense...")
    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.color, COLOR_W, COLOR_H, rs.format.bgr8, COLOR_FPS)
    config.enable_stream(rs.stream.depth, DEPTH_W, DEPTH_H, rs.format.z16, DEPTH_FPS)

    align = rs.align(rs.stream.color)
    registry = VisionModelRegistry()
    circle_mask = build_circle_mask(DEPTH_SAMPLE_RADIUS)
    dbg_t = time.time()
    video_count = 0
    last_vision_pub_t = 0.0

    try:
        profile = pipeline.start(config)
        depth_sensor = profile.get_device().first_depth_sensor()
        depth_scale = float(depth_sensor.get_depth_scale())

        color_stream = profile.get_stream(rs.stream.color).as_video_stream_profile()
        depth_stream = profile.get_stream(rs.stream.depth).as_video_stream_profile()
        color_intr = color_stream.get_intrinsics()
        depth_intr = depth_stream.get_intrinsics()

        with state_lock:
            state.camera_ok = True
            state.depth_scale = depth_scale
            state.last_camera_ts = time.time()

        publish_sensor(
            "cam_info",
            {
                "ts": round(time.time(), 3),
                "color": {
                    "w": color_intr.width,
                    "h": color_intr.height,
                    "fx": color_intr.fx,
                    "fy": color_intr.fy,
                    "ppx": color_intr.ppx,
                    "ppy": color_intr.ppy,
                },
                "depth": {
                    "w": depth_intr.width,
                    "h": depth_intr.height,
                    "fx": depth_intr.fx,
                    "fy": depth_intr.fy,
                    "ppx": depth_intr.ppx,
                    "ppy": depth_intr.ppy,
                    "scale_m_per_unit": depth_scale,
                },
                "vision": {
                    "pose_model": POSE_MODEL_PATH,
                    "segment_model": SEG_MODEL_PATH,
                    "imgsz": VISION_IMGSZ,
                    "conf_th": VISION_CONF_TH,
                    "device": VISION_DEVICE,
                },
            },
        )

        print(f"[CAM] OK | depth_scale={depth_scale}")

        while running:
            frames = pipeline.wait_for_frames(timeout_ms=2000)
            aligned = align.process(frames)

            depth_frame = aligned.get_depth_frame()
            color_frame = aligned.get_color_frame()
            if not depth_frame or not color_frame:
                continue

            active_camera_mode, _, _, _ = get_active_modes()
            depth_z16 = np.asanyarray(depth_frame.get_data())
            color_image = np.asanyarray(color_frame.get_data())
            annotated = color_image.copy()

            vision_payload = {
                "ts": round(time.time(), 3),
                "mode": active_camera_mode,
                "conf_th": VISION_CONF_TH,
                "imgsz": VISION_IMGSZ,
                "selected": None,
                "targets": [],
            }

            try:
                if active_camera_mode == "pose":
                    model = registry.get_pose()
                    results = model.predict(
                        source=color_image,
                        conf=VISION_CONF_TH,
                        imgsz=VISION_IMGSZ,
                        device=VISION_DEVICE,
                        verbose=False,
                    )
                    r0 = results[0]
                    annotated = r0.plot()
                    targets = find_pose_targets(r0, depth_z16, depth_scale, circle_mask)
                    selected = pick_best_target(targets)
                    annotated = draw_pose_overlay(annotated, selected)
                    vision_payload["targets"] = [sanitize_target_for_json(t) for t in targets]
                    vision_payload["selected"] = sanitize_target_for_json(selected)
                    vision_payload["model"] = POSE_MODEL_PATH

                elif active_camera_mode == "segment":
                    model = registry.get_segment()
                    results = model.predict(
                        source=color_image,
                        conf=VISION_CONF_TH,
                        imgsz=VISION_IMGSZ,
                        device=VISION_DEVICE,
                        verbose=False,
                    )
                    r0 = results[0]
                    annotated = r0.plot()
                    targets = find_segment_targets(r0, depth_z16, depth_scale, circle_mask)
                    selected = pick_best_target(targets)
                    annotated = draw_segment_overlay(annotated, selected)
                    vision_payload["targets"] = [sanitize_target_for_json(t) for t in targets]
                    vision_payload["selected"] = sanitize_target_for_json(selected)
                    vision_payload["model"] = SEG_MODEL_PATH

                elif active_camera_mode == "normal":
                    cv2.putText(annotated, "CAM NORMAL", (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                                0.8, (0, 255, 0), 2, cv2.LINE_AA)
                    vision_payload["model"] = None
                else:
                    annotated = np.zeros_like(color_image)
                    cv2.putText(annotated, "CAM OFF", (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                                0.8, (0, 0, 255), 2, cv2.LINE_AA)
                    vision_payload["model"] = None

            except Exception as vision_e:
                publish_sensor(
                    "error",
                    {
                        "ts": round(time.time(), 3),
                        "source": "vision",
                        "mode": active_camera_mode,
                        "msg": str(vision_e),
                    },
                )
                cv2.putText(annotated, f"VISION ERROR: {str(vision_e)[:60]}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2, cv2.LINE_AA)

            if active_camera_mode != "off":
                ok_rgb, encoded_rgb = cv2.imencode(".jpg", annotated, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY])
                if ok_rgb:
                    publish_video(VIDEO_TOPIC_RGB, encoded_rgb.tobytes())
                    video_count += 1

            now = time.time()
            if (now - last_vision_pub_t) >= (1.0 / VISION_PUBLISH_HZ):
                publish_sensor("vision", vision_payload)
                last_vision_pub_t = now

            with state_lock:
                state.camera_ok = True
                state.last_camera_ts = now

            if now - dbg_t >= 1.0:
                print(f"[CAM] camera_mode={active_camera_mode} | pub/s={video_count}")
                video_count = 0
                dbg_t = now

    except Exception as e:
        with state_lock:
            state.camera_ok = False
        publish_sensor("error", {"ts": round(time.time(), 3), "source": "camera", "msg": str(e)})
        print(f"[CAM] Error: {e}")

    finally:
        try:
            pipeline.stop()
        except Exception:
            pass
        with state_lock:
            state.camera_ok = False
        print("[CAM] Cerrada.")


# ------------------------- LIDAR + WALLS -------------------------
async def lidar_async_worker():
    print(f"[LIDAR] Inicializando RPLidar C1 en {LIDAR_PORT} @ {LIDAR_BAUD}...")
    lidar = RPLidar(LIDAR_PORT, LIDAR_BAUD)

    try:
        try:
            hc = lidar.healthcheck()
            print(f"[LIDAR] Health: {hc}")
        except Exception as e:
            print(f"[LIDAR] Healthcheck no disponible: {e}")

        with state_lock:
            state.lidar_ok = True
            state.last_lidar_ts = time.time()

        scan_task = asyncio.create_task(lidar.simple_scan(make_return_dict=False))

        dist_bins = [0] * 360
        ts_bins = [0.0] * 360
        last_grid_pub_t = time.time()
        grid_period = 1.0 / LIDAR_GRID_HZ

        walls_buf: Deque[Tuple[float, float, float]] = deque()
        recent_points_buf: Deque[Tuple[float, float, float]] = deque()
        last_walls_process_t = 0.0
        last_points_pub_t = 0.0
        active_wall_keys: Set[Tuple[int, int, int, int]] = set()
        wall_seq = 0
        points_seq = 0

        while running:
            item = await lidar.output_queue.get()
            if not isinstance(item, dict):
                continue

            d_raw = item.get("d_mm", None)
            a_raw = item.get("a_deg", None)
            q_raw = item.get("q", 0)

            if d_raw is None or a_raw is None:
                continue

            d = int(d_raw)
            a = float(a_raw)
            q = int(q_raw) if q_raw is not None else 0

            if d <= 0 or d > MAX_RANGE_MM or q < MIN_QUALITY:
                continue

            idx = int(round(a)) % 360
            now = time.time()
            dist_bins[idx] = d
            ts_bins[idx] = now

            x_mm, y_mm = deg_to_local_xy_mm(a, d)
            x_m, y_m = x_mm / 1000.0, y_mm / 1000.0
            walls_buf.append((now, x_m, y_m))
            while walls_buf and (now - walls_buf[0][0]) > WALLS_WINDOW_SECONDS:
                walls_buf.popleft()
            while len(walls_buf) > WALLS_MAX_POINTS_BUFFER:
                walls_buf.popleft()

            recent_points_buf.append((now, x_m, y_m))
            while recent_points_buf and (now - recent_points_buf[0][0]) > POINTS_WINDOW_SECONDS:
                recent_points_buf.popleft()
            while len(recent_points_buf) > POINTS_MAX_BUFFER:
                recent_points_buf.popleft()

            _, active_lidar_mode, walls_enabled, points_enabled = get_active_modes()

            if active_lidar_mode != "off" and (now - last_grid_pub_t) >= grid_period:
                grid_msg = build_lidar_grid(dist_bins, ts_bins, active_lidar_mode, now)
                publish_sensor("lidar_grid", grid_msg)
                last_grid_pub_t = now

            if points_enabled and (now - last_points_pub_t) >= (1.0 / POINTS_PUBLISH_HZ) and len(recent_points_buf) > 0:
                last_points_pub_t = now
                pts_xy = np.array([(p[1], p[2]) for p in recent_points_buf], dtype=np.float32)
                pts_mm = quantize_points_to_mm(pts_xy)

                with state_lock:
                    snapshot_points_pending = state.points_snapshot_pending
                    state.points_snapshot_pending = False
                    state.points_ok = True
                    state.last_points_ts = now

                points_seq += 1
                with state_lock:
                    state.points_seq = points_seq

                if snapshot_points_pending:
                    publish_points(b"lidar_points_snapshot", encode_points_packet(POINTS_SNAPSHOT_MAGIC, points_seq, pts_mm))

                publish_points(b"lidar_points_frame", encode_points_packet(POINTS_FRAME_MAGIC, points_seq, pts_mm))
                publish_sensor(
                    "points_status",
                    {
                        "ts": round(now, 3),
                        "seq": points_seq,
                        "snapshot": snapshot_points_pending,
                        "enabled": True,
                        "count": len(pts_mm),
                        "window_s": POINTS_WINDOW_SECONDS,
                        "local_frame": "lidar",
                    },
                )
            elif not points_enabled:
                with state_lock:
                    state.points_ok = False

            if walls_enabled and (now - last_walls_process_t) >= (1.0 / WALLS_PROCESS_HZ) and len(walls_buf) > 200:
                last_walls_process_t = now

                pts = np.array([(p[1], p[2]) for p in walls_buf], dtype=np.float32)
                new_keys, meta = build_walls_segment_keys(pts)

                with state_lock:
                    snapshot_pending = state.walls_snapshot_pending
                    state.walls_snapshot_pending = False
                    state.walls_ok = True
                    state.last_walls_ts = now

                wall_seq += 1
                with state_lock:
                    state.walls_seq = wall_seq

                if snapshot_pending:
                    snap_keys = sorted(list(new_keys))
                    publish_walls(b"walls_snapshot", encode_walls_snapshot(wall_seq, snap_keys))
                    publish_sensor(
                        "walls_status",
                        {
                            "ts": round(now, 3),
                            "seq": wall_seq,
                            "snapshot": True,
                            "enabled": True,
                            **meta,
                        },
                    )

                adds = sorted(list(new_keys - active_wall_keys))
                rems = sorted(list(active_wall_keys - new_keys))
                if adds or rems:
                    publish_walls(b"walls_delta", encode_walls_delta(wall_seq, adds, rems))

                active_wall_keys = new_keys

                publish_sensor(
                    "walls_status",
                    {
                        "ts": round(now, 3),
                        "seq": wall_seq,
                        "snapshot": False,
                        "enabled": True,
                        "adds": len(adds),
                        "rems": len(rems),
                        **meta,
                    },
                )

            elif not walls_enabled:
                with state_lock:
                    state.walls_ok = False

            with state_lock:
                state.lidar_ok = True
                state.last_lidar_ts = now

        try:
            lidar.stop_event.set()
        except Exception:
            pass

        if not scan_task.done():
            scan_task.cancel()
            try:
                await scan_task
            except Exception:
                pass

    except Exception as e:
        with state_lock:
            state.lidar_ok = False
            state.walls_ok = False
            state.points_ok = False
        publish_sensor("error", {"ts": round(time.time(), 3), "source": "lidar", "msg": str(e)})
        print(f"[LIDAR] Error: {e}")

    finally:
        try:
            lidar.reset()
        except Exception:
            pass
        with state_lock:
            state.lidar_ok = False
            state.walls_ok = False
            state.points_ok = False
        print("[LIDAR] Cerrado.")


def lidar_thread():
    asyncio.run(lidar_async_worker())


def main():
    global running

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    context = zmq.Context.instance()

    print("=== NUC MASTER SERVER | CAMERA MODES + LIDAR + WALLS + POINTS ===")
    print(f" -> Sensores     : tcp://*:{PORT_SENSORS}")
    print(f" -> Video        : tcp://*:{PORT_VIDEO}")
    print(f" -> Comandos     : tcp://*:{PORT_CMD}")
    print(f" -> Walls/Points : tcp://*:{PORT_WALLS}")
    print(f" -> Serial master: {SERIAL_MASTER_PORT} @ {SERIAL_MASTER_BAUD}")
    print(f" -> Gripper ser  : {GRIPPER_SERIAL_PORT} @ {GRIPPER_SERIAL_BAUD}")
    print(f" -> Lidar        : {LIDAR_PORT} @ {LIDAR_BAUD}")
    print(f" -> D435i RGB    : {COLOR_W}x{COLOR_H} @ {COLOR_FPS}fps")
    print(f" -> D435i Depth  : {DEPTH_W}x{DEPTH_H} @ {DEPTH_FPS}fps")
    print(f" -> Camera modes : {sorted(VALID_CAMERA_MODES)}")
    print(f" -> Lidar modes  : {sorted(VALID_LIDAR_MODES)}")
    print(f" -> Init         : camera={state.active_camera_mode} lidar={state.active_lidar_mode} walls={state.walls_enabled} points={state.points_enabled}")

    threads = [
        threading.Thread(target=sensor_pub_thread, args=(context,), daemon=True),
        threading.Thread(target=video_pub_thread, args=(context,), daemon=True),
        threading.Thread(target=walls_pub_thread, args=(context,), daemon=True),
        threading.Thread(target=command_listener_thread, args=(context,), daemon=True),
        threading.Thread(target=serial_master_thread, daemon=True),
        threading.Thread(target=serial_gripper_thread, daemon=True),
        threading.Thread(target=status_thread, daemon=True),
        threading.Thread(target=camera_thread, daemon=True),
        threading.Thread(target=lidar_thread, daemon=True),
    ]

    for t in threads:
        t.start()

    try:
        while running:
            time.sleep(0.25)
    finally:
        running = False
        time.sleep(0.5)
        context.term()
        print("[MAIN] Recursos liberados.")


if __name__ == "__main__":
    main()