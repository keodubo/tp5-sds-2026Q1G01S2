from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from .model import AnimationInputError, Metadata, Observables, States


OBSERVABLES_HEADER = ["t", "mean_v", "sigma_v", "mean_w"]
STATES_HEADER = ["t", "i", "v", "w"]
ADJACENCY_HEADER = ["i", "j", "Aij"]


def read_metadata(run_dir: Path) -> Metadata:
    path = run_dir / "metadata.properties"
    if not path.exists():
        raise AnimationInputError(f"metadata.properties not found in {run_dir}")

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise AnimationInputError(f"invalid metadata line in {path}: {raw_line}")
        key, value = line.split("=", 1)
        values[key] = value

    try:
        return Metadata(
            mode=values["mode"],
            topology=values["topology"],
            n=int(values["N"]),
            k_value=float(values["K"]),
            p_value=_optional_float(values.get("p", "")),
            ring_k=_optional_int(values.get("k", "")),
            dt=float(values["dt"]),
            total_time=float(values["T"]),
            save_interval=float(values["saveInterval"]),
            realization=int(values["realization"]),
            base_seed=int(values["baseSeed"]),
            run_seed=int(values["runSeed"]),
            save_states=_bool_value(values["saveStates"]),
            save_adjacency=_bool_value(values["saveAdjacency"]),
            topology_type=values.get("topologyType", values["topology"].upper()),
            source_dir=run_dir,
        )
    except KeyError as exc:
        raise AnimationInputError(f"metadata.properties missing key: {exc.args[0]}") from exc
    except ValueError as exc:
        raise AnimationInputError(f"metadata.properties contains invalid value: {exc}") from exc


def read_observables(run_dir: Path) -> Observables:
    path = run_dir / "observables.csv"
    rows = _read_csv_rows(path, OBSERVABLES_HEADER)
    if not rows:
        raise AnimationInputError(f"observables.csv has no data rows in {run_dir}")

    data = np.array(
        [
            [_read_float(row, name, path, row_number) for name in OBSERVABLES_HEADER]
            for row_number, row in enumerate(rows, start=2)
        ],
        dtype=float,
    )

    return Observables(
        t=data[:, 0],
        mean_v=data[:, 1],
        sigma_v=data[:, 2],
        mean_w=data[:, 3],
    )


def read_states(run_dir: Path, n: int) -> States:
    path = run_dir / "states.csv"
    rows = _read_csv_rows(path, STATES_HEADER)
    if not rows:
        raise AnimationInputError(f"states.csv has no data rows in {run_dir}")

    frames: dict[float, dict[int, tuple[float, float]]] = {}
    for row_number, row in enumerate(rows, start=2):
        t = _read_float(row, "t", path, row_number)
        i = _read_int(row, "i", path, row_number)
        v_value = _read_float(row, "v", path, row_number)
        w_value = _read_float(row, "w", path, row_number)
        if i < 0 or i >= n:
            raise AnimationInputError(f"states.csv index out of range: {i}; expected 0..{n - 1}")
        frame = frames.setdefault(t, {})
        if i in frame:
            raise AnimationInputError(f"duplicate state row at row {row_number}: t={t}, i={i}")
        frame[i] = (v_value, w_value)

    times = sorted(frames)
    if len(times) < 2:
        raise AnimationInputError("states.csv must contain at least two state frames to produce MP4")

    v = np.zeros((len(times), n), dtype=float)
    w = np.zeros((len(times), n), dtype=float)
    for frame_index, t in enumerate(times):
        frame = frames[t]
        if len(frame) != n:
            raise AnimationInputError(
                f"incomplete state frame at t={t}: got {len(frame)} rows, expected {n}"
            )
        for i in range(n):
            if i not in frame:
                raise AnimationInputError(f"incomplete state frame at t={t}: missing i={i}")
            v[frame_index, i], w[frame_index, i] = frame[i]

    return States(t=np.array(times, dtype=float), v=v, w=w)


def _optional_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _optional_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def _bool_value(value: str) -> bool:
    if value == "true":
        return True
    if value == "false":
        return False
    raise ValueError(f"invalid boolean {value!r}")


def _read_float(row: dict[str, str], name: str, path: Path, row_number: int) -> float:
    value = row[name]
    if value is None or value == "":
        raise AnimationInputError(
            f"{path.name} contains invalid value at row {row_number}, column {name}: missing value"
        )
    try:
        return float(value)
    except ValueError as exc:
        raise AnimationInputError(
            f"{path.name} contains invalid value at row {row_number}, column {name}: {value!r}"
        ) from exc


def _read_int(row: dict[str, str], name: str, path: Path, row_number: int) -> int:
    value = row[name]
    if value is None or value == "":
        raise AnimationInputError(
            f"{path.name} contains invalid value at row {row_number}, column {name}: missing value"
        )
    try:
        return int(value)
    except ValueError as exc:
        raise AnimationInputError(
            f"{path.name} contains invalid value at row {row_number}, column {name}: {value!r}"
        ) from exc


def _read_csv_rows(path: Path, expected_header: list[str]) -> list[dict[str, str]]:
    if not path.exists():
        raise AnimationInputError(f"{path.name} not found in {path.parent}")
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != expected_header:
            raise AnimationInputError(
                f"{path.name} header must be {','.join(expected_header)}; got {reader.fieldnames}"
            )
        rows = []
        for row_number, row in enumerate(reader, start=2):
            if None in row:
                extra_values = row[None]
                raise AnimationInputError(
                    f"{path.name} contains invalid row {row_number}: extra values {extra_values}"
                )
            rows.append(row)
        return rows


from .model import RunData


def load_run(run_dir: Path, require_graph: bool) -> RunData:
    from .graph import build_graph_from_adjacency

    metadata = read_metadata(run_dir)
    observables = read_observables(run_dir)
    states = read_states(run_dir, metadata.n)
    graph_data = None
    if require_graph:
        graph_data = build_graph_from_adjacency(run_dir, metadata.n)
    elif (run_dir / "adjacency.csv").exists():
        graph_data = build_graph_from_adjacency(run_dir, metadata.n)
    return RunData(
        metadata=metadata,
        observables=observables,
        states=states,
        graph_data=graph_data,
    )
