#!/usr/bin/env python3
"""
wfiot_make_figures.py — Publication figures for the WF-IoT 2026 paper (v3).

Regenerates all results figures from the raw per-probe CSVs in logs/,
in a consistent IEEE-column style (vector PDF + PNG preview):

  fig_rtt_box.pdf       boxplot of RTT per condition (whiskers at P5/P95)
  fig_rtt_cdf.pdf       empirical CDF per condition with 100 ms reference
  fig_tail_vs_load.pdf  median / P95 (bootstrap CI) vs offered load
  fig_burst_c1.pdf      C1 vs C7 time series highlighting the C1 burst

Usage (from repo root):
    python validation/tools/wfiot_make_figures.py
"""

import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wfiot_stats_analysis import (  # noqa: E402
    CONDITION_ORDER, CONDITION_STREAMS, REPO_ROOT, TAIL_THRESHOLD_MS,
    bootstrap_cis, lidar_payload_bytes, load_data, summarize,
    video_frame_bytes,
)

FIG_DIR = os.path.join(REPO_ROOT, "IEEE_IOT", "figs")

SHORT_LABELS = ["C1\nControl", "C2\nVideo", "C3\nLiDAR\ndetail",
                "C4\nLiDAR\nmedium", "C5\nLiDAR\npanorama",
                "C6\nVideo+\ndetail", "C7\nVideo+\npanorama"]
LEGEND_LABELS = ["C1 Control", "C2 Video", "C3 LiDAR detail", "C4 LiDAR medium",
                 "C5 LiDAR panorama", "C6 Video+detail", "C7 Video+panorama"]

COL_W = 3.5  # IEEE column width in inches

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": 8,
    "axes.labelsize": 8,
    "axes.titlesize": 8,
    "legend.fontsize": 6.5,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "axes.linewidth": 0.6,
    "lines.linewidth": 1.0,
    "grid.linewidth": 0.4,
    "grid.alpha": 0.4,
    "pdf.fonttype": 42,
})

COLORS = plt.cm.viridis(np.linspace(0.0, 0.85, 7))


def save(fig, name):
    fig.savefig(os.path.join(FIG_DIR, name + ".pdf"), bbox_inches="tight")
    fig.savefig(os.path.join(FIG_DIR, name + ".png"), bbox_inches="tight", dpi=300)
    plt.close(fig)
    print("  wrote %s.pdf" % name)


def groups_from(measured):
    return [measured.loc[measured["condition"] == c, "rtt_ms"].to_numpy()
            for c in CONDITION_ORDER]


def fig_rtt_box(groups):
    fig, ax = plt.subplots(figsize=(COL_W, 2.3))
    bp = ax.boxplot(groups, whis=(5, 95), showfliers=False, widths=0.55,
                    medianprops={"color": "#d95f02", "linewidth": 1.2},
                    boxprops={"linewidth": 0.7},
                    whiskerprops={"linewidth": 0.7},
                    capprops={"linewidth": 0.7})
    ax.set_xticklabels(SHORT_LABELS, fontsize=6)
    ax.set_ylabel("RTT (ms)")
    ax.set_ylim(0, 80)
    ax.yaxis.grid(True)
    ax.set_axisbelow(True)
    save(fig, "fig_rtt_box")


def fig_rtt_cdf(groups):
    fig, ax = plt.subplots(figsize=(COL_W, 2.1))
    for g, color, label in zip(groups, COLORS, LEGEND_LABELS):
        x = np.sort(g)
        y = np.arange(1, len(x) + 1) / len(x)
        ax.plot(x, y, color=color, label=label, linewidth=0.9)
    ax.axvline(TAIL_THRESHOLD_MS, color="gray", linestyle="--", linewidth=0.7)
    ax.text(TAIL_THRESHOLD_MS + 2, 0.45, "100 ms", color="gray", fontsize=6.5,
            rotation=90, va="center")
    ax.set_xlim(0, 130)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("RTT (ms)")
    ax.set_ylabel("Cumulative probability")
    ax.grid(True)
    ax.set_axisbelow(True)
    ax.legend(loc="lower right", framealpha=0.9, handlelength=1.4)
    save(fig, "fig_rtt_cdf")


def fig_tail_vs_load(summary, cis):
    jpeg_mean, _ = video_frame_bytes()
    loads = []
    for cond in CONDITION_ORDER:
        s = CONDITION_STREAMS[cond]
        lidar_b = lidar_payload_bytes(s["lidar_mode"]) if s["lidar_mode"] else 0
        bps = s["video_fps"] * jpeg_mean + s["lidar_hz"] * lidar_b
        loads.append(bps * 8.0 / 1e6)
    loads = np.array(loads)

    med = summary["median"].to_numpy()
    p95 = cis["p95"].to_numpy()
    p95_lo = cis["p95_ci_lo"].to_numpy()
    p95_hi = cis["p95_ci_hi"].to_numpy()

    fig, ax = plt.subplots(figsize=(COL_W, 2.1))
    order = np.argsort(loads)
    ax.errorbar(loads[order], p95[order],
                yerr=[p95[order] - p95_lo[order], p95_hi[order] - p95[order]],
                fmt="s-", color="#d95f02", markersize=4, capsize=2,
                linewidth=1.0, elinewidth=0.7, label="P95 RTT (95% CI)")
    ax.plot(loads[order], med[order], "o-", color="#1b9e77", markersize=4,
            label="Median RTT")
    for i, cond in enumerate(CONDITION_ORDER):
        cid = cond.split("_")[0]
        ax.annotate(cid, (loads[i], p95[i]), textcoords="offset points",
                    xytext=(0, 6), ha="center", fontsize=6.5)
    ax.set_xlabel("Offered perception load (Mb/s)")
    ax.set_ylabel("RTT (ms)")
    ax.set_ylim(0, 85)
    ax.grid(True)
    ax.set_axisbelow(True)
    ax.legend(loc="center right")
    save(fig, "fig_tail_vs_load")


def fig_burst_c1(measured):
    fig, axes = plt.subplots(2, 1, figsize=(COL_W, 2.5), sharex=True, sharey=True)
    for ax, cond, label, color in zip(
            axes, ["C1_control_only", "C7_full_panorama"],
            ["C1 Control only (no perception load)",
             "C7 Video + panorama (heaviest load)"],
            ["#1f77b4", "#d62728"]):
        g = measured[measured["condition"] == cond].sort_values("t_send_unix")
        t = g["t_send_unix"].to_numpy()
        t = t - t[0]
        r = g["rtt_ms"].to_numpy()
        ax.plot(t, r, color=color, linewidth=0.5)
        ax.axhline(TAIL_THRESHOLD_MS, color="gray", linestyle="--", linewidth=0.6)
        ax.set_ylabel("RTT (ms)")
        ax.set_title(label, fontsize=7, pad=2)
        ax.grid(True)
        ax.set_axisbelow(True)

        if cond == "C1_control_only":
            ev_t = t[r > TAIL_THRESHOLD_MS]
            if len(ev_t):
                # highlight the main burst window
                gaps = np.diff(ev_t)
                split = np.where(gaps > 5.0)[0]
                starts = np.concatenate(([0], split + 1))
                ends = np.concatenate((split, [len(ev_t) - 1]))
                sizes = ends - starts + 1
                k = int(np.argmax(sizes))
                w0, w1 = ev_t[starts[k]], ev_t[ends[k]]
                ax.axvspan(w0 - 1, w1 + 1, color="orange", alpha=0.25, zorder=0)
                ax.annotate("burst: %d probes > 100 ms\nin %.1f s (max %.0f ms)"
                            % (sizes[k], w1 - w0, r.max()),
                            xy=(w0, r.max()), xytext=(8, 240),
                            textcoords="data", fontsize=6.5,
                            arrowprops={"arrowstyle": "->", "linewidth": 0.6})
    axes[1].set_xlabel("Elapsed time within condition (s)")
    axes[0].set_ylim(0, 320)
    fig.tight_layout(h_pad=0.6)
    save(fig, "fig_burst_c1")


def main():
    os.makedirs(FIG_DIR, exist_ok=True)
    _, measured = load_data()
    groups = groups_from(measured)
    summary = summarize(measured)
    cis = bootstrap_cis(measured)

    print("Generating figures into %s" % FIG_DIR)
    fig_rtt_box(groups)
    fig_rtt_cdf(groups)
    fig_tail_vs_load(summary, cis)
    fig_burst_c1(measured)
    print("Done.")


if __name__ == "__main__":
    main()
