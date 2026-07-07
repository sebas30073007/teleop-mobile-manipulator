#!/usr/bin/env python3
"""
wfiot_stats_analysis.py — Statistical analysis for the WF-IoT 2026 paper (v3).

Reads the raw per-probe CSVs produced by wfiot_nuc_latency_simulator.py
(logs/wfiot_latency_C*_*.csv), excludes warm-up samples, and computes:

  1. Per-condition summary statistics (sanity-checked against the
     simulator-generated summary CSV).
  2. Kruskal–Wallis omnibus test across C1–C7.
  3. Pairwise Mann–Whitney U tests vs the C1 baseline with
     Holm–Bonferroni correction and Cliff's delta effect sizes.
  4. Bootstrap 95% CIs for the median and P95 of each condition.
  5. Tail probability P(RTT > 100 ms) per condition.
  6. Burst (outlier cluster) characterization per condition.
  7. Offered-load model: exact per-message payload sizes replicated from
     the simulator's deterministic generators (LiDAR JSON grid, synthetic
     JPEG frames), and Spearman correlation between offered load and P95.

Outputs a markdown report and CSV tables to IEEE_IOT/analysis/.

Usage (from repo root):
    python validation/tools/wfiot_stats_analysis.py
"""

import glob
import json
import math
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LOGS_DIR = os.path.join(REPO_ROOT, "logs")
OUT_DIR = os.path.join(REPO_ROOT, "IEEE_IOT", "analysis")

CONDITION_ORDER = [
    "C1_control_only", "C2_video_normal", "C3_lidar_detail",
    "C4_lidar_medium", "C5_lidar_panorama", "C6_full_detail",
    "C7_full_panorama",
]
CONDITION_LABELS = {
    "C1_control_only":  "C1 Control only",
    "C2_video_normal":  "C2 Video normal",
    "C3_lidar_detail":  "C3 LiDAR detail",
    "C4_lidar_medium":  "C4 LiDAR medium",
    "C5_lidar_panorama": "C5 LiDAR panorama",
    "C6_full_detail":   "C6 Video + detail",
    "C7_full_panorama": "C7 Video + panorama",
}

# Per-condition stream rates, mirroring CONDITIONS in the simulator.
CONDITION_STREAMS = {
    "C1_control_only":  {"video_fps": 0,  "lidar_mode": None,       "lidar_hz": 0},
    "C2_video_normal":  {"video_fps": 30, "lidar_mode": None,       "lidar_hz": 0},
    "C3_lidar_detail":  {"video_fps": 0,  "lidar_mode": "detail",   "lidar_hz": 12},
    "C4_lidar_medium":  {"video_fps": 0,  "lidar_mode": "medium",   "lidar_hz": 8},
    "C5_lidar_panorama": {"video_fps": 0, "lidar_mode": "panorama", "lidar_hz": 4},
    "C6_full_detail":   {"video_fps": 30, "lidar_mode": "detail",   "lidar_hz": 12},
    "C7_full_panorama": {"video_fps": 30, "lidar_mode": "panorama", "lidar_hz": 4},
}

LIDAR_MODES = {
    "detail":   {"grid_size": 200, "cell_size_m": 0.01, "radius_m": 1.0},
    "medium":   {"grid_size": 400, "cell_size_m": 0.01, "radius_m": 2.0},
    "panorama": {"grid_size": 600, "cell_size_m": 0.01, "radius_m": 3.0},
}

TAIL_THRESHOLD_MS = 100.0
BURST_GAP_S = 5.0
N_BOOT = 10000
RNG_SEED = 42


# ── Data loading ──────────────────────────────────────────────────────────────

def load_data():
    """Load all per-probe CSVs, excluding warm-up samples."""
    frames = []
    for cond in CONDITION_ORDER:
        paths = sorted(glob.glob(os.path.join(LOGS_DIR, "wfiot_latency_%s_*.csv" % cond)))
        if not paths:
            raise FileNotFoundError("No detail CSV found for %s" % cond)
        df = pd.read_csv(paths[-1])
        df["warmup"] = df["warmup"].astype(str).str.lower() == "true"
        frames.append(df)
    full = pd.concat(frames, ignore_index=True)
    measured = full[~full["warmup"]].copy()
    return full, measured


# ── Summary statistics (same percentile/std conventions as the simulator) ────

def summarize(measured):
    rows = []
    for cond in CONDITION_ORDER:
        r = measured.loc[measured["condition"] == cond, "rtt_ms"].to_numpy()
        rows.append({
            "condition": cond,
            "n": len(r),
            "mean": np.mean(r),
            "median": np.percentile(r, 50),
            "min": np.min(r),
            "max": np.max(r),
            "p95": np.percentile(r, 95),
            "p99": np.percentile(r, 99),
            "jitter_std": np.std(r),  # population std, ddof=0 (matches simulator)
        })
    return pd.DataFrame(rows)


def sanity_check(summary_df):
    """Compare recomputed stats against the simulator-generated summary CSV."""
    paths = sorted(glob.glob(os.path.join(LOGS_DIR, "wfiot_latency_summary_*.csv")))
    ref = pd.read_csv(paths[-1])
    ok = True
    for _, row in summary_df.iterrows():
        r = ref[ref["condition"] == row["condition"]].iloc[0]
        checks = [
            ("mean", r["rtt_mean_ms"]), ("median", r["rtt_median_ms"]),
            ("p95", r["rtt_p95_ms"]), ("p99", r["rtt_p99_ms"]),
            ("max", r["rtt_max_ms"]), ("jitter_std", r["jitter_std_ms"]),
        ]
        for key, ref_val in checks:
            if abs(row[key] - ref_val) > 0.01:
                print("  MISMATCH %s %s: recomputed %.3f vs summary %.3f"
                      % (row["condition"], key, row[key], ref_val))
                ok = False
    return ok


# ── Hypothesis tests ──────────────────────────────────────────────────────────

def cliffs_delta_from_u(u_stat, n1, n2):
    """Cliff's delta from the Mann-Whitney U statistic of sample 1."""
    return 2.0 * u_stat / (n1 * n2) - 1.0


def holm_correction(pvals):
    """Holm–Bonferroni step-down adjusted p-values."""
    m = len(pvals)
    order = np.argsort(pvals)
    adj = np.empty(m)
    running_max = 0.0
    for rank, idx in enumerate(order):
        val = min((m - rank) * pvals[idx], 1.0)
        running_max = max(running_max, val)
        adj[idx] = running_max
    return adj


def hypothesis_tests(measured):
    groups = [measured.loc[measured["condition"] == c, "rtt_ms"].to_numpy()
              for c in CONDITION_ORDER]

    kw_h, kw_p = stats.kruskal(*groups)

    baseline = groups[0]
    rows = []
    for cond, g in zip(CONDITION_ORDER[1:], groups[1:]):
        u, p = stats.mannwhitneyu(g, baseline, alternative="two-sided")
        delta = cliffs_delta_from_u(u, len(g), len(baseline))
        rows.append({"condition": cond, "U": u, "p_raw": p, "cliffs_delta": delta})
    pw = pd.DataFrame(rows)
    pw["p_holm"] = holm_correction(pw["p_raw"].to_numpy())
    return kw_h, kw_p, pw


def bootstrap_cis(measured, n_boot=N_BOOT, seed=RNG_SEED):
    rng = np.random.default_rng(seed)
    rows = []
    for cond in CONDITION_ORDER:
        r = measured.loc[measured["condition"] == cond, "rtt_ms"].to_numpy()
        idx = rng.integers(0, len(r), size=(n_boot, len(r)))
        boot = r[idx]
        med = np.percentile(boot, 50, axis=1)
        p95 = np.percentile(boot, 95, axis=1)
        rows.append({
            "condition": cond,
            "median": np.percentile(r, 50),
            "median_ci_lo": np.percentile(med, 2.5),
            "median_ci_hi": np.percentile(med, 97.5),
            "p95": np.percentile(r, 95),
            "p95_ci_lo": np.percentile(p95, 2.5),
            "p95_ci_hi": np.percentile(p95, 97.5),
        })
    return pd.DataFrame(rows)


# ── Tail and burst analysis ───────────────────────────────────────────────────

def tail_analysis(measured, threshold=TAIL_THRESHOLD_MS):
    rows = []
    for cond in CONDITION_ORDER:
        g = measured[measured["condition"] == cond]
        n = len(g)
        n_over = int((g["rtt_ms"] > threshold).sum())
        rows.append({
            "condition": cond, "n": n,
            "n_over": n_over,
            "pct_over": 100.0 * n_over / n,
        })
    return pd.DataFrame(rows)


def burst_analysis(measured, threshold=TAIL_THRESHOLD_MS, gap_s=BURST_GAP_S):
    """Cluster threshold-exceeding samples by send-time proximity."""
    rows = []
    for cond in CONDITION_ORDER:
        g = measured[measured["condition"] == cond].sort_values("t_send_unix")
        ev = g[g["rtt_ms"] > threshold]
        if len(ev) == 0:
            rows.append({"condition": cond, "n_events": 0, "n_clusters": 0,
                         "largest_cluster": 0, "largest_span_s": 0.0,
                         "max_rtt_ms": g["rtt_ms"].max()})
            continue
        times = ev["t_send_unix"].to_numpy()
        clusters = []
        start = 0
        for i in range(1, len(times)):
            if times[i] - times[i - 1] > gap_s:
                clusters.append((start, i - 1))
                start = i
        clusters.append((start, len(times) - 1))
        sizes = [(b - a + 1) for a, b in clusters]
        spans = [times[b] - times[a] for a, b in clusters]
        big = int(np.argmax(sizes))
        rows.append({
            "condition": cond,
            "n_events": len(ev),
            "n_clusters": len(clusters),
            "largest_cluster": sizes[big],
            "largest_span_s": spans[big],
            "max_rtt_ms": g["rtt_ms"].max(),
        })
    return pd.DataFrame(rows)


# ── Offered-load model (replicated from the simulator's generators) ──────────

def _build_lidar_occupancy(grid_size):
    """Identical to wfiot_nuc_latency_simulator._build_lidar_occupancy (non-compact)."""
    occ = np.zeros(grid_size * grid_size, dtype=np.uint8)
    center = grid_size // 2
    n_pts = max(50, min(120, grid_size // 2))
    for i in range(n_pts):
        angle = math.pi * i / n_pts
        r = center * 0.70
        x = int(center + r * math.cos(angle))
        y = int(center + r * math.sin(angle))
        if 0 <= x < grid_size and 0 <= y < grid_size:
            occ[y * grid_size + x] = 1
    return occ


def lidar_payload_bytes(mode):
    p = LIDAR_MODES[mode]
    gs = p["grid_size"]
    occ = _build_lidar_occupancy(gs)
    payload = {"ts": 1779496190.0, "mode": mode, "grid_size": gs,
               "cell_size_m": p["cell_size_m"], "radius_m": p["radius_m"],
               "hits": int(np.sum(occ)), "occupancy": occ.tolist()}
    return len(json.dumps(payload).encode("utf-8"))


def video_frame_bytes(n_frames=300, quality=85):
    """Mean synthetic JPEG size, replicating _generate_frame(mode='normal')."""
    import cv2
    sizes = []
    for fc in range(n_frames):
        img = np.full((480, 640, 3), (40, 40, 40), dtype=np.uint8)
        font = cv2.FONT_HERSHEY_SIMPLEX
        col = (200, 200, 200)
        ts = 1779496190.0 + fc / 30.0
        cv2.putText(img, "ts:%.3f" % ts, (10, 28), font, 0.5, col, 1)
        cv2.putText(img, "mode:normal", (10, 52), font, 0.5, col, 1)
        cv2.putText(img, "frame:%d" % fc, (10, 76), font, 0.5, col, 1)
        cv2.putText(img, "id:C2_video_normal", (10, 100), font, 0.42, (170, 170, 170), 1)
        ok, jpeg = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, quality])
        sizes.append(len(jpeg.tobytes()))
    return float(np.mean(sizes)), float(np.std(sizes))


def offered_load_table(summary_df):
    jpeg_mean, jpeg_std = video_frame_bytes()
    lidar_bytes = {m: lidar_payload_bytes(m) for m in LIDAR_MODES}
    rows = []
    for cond in CONDITION_ORDER:
        s = CONDITION_STREAMS[cond]
        video_bps = s["video_fps"] * jpeg_mean
        lidar_b = lidar_bytes[s["lidar_mode"]] if s["lidar_mode"] else 0
        lidar_bps = s["lidar_hz"] * lidar_b
        total_mbps = (video_bps + lidar_bps) * 8.0 / 1e6
        rows.append({
            "condition": cond,
            "video_fps": s["video_fps"],
            "jpeg_bytes_mean": jpeg_mean if s["video_fps"] else 0,
            "lidar_mode": s["lidar_mode"] or "off",
            "lidar_hz": s["lidar_hz"],
            "lidar_payload_bytes": lidar_b,
            "offered_load_mbps": total_mbps,
        })
    df = pd.DataFrame(rows)
    df = df.merge(summary_df[["condition", "median", "p95", "p99"]], on="condition")
    return df, jpeg_mean, jpeg_std, lidar_bytes


# ── Report ────────────────────────────────────────────────────────────────────

def fmt_p(p):
    if p < 0.001:
        return "<0.001"
    return "%.3f" % p


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    full, measured = load_data()

    n_total = len(measured)
    print("Loaded %d measured probes (+%d warm-up excluded)"
          % (n_total, len(full) - n_total))

    summary = summarize(measured)
    print("\nSanity check vs simulator summary CSV:",
          "OK" if sanity_check(summary) else "FAILED")

    kw_h, kw_p, pw = hypothesis_tests(measured)
    cis = bootstrap_cis(measured)
    tail = tail_analysis(measured)
    burst = burst_analysis(measured)
    load_df, jpeg_mean, jpeg_std, lidar_bytes = offered_load_table(summary)

    rho, rho_p = stats.spearmanr(load_df["offered_load_mbps"], load_df["p95"])

    # ── Save CSV tables ──
    summary.to_csv(os.path.join(OUT_DIR, "stats_summary.csv"), index=False)
    pw.to_csv(os.path.join(OUT_DIR, "stats_pairwise.csv"), index=False)
    cis.to_csv(os.path.join(OUT_DIR, "stats_bootstrap_cis.csv"), index=False)
    tail.to_csv(os.path.join(OUT_DIR, "stats_tail.csv"), index=False)
    burst.to_csv(os.path.join(OUT_DIR, "stats_bursts.csv"), index=False)
    load_df.to_csv(os.path.join(OUT_DIR, "stats_offered_load.csv"), index=False)

    # ── Markdown report ──
    lines = []
    lines.append("# WF-IoT v3 statistical analysis report\n")
    lines.append("Measured probes: %d across %d conditions (warm-up excluded).\n"
                 % (n_total, len(CONDITION_ORDER)))

    lines.append("## 1. Summary statistics (recomputed from raw CSVs)\n")
    lines.append(summary.to_markdown(index=False, floatfmt=".2f") + "\n")

    lines.append("## 2. Kruskal-Wallis omnibus (RTT ~ condition)\n")
    lines.append("H = %.2f, p = %s, k = 7, n = %d\n" % (kw_h, fmt_p(kw_p), n_total))

    lines.append("## 3. Pairwise Mann-Whitney U vs C1 baseline (Holm-corrected) + Cliff's delta\n")
    pw_disp = pw.copy()
    pw_disp["p_raw"] = pw_disp["p_raw"].map(fmt_p)
    pw_disp["p_holm"] = pw_disp["p_holm"].map(fmt_p)
    lines.append(pw_disp.to_markdown(index=False, floatfmt=".3f") + "\n")

    lines.append("## 4. Bootstrap 95% CIs (10k resamples)\n")
    lines.append(cis.to_markdown(index=False, floatfmt=".2f") + "\n")

    lines.append("## 5. Tail probability P(RTT > %.0f ms)\n" % TAIL_THRESHOLD_MS)
    lines.append(tail.to_markdown(index=False, floatfmt=".3f") + "\n")

    lines.append("## 6. Burst clusters (RTT > %.0f ms, gap < %.0f s)\n"
                 % (TAIL_THRESHOLD_MS, BURST_GAP_S))
    lines.append(burst.to_markdown(index=False, floatfmt=".2f") + "\n")

    lines.append("## 7. Offered-load model and tail correlation\n")
    lines.append("Synthetic JPEG (640x480, q85, mode=normal): mean %.0f bytes (std %.0f)\n"
                 % (jpeg_mean, jpeg_std))
    for m, b in lidar_bytes.items():
        lines.append("- LiDAR %s grid payload: %d bytes (JSON)\n" % (m, b))
    lines.append("\n" + load_df.to_markdown(index=False, floatfmt=".3f") + "\n")
    lines.append("\nSpearman rho(offered load, P95) = %.3f, p = %s (n = 7 conditions)\n"
                 % (rho, fmt_p(rho_p)))

    report = "\n".join(lines)
    report_path = os.path.join(OUT_DIR, "stats_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print("\n" + report)
    print("\nReport written to %s" % report_path)


if __name__ == "__main__":
    main()
