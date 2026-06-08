#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from scripts.analysis.fhn import (
    GroupKey,
    RunRecord,
    aggregate_metrics,
    coverage_gaps,
    format_probability,
    grid01,
    group_records,
    load_records,
    mean_curve,
    p_grid,
)

LINE_STYLES = ["-", "--", "-.", ":"]
MARKERS = ["o", "s", "^", "D", "v", "P", "X", "*", "h", "<", ">"]
TEMPORAL_K_VALUES = (0.0, 0.5, 1.0)
LABEL_MEAN_V = r"$\langle v(t)\rangle$"
LABEL_SIGMA_V = r"$\sigma_v(t)$"
LABEL_SIGMA_V_STATIONARY = r"$\sigma_v$ estacionaria"
LABEL_TAIL_MEAN_V = r"$\langle v\rangle$ promedio en la cola"
LABEL_SYNC_TIME = r"$t_{\mathrm{sync}}$"
LABEL_K = r"$K$"
LABEL_P = r"$p$"
LABEL_RING_K = r"$k$"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="analyze_fhn_outputs.py",
        description="Generate TP5 Sistema 2 figures and summary metrics from FHN observables.",
    )
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--complete-log-input-dir", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--sync-threshold", type=float, default=0.01)
    parser.add_argument("--tail-fraction", type=float, default=0.2)
    parser.add_argument("--stationary-abs-tol", type=float, default=0.001)
    parser.add_argument("--stationary-rel-tol", type=float, default=0.05)
    parser.add_argument("--expected-realizations", type=int, default=15)
    parser.add_argument("--representative-p", type=float, default=0.1)
    parser.add_argument("--representative-ring-k", type=int, default=10)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.sync_threshold < 0:
        raise SystemExit("--sync-threshold must be non-negative")
    if not 0.0 < args.tail_fraction <= 1.0:
        raise SystemExit("--tail-fraction must be in (0, 1]")
    if args.expected_realizations <= 0:
        raise SystemExit("--expected-realizations must be positive")
    if not 1.0e-4 <= args.representative_p <= 1.0e-1:
        raise SystemExit("--representative-p must be in [1e-4, 1e-1]")
    if not 1 <= args.representative_ring_k <= 10:
        raise SystemExit("--representative-ring-k must be in [1, 10]")

    records = load_records(
        args.input_dir,
        sync_threshold=args.sync_threshold,
        tail_fraction=args.tail_fraction,
        stationary_abs_tol=args.stationary_abs_tol,
        stationary_rel_tol=args.stationary_rel_tol,
    )
    if not records:
        raise SystemExit(f"no runs with metadata.properties and observables.csv found in {args.input_dir}")

    output_dir = args.output_dir
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    groups = group_records(records)
    summaries = {key: aggregate_metrics([record.metrics for record in value]) for key, value in groups.items()}
    gaps = coverage_gaps(groups, expected_realizations=args.expected_realizations)

    write_run_metrics(output_dir / "run_metrics.csv", records)
    write_group_summary(output_dir / "summary_by_group.csv", summaries)
    write_coverage_gaps(output_dir / "coverage_gaps.csv", gaps)

    complete_log_records: list[RunRecord] = []
    complete_log_groups: dict[GroupKey, list[RunRecord]] = {}
    complete_log_summaries: dict[GroupKey, dict[str, Any]] = {}
    if args.complete_log_input_dir is not None:
        complete_log_records = load_records(
            args.complete_log_input_dir,
            sync_threshold=args.sync_threshold,
            tail_fraction=args.tail_fraction,
            stationary_abs_tol=args.stationary_abs_tol,
            stationary_rel_tol=args.stationary_rel_tol,
        )
        if not complete_log_records:
            raise SystemExit(
                f"no runs with metadata.properties and observables.csv found in {args.complete_log_input_dir}"
            )
        complete_log_groups = group_records(complete_log_records)
        complete_log_summaries = {
            key: aggregate_metrics([record.metrics for record in value])
            for key, value in complete_log_groups.items()
        }
        write_run_metrics(output_dir / "complete_log_run_metrics.csv", complete_log_records)
        write_group_summary(output_dir / "complete_log_summary_by_group.csv", complete_log_summaries)

    figures = generate_figures(
        figures_dir,
        groups,
        summaries,
        complete_log_summaries=complete_log_summaries,
        sync_threshold=args.sync_threshold,
        representative_p=args.representative_p,
        representative_ring_k=args.representative_ring_k,
    )
    write_report(
        output_dir / "analysis_report.md",
        args=args,
        records=records,
        summaries=summaries,
        gaps=gaps,
        figures=figures,
        complete_log_records=complete_log_records,
    )

    print(f"OK analysis output: {output_dir}")
    print(f"  runs: {len(records)}")
    print(f"  groups: {len(groups)}")
    print(f"  complete log runs: {len(complete_log_records)}")
    print(f"  figures: {len(figures)}")
    print(f"  gaps: {len(gaps)}")
    return 0


def write_run_metrics(path: Path, records: list[RunRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "topology",
        "K",
        "p",
        "k",
        "realization",
        "run_dir",
        "sync_time",
        "tail_sigma_mean",
        "tail_sigma_std",
        "tail_mean_v_mean",
        "tail_mean_v_std",
        "stationary_delta",
        "stationary_ok",
        "final_time",
        "row_count",
    ]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for record in sorted(records, key=record_sort_key):
            metadata = record.metadata
            metrics = record.metrics
            writer.writerow(
                {
                    "topology": metadata.topology,
                    "K": fmt(metadata.k_value),
                    "p": "" if metadata.p_value is None else fmt(metadata.p_value),
                    "k": "" if metadata.ring_k is None else metadata.ring_k,
                    "realization": metadata.realization,
                    "run_dir": record.run_dir,
                    "sync_time": "" if metrics.sync_time is None else fmt(metrics.sync_time),
                    "tail_sigma_mean": fmt(metrics.tail_sigma_mean),
                    "tail_sigma_std": fmt(metrics.tail_sigma_std),
                    "tail_mean_v_mean": fmt(metrics.tail_mean_v_mean),
                    "tail_mean_v_std": fmt(metrics.tail_mean_v_std),
                    "stationary_delta": fmt(metrics.stationary_delta),
                    "stationary_ok": str(metrics.stationary_ok).lower(),
                    "final_time": fmt(metrics.final_time),
                    "row_count": metrics.row_count,
                }
            )


def write_group_summary(path: Path, summaries: dict[GroupKey, dict[str, Any]]) -> None:
    fieldnames = [
        "topology",
        "K",
        "p",
        "k",
        "run_count",
        "sync_fraction",
        "sync_time_mean",
        "sync_time_std",
        "stable_sync_fraction",
        "stable_sync_time_mean",
        "stable_sync_time_std",
        "stationary_ok_fraction",
        "tail_sigma_mean",
        "tail_sigma_run_std",
        "tail_sigma_temporal_std_mean",
        "tail_mean_v_mean",
        "tail_mean_v_run_std",
        "stationary_delta_mean",
        "final_time_min",
        "row_count_min",
    ]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for key in sorted(summaries, key=group_sort_key):
            row = {
                "topology": key.topology,
                "K": fmt(key.k_value),
                "p": "" if key.p_value is None else fmt(key.p_value),
                "k": "" if key.ring_k is None else key.ring_k,
            }
            row.update({name: fmt(value) for name, value in summaries[key].items()})
            writer.writerow(row)


def write_coverage_gaps(path: Path, gaps: list[dict[str, Any]]) -> None:
    fieldnames = ["topology", "K", "p", "k", "present_runs", "expected_runs", "missing_runs", "status"]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for gap in gaps:
            row = dict(gap)
            row["K"] = fmt(row["K"])
            if row["p"] != "":
                row["p"] = fmt(row["p"])
            writer.writerow(row)


def generate_figures(
    figures_dir: Path,
    groups: dict[GroupKey, list[RunRecord]],
    summaries: dict[GroupKey, dict[str, Any]],
    *,
    complete_log_summaries: dict[GroupKey, dict[str, Any]],
    sync_threshold: float,
    representative_p: float,
    representative_ring_k: int,
) -> list[Path]:
    figures: list[Path] = []
    for field, ylabel, filename, title in [
        ("mean_v", LABEL_MEAN_V, "complete_mean_v_timeseries.png", r"Red completa: $\langle v(t)\rangle$"),
        ("sigma_v", LABEL_SIGMA_V, "complete_sigma_v_timeseries.png", r"Red completa: $\sigma_v(t)$"),
    ]:
        path = figures_dir / filename
        if plot_complete_timeseries(
            path,
            groups,
            field=field,
            ylabel=ylabel,
            title=title,
            sync_threshold=sync_threshold if field == "sigma_v" else None,
        ):
            figures.append(path)

    for value_name, ylabel, filename, title in [
        (
            "tail_sigma_mean",
            LABEL_SIGMA_V_STATIONARY,
            "complete_stationary_sigma_vs_K.png",
            r"Red completa: $\sigma_v$ estacionaria vs $K$",
        ),
        (
            "sync_time_mean",
            LABEL_SYNC_TIME,
            "complete_sync_time_vs_K.png",
            r"Red completa: $t_{\mathrm{sync}}$ vs $K$",
        ),
    ]:
        path = figures_dir / filename
        if plot_complete_errorbar(path, summaries, value_name=value_name, ylabel=ylabel, title=title):
            figures.append(path)

    for value_name, ylabel, filename, title in [
        (
            "tail_sigma_mean",
            LABEL_SIGMA_V_STATIONARY,
            "complete_log_stationary_sigma_vs_K.png",
            r"Red completa: zoom logaritmico de $\sigma_v$ estacionaria",
        ),
        (
            "sync_time_mean",
            LABEL_SYNC_TIME,
            "complete_log_sync_time_vs_K.png",
            r"Red completa: zoom logaritmico de $t_{\mathrm{sync}}$",
        ),
    ]:
        path = figures_dir / filename
        if plot_complete_log_errorbar(
            path,
            complete_log_summaries,
            value_name=value_name,
            ylabel=ylabel,
            title=title,
        ):
            figures.append(path)

    for value_name, filename, title in [
        (
            "tail_sigma_mean",
            "random_stationary_sigma_heatmap.png",
            r"Red aleatoria: $\sigma_v$ estacionaria",
        ),
        (
            "sync_time_mean",
            "random_sync_time_heatmap.png",
            r"Red aleatoria: $t_{\mathrm{sync}}$",
        ),
        (
            "stable_sync_time_mean",
            "random_stable_sync_time_heatmap.png",
            r"Red aleatoria: $t_{\mathrm{sync}}$ estable",
        ),
        (
            "stationary_ok_fraction",
            "random_stationary_fraction_heatmap.png",
            "Red aleatoria: fraccion de corridas estacionarias",
        ),
        (
            "sync_fraction",
            "random_sync_fraction_heatmap.png",
            "Red aleatoria: fraccion sincronizada",
        ),
        (
            "stable_sync_fraction",
            "random_stable_sync_fraction_heatmap.png",
            "Red aleatoria: fraccion sincronizada estable",
        ),
    ]:
        path = figures_dir / filename
        if plot_random_heatmap(path, summaries, value_name=value_name, title=title):
            figures.append(path)

    for value_name, filename, title in [
        (
            "tail_sigma_mean",
            "ring_stationary_sigma_heatmap.png",
            r"Red anillo: $\sigma_v$ estacionaria",
        ),
        (
            "sync_time_mean",
            "ring_sync_time_heatmap.png",
            r"Red anillo: $t_{\mathrm{sync}}$",
        ),
        (
            "stable_sync_time_mean",
            "ring_stable_sync_time_heatmap.png",
            r"Red anillo: $t_{\mathrm{sync}}$ estable",
        ),
        (
            "stationary_ok_fraction",
            "ring_stationary_fraction_heatmap.png",
            "Red anillo: fraccion de corridas estacionarias",
        ),
        (
            "stable_sync_fraction",
            "ring_stable_sync_fraction_heatmap.png",
            "Red anillo: fraccion sincronizada estable",
        ),
    ]:
        path = figures_dir / filename
        if plot_ring_heatmap(path, summaries, value_name=value_name, title=title):
            figures.append(path)

    for field, ylabel, filename, title in [
        (
            "mean_v",
            LABEL_MEAN_V,
            "random_K0p1_mean_v_timeseries.png",
            r"Red aleatoria, $K=0.1$: $\langle v(t)\rangle$",
        ),
        (
            "sigma_v",
            LABEL_SIGMA_V,
            "random_K0p1_sigma_v_timeseries.png",
            r"Red aleatoria, $K=0.1$: $\sigma_v(t)$",
        ),
    ]:
        path = figures_dir / filename
        if plot_random_k01_timeseries(
            path,
            groups,
            field=field,
            ylabel=ylabel,
            title=title,
            sync_threshold=sync_threshold if field == "sigma_v" else None,
        ):
            figures.append(path)

    path = figures_dir / "random_K0p1_stationary_vs_p.png"
    if plot_random_k01_stationary(path, summaries):
        figures.append(path)

    path = figures_dir / "random_K0p1_observables_vs_p.png"
    if plot_random_k01_observables(path, summaries):
        figures.append(path)

    path = figures_dir / "random_representative_p_behavior_vs_K.png"
    if plot_k_behavior(
        path,
        groups,
        topology="random",
        representative_p=representative_p,
        representative_ring_k=None,
        sync_threshold=sync_threshold,
    ):
        figures.append(path)

    for field, ylabel, filename, title in [
        (
            "mean_v",
            LABEL_MEAN_V,
            "ring_K0p1_mean_v_timeseries.png",
            r"Red anillo, $K=0.1$: $\langle v(t)\rangle$",
        ),
        (
            "sigma_v",
            LABEL_SIGMA_V,
            "ring_K0p1_sigma_v_timeseries.png",
            r"Red anillo, $K=0.1$: $\sigma_v(t)$",
        ),
    ]:
        path = figures_dir / filename
        if plot_ring_k01_timeseries(
            path,
            groups,
            field=field,
            ylabel=ylabel,
            title=title,
            sync_threshold=sync_threshold if field == "sigma_v" else None,
        ):
            figures.append(path)

    path = figures_dir / "ring_K0p1_stationary_vs_k.png"
    if plot_ring_k01_stationary(path, summaries):
        figures.append(path)

    path = figures_dir / "ring_K0p1_observables_vs_k.png"
    if plot_ring_k01_observables(path, summaries):
        figures.append(path)

    path = figures_dir / "ring_representative_k_behavior_vs_K.png"
    if plot_k_behavior(
        path,
        groups,
        topology="ring",
        representative_p=None,
        representative_ring_k=representative_ring_k,
        sync_threshold=sync_threshold,
    ):
        figures.append(path)

    path = figures_dir / "sync_time_comparison_by_topology.png"
    if plot_sync_time_comparison(
        path,
        summaries,
        representative_p=representative_p,
        representative_ring_k=representative_ring_k,
    ):
        figures.append(path)

    path = figures_dir / "available_runs_by_topology.png"
    if plot_available_runs(path, summaries):
        figures.append(path)

    return figures


def style_for_series(index: int, color: Any, sample_count: int) -> dict[str, Any]:
    return {
        "color": color,
        "linestyle": LINE_STYLES[index % len(LINE_STYLES)],
        "marker": MARKERS[index % len(MARKERS)],
        "markevery": max(1, sample_count // 24),
        "markersize": 4.2,
        "linewidth": 1.5,
        "markerfacecolor": "white",
        "markeredgewidth": 0.9,
    }


def add_sync_threshold(axis: Any, sync_threshold: float | None) -> None:
    if sync_threshold is None:
        return
    axis.axhline(
        sync_threshold,
        color="#d62728",
        linestyle="--",
        linewidth=1.4,
        label=rf"umbral $\sigma_v={sync_threshold:g}$",
    )


def is_temporal_k(value: float) -> bool:
    return any(np.isclose(value, representative) for representative in TEMPORAL_K_VALUES)


def plot_complete_timeseries(
    path: Path,
    groups: dict[GroupKey, list[RunRecord]],
    *,
    field: str,
    ylabel: str,
    title: str,
    sync_threshold: float | None = None,
) -> bool:
    keys = sorted(
        [key for key in groups if key.topology == "complete" and is_temporal_k(key.k_value)],
        key=lambda key: key.k_value,
    )
    if not keys:
        return False
    fig, axis = plt.subplots(figsize=(10, 6), constrained_layout=True)
    colors = plt.cm.viridis(np.linspace(0.0, 1.0, len(keys)))
    for index, (color, key) in enumerate(zip(colors, keys)):
        curve = mean_curve(groups[key], field)
        if curve is None:
            continue
        t, values = curve
        axis.plot(t, values, label=f"K={key.k_value:.1f}", **style_for_series(index, color, len(t)))
    axis.set_title(title)
    axis.set_xlabel(r"$t$")
    axis.set_ylabel(ylabel)
    add_sync_threshold(axis, sync_threshold)
    axis.grid(True, alpha=0.25)
    axis.legend(ncols=2, fontsize=8)
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return True


def plot_complete_errorbar(
    path: Path,
    summaries: dict[GroupKey, dict[str, Any]],
    *,
    value_name: str,
    ylabel: str,
    title: str,
) -> bool:
    keys = sorted([key for key in summaries if key.topology == "complete"], key=lambda key: key.k_value)
    if not keys:
        return False
    x = np.array([key.k_value for key in keys])
    y = np.array([float(summaries[key][value_name]) for key in keys])
    if value_name == "tail_sigma_mean":
        yerr_name = "tail_sigma_run_std"
    elif value_name.endswith("_mean"):
        yerr_name = f"{value_name[:-5]}_std"
    else:
        yerr_name = ""
    yerr = np.array([float(summaries[key].get(yerr_name, float("nan"))) for key in keys])
    fig, axis = plt.subplots(figsize=(8, 5), constrained_layout=True)
    axis.errorbar(x, y, yerr=yerr, marker="o", linewidth=1.4, capsize=3)
    axis.set_title(title)
    axis.set_xlabel(LABEL_K)
    axis.set_ylabel(ylabel)
    axis.set_xticks(grid01())
    axis.grid(True, alpha=0.25)
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return True


def plot_complete_log_errorbar(
    path: Path,
    summaries: dict[GroupKey, dict[str, Any]],
    *,
    value_name: str,
    ylabel: str,
    title: str,
) -> bool:
    keys = sorted(
        [key for key in summaries if key.topology == "complete" and key.k_value > 0.0],
        key=lambda key: key.k_value,
    )
    if not keys:
        return False

    x = np.array([key.k_value for key in keys])
    y = np.array([float(summaries[key][value_name]) for key in keys])
    if value_name == "tail_sigma_mean":
        yerr_name = "tail_sigma_run_std"
    elif value_name.endswith("_mean"):
        yerr_name = f"{value_name[:-5]}_std"
    else:
        yerr_name = ""
    yerr = np.array([float(summaries[key].get(yerr_name, float("nan"))) for key in keys])

    fig, axis = plt.subplots(figsize=(8, 5), constrained_layout=True)
    axis.errorbar(x, y, yerr=yerr, marker="o", linewidth=1.4, capsize=3, label=r"$K>0$")
    zero_keys = [
        key for key in summaries if key.topology == "complete" and np.isclose(key.k_value, 0.0)
    ]
    if zero_keys:
        zero_value = float(summaries[zero_keys[0]][value_name])
        if np.isfinite(zero_value):
            axis.axhline(zero_value, color="#d62728", linestyle="--", label=r"$K=0$ (referencia)")
        else:
            axis.text(
                0.02,
                0.95,
                r"$K=0$: no sincroniza",
                transform=axis.transAxes,
                ha="left",
                va="top",
            )
    axis.set_title(title)
    axis.set_xlabel(LABEL_K)
    axis.set_ylabel(ylabel)
    axis.set_xscale("log")
    axis.grid(True, which="both", alpha=0.25)
    axis.legend()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return True


def plot_random_heatmap(
    path: Path,
    summaries: dict[GroupKey, dict[str, Any]],
    *,
    value_name: str,
    title: str,
) -> bool:
    p_values = sorted({key.p_value for key in summaries if key.topology == "random" and key.p_value is not None})
    k_values = sorted({round(key.k_value, 1) for key in summaries if key.topology == "random"})
    if not p_values or not k_values:
        return False
    matrix = np.full((len(p_values), len(k_values)), np.nan)
    for key, summary in summaries.items():
        if key.topology != "random" or key.p_value is None:
            continue
        p_index = p_values.index(key.p_value)
        k_index = k_values.index(round(key.k_value, 1))
        matrix[p_index, k_index] = float(summary[value_name])
    if np.isnan(matrix).all():
        return False

    fig, axis = plt.subplots(figsize=(8, 6), constrained_layout=True)
    image = axis.imshow(matrix, origin="lower", aspect="auto", cmap="viridis")
    axis.set_title(title)
    axis.set_xlabel(LABEL_K)
    axis.set_ylabel(LABEL_P)
    axis.set_xticks(range(len(k_values)), [f"{value:.1f}" for value in k_values], rotation=45)
    axis.set_yticks(range(len(p_values)), [format_probability(value) for value in p_values])
    colorbar = fig.colorbar(image, ax=axis)
    colorbar.set_label(label_for_value(value_name))
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return True


def plot_ring_heatmap(
    path: Path,
    summaries: dict[GroupKey, dict[str, Any]],
    *,
    value_name: str,
    title: str,
) -> bool:
    ring_values = sorted({key.ring_k for key in summaries if key.topology == "ring" and key.ring_k is not None})
    k_values = sorted({round(key.k_value, 1) for key in summaries if key.topology == "ring"})
    if not ring_values or not k_values:
        return False
    matrix = np.full((len(ring_values), len(k_values)), np.nan)
    for key, summary in summaries.items():
        if key.topology != "ring" or key.ring_k is None:
            continue
        ring_index = ring_values.index(key.ring_k)
        k_index = k_values.index(round(key.k_value, 1))
        matrix[ring_index, k_index] = float(summary[value_name])
    if np.isnan(matrix).all():
        return False

    fig, axis = plt.subplots(figsize=(8, 6), constrained_layout=True)
    image = axis.imshow(matrix, origin="lower", aspect="auto", cmap="viridis")
    axis.set_title(title)
    axis.set_xlabel(LABEL_K)
    axis.set_ylabel(LABEL_RING_K)
    axis.set_xticks(range(len(k_values)), [f"{value:.1f}" for value in k_values], rotation=45)
    axis.set_yticks(range(len(ring_values)), [str(value) for value in ring_values])
    colorbar = fig.colorbar(image, ax=axis)
    colorbar.set_label(label_for_value(value_name))
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return True


def plot_random_k01_timeseries(
    path: Path,
    groups: dict[GroupKey, list[RunRecord]],
    *,
    field: str,
    ylabel: str,
    title: str,
    sync_threshold: float | None = None,
) -> bool:
    keys = sorted(
        [key for key in groups if key.topology == "random" and np.isclose(key.k_value, 0.1)],
        key=lambda key: -1.0 if key.p_value is None else key.p_value,
    )
    if not keys:
        return False
    fig, axis = plt.subplots(figsize=(10, 6), constrained_layout=True)
    colors = plt.cm.plasma(np.linspace(0.0, 1.0, len(keys)))
    for index, (color, key) in enumerate(zip(colors, keys)):
        curve = mean_curve(groups[key], field)
        if curve is None:
            continue
        t, values = curve
        axis.plot(t, values, label=f"p={format_probability(key.p_value)}", **style_for_series(index, color, len(t)))
    axis.set_title(title)
    axis.set_xlabel(r"$t$")
    axis.set_ylabel(ylabel)
    add_sync_threshold(axis, sync_threshold)
    axis.grid(True, alpha=0.25)
    axis.legend(ncols=2, fontsize=8)
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return True


def plot_ring_k01_timeseries(
    path: Path,
    groups: dict[GroupKey, list[RunRecord]],
    *,
    field: str,
    ylabel: str,
    title: str,
    sync_threshold: float | None = None,
) -> bool:
    keys = sorted(
        [key for key in groups if key.topology == "ring" and np.isclose(key.k_value, 0.1)],
        key=lambda key: -1 if key.ring_k is None else key.ring_k,
    )
    if not keys:
        return False
    fig, axis = plt.subplots(figsize=(10, 6), constrained_layout=True)
    colors = plt.cm.cividis(np.linspace(0.0, 1.0, len(keys)))
    for index, (color, key) in enumerate(zip(colors, keys)):
        curve = mean_curve(groups[key], field)
        if curve is None:
            continue
        t, values = curve
        axis.plot(t, values, label=f"k={key.ring_k}", **style_for_series(index, color, len(t)))
    axis.set_title(title)
    axis.set_xlabel(r"$t$")
    axis.set_ylabel(ylabel)
    add_sync_threshold(axis, sync_threshold)
    axis.grid(True, alpha=0.25)
    axis.legend(ncols=2, fontsize=8)
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return True


def plot_random_k01_stationary(path: Path, summaries: dict[GroupKey, dict[str, Any]]) -> bool:
    keys = sorted(
        [key for key in summaries if key.topology == "random" and np.isclose(key.k_value, 0.1)],
        key=lambda key: -1.0 if key.p_value is None else key.p_value,
    )
    if not keys:
        return False
    x = np.array([float(key.p_value) for key in keys if key.p_value is not None])
    y = np.array([float(summaries[key]["tail_sigma_mean"]) for key in keys if key.p_value is not None])
    yerr = np.array([float(summaries[key]["tail_sigma_run_std"]) for key in keys if key.p_value is not None])
    fig, axis = plt.subplots(figsize=(8, 5), constrained_layout=True)
    axis.errorbar(x, y, yerr=yerr, marker="o", linewidth=1.4, capsize=3)
    axis.set_title(r"Red aleatoria, $K=0.1$: $\sigma_v$ estacionaria vs $p$")
    axis.set_xlabel(LABEL_P)
    axis.set_ylabel(LABEL_SIGMA_V_STATIONARY)
    axis.set_xscale("log")
    axis.set_xticks(p_grid(), [format_probability(value) for value in p_grid()], rotation=45)
    axis.grid(True, alpha=0.25)
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return True


def plot_ring_k01_stationary(path: Path, summaries: dict[GroupKey, dict[str, Any]]) -> bool:
    keys = sorted(
        [key for key in summaries if key.topology == "ring" and np.isclose(key.k_value, 0.1)],
        key=lambda key: -1 if key.ring_k is None else key.ring_k,
    )
    if not keys:
        return False
    x = np.array([int(key.ring_k) for key in keys if key.ring_k is not None])
    y = np.array([float(summaries[key]["tail_sigma_mean"]) for key in keys if key.ring_k is not None])
    yerr = np.array([float(summaries[key]["tail_sigma_run_std"]) for key in keys if key.ring_k is not None])
    fig, axis = plt.subplots(figsize=(8, 5), constrained_layout=True)
    axis.errorbar(x, y, yerr=yerr, marker="o", linewidth=1.4, capsize=3)
    axis.set_title(r"Red anillo, $K=0.1$: $\sigma_v$ estacionaria vs $k$")
    axis.set_xlabel(LABEL_RING_K)
    axis.set_ylabel(LABEL_SIGMA_V_STATIONARY)
    axis.set_xticks(range(1, 11))
    axis.grid(True, alpha=0.25)
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return True


def plot_random_k01_observables(path: Path, summaries: dict[GroupKey, dict[str, Any]]) -> bool:
    keys = sorted(
        [
            key
            for key in summaries
            if key.topology == "random" and key.p_value is not None and np.isclose(key.k_value, 0.1)
        ],
        key=lambda key: float(key.p_value),
    )
    return plot_observables_vs_parameter(
        path,
        summaries,
        keys,
        x_values=np.array([float(key.p_value) for key in keys]),
        xlabel=LABEL_P,
        title=r"Red aleatoria, $K=0.1$: observables vs $p$",
        log_x=True,
    )


def plot_ring_k01_observables(path: Path, summaries: dict[GroupKey, dict[str, Any]]) -> bool:
    keys = sorted(
        [
            key
            for key in summaries
            if key.topology == "ring" and key.ring_k is not None and np.isclose(key.k_value, 0.1)
        ],
        key=lambda key: int(key.ring_k),
    )
    return plot_observables_vs_parameter(
        path,
        summaries,
        keys,
        x_values=np.array([int(key.ring_k) for key in keys]),
        xlabel=LABEL_RING_K,
        title=r"Red anillo, $K=0.1$: observables vs $k$",
        log_x=False,
    )


def plot_observables_vs_parameter(
    path: Path,
    summaries: dict[GroupKey, dict[str, Any]],
    keys: list[GroupKey],
    *,
    x_values: np.ndarray,
    xlabel: str,
    title: str,
    log_x: bool,
) -> bool:
    if not keys:
        return False

    mean_v = np.array([float(summaries[key]["tail_mean_v_mean"]) for key in keys])
    mean_v_std = np.array([float(summaries[key]["tail_mean_v_run_std"]) for key in keys])
    sigma_v = np.array([float(summaries[key]["tail_sigma_mean"]) for key in keys])
    sigma_v_std = np.array([float(summaries[key]["tail_sigma_run_std"]) for key in keys])

    fig, axes = plt.subplots(2, 1, figsize=(8, 8), sharex=True, constrained_layout=True)
    axes[0].errorbar(x_values, mean_v, yerr=mean_v_std, marker="o", linewidth=1.4, capsize=3)
    axes[0].set_ylabel(LABEL_TAIL_MEAN_V)
    axes[1].errorbar(x_values, sigma_v, yerr=sigma_v_std, marker="o", linewidth=1.4, capsize=3)
    axes[1].set_ylabel(LABEL_SIGMA_V_STATIONARY)
    axes[1].set_xlabel(xlabel)
    for axis in axes:
        axis.grid(True, alpha=0.25)
        if log_x:
            axis.set_xscale("log")
            axis.set_xticks(x_values, [format_probability(value) for value in x_values], rotation=45)
        else:
            axis.set_xticks(x_values)
    fig.suptitle(title + "\n(puntos: promedio de realizaciones; barras: desvio estandar)")
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return True


def plot_k_behavior(
    path: Path,
    groups: dict[GroupKey, list[RunRecord]],
    *,
    topology: str,
    representative_p: float | None,
    representative_ring_k: int | None,
    sync_threshold: float,
) -> bool:
    keys = sorted(
        [
            key
            for key in groups
            if key.topology == topology
            and is_temporal_k(key.k_value)
            and (
                topology != "random"
                or (key.p_value is not None and representative_p is not None and np.isclose(key.p_value, representative_p))
            )
            and (topology != "ring" or key.ring_k == representative_ring_k)
        ],
        key=lambda key: key.k_value,
    )
    if not keys:
        return False

    fig, axes = plt.subplots(2, 1, figsize=(10, 9), sharex=True, constrained_layout=True)
    colors = plt.cm.viridis(np.linspace(0.0, 1.0, len(keys)))
    plotted = False
    for index, (color, key) in enumerate(zip(colors, keys)):
        mean_v_curve = mean_curve(groups[key], "mean_v")
        sigma_curve = mean_curve(groups[key], "sigma_v")
        if mean_v_curve is None or sigma_curve is None:
            continue
        mean_t, mean_v = mean_v_curve
        sigma_t, sigma_v = sigma_curve
        axes[0].plot(mean_t, mean_v, label=f"K={key.k_value:.1f}", **style_for_series(index, color, len(mean_t)))
        axes[1].plot(sigma_t, sigma_v, label=f"K={key.k_value:.1f}", **style_for_series(index, color, len(sigma_t)))
        plotted = True
    if not plotted:
        plt.close(fig)
        return False

    if topology == "random":
        selection = rf"$p={representative_p:g}$"
        topology_label = "aleatoria"
    else:
        selection = rf"$k={representative_ring_k}$"
        topology_label = "anillo"
    axes[0].set_ylabel(LABEL_MEAN_V)
    axes[1].set_ylabel(LABEL_SIGMA_V)
    axes[1].set_xlabel(r"$t$")
    add_sync_threshold(axes[1], sync_threshold)
    for axis in axes:
        axis.grid(True, alpha=0.25)
        axis.legend(ncols=2, fontsize=8)
    fig.suptitle(rf"Red {topology_label}, {selection}: comportamiento para distintos $K$")
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return True


def plot_sync_time_comparison(
    path: Path,
    summaries: dict[GroupKey, dict[str, Any]],
    *,
    representative_p: float,
    representative_ring_k: int,
) -> bool:
    selections = [
        (
            "Completa",
            lambda key: key.topology == "complete",
            "#4c78a8",
        ),
        (
            f"Aleatoria p={representative_p:g}",
            lambda key: key.topology == "random"
            and key.p_value is not None
            and np.isclose(key.p_value, representative_p),
            "#f58518",
        ),
        (
            f"Anillo k={representative_ring_k}",
            lambda key: key.topology == "ring" and key.ring_k == representative_ring_k,
            "#54a24b",
        ),
    ]
    fig, axis = plt.subplots(figsize=(9, 5.5), constrained_layout=True)
    plotted = False
    for label, predicate, color in selections:
        keys = sorted([key for key in summaries if predicate(key)], key=lambda key: key.k_value)
        if not keys:
            continue
        x = np.array([key.k_value for key in keys])
        y = np.array([float(summaries[key]["sync_time_mean"]) for key in keys])
        yerr = np.array([float(summaries[key]["sync_time_std"]) for key in keys])
        axis.errorbar(x, y, yerr=yerr, label=label, color=color, marker="o", linewidth=1.4, capsize=3)
        plotted = True
    if not plotted:
        plt.close(fig)
        return False

    axis.set_title("Comparacion representativa del tiempo de sincronizacion")
    axis.set_xlabel(LABEL_K)
    axis.set_ylabel(LABEL_SYNC_TIME)
    axis.set_xticks(grid01())
    axis.grid(True, alpha=0.25)
    axis.legend()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return True


def label_for_value(value_name: str) -> str:
    labels = {
        "tail_sigma_mean": LABEL_SIGMA_V_STATIONARY,
        "sync_time_mean": LABEL_SYNC_TIME,
        "stable_sync_time_mean": LABEL_SYNC_TIME,
        "stationary_ok_fraction": r"fraccion estacionaria",
        "sync_fraction": r"fraccion sincronizada",
        "stable_sync_fraction": r"fraccion sincronizada estable",
    }
    return labels.get(value_name, value_name)


def plot_available_runs(path: Path, summaries: dict[GroupKey, dict[str, Any]]) -> bool:
    totals = {"complete": 0, "random": 0, "ring": 0}
    for key, summary in summaries.items():
        totals[key.topology] = totals.get(key.topology, 0) + int(summary["run_count"])
    fig, axis = plt.subplots(figsize=(7, 4), constrained_layout=True)
    labels = list(totals)
    values = [totals[label] for label in labels]
    axis.bar(labels, values, color=["#4c78a8", "#f58518", "#54a24b"])
    axis.set_title("Corridas disponibles por topologia")
    axis.set_ylabel("cantidad de corridas")
    axis.grid(True, axis="y", alpha=0.25)
    for index, value in enumerate(values):
        axis.text(index, value, str(value), ha="center", va="bottom")
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return True


def write_report(
    path: Path,
    *,
    args: argparse.Namespace,
    records: list[RunRecord],
    summaries: dict[GroupKey, dict[str, Any]],
    gaps: list[dict[str, Any]],
    figures: list[Path],
    complete_log_records: list[RunRecord],
) -> None:
    topology_runs: dict[str, int] = {"complete": 0, "random": 0, "ring": 0}
    topology_groups: dict[str, int] = {"complete": 0, "random": 0, "ring": 0}
    for key, summary in summaries.items():
        topology_runs[key.topology] = topology_runs.get(key.topology, 0) + int(summary["run_count"])
        topology_groups[key.topology] = topology_groups.get(key.topology, 0) + 1

    complete_keys = [key for key in summaries if key.topology == "complete"]
    complete_synced = sum(1 for key in complete_keys if summaries[key]["stable_sync_fraction"] >= 1.0)
    random_keys = [key for key in summaries if key.topology == "random"]
    random_synced = sum(1 for key in random_keys if summaries[key]["stable_sync_fraction"] >= 1.0)
    ring_keys = [key for key in summaries if key.topology == "ring"]
    ring_synced = sum(1 for key in ring_keys if summaries[key]["stable_sync_fraction"] >= 1.0)
    stationary_groups = sum(1 for summary in summaries.values() if summary["stationary_ok_fraction"] >= 0.8)
    ring_assessment = (
        "- Para red anillo, los outputs cubren observables vs k para K=0.1, comportamiento temporal para distintos K y mapas 2D de dispersion/tiempo."
        if ring_keys
        else "- No hay outputs de red anillo en este directorio, asi que todavia no se puede cumplir esa parte ni la comparacion final entre topologias."
    )

    lines = [
        "# TP5 Sistema 2 - Analisis preliminar de outputs",
        "",
        f"- Generado: {datetime.now().isoformat(timespec='seconds')}",
        f"- Input: `{args.input_dir}`",
        f"- Input adicional red completa K logaritmico: `{args.complete_log_input_dir}` ({len(complete_log_records)} corridas)."
        if args.complete_log_input_dir is not None
        else "- Input adicional red completa K logaritmico: no provisto.",
        f"- Criterio de sincronizacion: primera muestra desde la cual `sigma_v(t) <= {args.sync_threshold:g}` hasta el final.",
        f"- Criterio de estacionario: cambio entre mitades de la cola final <= max({args.stationary_abs_tol:g}, {args.stationary_rel_tol:g} * sigma_tail).",
        f"- Cola usada para estacionario: ultimo {args.tail_fraction:.0%} de cada corrida.",
        f"- Comparacion representativa entre topologias: completa, aleatoria con `p={args.representative_p:g}` y anillo con `k={args.representative_ring_k}`.",
        "- Todas las figuras se construyen exclusivamente desde `metadata.properties` y `observables.csv`; no se completan ni interpolan datos faltantes.",
        "",
        "## Cobertura disponible",
        "",
        "| topologia | corridas | grupos de parametros |",
        "| --- | ---: | ---: |",
    ]
    for topology in ["complete", "random", "ring"]:
        lines.append(f"| {topology} | {topology_runs.get(topology, 0)} | {topology_groups.get(topology, 0)} |")

    lines.extend(
        [
            "",
            "## Lectura rapida",
            "",
            f"- Red completa: {complete_synced}/{len(complete_keys)} grupos tienen 100% de corridas con sincronizacion estable.",
            f"- Red aleatoria: {random_synced}/{len(random_keys)} grupos disponibles tienen 100% de corridas con sincronizacion estable.",
            f"- Red anillo: {ring_synced}/{len(ring_keys)} grupos disponibles tienen 100% de corridas con sincronizacion estable.",
            f"- Estacionario de `sigma_v`: {stationary_groups}/{len(summaries)} grupos disponibles pasan el criterio operativo.",
            f"- Gaps contra la grilla completa del enunciado: {len(gaps)} filas en `coverage_gaps.csv`.",
            "",
            "## Aceptabilidad preliminar",
            "",
            "- Para red completa, los outputs cubren evolucion temporal, `sigma_v` estacionaria vs K y tiempo de sincronizacion vs K.",
            "- El zoom logaritmico de red completa usa `K=0` solo como referencia; el eje logaritmico contiene exclusivamente `K>0`.",
            "- Para red aleatoria, los outputs cubren observables vs p para K=0.1, comportamiento temporal para distintos K y mapas 2D de dispersion/tiempo.",
            ring_assessment,
            "- `sigma_v` estacionaria puede estar bien definida aunque `<v(t)>` siga oscilando; conviene describirlo como regimen estacionario/oscilatorio, no necesariamente punto fijo.",
            f"- El umbral `sigma_v <= {args.sync_threshold:g}` es una convencion operativa para revisar con el profesor, no una verdad fisica definitiva.",
            "- Las animaciones obligatorias requieren corridas seleccionadas con `states.csv`; el barrido estadistico de observables no contiene estados por neurona.",
            "",
            "## Figuras generadas",
            "",
        ]
    )
    for figure in figures:
        lines.append(f"- `{figure}`")
    lines.extend(
        [
            "",
            "## Archivos tabulares",
            "",
            "- `run_metrics.csv`: una fila por corrida.",
            "- `summary_by_group.csv`: promedios por topologia y parametros.",
            "- `coverage_gaps.csv`: parametros faltantes o incompletos contra la grilla esperada.",
            "- `complete_log_run_metrics.csv` y `complete_log_summary_by_group.csv`: resultados del zoom logaritmico, cuando se provee ese input.",
            "",
            "## Preguntas sugeridas para el profesor",
            "",
            f"1. Para sincronizacion, estamos usando `sigma_v <= {args.sync_threshold:g}` sostenido hasta el final. Es un umbral razonable o prefiere otro criterio?",
            "2. Para llegada al estacionario, alcanza con estabilizacion de `sigma_v` aunque `<v(t)>` quede en oscilacion colectiva?",
            f"3. Para la comparacion final entre topologias, es adecuado comparar completa, aleatoria con `p={args.representative_p:g}` y anillo con `k={args.representative_ring_k}`?",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def record_sort_key(record: RunRecord) -> tuple[Any, ...]:
    return group_sort_key(record.group_key) + (record.metadata.realization,)


def group_sort_key(key: GroupKey) -> tuple[Any, ...]:
    order = {"complete": 0, "random": 1, "ring": 2}.get(key.topology, 99)
    return (
        order,
        -1.0 if key.p_value is None else key.p_value,
        -1 if key.ring_k is None else key.ring_k,
        key.k_value,
    )


def fmt(value: Any) -> Any:
    if isinstance(value, (int, str)):
        return value
    if value is None:
        return ""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return value
    if np.isnan(number):
        return ""
    return f"{number:.8g}"


if __name__ == "__main__":
    raise SystemExit(main())
