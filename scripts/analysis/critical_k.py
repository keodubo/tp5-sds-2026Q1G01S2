#!/usr/bin/env python3
"""Find the critical coupling K_c for each TP5 Sistema 2 (FHN) topology.

K_c is the smallest coupling at which the network transitions from "does not
synchronise" to "synchronises" within the simulated horizon T. We measure it from
the aggregated observables only (no per-neuron states needed):

  - sync_fraction(K): fraction of realizations whose sigma_v(t) stays <= threshold
    for the rest of the run (genuine synchronisation by the end of T).
  - steady sigma_v(K): mean tail sigma_v (spatial dispersion at steady state).

K_c is bracketed as (K_below, K_above): the last K with sync_fraction < onset and
the first K with sync_fraction >= onset (scanning low -> high). The point estimate is
the geometric mean of the bracket. If even the smallest K already synchronises we
report "<= K_min"; if no K reaches the onset we report "no sync within T".

Combine several sweep directories (e.g. the small-K sweep + output2) with repeated
--input-dir so the K axis spans {0, 1e-4, 1e-3, 1e-2, 0.1, ..., 1.0}.

Usage:
    python3 scripts/analysis/critical_k.py \
        --input-dir outputs/fhn-sweep-smallK-T500-dt005-init05-observables \
        --input-dir output2 \
        --output-dir results/2026-06-08_kc-smallK_v1
"""
from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from scripts.analysis.fhn import (
    GroupKey,
    aggregate_metrics,
    format_probability,
    group_records,
    load_records,
)

SAFE_LOG_K = 1.0e-5  # plot K=0 at this position on a log axis


@dataclass(frozen=True)
class KPoint:
    k: float
    sync_fraction: float
    stable_sync_fraction: float
    steady_sigma: float
    sync_time_mean: float
    run_count: int


@dataclass(frozen=True)
class CriticalK:
    k_below: float | None   # last K below the onset (None if even K_min syncs)
    k_above: float | None   # first K at/above the onset (None if never syncs)
    estimate: float | None  # geometric-mean point estimate inside the bracket

    def describe(self) -> str:
        if self.k_above is None:
            return "sin sincronizacion dentro de T"
        if self.k_below is None:
            return f"<= {fmt_k(self.k_above)}"
        if self.estimate is None:
            # only K=0 sits below the onset: the critical value is below the
            # smallest non-zero K tested (its true value is unresolved here).
            return f"< {fmt_k(self.k_above)}  (entre 0 y {fmt_k(self.k_above)})"
        return f"{fmt_k(self.estimate)}  (entre {fmt_k(self.k_below)} y {fmt_k(self.k_above)})"


def fmt_k(value: float | None) -> str:
    if value is None:
        return "-"
    if value == 0.0:
        return "0"
    if value >= 0.01:
        return f"{value:.3g}"
    return f"{value:.1e}"


def series_for(records, key_filter) -> list[KPoint]:
    """Aggregate the records matching key_filter into a K-sorted list of KPoints."""
    groups = group_records([r for r in records if key_filter(r.group_key)])
    points: list[KPoint] = []
    for key, recs in groups.items():
        agg = aggregate_metrics([r.metrics for r in recs])
        points.append(
            KPoint(
                k=key.k_value,
                sync_fraction=agg["sync_fraction"],
                stable_sync_fraction=agg["stable_sync_fraction"],
                steady_sigma=agg["tail_sigma_mean"],
                sync_time_mean=agg["sync_time_mean"],
                run_count=agg["run_count"],
            )
        )
    points.sort(key=lambda pt: pt.k)
    # collapse duplicate K (same K coming from two input dirs) keeping the richer one
    merged: dict[float, KPoint] = {}
    for pt in points:
        prev = merged.get(pt.k)
        if prev is None or pt.run_count > prev.run_count:
            merged[pt.k] = pt
    return [merged[k] for k in sorted(merged)]


def critical_k(points: list[KPoint], onset: float, *, use_stable: bool) -> CriticalK:
    """Bracket the onset of synchronisation scanning K from low to high."""
    if not points:
        return CriticalK(None, None, None)
    frac = (lambda pt: pt.stable_sync_fraction) if use_stable else (lambda pt: pt.sync_fraction)
    k_below: float | None = None
    for pt in points:
        if frac(pt) >= onset:
            if k_below is None:
                return CriticalK(None, pt.k, pt.k)  # already synced at the smallest K
            if k_below <= 0.0:
                # only K=0 is below the onset -> true K_c is below the smallest
                # non-zero K; a geometric-mean point estimate would be a fabrication.
                return CriticalK(0.0, pt.k, None)
            est = float(np.sqrt(k_below * pt.k))
            return CriticalK(k_below, pt.k, est)
        k_below = pt.k
    return CriticalK(k_below, None, None)  # never reaches the onset


# --------------------------------------------------------------------------- plots
def log_k(k: float) -> float:
    return SAFE_LOG_K if k <= 0.0 else k


def plot_complete(points: list[KPoint], kc: CriticalK, out: Path, onset: float) -> None:
    ks = [log_k(pt.k) for pt in points]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 5.0))

    ax1.plot(ks, [pt.sync_fraction for pt in points], "o-", color="#1f77b4", label="frac. sincroniza")
    ax1.plot(ks, [pt.stable_sync_fraction for pt in points], "s--", color="#9467bd", label="frac. estable")
    ax1.axhline(onset, color="gray", lw=0.8, ls=":")
    if kc.estimate is not None:
        ax1.axvline(log_k(kc.estimate), color="#d62728", lw=1.2, ls="-",
                    label=rf"$K_c \approx$ {fmt_k(kc.estimate)}")
        if kc.k_below is not None and kc.k_above is not None:
            ax1.axvspan(log_k(kc.k_below), log_k(kc.k_above), color="#d62728", alpha=0.10)
    ax1.set_xscale("log")
    ax1.set_xlabel(r"$K$  (0 dibujado en $10^{-5}$)")
    ax1.set_ylabel("fraccion de realizaciones (15)")
    ax1.set_ylim(-0.03, 1.03)
    ax1.set_title("Red completa: sincronizacion vs K")
    ax1.legend(fontsize=9)
    ax1.grid(alpha=0.25)

    ax2.plot(ks, [pt.steady_sigma for pt in points], "o-", color="#2ca02c")
    ax2.set_xscale("log")
    ax2.set_yscale("log")
    ax2.set_xlabel(r"$K$  (0 dibujado en $10^{-5}$)")
    ax2.set_ylabel(r"$\sigma_v$ estacionaria")
    ax2.set_title("Red completa: dispersion estacionaria vs K")
    ax2.grid(alpha=0.25, which="both")

    fig.suptitle(rf"Red completa — $K_c$ {kc.describe()}", fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(out, dpi=130)
    plt.close(fig)


def plot_family(param_series: list[tuple[str, float, list[KPoint], CriticalK]],
                param_name: str, out: Path, onset: float, title: str) -> None:
    """Heatmap of sync_fraction over (parameter, K) with K_c(param) overlaid."""
    param_series = [ps for ps in param_series if ps[2]]
    if not param_series:
        return
    all_ks = sorted({pt.k for _, _, pts, _ in param_series for pt in pts})
    k_idx = {k: i for i, k in enumerate(all_ks)}
    grid = np.full((len(param_series), len(all_ks)), np.nan)
    for row, (_, _, pts, _) in enumerate(param_series):
        for pt in pts:
            grid[row, k_idx[pt.k]] = pt.sync_fraction

    fig, (axh, axl) = plt.subplots(1, 2, figsize=(13.5, 5.4),
                                   gridspec_kw={"width_ratios": [1.35, 1.0]})

    im = axh.imshow(grid, aspect="auto", cmap="viridis", vmin=0.0, vmax=1.0, origin="lower")
    axh.set_xticks(range(len(all_ks)))
    axh.set_xticklabels([fmt_k(k) for k in all_ks], rotation=45, ha="right", fontsize=8)
    axh.set_yticks(range(len(param_series)))
    axh.set_yticklabels([lbl for lbl, _, _, _ in param_series], fontsize=8)
    axh.set_xlabel(r"$K$")
    axh.set_ylabel(param_name)
    axh.set_title("Fraccion que sincroniza")
    # overlay K_c bracket as a marker per row
    for row, (_, _, _, kc) in enumerate(param_series):
        if kc.estimate is not None:
            axh.plot(np.interp(np.log10(log_k(kc.estimate)),
                               [np.log10(log_k(k)) for k in all_ks], range(len(all_ks))),
                     row, "rx", markersize=7, markeredgewidth=1.6)
    fig.colorbar(im, ax=axh, shrink=0.85, label="frac. sync")

    # K_c vs parameter
    pvals = [pv for _, pv, _, _ in param_series]
    lows = [kc.k_below if kc.k_below not in (None, 0.0) else SAFE_LOG_K for _, _, _, kc in param_series]
    highs = [kc.k_above if kc.k_above is not None else np.nan for _, _, _, kc in param_series]
    ests = [kc.estimate if kc.estimate is not None else np.nan for _, _, _, kc in param_series]
    axl.plot(pvals, ests, "o-", color="#d62728", label=r"$K_c$ (estimado)")
    for pv, lo, hi in zip(pvals, lows, highs):
        if not np.isnan(hi):
            axl.plot([pv, pv], [lo, hi], color="#d62728", alpha=0.35, lw=2)
    axl.set_xscale("log")
    axl.set_yscale("log")
    axl.set_xlabel(param_name)
    axl.set_ylabel(r"$K_c$")
    axl.set_title(r"$K_c$ vs " + param_name + " (barra = bracket)")
    axl.grid(alpha=0.25, which="both")
    axl.legend(fontsize=9)

    fig.suptitle(title, fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(out, dpi=130)
    plt.close(fig)


# --------------------------------------------------------------------------- main
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Critical coupling K_c for FHN topologies.")
    p.add_argument("--input-dir", type=Path, action="append", required=True,
                   help="sweep dir (repeatable; combine small-K sweep + output2)")
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--sync-threshold", type=float, default=0.01)
    p.add_argument("--onset", type=float, default=0.5, help="sync-fraction onset for K_c")
    p.add_argument("--tail-fraction", type=float, default=0.2)
    p.add_argument("--stationary-abs-tol", type=float, default=0.001)
    p.add_argument("--stationary-rel-tol", type=float, default=0.05)
    p.add_argument("--use-stable", action="store_true",
                   help="use the stable-sync fraction (stationary steady state) for the onset")
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
        raise SystemExit("ERROR: no runs found in the given --input-dir(s)")

    onset = args.onset
    rows: list[dict] = []

    # ----- complete
    comp = series_for(records, lambda gk: gk.topology == "complete")
    kc_comp = critical_k(comp, onset, use_stable=args.use_stable)
    plot_complete(comp, kc_comp, args.output_dir / "kc_complete.png", onset)
    rows.append({"topology": "complete", "p": "", "k": "",
                 "K_c_estimate": kc_comp.estimate, "K_c_low": kc_comp.k_below,
                 "K_c_high": kc_comp.k_above, "describe": kc_comp.describe()})

    # ----- random: K_c(p)
    p_values = sorted({gk.p_value for r in records for gk in [r.group_key]
                       if gk.topology == "random" and gk.p_value is not None})
    random_series = []
    for pv in p_values:
        pts = series_for(records, lambda gk, pv=pv: gk.topology == "random" and gk.p_value == pv)
        kc = critical_k(pts, onset, use_stable=args.use_stable)
        random_series.append((f"p={format_probability(pv)}", pv, pts, kc))
        rows.append({"topology": "random", "p": format_probability(pv), "k": "",
                     "K_c_estimate": kc.estimate, "K_c_low": kc.k_below,
                     "K_c_high": kc.k_above, "describe": kc.describe()})
    plot_family(random_series, r"$p$", args.output_dir / "kc_random_vs_p.png", onset,
                r"Red aleatoria — $K_c$ en funcion de $p$")

    # ----- ring: K_c(k)
    k_values = sorted({gk.ring_k for r in records for gk in [r.group_key]
                       if gk.topology == "ring" and gk.ring_k is not None})
    ring_series = []
    for kv in k_values:
        pts = series_for(records, lambda gk, kv=kv: gk.topology == "ring" and gk.ring_k == kv)
        kc = critical_k(pts, onset, use_stable=args.use_stable)
        ring_series.append((f"k={kv:02d}", float(kv), pts, kc))
        rows.append({"topology": "ring", "p": "", "k": kv,
                     "K_c_estimate": kc.estimate, "K_c_low": kc.k_below,
                     "K_c_high": kc.k_above, "describe": kc.describe()})
    plot_family(ring_series, r"$k$ (vecinos)", args.output_dir / "kc_ring_vs_k.png", onset,
                r"Red anillo — $K_c$ en funcion de $k$")

    # ----- CSV + console summary
    csv_path = args.output_dir / "kc_summary.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["topology", "p", "k", "K_c_estimate",
                                               "K_c_low", "K_c_high", "describe"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"\nonset = sync_fraction >= {onset}"
          f"{' (stable)' if args.use_stable else ''}, threshold sigma_v <= {args.sync_threshold}")
    print(f"complete: K_c {kc_comp.describe()}")
    print("random  K_c(p):")
    for lbl, _, _, kc in random_series:
        print(f"   {lbl:>14}: {kc.describe()}")
    print("ring    K_c(k):")
    for lbl, _, _, kc in ring_series:
        print(f"   {lbl:>14}: {kc.describe()}")
    print(f"\nfigures + {csv_path.name} -> {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
