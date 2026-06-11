#!/usr/bin/env python3
"""Generate the initial-condition contrast figure for TP5 conclusion 3.

The figure compares complete-network, K=0 FitzHugh-Nagumo runs with two
initial-condition ranges. It only uses observables.csv files and can generate
the missing runs before plotting.
"""
from __future__ import annotations

import argparse
import csv
import math
import subprocess
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

from scripts.analysis.fhn import first_time_stays_below


@dataclass(frozen=True)
class Condition:
    name: str
    output_dir: Path
    initial_min: float
    initial_max: float
    label: str
    color: str


@dataclass(frozen=True)
class ConditionStats:
    t: np.ndarray
    mean_sigma: np.ndarray
    std_sigma: np.ndarray
    sigma0_mean: float
    tail_sigma_mean: float
    tail_sigma_std: float
    sync_count: int
    run_count: int


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the CI contrast figure for conclusion 3.")
    parser.add_argument("--output-dir", type=Path, default=Path("results/2026-06-11_ci-conclusion3_v1"))
    parser.add_argument("--threads", type=int, default=5)
    parser.add_argument("--skip-simulations", action="store_true")
    parser.add_argument("--N", type=int, default=501)
    parser.add_argument("--T", type=float, default=500.0)
    parser.add_argument("--dt", type=float, default=0.005)
    parser.add_argument("--save-interval", type=float, default=0.1)
    parser.add_argument("--realizations", type=int, default=15)
    parser.add_argument("--base-seed", type=int, default=20260607)
    parser.add_argument("--sync-threshold", type=float, default=0.01)
    parser.add_argument("--tail-fraction", type=float, default=0.2)
    parser.add_argument(
        "--narrow-dir",
        type=Path,
        default=Path("outputs/fhn-sweep-T500-dt005-observables"),
    )
    parser.add_argument(
        "--wide-dir",
        type=Path,
        default=Path("outputs/fhn-sweep-T500-dt005-init05-observables"),
    )
    return parser


def run_command(command: list[str]) -> None:
    print("$ " + " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT_DIR, check=True)


def generate_condition(condition: Condition, args: argparse.Namespace) -> None:
    run_command(["mvn", "-q", "-DskipTests", "compile"])
    run_command(
        [
            "java",
            "-cp",
            "target/classes",
            "ar.edu.itba.sds.tp5.Main",
            "sweep",
            "--topology",
            "complete",
            "--k-values",
            "0",
            "--N",
            str(args.N),
            "--T",
            str(args.T),
            "--dt",
            str(args.dt),
            "--save-interval",
            str(args.save_interval),
            "--realizations",
            str(args.realizations),
            "--threads",
            str(args.threads),
            "--base-seed",
            str(args.base_seed),
            "--initial-state-min",
            str(condition.initial_min),
            "--initial-state-max",
            str(condition.initial_max),
            "--output-dir",
            str(condition.output_dir),
        ]
    )


def observables_paths(condition: Condition, realizations: int) -> list[Path]:
    root = ROOT_DIR / condition.output_dir / "runs" / "complete" / "K_0.00"
    return [root / f"seed_{idx:04d}" / "observables.csv" for idx in range(1, realizations + 1)]


def missing_paths(condition: Condition, realizations: int) -> list[Path]:
    return [path for path in observables_paths(condition, realizations) if not path.exists()]


def read_observables(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    data = np.genfromtxt(path, delimiter=",", names=True)
    return (
        np.asarray(data["t"], dtype=float),
        np.asarray(data["mean_v"], dtype=float),
        np.asarray(data["sigma_v"], dtype=float),
    )


def load_condition(condition: Condition, args: argparse.Namespace) -> ConditionStats:
    paths = observables_paths(condition, args.realizations)
    missing = [path for path in paths if not path.exists()]
    if missing:
        missing_list = "\n".join(str(path.relative_to(ROOT_DIR)) for path in missing)
        raise SystemExit(f"ERROR: missing observables for {condition.name}:\n{missing_list}")

    times: list[np.ndarray] = []
    mean_vs: list[np.ndarray] = []
    sigma_vs: list[np.ndarray] = []
    for path in paths:
        t, mean_v, sigma_v = read_observables(path)
        times.append(t)
        mean_vs.append(mean_v)
        sigma_vs.append(sigma_v)

    reference_t = times[0]
    for path, t in zip(paths, times, strict=True):
        if len(t) != len(reference_t) or not np.allclose(t, reference_t, rtol=0.0, atol=1e-12):
            raise SystemExit(f"ERROR: time grid mismatch in {path.relative_to(ROOT_DIR)}")

    sigma = np.vstack(sigma_vs)
    tail_count = max(2, int(math.ceil(sigma.shape[1] * args.tail_fraction)))
    tail_count = min(tail_count, sigma.shape[1])
    tail_by_run = np.mean(sigma[:, -tail_count:], axis=1)
    sync_count = sum(
        first_time_stays_below(reference_t, run_sigma, args.sync_threshold) is not None
        for run_sigma in sigma
    )

    return ConditionStats(
        t=reference_t,
        mean_sigma=np.mean(sigma, axis=0),
        std_sigma=np.std(sigma, axis=0),
        sigma0_mean=float(np.mean(sigma[:, 0])),
        tail_sigma_mean=float(np.mean(tail_by_run)),
        tail_sigma_std=float(np.std(tail_by_run)),
        sync_count=int(sync_count),
        run_count=int(sigma.shape[0]),
    )


def plot(stats_by_condition: dict[Condition, ConditionStats], args: argparse.Namespace) -> Path:
    args.output_dir.mkdir(parents=True, exist_ok=True)
    out = args.output_dir / "slide_ci_sigma_vs_t.png"

    plt.rcParams.update(
        {
            "font.size": 20,
            "axes.labelsize": 22,
            "xtick.labelsize": 20,
            "ytick.labelsize": 20,
            "legend.fontsize": 20,
        }
    )

    fig, ax = plt.subplots(figsize=(10.8, 6.0))
    for condition, stats in stats_by_condition.items():
        lower = np.maximum(stats.mean_sigma - stats.std_sigma, 0.0)
        upper = stats.mean_sigma + stats.std_sigma
        ax.plot(stats.t, stats.mean_sigma, lw=2.4, color=condition.color, label=condition.label)
        ax.fill_between(stats.t, lower, upper, color=condition.color, alpha=0.18, linewidth=0)

    ax.axhline(
        args.sync_threshold,
        color="#4d4d4d",
        linestyle=":",
        linewidth=2.0,
    )
    ax.text(
        322,
        args.sync_threshold * 3.0,
        r"umbral  $\sigma_v = 10^{-2}$",
        color="#4d4d4d",
        fontsize=20,
        ha="left",
        va="bottom",
    )
    ax.set_xlabel(r"tiempo  $t$")
    ax.set_ylabel(r"dispersión espacial  $\sigma_v$")
    ax.grid(alpha=0.25)
    ax.set_xlim(left=0.0)
    ax.set_ylim(bottom=0.0)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.18), ncol=2, frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    fig.savefig(out, dpi=180, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    return out


def write_metrics(stats_by_condition: dict[Condition, ConditionStats], args: argparse.Namespace) -> Path:
    out = args.output_dir / "ci_conclusion3_metrics.csv"
    with out.open("w", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(
            [
                "condition",
                "initial_min",
                "initial_max",
                "run_count",
                "sigma_v_0_mean",
                "tail_sigma_v_mean",
                "tail_sigma_v_run_std",
                "sync_count",
                "sync_threshold",
            ]
        )
        for condition, stats in stats_by_condition.items():
            writer.writerow(
                [
                    condition.name,
                    condition.initial_min,
                    condition.initial_max,
                    stats.run_count,
                    f"{stats.sigma0_mean:.12g}",
                    f"{stats.tail_sigma_mean:.12g}",
                    f"{stats.tail_sigma_std:.12g}",
                    stats.sync_count,
                    args.sync_threshold,
                ]
            )
    return out


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    conditions = [
        Condition(
            name="angosta",
            output_dir=args.narrow_dir,
            initial_min=-0.05,
            initial_max=0.05,
            label=r"$v_0,w_0\in[-5{\times}10^{-2},5{\times}10^{-2}]$",
            color="#1f77b4",
        ),
        Condition(
            name="ancha",
            output_dir=args.wide_dir,
            initial_min=-0.5,
            initial_max=0.5,
            label=r"$v_0,w_0\in[-5{\times}10^{-1},5{\times}10^{-1}]$",
            color="#ff7f0e",
        ),
    ]

    if not args.skip_simulations:
        for condition in conditions:
            if missing_paths(condition, args.realizations):
                generate_condition(condition, args)

    stats_by_condition = {condition: load_condition(condition, args) for condition in conditions}
    figure = plot(stats_by_condition, args)
    metrics = write_metrics(stats_by_condition, args)

    print(f"figure: {figure}")
    print(f"metrics: {metrics}")
    for condition, stats in stats_by_condition.items():
        print(
            f"{condition.name}: sigma_v(0)={stats.sigma0_mean:.6g}, "
            f"tail_sigma_v={stats.tail_sigma_mean:.6g}, "
            f"sync={stats.sync_count}/{stats.run_count}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
