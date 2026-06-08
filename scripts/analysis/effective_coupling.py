#!/usr/bin/env python3
"""Test whether the synchronization transition collapses onto an effective coupling.

Hypothesis (current conclusion #2): what governs synchronization is not K alone but the
effective coupling K_eff = K * <degree>, where the mean degree is:
    complete : N-1            = 500
    random p : p * (N-1)      = 500 p
    ring k   : 2 k

If true, plotting steady-state sigma_v vs K_eff should collapse all topologies onto one
transition curve. This figure lets the conclusion be *shown* (format guide 2.5).

Usage:
    python3 scripts/analysis/effective_coupling.py \
        --input-dir outputs/fhn-sweep-smallK-T500-dt005-init05-observables \
        --input-dir output2 \
        --output-dir results/2026-06-08_effective-coupling_v1
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

from scripts.analysis.fhn import aggregate_metrics, group_records, load_records

N = 501


def mean_degree(gk) -> float:
    if gk.topology == "complete":
        return N - 1
    if gk.topology == "random":
        return gk.p_value * (N - 1)
    if gk.topology == "ring":
        return 2 * gk.ring_k
    return float("nan")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Effective-coupling collapse (FHN TP5).")
    p.add_argument("--input-dir", type=Path, action="append", required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--sync-threshold", type=float, default=0.01)
    p.add_argument("--tail-fraction", type=float, default=0.2)
    p.add_argument("--stationary-abs-tol", type=float, default=0.001)
    p.add_argument("--stationary-rel-tol", type=float, default=0.05)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    records = []
    for d in args.input_dir:
        records.extend(load_records(
            d, sync_threshold=args.sync_threshold, tail_fraction=args.tail_fraction,
            stationary_abs_tol=args.stationary_abs_tol, stationary_rel_tol=args.stationary_rel_tol,
        ))
    groups = group_records(records)

    pts = {"complete": [], "random": [], "ring": []}
    for gk, recs in groups.items():
        if gk.k_value <= 0.0:
            continue
        keff = gk.k_value * mean_degree(gk)
        sigma = aggregate_metrics([r.metrics for r in recs])["tail_sigma_mean"]
        pts[gk.topology].append((keff, sigma))

    fig, ax = plt.subplots(figsize=(11.5, 6.5))
    styles = {"complete": ("#1f77b4", "o", "completa"),
              "random": ("#ff7f0e", "s", "aleatoria"),
              "ring": ("#2ca02c", "^", "anillo")}
    for topo, (color, marker, label) in styles.items():
        data = sorted(pts[topo])
        if not data:
            continue
        x = np.array([d[0] for d in data])
        y = np.array([d[1] for d in data])
        ax.scatter(x, y, c=color, marker=marker, s=52, alpha=0.75, edgecolors="none", label=label)
    ax.set_xscale("log")
    ax.set_xlabel(r"acople efectivo  $K\,\langle\mathrm{grado}\rangle$", fontsize=22)
    ax.set_ylabel(r"dispersión estacionaria  $\sigma_v$", fontsize=22)
    ax.tick_params(labelsize=16)
    ax.grid(alpha=0.25, which="both")
    ax.legend(fontsize=17, framealpha=0.92)
    fig.tight_layout()
    out = args.output_dir / "effective_coupling_collapse.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    print(f"-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
