from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from .model import AnimationInputError, Metadata, Observables


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
