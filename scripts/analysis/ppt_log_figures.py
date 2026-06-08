#!/usr/bin/env python3
"""Regenerate the TP5 Sistema 2 presentation figures with a LOGARITHMIC K axis.

The original presentation plots the K-dependent results on a linear K axis (0..1.0),
where the whole transition is squeezed into K in (0, 0.1) and invisible. With the new
small-K runs (K = 1e-4, 1e-3, 1e-2) combined with output2 (K = 0, 0.1, ..., 1.0) the K
axis spans {0, 1e-4, 1e-3, 1e-2, 0.1, ..., 1.0} and a log scale reveals the structure.

Regenerated (slide -> figure):
  16  complete sigma_v(steady) vs K           -> slide16_complete_stationary_vs_K_log.png
  17  complete t_sync vs K                     -> slide17_complete_tsync_vs_K_log.png
  21  random heatmap sigma_v(steady) (p, K)    -> slide21_random_heatmap_sigma_p_K_log.png
  22  random sigma_v(steady) vs p (K=0.1)      -> slide22_random_stationary_vs_p_log.png
  26  ring heatmap sigma_v(steady) (k, K)      -> slide26_ring_heatmap_sigma_k_K_log.png
  27  ring sigma_v(steady) vs k (K=0.1)        -> slide27_ring_stationary_vs_k.png
  28  t_sync vs K by topology                  -> slide28_tsync_vs_K_by_topology_log.png

K=0 has no logarithm; on the line plots it is shown as a dashed "sin acople" reference
line (its sigma_v) and dropped from the heatmaps (which focus on the K>0 transition).

Usage:
    python3 scripts/analysis/ppt_log_figures.py \
        --input-dir outputs/fhn-sweep-smallK-T500-dt005-init05-observables \
        --input-dir output2 \
        --output-dir results/2026-06-08_ppt-log-figures_v1
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from scripts.analysis.fhn import (
    aggregate_metrics,
    format_probability,
    group_records,
    load_records,
)

LABEL_SIGMA_STAT = r"$\sigma_v$ estacionaria"
LABEL_TSYNC = r"$t_{\mathrm{sync}}$"
LABEL_K = r"$K$"


def fmt_k(value: float) -> str:
    if value == 0.0:
        return "0"
    if value >= 0.01:
        return f"{value:g}"
    return f"{value:.0e}".replace("e-0", "e-")


def series_for(records, key_filter):
    """Return a K-sorted list of (K, aggregate-dict) for records matching key_filter."""
    groups = group_records([r for r in records if key_filter(r.group_key)])
    by_k: dict[float, dict] = {}
    for key, recs in groups.items():
        agg = aggregate_metrics([r.metrics for r in recs])
        prev = by_k.get(key.k_value)
        if prev is None or agg["run_count"] > prev["run_count"]:
            by_k[key.k_value] = agg
    return [(k, by_k[k]) for k in sorted(by_k)]


def log_edges(centers: np.ndarray) -> np.ndarray:
    logc = np.log10(centers)
    mids = (logc[:-1] + logc[1:]) / 2.0
    first = logc[0] - (mids[0] - logc[0]) if len(mids) else logc[0] - 0.5
    last = logc[-1] + (logc[-1] - mids[-1]) if len(mids) else logc[-1] + 0.5
    return 10.0 ** np.concatenate([[first], mids, [last]])


def lin_edges(centers: np.ndarray) -> np.ndarray:
    mids = (centers[:-1] + centers[1:]) / 2.0
    first = centers[0] - (mids[0] - centers[0]) if len(mids) else centers[0] - 0.5
    last = centers[-1] + (centers[-1] - mids[-1]) if len(mids) else centers[-1] + 0.5
    return np.concatenate([[first], mids, [last]])


# --------------------------------------------------------------------- line plots
def plot_complete_stationary(series, out: Path) -> None:
    fig, ax = plt.subplots(figsize=(8.2, 5.2))
    pos = [(k, a) for k, a in series if k > 0.0]
    ks = np.array([k for k, _ in pos])
    mean = np.array([a["tail_sigma_mean"] for _, a in pos])
    err = np.array([a["tail_sigma_run_std"] for _, a in pos])
    ax.errorbar(ks, mean, yerr=err, fmt="o-", capsize=3, color="#1f77b4", label=r"$K>0$")
    zero = next((a["tail_sigma_mean"] for k, a in series if k == 0.0), None)
    if zero is not None:
        ax.axhline(zero, color="#d62728", ls="--", lw=1.1, label=rf"$K=0$ (sin acople): {zero:.2f}")
    ax.set_xscale("log")
    ax.set_xlabel(LABEL_K)
    ax.set_ylabel(LABEL_SIGMA_STAT)
    ax.set_title("Red completa — dispersión estacionaria vs K (escala log)")
    ax.grid(alpha=0.25, which="both")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)


def plot_complete_tsync(series, out: Path) -> None:
    fig, ax = plt.subplots(figsize=(8.2, 5.2))
    pos = [(k, a) for k, a in series if k > 0.0 and a["sync_fraction"] > 0.0
           and np.isfinite(a["sync_time_mean"])]
    ks = np.array([k for k, _ in pos])
    mean = np.array([a["sync_time_mean"] for _, a in pos])
    err = np.array([a["sync_time_std"] for _, a in pos])
    ax.errorbar(ks, mean, yerr=err, fmt="o-", capsize=3, color="#1f77b4")
    ax.set_xscale("log")
    ax.set_xlabel(LABEL_K)
    ax.set_ylabel(LABEL_TSYNC)
    ax.set_title("Red completa — tiempo de sincronización vs K (escala log)")
    ax.grid(alpha=0.25, which="both")
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)


def plot_tsync_by_topology(series_by_label, out: Path) -> None:
    fig, ax = plt.subplots(figsize=(8.6, 5.4))
    colors = {"Completa": "#1f77b4", "Aleatoria p=0.1": "#ff7f0e", "Anillo k=10": "#2ca02c"}
    for label, series in series_by_label:
        pos = [(k, a) for k, a in series if k > 0.0 and a["sync_fraction"] > 0.0
               and np.isfinite(a["sync_time_mean"])]
        if not pos:
            continue
        ks = np.array([k for k, _ in pos])
        mean = np.array([a["sync_time_mean"] for _, a in pos])
        err = np.array([a["sync_time_std"] for _, a in pos])
        ax.errorbar(ks, mean, yerr=err, fmt="o-", capsize=3,
                    color=colors.get(label), label=label)
    ax.set_xscale("log")
    ax.set_xlabel(LABEL_K)
    ax.set_ylabel(LABEL_TSYNC)
    ax.set_title("Tiempo al estacionario entre redes vs K (escala log)")
    ax.grid(alpha=0.25, which="both")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)


def plot_stationary_vs_param(points, param_label: str, out: Path, title: str,
                             log_x: bool) -> None:
    fig, ax = plt.subplots(figsize=(8.2, 5.2))
    xs = np.array([x for x, _ in points])
    mean = np.array([a["tail_sigma_mean"] for _, a in points])
    err = np.array([a["tail_sigma_run_std"] for _, a in points])
    ax.errorbar(xs, mean, yerr=err, fmt="o-", capsize=3, color="#1f77b4")
    if log_x:
        ax.set_xscale("log")
    ax.set_xlabel(param_label)
    ax.set_ylabel(LABEL_SIGMA_STAT)
    ax.set_title(title)
    ax.grid(alpha=0.25, which="both")
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)


# ------------------------------------------------------------------------ heatmaps
def plot_heatmap(records, topology: str, param_values, param_filter, param_label: str,
                 out: Path, title: str, log_y: bool) -> None:
    k_set = sorted({gk.k_value for r in records for gk in [r.group_key]
                    if gk.topology == topology and gk.k_value > 0.0})
    ks = np.array(k_set)
    rows = []
    for pv in param_values:
        series = dict(series_for(records, lambda gk, pv=pv: param_filter(gk, pv)))
        rows.append([series[k]["tail_sigma_mean"] if k in series else np.nan for k in ks])
    grid = np.array(rows)

    fig, ax = plt.subplots(figsize=(9.2, 5.6))
    x_edges = log_edges(ks)
    y_edges = log_edges(np.array(param_values)) if log_y else lin_edges(np.array(param_values, float))
    mesh = ax.pcolormesh(x_edges, y_edges, grid, cmap="viridis", vmin=0.0, vmax=0.9,
                         shading="flat")
    ax.set_xscale("log")
    if log_y:
        ax.set_yscale("log")
    ax.set_xlabel(LABEL_K)
    ax.set_ylabel(param_label)
    ax.set_title(title)
    fig.colorbar(mesh, ax=ax, label=LABEL_SIGMA_STAT)
    zero = [a["tail_sigma_mean"] for k, a in series_for(records, lambda gk: gk.topology == topology and gk.k_value == 0.0)]
    note = f"K=0 (sin acople): σ_v ≈ {np.mean(zero):.2f}  ·  oscuro = sincronizado" if zero else ""
    if note:
        fig.text(0.5, 0.01, note, ha="center", fontsize=9, color="#444444")
    fig.tight_layout(rect=(0, 0.035, 1, 1))
    fig.savefig(out, dpi=160)
    plt.close(fig)


# ---------------------------------------------------------------------------- main
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Presentation figures with log-K axis (FHN TP5).")
    p.add_argument("--input-dir", type=Path, action="append", required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--sync-threshold", type=float, default=0.01)
    p.add_argument("--tail-fraction", type=float, default=0.2)
    p.add_argument("--stationary-abs-tol", type=float, default=0.001)
    p.add_argument("--stationary-rel-tol", type=float, default=0.05)
    p.add_argument("--representative-p", type=float, default=0.1)
    p.add_argument("--representative-ring-k", type=int, default=10)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    records = []
    for input_dir in args.input_dir:
        recs = load_records(
            input_dir,
            sync_threshold=args.sync_threshold,
            tail_fraction=args.tail_fraction,
            stationary_abs_tol=args.stationary_abs_tol,
            stationary_rel_tol=args.stationary_rel_tol,
        )
        print(f"loaded {len(recs):4d} runs from {input_dir}")
        records.extend(recs)
    if not records:
        raise SystemExit("ERROR: no runs in the given --input-dir(s)")

    out = args.output_dir
    rep_p = args.representative_p
    rep_k = args.representative_ring_k

    # complete (slides 16, 17)
    comp = series_for(records, lambda gk: gk.topology == "complete")
    plot_complete_stationary(comp, out / "slide16_complete_stationary_vs_K_log.png")
    plot_complete_tsync(comp, out / "slide17_complete_tsync_vs_K_log.png")

    # random heatmap + vs p (slides 21, 22)
    p_values = sorted({gk.p_value for r in records for gk in [r.group_key]
                       if gk.topology == "random" and gk.p_value is not None})
    plot_heatmap(records, "random", p_values,
                 lambda gk, pv: gk.topology == "random" and gk.p_value == pv, r"$p$",
                 out / "slide21_random_heatmap_sigma_p_K_log.png",
                 "Red aleatoria — σ_v estacionaria (p, K) · escala log", log_y=True)
    rand_vs_p = [(pv, a) for pv in p_values
                 for a in [dict(series_for(records, lambda gk, pv=pv: gk.topology == "random"
                                           and gk.p_value == pv)).get(0.1)] if a]
    plot_stationary_vs_param(rand_vs_p, r"$p$",
                             out / "slide22_random_stationary_vs_p_log.png",
                             "Red aleatoria — σ_v estacionaria vs p (K=0.1, escala log)",
                             log_x=True)

    # ring heatmap + vs k (slides 26, 27)
    k_values = sorted({gk.ring_k for r in records for gk in [r.group_key]
                       if gk.topology == "ring" and gk.ring_k is not None})
    plot_heatmap(records, "ring", k_values,
                 lambda gk, kv: gk.topology == "ring" and gk.ring_k == kv, r"$k$ (vecinos)",
                 out / "slide26_ring_heatmap_sigma_k_K_log.png",
                 "Red anillo — σ_v estacionaria (k, K) · K escala log", log_y=False)
    ring_vs_k = [(kv, a) for kv in k_values
                 for a in [dict(series_for(records, lambda gk, kv=kv: gk.topology == "ring"
                                           and gk.ring_k == kv)).get(0.1)] if a]
    plot_stationary_vs_param(ring_vs_k, r"$k$ (vecinos)",
                             out / "slide27_ring_stationary_vs_k.png",
                             "Red anillo — σ_v estacionaria vs k (K=0.1)", log_x=False)

    # t_sync by topology (slide 28)
    series_by_label = [
        ("Completa", comp),
        ("Aleatoria p=0.1", series_for(records, lambda gk: gk.topology == "random" and gk.p_value == rep_p)),
        ("Anillo k=10", series_for(records, lambda gk: gk.topology == "ring" and gk.ring_k == rep_k)),
    ]
    plot_tsync_by_topology(series_by_label, out / "slide28_tsync_vs_K_by_topology_log.png")

    print(f"\n7 figuras (eje K log) -> {out}")
    for f in sorted(out.glob("slide*.png")):
        print(f"  {f.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
