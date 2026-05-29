from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np

from scripts.animation.io import read_metadata, read_observables
from scripts.animation.model import Metadata, Observables


@dataclass(frozen=True)
class GroupKey:
    topology: str
    k_value: float
    p_value: float | None
    ring_k: int | None

    def label(self) -> str:
        if self.topology == "complete":
            return f"complete K={self.k_value:.2f}"
        if self.topology == "random":
            return f"random p={self.p_value:.2f} K={self.k_value:.2f}"
        if self.topology == "ring":
            return f"ring k={self.ring_k:02d} K={self.k_value:.2f}"
        return f"{self.topology} K={self.k_value:.2f}"


@dataclass(frozen=True)
class RunMetrics:
    sync_time: float | None
    tail_sigma_mean: float
    tail_sigma_std: float
    tail_mean_v_mean: float
    tail_mean_v_std: float
    stationary_delta: float
    stationary_ok: bool
    final_time: float
    row_count: int


@dataclass(frozen=True)
class RunRecord:
    run_dir: Path
    metadata: Metadata
    observables: Observables
    metrics: RunMetrics

    @property
    def group_key(self) -> GroupKey:
        return GroupKey(
            topology=self.metadata.topology,
            k_value=self.metadata.k_value,
            p_value=self.metadata.p_value,
            ring_k=self.metadata.ring_k,
        )


def first_time_stays_below(t: np.ndarray, values: np.ndarray, threshold: float) -> float | None:
    if t.shape != values.shape:
        raise ValueError("time and value arrays must have the same shape")
    if len(t) == 0:
        return None

    suffix_max = np.maximum.accumulate(values[::-1])[::-1]
    indices = np.flatnonzero(suffix_max <= threshold)
    if len(indices) == 0:
        return None
    return float(t[int(indices[0])])


def summarize_series(
    t: np.ndarray,
    mean_v: np.ndarray,
    sigma_v: np.ndarray,
    *,
    sync_threshold: float,
    tail_fraction: float,
    stationary_abs_tol: float,
    stationary_rel_tol: float,
) -> RunMetrics:
    if not (len(t) == len(mean_v) == len(sigma_v)):
        raise ValueError("time, mean_v, and sigma_v arrays must have the same length")
    if len(t) < 2:
        raise ValueError("at least two samples are required")
    if not 0.0 < tail_fraction <= 1.0:
        raise ValueError("tail_fraction must be in (0, 1]")

    tail_count = max(2, int(np.ceil(len(t) * tail_fraction)))
    tail_count = min(tail_count, len(t))
    tail_sigma = sigma_v[-tail_count:]
    tail_mean_v = mean_v[-tail_count:]

    split = max(1, tail_count // 2)
    first_half = tail_sigma[:split]
    second_half = tail_sigma[split:]
    if len(second_half) == 0:
        second_half = first_half

    first_mean = float(np.mean(first_half))
    second_mean = float(np.mean(second_half))
    stationary_delta = abs(second_mean - first_mean)
    tail_sigma_mean = float(np.mean(tail_sigma))
    tolerance = max(stationary_abs_tol, stationary_rel_tol * max(abs(tail_sigma_mean), 1e-12))

    return RunMetrics(
        sync_time=first_time_stays_below(t, sigma_v, sync_threshold),
        tail_sigma_mean=tail_sigma_mean,
        tail_sigma_std=float(np.std(tail_sigma)),
        tail_mean_v_mean=float(np.mean(tail_mean_v)),
        tail_mean_v_std=float(np.std(tail_mean_v)),
        stationary_delta=stationary_delta,
        stationary_ok=stationary_delta <= tolerance,
        final_time=float(t[-1]),
        row_count=int(len(t)),
    )


def load_records(
    input_dir: Path,
    *,
    sync_threshold: float,
    tail_fraction: float,
    stationary_abs_tol: float,
    stationary_rel_tol: float,
) -> list[RunRecord]:
    runs_root = input_dir / "runs" if (input_dir / "runs").exists() else input_dir
    records: list[RunRecord] = []

    for metadata_path in sorted(runs_root.rglob("metadata.properties")):
        run_dir = metadata_path.parent
        if not (run_dir / "observables.csv").exists():
            continue
        metadata = read_metadata(run_dir)
        observables = read_observables(run_dir)
        metrics = summarize_series(
            observables.t,
            observables.mean_v,
            observables.sigma_v,
            sync_threshold=sync_threshold,
            tail_fraction=tail_fraction,
            stationary_abs_tol=stationary_abs_tol,
            stationary_rel_tol=stationary_rel_tol,
        )
        records.append(
            RunRecord(
                run_dir=run_dir,
                metadata=metadata,
                observables=observables,
                metrics=metrics,
            )
        )

    return records


def group_records(records: Iterable[RunRecord]) -> dict[GroupKey, list[RunRecord]]:
    groups: dict[GroupKey, list[RunRecord]] = {}
    for record in records:
        groups.setdefault(record.group_key, []).append(record)
    return groups


def coverage_gaps(
    groups: dict[GroupKey, list[object]],
    *,
    expected_realizations: int,
) -> list[dict[str, float | int | str]]:
    gaps: list[dict[str, float | int | str]] = []
    for key in expected_group_keys():
        present = len(groups.get(key, []))
        if present >= expected_realizations:
            continue
        gaps.append(
            {
                "topology": key.topology,
                "K": key.k_value,
                "p": "" if key.p_value is None else key.p_value,
                "k": "" if key.ring_k is None else key.ring_k,
                "present_runs": present,
                "expected_runs": expected_realizations,
                "missing_runs": max(0, expected_realizations - present),
                "status": "missing" if present == 0 else "partial",
            }
        )
    return gaps


def expected_group_keys() -> list[GroupKey]:
    keys: list[GroupKey] = []
    for k_value in grid01():
        keys.append(GroupKey("complete", k_value, None, None))
    for p_value in grid01():
        for k_value in grid01():
            keys.append(GroupKey("random", k_value, p_value, None))
    for ring_k in range(1, 11):
        for k_value in grid01():
            keys.append(GroupKey("ring", k_value, None, ring_k))
    return keys


def grid01() -> list[float]:
    return [round(i / 10.0, 1) for i in range(11)]


def aggregate_metrics(metrics: list[RunMetrics]) -> dict[str, float | int]:
    if not metrics:
        return {
            "run_count": 0,
            "sync_fraction": 0.0,
            "sync_time_mean": float("nan"),
            "sync_time_std": float("nan"),
            "stable_sync_fraction": 0.0,
            "stable_sync_time_mean": float("nan"),
            "stable_sync_time_std": float("nan"),
            "stationary_ok_fraction": 0.0,
            "tail_sigma_mean": float("nan"),
            "tail_sigma_run_std": float("nan"),
            "tail_sigma_temporal_std_mean": float("nan"),
            "tail_mean_v_mean": float("nan"),
            "tail_mean_v_run_std": float("nan"),
            "stationary_delta_mean": float("nan"),
            "final_time_min": float("nan"),
            "row_count_min": 0,
        }

    sync_times = np.array([m.sync_time for m in metrics if m.sync_time is not None], dtype=float)
    stable_sync_times = np.array(
        [m.sync_time for m in metrics if m.sync_time is not None and m.stationary_ok],
        dtype=float,
    )
    tail_sigma = np.array([m.tail_sigma_mean for m in metrics], dtype=float)
    tail_mean_v = np.array([m.tail_mean_v_mean for m in metrics], dtype=float)

    return {
        "run_count": len(metrics),
        "sync_fraction": float(len(sync_times) / len(metrics)),
        "sync_time_mean": float(np.mean(sync_times)) if len(sync_times) else float("nan"),
        "sync_time_std": float(np.std(sync_times)) if len(sync_times) else float("nan"),
        "stable_sync_fraction": float(len(stable_sync_times) / len(metrics)),
        "stable_sync_time_mean": float(np.mean(stable_sync_times)) if len(stable_sync_times) else float("nan"),
        "stable_sync_time_std": float(np.std(stable_sync_times)) if len(stable_sync_times) else float("nan"),
        "stationary_ok_fraction": float(np.mean([m.stationary_ok for m in metrics])),
        "tail_sigma_mean": float(np.mean(tail_sigma)),
        "tail_sigma_run_std": float(np.std(tail_sigma)),
        "tail_sigma_temporal_std_mean": float(np.mean([m.tail_sigma_std for m in metrics])),
        "tail_mean_v_mean": float(np.mean(tail_mean_v)),
        "tail_mean_v_run_std": float(np.std(tail_mean_v)),
        "stationary_delta_mean": float(np.mean([m.stationary_delta for m in metrics])),
        "final_time_min": float(min(m.final_time for m in metrics)),
        "row_count_min": int(min(m.row_count for m in metrics)),
    }


def mean_curve(records: list[RunRecord], field: str) -> tuple[np.ndarray, np.ndarray] | None:
    if not records:
        return None
    times = records[0].observables.t
    values = []
    for record in records:
        if record.observables.t.shape != times.shape or not np.allclose(record.observables.t, times):
            return None
        series = getattr(record.observables, field)
        values.append(series)
    return times, np.mean(np.vstack(values), axis=0)
