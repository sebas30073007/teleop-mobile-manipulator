#!/usr/bin/env python3
"""
wfiot_nuc_latency_simulator.py  —  IEEE WF-IoT Latency Orchestrator
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

NEW ARCHITECTURE (PC-orchestrated, Quest passive):
  PC → Quest   latency_probe  via PUB :5001   (PC sends probes)
  Quest → PC   latency_ack   via SUB :5002   (Quest echoes ACKs)
  RTT = t_ack_recv − t_probe_enqueue   (measured entirely on PC clock)

ZMQ socket ownership (one socket per thread):
  cmd_listener_thread  SUB bind :5002  ← latency_ack + any cmd from Quest
  sensor_pub_thread    PUB bind :5001  → latency_probe, stat, mode_ack,
                                          lidar_grid, start_condition, …
  video_pub_thread     PUB bind :5555  → video_rgb  (synthetic JPEG)
  walls_pub_thread     PUB bind :5007  → placeholder
  stat_generator_thread  (no socket)
  lidar_generator_thread (no socket)
  orchestrator_thread    (no socket)  — runs C1–C7 automatically
  csv_writer_thread      (no socket)  — server-side event log

zmq.Context shared (thread-safe). All :5001 traffic via sensor_queue.
All :5001 probes via probe_queue (high-priority, drained first).
"""

import argparse
import csv
import json
import logging
import math
import os
import queue
import signal
import socket
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import cv2
import numpy as np
import zmq

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("wfiot_sim")

# ── Experiment conditions ─────────────────────────────────────────────────────
CONDITIONS = [
    {"test_id": "C1_control_only",  "video_enabled": False, "lidar_enabled": False,
     "camera_mode": "off",    "lidar_mode": "off",      "lidar_hz": 0,  "video_fps": 0},
    {"test_id": "C2_video_normal",  "video_enabled": True,  "lidar_enabled": False,
     "camera_mode": "normal", "lidar_mode": "off",      "lidar_hz": 0,  "video_fps": 30},
    {"test_id": "C3_lidar_detail",  "video_enabled": False, "lidar_enabled": True,
     "camera_mode": "off",    "lidar_mode": "detail",   "lidar_hz": 12, "video_fps": 0},
    {"test_id": "C4_lidar_medium",  "video_enabled": False, "lidar_enabled": True,
     "camera_mode": "off",    "lidar_mode": "medium",   "lidar_hz": 8,  "video_fps": 0},
    {"test_id": "C5_lidar_panorama","video_enabled": False, "lidar_enabled": True,
     "camera_mode": "off",    "lidar_mode": "panorama", "lidar_hz": 4,  "video_fps": 0},
    {"test_id": "C6_full_detail",   "video_enabled": True,  "lidar_enabled": True,
     "camera_mode": "normal", "lidar_mode": "detail",   "lidar_hz": 12, "video_fps": 30},
    {"test_id": "C7_full_panorama", "video_enabled": True,  "lidar_enabled": True,
     "camera_mode": "normal", "lidar_mode": "panorama", "lidar_hz": 4,  "video_fps": 30},
]

# ── Probe item (enqueued by orchestrator, consumed by sensor_pub_thread) ──────
@dataclass
class ProbeItem:
    seq:          int
    t_enqueue:    float   # time.time() just before queue.put() — used for RTT
    test_id:      str
    condition:    str
    warmup:       bool
    camera_mode:  str
    lidar_mode:   str
    video_enabled: bool
    lidar_enabled: bool

# ── Shared state ──────────────────────────────────────────────────────────────
state_lock = threading.Lock()
state = {
    "active_camera_mode": "off",
    "active_lidar_mode":  "off",
    "video_enabled":      False,
    "lidar_enabled":      False,
    "video_fps":          30.0,
    "stat_hz":            2.0,
    "lidar_hz":           12.0,
    "current_test_id":    "",
    "current_condition":  "",
    "running":            True,
}

# ── Queues ────────────────────────────────────────────────────────────────────
probe_queue  = queue.Queue()        # ProbeItem objects  (high priority → :5001)
sensor_queue = queue.Queue()        # (topic_str, payload_str) → :5001
video_queue  = queue.Queue(maxsize=2)
log_queue    = queue.Queue()

# ── Latency results ───────────────────────────────────────────────────────────
pending_lock   = threading.Lock()
pending_probes = {}   # seq → ProbeItem (populated by sensor_pub_thread at send time)

results_lock = threading.Lock()
all_results  = []    # list of result dicts appended by cmd_listener_thread

sent_counts  = {}    # {test_id: n_non_warmup_probes_sent}
sent_lock    = threading.Lock()

# ── Sequence counter ──────────────────────────────────────────────────────────
_seq_counter = 0
_seq_lock    = threading.Lock()

def _next_seq() -> int:
    global _seq_counter
    with _seq_lock:
        _seq_counter += 1
        return _seq_counter

# ── ZMQ Context ───────────────────────────────────────────────────────────────
ctx: zmq.Context = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"


def _send_to_quest(topic: str, payload_dict: dict):
    """Queue a JSON message for :5001 PUB (config/mode commands to Quest)."""
    sensor_queue.put((topic, json.dumps(payload_dict)))


def _interruptible_sleep(seconds: float, step: float = 0.1):
    t0 = time.time()
    while time.time() - t0 < seconds:
        with state_lock:
            if not state["running"]:
                break
        time.sleep(step)


def enqueue_log(event: str, topic: str, seq: int, test_id: str, condition: str,
                payload_bytes: int, notes: str = "") -> None:
    snap = {}
    with state_lock:
        snap = {
            "active_camera_mode": state["active_camera_mode"],
            "active_lidar_mode":  state["active_lidar_mode"],
            "video_enabled":      state["video_enabled"],
            "lidar_enabled":      state["lidar_enabled"],
        }
    log_queue.put({
        "unix_ts":            time.time(),
        "event":              event,
        "topic":              topic,
        "seq":                seq,
        "test_id":            test_id,
        "condition":          condition,
        "payload_bytes":      payload_bytes,
        "active_camera_mode": snap["active_camera_mode"],
        "active_lidar_mode":  snap["active_lidar_mode"],
        "video_enabled":      snap["video_enabled"],
        "lidar_enabled":      snap["lidar_enabled"],
        "notes":              notes,
    })


# ── Thread: cmd_listener (SUB :5002) ─────────────────────────────────────────
# Receives latency_ack from Quest AND any cmd from old Unity clients.

def cmd_listener_thread(host: str) -> None:
    sock = ctx.socket(zmq.SUB)
    sock.setsockopt(zmq.RCVHWM, 500)
    sock.setsockopt_string(zmq.SUBSCRIBE, "latency_ack")  # NEW: Quest echoes here
    sock.setsockopt_string(zmq.SUBSCRIBE, "cmd")           # legacy Unity commands
    sock.bind(f"tcp://{host}:5002")
    log.info(f"[CMD] SUB bound tcp://{host}:5002")

    try:
        while True:
            with state_lock:
                if not state["running"]: break

            if not sock.poll(timeout=100):
                continue

            try:
                parts = sock.recv_multipart(zmq.NOBLOCK)
            except zmq.ZMQError:
                continue

            if len(parts) < 2:
                continue

            topic        = parts[0].decode("utf-8")
            payload_str  = parts[1].decode("utf-8")
            t_recv       = time.time()

            # ── latency_ack from Quest ────────────────────────────────────────
            if topic == "latency_ack":
                try:
                    ack = json.loads(payload_str)
                    seq = ack.get("seq", -1)

                    with pending_lock:
                        probe_info = pending_probes.pop(seq, None)

                    if probe_info is not None:
                        rtt_ms = (t_recv - probe_info.t_enqueue) * 1000.0
                        result = {
                            "unix_ts_recv":   t_recv,
                            "seq":            seq,
                            "rtt_ms":         round(rtt_ms, 4),
                            "t_send_unix":    probe_info.t_enqueue,
                            "warmup":         probe_info.warmup,
                            "test_id":        probe_info.test_id,
                            "condition":      probe_info.condition,
                            "camera_mode":    probe_info.camera_mode,
                            "lidar_mode":     probe_info.lidar_mode,
                            "video_enabled":  probe_info.video_enabled,
                            "lidar_enabled":  probe_info.lidar_enabled,
                        }
                        with results_lock:
                            all_results.append(result)
                        enqueue_log("ack_recv", "latency_ack", seq,
                                    probe_info.test_id, probe_info.condition,
                                    len(payload_str),
                                    notes=f"rtt={rtt_ms:.2f}ms")
                except Exception as exc:
                    log.warning(f"[CMD] latency_ack parse error: {exc}")
                continue

            # ── Legacy cmd from old Unity manager (optional, keep working) ────
            if topic == "cmd":
                try:
                    msg      = json.loads(payload_str)
                    msg_type = msg.get("type", "")
                    with state_lock:
                        tid = state["current_test_id"]
                        cnd = state["current_condition"]
                    enqueue_log("cmd_recv", "cmd", -1, tid, cnd, len(payload_str),
                                notes=f"type={msg_type}")
                except Exception:
                    pass
    finally:
        sock.close()
        log.info("[CMD] thread stopped")


# ── Thread: sensor_pub (PUB :5001) ───────────────────────────────────────────

def sensor_pub_thread(host: str) -> None:
    sock = ctx.socket(zmq.PUB)
    sock.setsockopt(zmq.SNDHWM, 500)
    sock.bind(f"tcp://{host}:5001")
    log.info(f"[SENSOR] PUB bound tcp://{host}:5001")
    time.sleep(0.5)

    try:
        while True:
            with state_lock:
                running = state["running"]

            # ── High priority: drain probe_queue ──────────────────────────────
            while True:
                try:
                    item: ProbeItem = probe_queue.get_nowait()
                except queue.Empty:
                    break

                payload = json.dumps({
                    "type":      "latency_probe",
                    "seq":       item.seq,
                    "test_id":   item.test_id,
                    "condition": item.condition,
                })
                # Register AFTER building payload so t_enqueue is accurate
                with pending_lock:
                    pending_probes[item.seq] = item

                try:
                    sock.send_multipart([b"latency_probe", payload.encode()])
                except zmq.ZMQError as exc:
                    log.warning(f"[SENSOR] probe send error: {exc}")

            # ── Normal: drain sensor_queue with short timeout ─────────────────
            try:
                topic, payload_str = sensor_queue.get(timeout=0.001)
            except queue.Empty:
                if not running:
                    break
                continue

            # Stamp server_send_unix if this is a latency_ack (legacy path, unused now)
            try:
                sock.send_multipart([topic.encode("utf-8"), payload_str.encode("utf-8")])
            except zmq.ZMQError as exc:
                log.warning(f"[SENSOR] send error: {exc}")

    finally:
        try:
            while True: sensor_queue.get_nowait()
        except queue.Empty:
            pass
        sock.close()
        log.info("[SENSOR] thread stopped")


# ── Thread: stat_generator ────────────────────────────────────────────────────

def stat_generator_thread() -> None:
    start_time = time.time()
    log.info("[STAT_GEN] started")
    while True:
        with state_lock:
            if not state["running"]: break
            hz   = state["stat_hz"]
            snap = dict(state)
        interval = 1.0 / max(hz, 0.1)
        t0 = time.time()
        stat = {
            "camera_ok": True, "lidar_ok": True, "cmd_link_ok": True,
            "active_camera_mode": snap["active_camera_mode"],
            "active_lidar_mode":  snap["active_lidar_mode"],
            "video_enabled":      snap["video_enabled"],
            "lidar_enabled":      snap["lidar_enabled"],
            "current_test_id":    snap["current_test_id"],
            "uptime_s":           round(time.time() - start_time, 2),
            "ts":                 time.time(),
        }
        sensor_queue.put(("stat", json.dumps(stat)))
        elapsed = time.time() - t0
        sl = interval - elapsed
        if sl > 0: time.sleep(sl)
    log.info("[STAT_GEN] stopped")


# ── LiDAR grid generation ─────────────────────────────────────────────────────
LIDAR_MODES = {
    "detail":   {"grid_size": 200, "cell_size_m": 0.01, "radius_m": 1.0},
    "medium":   {"grid_size": 400, "cell_size_m": 0.01, "radius_m": 2.0},
    "panorama": {"grid_size": 600, "cell_size_m": 0.01, "radius_m": 3.0},
}

def _rle_encode(arr: np.ndarray) -> list:
    rle, cur_val, count = [], int(arr[0]), 1
    for v in arr[1:]:
        iv = int(v)
        if iv == cur_val: count += 1
        else:
            rle.append([cur_val, count])
            cur_val, count = iv, 1
    rle.append([cur_val, count])
    return rle

def _build_lidar_occupancy(grid_size: int, compact: bool):
    occ    = np.zeros(grid_size * grid_size, dtype=np.uint8)
    center = grid_size // 2
    n_pts  = max(50, min(120, grid_size // 2))
    for i in range(n_pts):
        angle = math.pi * i / n_pts
        r = center * 0.70
        x = int(center + r * math.cos(angle))
        y = int(center + r * math.sin(angle))
        if 0 <= x < grid_size and 0 <= y < grid_size:
            occ[y * grid_size + x] = 1
    hits = int(np.sum(occ))
    if compact:
        return _rle_encode(occ), hits, True
    return occ.tolist(), hits, False

def lidar_generator_thread(compact: bool) -> None:
    log.info("[LIDAR_GEN] started")
    while True:
        with state_lock:
            if not state["running"]: break
            lid_mode  = state["active_lidar_mode"]
            lid_en    = state["lidar_enabled"]
            hz        = state["lidar_hz"]
            test_id   = state["current_test_id"]
            condition = state["current_condition"]
        if not lid_en or lid_mode not in LIDAR_MODES:
            time.sleep(0.1); continue
        interval = 1.0 / max(hz, 0.1)
        t0 = time.time()
        p  = LIDAR_MODES[lid_mode]
        gs = p["grid_size"]
        occ, hits, is_rle = _build_lidar_occupancy(gs, compact)
        payload_dict = {"ts": time.time(), "mode": lid_mode, "grid_size": gs,
                        "cell_size_m": p["cell_size_m"], "radius_m": p["radius_m"],
                        "hits": hits}
        if is_rle: payload_dict["occupancy_rle"] = occ
        else:      payload_dict["occupancy"]      = occ
        sensor_queue.put(("lidar_grid", json.dumps(payload_dict)))
        sl = interval - (time.time() - t0)
        if sl > 0: time.sleep(sl)
    log.info("[LIDAR_GEN] stopped")


# ── Synthetic video ───────────────────────────────────────────────────────────
_MODE_BG = {"normal":(40,40,40), "pose":(80,40,30), "segment":(40,60,30), "off":(10,10,10)}
_POSE_KPT = [(320,80),(320,140),(260,180),(380,180),(230,250),(410,250),(210,320)]
_POSE_LNK = [(0,1),(1,2),(1,3),(2,4),(3,5),(4,6)]

def _generate_frame(cam_mode: str, frame_counter: int, test_id: str, quality: int) -> bytes:
    W, H = 640, 480
    img  = np.full((H, W, 3), _MODE_BG.get(cam_mode, (40,40,40)), dtype=np.uint8)
    font = cv2.FONT_HERSHEY_SIMPLEX
    col  = (200, 200, 200)
    cv2.putText(img, f"ts:{time.time():.3f}",  (10,28), font, 0.5, col, 1)
    cv2.putText(img, f"mode:{cam_mode}",        (10,52), font, 0.5, col, 1)
    cv2.putText(img, f"frame:{frame_counter}",  (10,76), font, 0.5, col, 1)
    cv2.putText(img, f"id:{test_id[:24]}",      (10,100),font, 0.42,(170,170,170),1)
    if cam_mode == "pose":
        for kx,ky in _POSE_KPT: cv2.circle(img,(kx,ky),6,(255,255,255),-1)
        for a,b in _POSE_LNK:   cv2.line(img,_POSE_KPT[a],_POSE_KPT[b],(180,180,255),2)
    elif cam_mode == "segment":
        rng = np.random.default_rng(frame_counter % 30)
        for clr in [(0,130,220),(0,210,110)]:
            x1,y1 = int(rng.integers(40,200)), int(rng.integers(40,150))
            x2,y2 = x1+int(rng.integers(80,160)), y1+int(rng.integers(80,150))
            ov = img.copy(); cv2.rectangle(ov,(x1,y1),(x2,y2),clr,-1)
            cv2.addWeighted(ov,0.4,img,0.6,0,img); cv2.rectangle(img,(x1,y1),(x2,y2),clr,2)
    _, jpeg = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return jpeg.tobytes()

def video_pub_thread(host: str, jpeg_quality: int) -> None:
    sock = ctx.socket(zmq.PUB)
    sock.setsockopt(zmq.SNDHWM, 2)
    sock.bind(f"tcp://{host}:5555")
    log.info(f"[VIDEO] PUB bound tcp://{host}:5555")
    time.sleep(0.5)
    frame_counter = 0
    try:
        while True:
            with state_lock:
                running  = state["running"]
                vid_en   = state["video_enabled"]
                fps      = state["video_fps"]
                cam_mode = state["active_camera_mode"]
                test_id  = state["current_test_id"]
            if not running: break
            if not vid_en or cam_mode == "off":
                time.sleep(0.1); continue
            t0   = time.time()
            jpeg = _generate_frame(cam_mode, frame_counter, test_id, jpeg_quality)
            try:
                sock.send_multipart([b"video_rgb", jpeg])
                frame_counter += 1
            except zmq.ZMQError: pass
            sl = 1.0/max(fps,1.0) - (time.time()-t0)
            if sl > 0: time.sleep(sl)
    finally:
        sock.close(); log.info("[VIDEO] thread stopped")

def walls_pub_thread(host: str) -> None:
    sock = ctx.socket(zmq.PUB)
    sock.setsockopt(zmq.SNDHWM, 50)
    sock.bind(f"tcp://{host}:5007")
    log.info(f"[WALLS] PUB bound tcp://{host}:5007 (placeholder)")
    time.sleep(0.5)
    try:
        while True:
            with state_lock:
                if not state["running"]: break
            time.sleep(1.0)
    finally:
        sock.close(); log.info("[WALLS] thread stopped")


# ── CSV helpers ───────────────────────────────────────────────────────────────
_DETAIL_COLS = ["unix_ts_recv","seq","rtt_ms","t_send_unix","warmup",
                "test_id","condition","camera_mode","lidar_mode",
                "video_enabled","lidar_enabled"]

def _percentile(sorted_data: list, p: float) -> float:
    if not sorted_data: return 0.0
    idx = (p / 100.0) * (len(sorted_data) - 1)
    lo, hi = int(idx), min(int(idx)+1, len(sorted_data)-1)
    return sorted_data[lo] + (idx-lo)*(sorted_data[hi]-sorted_data[lo])

def _save_condition_csv(test_id: str, log_dir: str, probes_per_condition: int) -> Optional[str]:
    with results_lock:
        cond_results = [r for r in all_results if r["test_id"] == test_id]
    if not cond_results:
        log.warning(f"[ORCH] No results for {test_id}")
        return None

    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(log_dir, f"wfiot_latency_{test_id}_{ts}.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=_DETAIL_COLS)
        w.writeheader()
        for r in cond_results:
            w.writerow({k: r.get(k,"") for k in _DETAIL_COLS})

    valid_rtts = [r["rtt_ms"] for r in cond_results if not r["warmup"]]
    n_recv     = len(valid_rtts)
    n_sent     = sent_counts.get(test_id, probes_per_condition)
    loss       = (n_sent - n_recv) * 100.0 / n_sent if n_sent > 0 else 0.0

    if valid_rtts:
        sr     = sorted(valid_rtts)
        mean   = sum(valid_rtts) / len(valid_rtts)
        median = _percentile(sr, 50)
        p95    = _percentile(sr, 95)
        p99    = _percentile(sr, 99)
        mx     = sr[-1]
        std    = math.sqrt(sum((r-mean)**2 for r in valid_rtts)/len(valid_rtts))
        log.info(
            f"[ORCH] ✓ {test_id}: recv={n_recv}/{n_sent} loss={loss:.1f}%  "
            f"mean={mean:.1f}  p50={median:.1f}  p95={p95:.1f}  "
            f"p99={p99:.1f}  max={mx:.1f}  σ={std:.1f} ms"
        )
    log.info(f"[ORCH]   Detail CSV → {path}")
    return path


def _save_summary_csv(log_dir: str, probes_per_condition: int) -> str:
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(log_dir, f"wfiot_latency_summary_{ts}.csv")
    cols = ["condition","samples_sent","samples_received","loss_percent",
            "rtt_mean_ms","rtt_median_ms","rtt_min_ms","rtt_max_ms",
            "rtt_p95_ms","rtt_p99_ms","jitter_std_ms"]

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for cond in CONDITIONS:
            tid = cond["test_id"]
            with results_lock:
                rows = [r for r in all_results if r["test_id"]==tid and not r["warmup"]]
            rtts   = [r["rtt_ms"] for r in rows]
            n_recv = len(rtts)
            n_sent = sent_counts.get(tid, probes_per_condition)
            loss   = (n_sent-n_recv)*100.0/n_sent if n_sent>0 else 0.0
            if rtts:
                sr   = sorted(rtts)
                mean = sum(rtts)/len(rtts)
                var  = sum((r-mean)**2 for r in rtts)/len(rtts)
                row  = {
                    "condition":        tid,
                    "samples_sent":     n_sent,
                    "samples_received": n_recv,
                    "loss_percent":     round(loss,2),
                    "rtt_mean_ms":      round(mean,3),
                    "rtt_median_ms":    round(_percentile(sr,50),3),
                    "rtt_min_ms":       round(sr[0],3),
                    "rtt_max_ms":       round(sr[-1],3),
                    "rtt_p95_ms":       round(_percentile(sr,95),3),
                    "rtt_p99_ms":       round(_percentile(sr,99),3),
                    "jitter_std_ms":    round(math.sqrt(var),3),
                }
            else:
                row = {c: "" for c in cols}
                row["condition"] = tid
                row["samples_sent"] = n_sent
                row["samples_received"] = 0
                row["loss_percent"] = 100.0
            w.writerow(row)

    log.info(f"[ORCH] Summary CSV → {path}")
    return path


# ── Thread: orchestrator ──────────────────────────────────────────────────────

def orchestrator_thread(args) -> None:
    """
    Runs the full C1–C7 experiment sequence automatically.
    Sends latency_probe via probe_queue → sensor_pub_thread → :5001.
    RTT measured as t_ack_recv − probe_item.t_enqueue (pure PC clock).
    """
    log.info(f"[ORCH] Experiment will start in {args.start_delay}s.")
    log.info(f"[ORCH] Conditions: {len(CONDITIONS)}  |  "
             f"Probes/condition: {args.probes_per_condition}  |  "
             f"Warmup probes: {args.warmup_probes}  |  "
             f"Rate: {args.probe_hz} Hz")
    log.info(f"[ORCH] Estimated duration: "
             f"~{(args.probes_per_condition+args.warmup_probes)/args.probe_hz*len(CONDITIONS)/60:.0f} min")

    for remaining in range(args.start_delay, 0, -1):
        sys.stdout.write(
            f"\r[ORCH] Starting in {remaining:3d}s … "
            "(start Quest WFIoTLatencyResponder scene now)"
        )
        sys.stdout.flush()
        time.sleep(1)
        with state_lock:
            if not state["running"]: return
    print()  # newline after countdown

    n_cond = len(CONDITIONS)
    probe_interval = 1.0 / max(args.probe_hz, 0.1)

    for ci, cond in enumerate(CONDITIONS):
        with state_lock:
            if not state["running"]: break

        test_id = cond["test_id"]
        log.info(f"\n[ORCH] ══ Condition {ci+1}/{n_cond}: {test_id} ══")

        # 1. Update shared state
        with state_lock:
            state["active_camera_mode"] = cond["camera_mode"]
            state["active_lidar_mode"]  = cond["lidar_mode"]
            state["video_enabled"]      = cond["video_enabled"]
            state["lidar_enabled"]      = cond["lidar_enabled"]
            state["current_test_id"]    = test_id
            state["current_condition"]  = test_id
            if cond["lidar_hz"] > 0:  state["lidar_hz"]  = float(cond["lidar_hz"])
            if cond["video_fps"] > 0: state["video_fps"] = float(cond["video_fps"])

        # 2. Send configuration to Quest via :5001
        _send_to_quest("start_condition",  {"type":"start_condition","test_id":test_id,"condition":test_id})
        _send_to_quest("set_camera_mode",  {"type":"set_camera_mode","mode":cond["camera_mode"]})
        _send_to_quest("set_lidar_mode",   {"type":"set_lidar_mode","mode":cond["lidar_mode"]})
        _send_to_quest("set_stream_config",{
            "type":"set_stream_config",
            "video_enabled":  cond["video_enabled"],
            "stat_enabled":   True,
            "lidar_enabled":  cond["lidar_enabled"],
            "video_fps":      float(cond["video_fps"] or 30),
            "stat_hz":        2.0,
            "lidar_hz":       float(cond["lidar_hz"] or 4),
        })

        # 3. Warmup delay
        log.info(f"[ORCH] Warmup {args.warmup_delay:.1f}s …")
        _interruptible_sleep(args.warmup_delay)
        with state_lock:
            if not state["running"]: break

        # 4. Fire probes
        total_probes = args.warmup_probes + args.probes_per_condition
        log.info(f"[ORCH] Firing {total_probes} probes "
                 f"({args.warmup_probes} warmup + {args.probes_per_condition} measured) …")

        n_sent_non_warmup = 0
        for i in range(total_probes):
            with state_lock:
                if not state["running"]: break

            warmup = (i < args.warmup_probes)
            seq    = _next_seq()
            t_now  = time.time()

            item = ProbeItem(
                seq=seq, t_enqueue=t_now, test_id=test_id, condition=test_id,
                warmup=warmup, camera_mode=cond["camera_mode"],
                lidar_mode=cond["lidar_mode"],
                video_enabled=cond["video_enabled"],
                lidar_enabled=cond["lidar_enabled"],
            )
            probe_queue.put(item)

            if not warmup:
                n_sent_non_warmup += 1

            if (i+1) % 100 == 0 or i == total_probes-1:
                log.info(f"[ORCH]   {i+1}/{total_probes} probes queued "
                         f"(seq={seq}, warmup={warmup})")

            elapsed = time.time() - t_now
            sl = probe_interval - elapsed
            if sl > 0: time.sleep(sl)

        with sent_lock:
            sent_counts[test_id] = n_sent_non_warmup

        # 5. Wait for remaining ACKs
        log.info(f"[ORCH] Post-probe wait {args.post_probe_wait:.1f}s …")
        _interruptible_sleep(args.post_probe_wait)

        # 6. Stop condition
        _send_to_quest("stop_condition", {"type":"stop_condition","test_id":test_id})

        # 7. Save detail CSV for this condition
        _save_condition_csv(test_id, args.log_dir, args.probes_per_condition)

        # 8. Inter-condition gap
        if ci < n_cond - 1:
            log.info(f"[ORCH] Inter-condition pause {args.inter_condition_delay:.1f}s …")
            _interruptible_sleep(args.inter_condition_delay)

    # 9. Final summary
    log.info("\n[ORCH] ══ All conditions complete ══")
    _save_summary_csv(args.log_dir, args.probes_per_condition)
    log.info("[ORCH] Press Ctrl+C to exit.")


# ── Thread: server CSV log ────────────────────────────────────────────────────
_CSV_LOG_COLS = ["unix_ts","event","topic","seq","test_id","condition",
                 "payload_bytes","active_camera_mode","active_lidar_mode",
                 "video_enabled","lidar_enabled","notes"]

def csv_writer_thread(log_dir: str) -> None:
    os.makedirs(log_dir, exist_ok=True)
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(log_dir, f"wfiot_nuc_sim_log_{ts}.csv")
    log.info(f"[CSV] Server event log → {path}")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=_CSV_LOG_COLS)
        w.writeheader(); f.flush()
        while True:
            with state_lock:
                running = state["running"]
            try:
                row = log_queue.get(timeout=0.25)
                w.writerow(row); f.flush()
            except queue.Empty:
                if not running:
                    try:
                        while True:
                            w.writerow(log_queue.get_nowait())
                    except queue.Empty:
                        break
    log.info(f"[CSV] Event log closed: {path}")


# ── Signal handler ────────────────────────────────────────────────────────────
def _shutdown(signum, frame):
    log.info("\n[SIM] Shutdown received — stopping …")
    with state_lock:
        state["running"] = False


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    global ctx

    p = argparse.ArgumentParser(
        description="WF-IoT NUC Latency Simulator & Orchestrator\n"
                    "PC sends probes → Quest echoes ACKs → PC measures RTT"
    )
    p.add_argument("--host",                 default="0.0.0.0")
    p.add_argument("--video-fps",            type=float, default=30.0)
    p.add_argument("--stat-hz",              type=float, default=2.0)
    p.add_argument("--lidar-hz",             type=float, default=12.0,
                   help="Default LiDAR Hz (overridden per-condition)")
    p.add_argument("--jpeg-quality",         type=int,   default=85)
    p.add_argument("--compact-lidar",        action="store_true")
    p.add_argument("--log-dir",              default="logs")
    # Orchestrator parameters
    p.add_argument("--start-delay",          type=int,   default=15,
                   help="Seconds to wait before starting C1 (time to put on Quest)")
    p.add_argument("--probes-per-condition", type=int,   default=1050,
                   help="Number of measured probes per condition (default 1050 ≥ 1000)")
    p.add_argument("--warmup-probes",        type=int,   default=50,
                   help="Warm-up probes discarded per condition")
    p.add_argument("--probe-hz",             type=float, default=10.0,
                   help="Probe send rate Hz (default 10 → 105s per condition)")
    p.add_argument("--warmup-delay",         type=float, default=1.5,
                   help="Seconds to wait after sending config before probes")
    p.add_argument("--post-probe-wait",      type=float, default=2.0,
                   help="Seconds to wait after last probe for remaining ACKs")
    p.add_argument("--inter-condition-delay",type=float, default=3.0,
                   help="Seconds between conditions")
    args = p.parse_args()

    with state_lock:
        state["video_fps"] = args.video_fps
        state["stat_hz"]   = args.stat_hz
        state["lidar_hz"]  = args.lidar_hz

    signal.signal(signal.SIGINT,  _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    ctx = zmq.Context.instance()
    local_ip = get_local_ip()
    os.makedirs(args.log_dir, exist_ok=True)

    total_s = (args.probes_per_condition + args.warmup_probes) / args.probe_hz
    eta_min  = (total_s * len(CONDITIONS) + args.start_delay +
                args.inter_condition_delay * (len(CONDITIONS)-1)) / 60

    print("═"*64)
    print("  WF-IoT NUC Latency Simulator  —  PC-Orchestrated Mode")
    print("═"*64)
    print(f"  Local IP         : {local_ip}")
    print(f"  CMD  SUB  :5002  ← latency_ack from Quest")
    print(f"  SENS PUB  :5001  → latency_probe + stat + lidar_grid")
    print(f"  VIDEO PUB :5555  → video_rgb (synthetic)")
    print("─"*64)
    print(f"  Probe rate       : {args.probe_hz} Hz")
    print(f"  Probes/condition : {args.probes_per_condition} measured + {args.warmup_probes} warmup")
    print(f"  Conditions       : {len(CONDITIONS)}  (C1–C7)")
    print(f"  Estimated time   : ~{eta_min:.0f} min")
    print(f"  Log dir          : {os.path.abspath(args.log_dir)}")
    print("─"*64)
    print(f"  → Quest IP must point to: {local_ip}")
    print(f"  → Open WFIoTLatencyResponder scene on Quest")
    print(f"  → Sequence starts in {args.start_delay}s automatically")
    print(f"  → Press Ctrl+C to abort")
    print("═"*64)

    threads = [
        threading.Thread(target=cmd_listener_thread,    args=(args.host,),
                         name="cmd_listener",    daemon=True),
        threading.Thread(target=sensor_pub_thread,      args=(args.host,),
                         name="sensor_pub",      daemon=True),
        threading.Thread(target=stat_generator_thread,
                         name="stat_gen",        daemon=True),
        threading.Thread(target=lidar_generator_thread, args=(args.compact_lidar,),
                         name="lidar_gen",       daemon=True),
        threading.Thread(target=video_pub_thread,       args=(args.host, args.jpeg_quality),
                         name="video_pub",       daemon=True),
        threading.Thread(target=walls_pub_thread,       args=(args.host,),
                         name="walls_pub",       daemon=True),
        threading.Thread(target=orchestrator_thread,    args=(args,),
                         name="orchestrator",    daemon=True),
        threading.Thread(target=csv_writer_thread,      args=(args.log_dir,),
                         name="csv_writer",      daemon=False),  # not daemon → ensures flush
    ]

    for t in threads:
        t.start()

    while True:
        with state_lock:
            if not state["running"]: break
        time.sleep(0.2)

    log.info("[SIM] Joining threads …")
    for t in threads:
        t.join(timeout=4.0)

    log.info("[SIM] Terminating ZMQ context …")
    try: ctx.term()
    except Exception: pass
    log.info("[SIM] Done.")


if __name__ == "__main__":
    main()
