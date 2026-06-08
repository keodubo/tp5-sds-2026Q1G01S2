#!/usr/bin/env python3
"""Regenerate the TP5 Sistema 2 presentation *timeseries* slides with FEWER curves.

The original timeseries slides (14,15,19,20,21,22,26,27,28,29) overplot 10-11 curves
and are unreadable. Here each is reduced to 3-4 representative series, following the
format guide (docs/Guias de Formato/GuiaPresentaciones.pdf):

  - 1.7  no title inside the figure (the slide carries the title)
  - 1.8  axis labels in words, scalar symbols in italics, large font
  - 1.9  powers-of-ten notation in legends (10^-3, not 0.001 / 1e-3 / 10^-3-with-caret)
  - 2.4.2 timeseries show a *typical* evolution -> a single representative realization
          (seed_0001); averaging across realizations would damp the oscillation by phase.

K=0 .. 10^-1 spans {0, 1e-3, 1e-2, 1e-1}; data combine the small-K sweep with output2.

Usage:
    python3 scripts/analysis/ppt_timeseries_reduced.py \
        --input-dir outputs/fhn-sweep-smallK-T500-dt005-init05-observables \
        --input-dir output2 \
        --output-dir results/2026-06-08_ppt-timeseries-reduced_v1
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

from scripts.analysis.fhn import load_records

plt.rcParams.update({
    "axes.labelsize": 22,
    "xtick.labelsize": 17,
    "ytick.labelsize": 17,
    "legend.fontsize": 16,
})

COLORS = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd"]
MARKERS = ["o", "s", "^", "D"]
LINESTYLES = ["-", "--", "-.", ":"]

X_LABEL = r"tiempo  $t$"
Y_MEANV = r"potencial medio  $\langle v\rangle$"
Y_SIGMA = r"dispersión espacial  $\sigma_v$"
THRESHOLD = 0.01


def k_pow_label(value: float) -> str:
    """Power-of-ten legend label for a coupling K (format guide 1.9)."""
    if value == 0.0:
        return r"$K = 0$"
    exp = int(round(np.log10(value)))
    return rf"$K = 10^{{{exp}}}$"


def p_pow_label(value: float) -> str:
    exp = int(round(np.log10(value)))
    return rf"$p = 10^{{{exp}}}$"


def k_int_label(value: int) -> str:
    return rf"$k = {value}$"


def matches(gk, topology, *, K=None, p=None, ring_k=None) -> bool:
    if gk.topology != topology:
        return False
    if K is not None and not np.isclose(gk.k_value, K, rtol=1e-6, atol=1e-12):
        return False
    if p is not None and (gk.p_value is None or not np.isclose(gk.p_value, p, rtol=1e-3)):
        return False
    if ring_k is not None and gk.ring_k != ring_k:
        return False
    return True


def representative(records, key_filter, seed: str = "seed_0001"):
    """The single record matching key_filter for the representative realization."""
    cand = [r for r in records if key_filter(r.group_key) and r.run_dir.name == seed]
    if cand:
        return cand[0]
    any_match = [r for r in records if key_filter(r.group_key)]
    return any_match[0] if any_match else None


def plot_timeseries(records, series, observable: str, ylabel: str, out: Path,
                    show_threshold: bool) -> None:
    fig, ax = plt.subplots(figsize=(12.0, 6.6))
    plotted = 0
    for i, (key_filter, label) in enumerate(series):
        rec = representative(records, key_filter)
        if rec is None:
            print(f"  WARN missing series '{label}' for {out.name}")
            continue
        y = getattr(rec.observables, observable)
        t = rec.observables.t
        ax.plot(t, y, color=COLORS[i % len(COLORS)], ls=LINESTYLES[i % len(LINESTYLES)],
                marker=MARKERS[i % len(MARKERS)], markevery=max(1, len(t) // 11),
                markersize=7, linewidth=1.8, label=label)
        plotted += 1
    if show_threshold:
        ax.axhline(THRESHOLD, color="#7f7f7f", ls=":", lw=1.4,
                   label=r"umbral  $\sigma_v = 10^{-2}$")
    ax.set_xlabel(X_LABEL)
    ax.set_ylabel(ylabel)
    ax.grid(alpha=0.25)
    # legend as a framed "card" inside the axes, like the original slides
    ax.legend(loc="center left", framealpha=0.92, fancybox=True, borderpad=0.8,
              labelspacing=0.5)
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return plotted


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Reduced-curve presentation timeseries (FHN TP5).")
    p.add_argument("--input-dir", type=Path, action="append", required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--sync-threshold", type=float, default=0.01)
    p.add_argument("--tail-fraction", type=float, default=0.2)
    p.add_argument("--stationary-abs-tol", type=float, default=0.001)
    p.add_argument("--stationary-rel-tol", type=float, default=0.05)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

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
        raise SystemExit("ERROR: no runs found")

    K_VALUES = [0.0, 1e-3, 1e-2, 1e-1]
    P_VALUES = [1e-4, 1e-3, 1e-2, 1e-1]
    K_NEIGHBORS = [1, 2, 4, 10]

    def by_K(topology, **fixed):
        return [((lambda gk, k=k, f=fixed: matches(gk, topology, K=k, **f)), k_pow_label(k))
                for k in K_VALUES]

    # complete: vary K (slides 14, 15)
    complete_K = by_K("complete")
    # random: vary p at K=0.1 (slides 19, 20)
    random_p = [((lambda gk, p=p: matches(gk, "random", K=0.1, p=p)), p_pow_label(p))
                for p in P_VALUES]
    # random: vary K at p=0.1 (slides 21, 22)
    random_K = by_K("random", p=0.1)
    # ring: vary k at K=0.1 (slides 26, 27)
    ring_k = [((lambda gk, kk=kk: matches(gk, "ring", K=0.1, ring_k=kk)), k_int_label(kk))
              for kk in K_NEIGHBORS]
    # ring: vary K at k=10 (slides 28, 29)
    ring_K = by_K("ring", ring_k=10)

    jobs = [
        ("slide14_complete_meanv_vs_t.png", complete_K, "mean_v", Y_MEANV, False),
        ("slide15_complete_sigmav_vs_t.png", complete_K, "sigma_v", Y_SIGMA, True),
        ("slide19_random_meanv_vs_t_by_p.png", random_p, "mean_v", Y_MEANV, False),
        ("slide20_random_sigmav_vs_t_by_p.png", random_p, "sigma_v", Y_SIGMA, True),
        ("slide21_random_meanv_vs_t_by_K.png", random_K, "mean_v", Y_MEANV, False),
        ("slide22_random_sigmav_vs_t_by_K.png", random_K, "sigma_v", Y_SIGMA, True),
        ("slide26_ring_meanv_vs_t_by_k.png", ring_k, "mean_v", Y_MEANV, False),
        ("slide27_ring_sigmav_vs_t_by_k.png", ring_k, "sigma_v", Y_SIGMA, True),
        ("slide28_ring_meanv_vs_t_by_K.png", ring_K, "mean_v", Y_MEANV, False),
        ("slide29_ring_sigmav_vs_t_by_K.png", ring_K, "sigma_v", Y_SIGMA, True),
    ]
    for name, series, obs, ylabel, thr in jobs:
        n = plot_timeseries(records, series, obs, ylabel, out / name, thr)
        print(f"  {name}: {n} curvas")

    print(f"\n10 figuras -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
