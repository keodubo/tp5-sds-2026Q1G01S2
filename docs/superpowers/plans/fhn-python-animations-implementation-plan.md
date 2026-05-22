# FHN Python Animations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI that consumes existing FitzHugh-Nagumo motor output folders and generates NetworkX + Matplotlib MP4/PNG animations for the network and dashboard views.

**Architecture:** The implementation is a small Python package under `scripts/animation/` plus a thin CLI wrapper at `scripts/animate_fhn.py`. Parsing, validation, graph construction, output naming, and rendering are separate modules so tests can assert public behavior without inspecting internals. The Java motor remains untouched.

**Tech Stack:** Python 3.11+, standard `csv`/`argparse`/`pathlib`, `numpy`, `networkx`, `matplotlib`, `scipy`, `pytest`, Java/Maven motor only for smoke fixture generation.

---

## Source References

- Repo rules: `AGENTS.md`
- Approved spec: `docs/superpowers/specs/fhn-python-animations-design.md`
- Existing motor spec: `docs/superpowers/specs/fhn-motor-design.md`
- Existing motor CLI: `src/main/java/ar/edu/itba/sds/tp5/Main.java`
- Existing output writer: `src/main/java/ar/edu/itba/sds/tp5/OutputWriter.java`

## File Map

Create:

- `requirements.txt`: runtime + test dependencies for the animation module.
- `scripts/animate_fhn.py`: executable CLI entrypoint.
- `scripts/animation/__init__.py`: package marker.
- `scripts/animation/model.py`: public dataclasses/enums for loaded run data and CLI options.
- `scripts/animation/io.py`: parse `metadata.properties`, `observables.csv`, `states.csv`, and `adjacency.csv`.
- `scripts/animation/graph.py`: build NetworkX graph and deterministic layouts.
- `scripts/animation/render.py`: render network/dashboard MP4 and PNG artifacts.
- `scripts/animation/cli.py`: argument parsing, orchestration, skip/overwrite behavior, user-facing errors.
- `tests/python/test_animation_io.py`: parser and validation behavior.
- `tests/python/test_animation_graph.py`: graph construction and layout behavior.
- `tests/python/test_animation_cli.py`: CLI behavior and output contract on tiny fixtures.

Modify:

- `.gitignore`: ignore Python caches, virtualenvs, and `renders/`.

## Execution Notes

- Do not edit `docs/`, except this plan if corrections are needed.
- Do not modify Java motor behavior.
- Keep tests unit-level, blackbox, and behavior-only.
- Use temporary directories for generated test artifacts.
- Use tiny synthetic fixtures for most tests; use Java motor only for final smoke.
- Commit after each task.

## Commands

Install dependencies in a local venv:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Run Python tests:

```bash
python -m pytest tests/python -q
```

Run Java tests:

```bash
mvn -q test
```

Run final smoke:

```bash
mvn -q -DskipTests exec:java \
  -Dexec.args="single --topology ring --N 501 --K 0.2 --k 2 --dt 0.02 --T 0.2 --save-interval 0.02 --output-dir /tmp/tp5-fhn-animation-smoke --save-states --save-adjacency --overwrite"

python scripts/animate_fhn.py \
  --run-dir /tmp/tp5-fhn-animation-smoke/runs/ring/k_02/K_0.20/seed_0001 \
  --output-dir /tmp/tp5-fhn-animation-renders \
  --fps 12 \
  --dpi 100 \
  --overwrite
```

Expected final smoke outputs:

```text
/tmp/tp5-fhn-animation-renders/ring_k_02_K_0.20_seed_0001/network.mp4
/tmp/tp5-fhn-animation-renders/ring_k_02_K_0.20_seed_0001/network_frame.png
/tmp/tp5-fhn-animation-renders/ring_k_02_K_0.20_seed_0001/dashboard.mp4
/tmp/tp5-fhn-animation-renders/ring_k_02_K_0.20_seed_0001/dashboard_frame.png
```

---

### Task 1: Python Scaffold and Git Hygiene

**Files:**

- Modify: `.gitignore`
- Create: `requirements.txt`
- Create: `scripts/animation/__init__.py`
- Create: `scripts/animate_fhn.py`
- Create: `scripts/animation/cli.py`

- [ ] **Step 1: Extend `.gitignore`**

Add these entries if they are missing:

```gitignore
renders/
.venv/
__pycache__/
.pytest_cache/
*.pyc
```

- [ ] **Step 2: Create `requirements.txt`**

```text
matplotlib>=3.8,<4
networkx>=3.2,<4
numpy>=1.26,<3
pytest>=8,<9
scipy>=1.11,<2
```

- [ ] **Step 3: Create the package marker**

Create `scripts/animation/__init__.py`:

```python
"""Animation helpers for TP5 FitzHugh-Nagumo outputs."""
```

- [ ] **Step 4: Create a failing CLI smoke test**

Create `tests/python/test_animation_cli.py`:

```python
import subprocess
import sys


def test_cli_requires_run_dir():
    result = subprocess.run(
        [sys.executable, "scripts/animate_fhn.py"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "--run-dir" in result.stderr
```

- [ ] **Step 5: Run the failing test**

Run:

```bash
python -m pytest tests/python/test_animation_cli.py::test_cli_requires_run_dir -q
```

Expected before implementation:

```text
FAILED
```

The failure can be `No such file or directory` or argparse missing, depending on which files already exist.

- [ ] **Step 6: Add the minimal CLI wrapper**

Create `scripts/animate_fhn.py`:

```python
#!/usr/bin/env python3
from animation.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
```

Create `scripts/animation/cli.py`:

```python
from __future__ import annotations

import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="animate_fhn.py",
        description="Generate FitzHugh-Nagumo animations from motor output files.",
    )
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("renders"))
    parser.add_argument("--only", choices=("network", "dashboard", "all"), default="all")
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--dpi", type=int, default=140)
    parser.add_argument("--frame-stride", type=int, default=1)
    parser.add_argument("--representative-time", type=float)
    parser.add_argument("--directed-edges", action="store_true")
    parser.add_argument("--layout", choices=("circular", "spring"), default="circular")
    parser.add_argument("--edge-alpha", type=float)
    parser.add_argument("--edge-width", type=float, default=0.25)
    parser.add_argument("--node-size", type=float, default=18.0)
    parser.add_argument("--colormap", default="coolwarm")
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    parser.parse_args(argv)
    return 0
```

- [ ] **Step 7: Run the CLI test**

Run:

```bash
python -m pytest tests/python/test_animation_cli.py::test_cli_requires_run_dir -q
```

Expected:

```text
1 passed
```

- [ ] **Step 8: Commit scaffold**

```bash
git add .gitignore requirements.txt scripts/animate_fhn.py scripts/animation/__init__.py scripts/animation/cli.py tests/python/test_animation_cli.py
git commit -m "chore: scaffold Python animation CLI"
```

---

### Task 2: Data Model and Run ID Contract

**Files:**

- Create: `scripts/animation/model.py`
- Modify: `tests/python/test_animation_io.py`

- [ ] **Step 1: Write tests for run id formatting**

Create `tests/python/test_animation_io.py`:

```python
from pathlib import Path

from scripts.animation.model import Metadata


def test_complete_run_id():
    metadata = Metadata(
        mode="single",
        topology="complete",
        n=501,
        k_value=0.2,
        p_value=None,
        ring_k=None,
        dt=0.02,
        total_time=0.2,
        save_interval=0.02,
        realization=1,
        base_seed=12345,
        run_seed=6080882486061793357,
        save_states=True,
        save_adjacency=True,
        topology_type="COMPLETE",
        source_dir=Path("/tmp/run"),
    )

    assert metadata.run_id() == "complete_K_0.20_seed_0001"


def test_random_run_id():
    metadata = Metadata(
        mode="single",
        topology="random",
        n=501,
        k_value=0.2,
        p_value=0.3,
        ring_k=None,
        dt=0.02,
        total_time=0.2,
        save_interval=0.02,
        realization=1,
        base_seed=12345,
        run_seed=-8485422715239165622,
        save_states=True,
        save_adjacency=True,
        topology_type="RANDOM",
        source_dir=Path("/tmp/run"),
    )

    assert metadata.run_id() == "random_p_0.30_K_0.20_seed_0001"


def test_ring_run_id():
    metadata = Metadata(
        mode="single",
        topology="ring",
        n=501,
        k_value=0.2,
        p_value=None,
        ring_k=2,
        dt=0.02,
        total_time=0.2,
        save_interval=0.02,
        realization=1,
        base_seed=12345,
        run_seed=6081439319154255393,
        save_states=True,
        save_adjacency=True,
        topology_type="RING",
        source_dir=Path("/tmp/run"),
    )

    assert metadata.run_id() == "ring_k_02_K_0.20_seed_0001"
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/python/test_animation_io.py -q
```

Expected:

```text
FAILED
```

The expected failure is `ModuleNotFoundError` or `ImportError` for `scripts.animation.model`.

- [ ] **Step 3: Implement model dataclasses**

Create `scripts/animation/model.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import networkx as nx
import numpy as np


class AnimationInputError(ValueError):
    """Raised when simulation output files cannot be consumed."""


@dataclass(frozen=True)
class Metadata:
    mode: str
    topology: str
    n: int
    k_value: float
    p_value: float | None
    ring_k: int | None
    dt: float
    total_time: float
    save_interval: float
    realization: int
    base_seed: int
    run_seed: int
    save_states: bool
    save_adjacency: bool
    topology_type: str
    source_dir: Path

    def run_id(self) -> str:
        seed = f"seed_{self.realization:04d}"
        if self.topology == "complete":
            return f"complete_K_{self.k_value:.2f}_{seed}"
        if self.topology == "random":
            if self.p_value is None:
                raise AnimationInputError("random metadata requires p")
            return f"random_p_{self.p_value:.2f}_K_{self.k_value:.2f}_{seed}"
        if self.topology == "ring":
            if self.ring_k is None:
                raise AnimationInputError("ring metadata requires k")
            return f"ring_k_{self.ring_k:02d}_K_{self.k_value:.2f}_{seed}"
        raise AnimationInputError(f"unsupported topology: {self.topology}")


@dataclass(frozen=True)
class Observables:
    t: np.ndarray
    mean_v: np.ndarray
    sigma_v: np.ndarray
    mean_w: np.ndarray


@dataclass(frozen=True)
class States:
    t: np.ndarray
    v: np.ndarray
    w: np.ndarray

    @property
    def frame_count(self) -> int:
        return int(self.t.shape[0])

    @property
    def n(self) -> int:
        return int(self.v.shape[1])


@dataclass(frozen=True)
class GraphData:
    graph: nx.DiGraph
    edge_count: int


@dataclass(frozen=True)
class RunData:
    metadata: Metadata
    observables: Observables
    states: States
    graph_data: GraphData | None


@dataclass(frozen=True)
class RenderOptions:
    output_dir: Path
    only: str
    fps: int
    dpi: int
    frame_stride: int
    representative_time: float | None
    directed_edges: bool
    layout: str
    edge_alpha: float | None
    edge_width: float
    node_size: float
    colormap: str
    overwrite: bool
```

- [ ] **Step 4: Run model tests**

Run:

```bash
python -m pytest tests/python/test_animation_io.py -q
```

Expected:

```text
3 passed
```

- [ ] **Step 5: Commit model**

```bash
git add scripts/animation/model.py tests/python/test_animation_io.py
git commit -m "feat: add animation data model"
```

---

### Task 3: Metadata and Observable Parsers

**Files:**

- Create: `scripts/animation/io.py`
- Modify: `tests/python/test_animation_io.py`

- [ ] **Step 1: Add parser tests**

Append to `tests/python/test_animation_io.py`:

```python
import pytest

from scripts.animation.io import read_metadata, read_observables
from scripts.animation.model import AnimationInputError


def test_read_metadata(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "metadata.properties").write_text(
        "\n".join(
            [
                "mode=single",
                "topology=ring",
                "N=501",
                "K=0.2",
                "p=",
                "k=2",
                "dt=0.02",
                "T=0.2",
                "saveInterval=0.02",
                "realization=1",
                "baseSeed=12345",
                "runSeed=6081439319154255393",
                "saveStates=true",
                "saveAdjacency=true",
                "topologyType=RING",
            ]
        ),
        encoding="utf-8",
    )

    metadata = read_metadata(run_dir)

    assert metadata.topology == "ring"
    assert metadata.n == 501
    assert metadata.k_value == 0.2
    assert metadata.p_value is None
    assert metadata.ring_k == 2
    assert metadata.save_states is True
    assert metadata.save_adjacency is True
    assert metadata.run_id() == "ring_k_02_K_0.20_seed_0001"


def test_read_metadata_requires_file(tmp_path):
    with pytest.raises(AnimationInputError, match="metadata.properties not found"):
        read_metadata(tmp_path)


def test_read_observables(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "observables.csv").write_text(
        "t,mean_v,sigma_v,mean_w\n"
        "0.0,0.1,0.2,0.3\n"
        "0.1,0.4,0.5,0.6\n",
        encoding="utf-8",
    )

    observables = read_observables(run_dir)

    assert observables.t.tolist() == [0.0, 0.1]
    assert observables.mean_v.tolist() == [0.1, 0.4]
    assert observables.sigma_v.tolist() == [0.2, 0.5]
    assert observables.mean_w.tolist() == [0.3, 0.6]


def test_read_observables_rejects_bad_header(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "observables.csv").write_text(
        "t,mean_v,sigma_v\n0.0,0.1,0.2\n",
        encoding="utf-8",
    )

    with pytest.raises(AnimationInputError, match="observables.csv header"):
        read_observables(run_dir)
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/python/test_animation_io.py -q
```

Expected:

```text
FAILED
```

The expected failure is import failure for `scripts.animation.io`.

- [ ] **Step 3: Implement metadata and observable parsing**

Create `scripts/animation/io.py`:

```python
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
        raise AnimationInputError(f"metadata.properties contains invalid numeric value: {exc}") from exc


def read_observables(run_dir: Path) -> Observables:
    path = run_dir / "observables.csv"
    rows = _read_csv_rows(path, OBSERVABLES_HEADER)
    if not rows:
        raise AnimationInputError(f"observables.csv has no data rows in {run_dir}")

    try:
        data = np.array([[float(row[name]) for name in OBSERVABLES_HEADER] for row in rows], dtype=float)
    except ValueError as exc:
        raise AnimationInputError(f"observables.csv contains invalid numeric value: {exc}") from exc

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


def _read_csv_rows(path: Path, expected_header: list[str]) -> list[dict[str, str]]:
    if not path.exists():
        raise AnimationInputError(f"{path.name} not found in {path.parent}")
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != expected_header:
            raise AnimationInputError(
                f"{path.name} header must be {','.join(expected_header)}; got {reader.fieldnames}"
            )
        return list(reader)
```

- [ ] **Step 4: Run parser tests**

Run:

```bash
python -m pytest tests/python/test_animation_io.py -q
```

Expected:

```text
7 passed
```

- [ ] **Step 5: Commit parsers**

```bash
git add scripts/animation/io.py tests/python/test_animation_io.py
git commit -m "feat: parse animation metadata and observables"
```

---

### Task 4: State Parser and Frame Validation

**Files:**

- Modify: `scripts/animation/io.py`
- Modify: `tests/python/test_animation_io.py`

- [ ] **Step 1: Add state parser tests**

Append to `tests/python/test_animation_io.py`:

```python
from scripts.animation.io import read_states


def test_read_states_orders_times_and_indices(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "states.csv").write_text(
        "t,i,v,w\n"
        "0.1,1,0.4,0.5\n"
        "0.0,1,0.2,0.3\n"
        "0.1,0,0.3,0.4\n"
        "0.0,0,0.1,0.2\n",
        encoding="utf-8",
    )

    states = read_states(run_dir, n=2)

    assert states.t.tolist() == [0.0, 0.1]
    assert states.v.tolist() == [[0.1, 0.2], [0.3, 0.4]]
    assert states.w.tolist() == [[0.2, 0.3], [0.4, 0.5]]


def test_read_states_rejects_incomplete_time(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "states.csv").write_text(
        "t,i,v,w\n"
        "0.0,0,0.1,0.2\n"
        "0.0,1,0.2,0.3\n"
        "0.1,0,0.3,0.4\n",
        encoding="utf-8",
    )

    with pytest.raises(AnimationInputError, match="incomplete state frame"):
        read_states(run_dir, n=2)


def test_read_states_requires_at_least_two_times(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "states.csv").write_text(
        "t,i,v,w\n"
        "0.0,0,0.1,0.2\n"
        "0.0,1,0.2,0.3\n",
        encoding="utf-8",
    )

    with pytest.raises(AnimationInputError, match="at least two state frames"):
        read_states(run_dir, n=2)
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/python/test_animation_io.py -q
```

Expected:

```text
FAILED
```

The expected failure is import failure for `read_states`.

- [ ] **Step 3: Implement `read_states`**

Append to `scripts/animation/io.py`:

```python
def read_states(run_dir: Path, n: int) -> States:
    path = run_dir / "states.csv"
    rows = _read_csv_rows(path, STATES_HEADER)
    if not rows:
        raise AnimationInputError(f"states.csv has no data rows in {run_dir}")

    frames: dict[float, dict[int, tuple[float, float]]] = {}
    try:
        for row in rows:
            t = float(row["t"])
            i = int(row["i"])
            if i < 0 or i >= n:
                raise AnimationInputError(f"states.csv index out of range: {i}; expected 0..{n - 1}")
            frames.setdefault(t, {})[i] = (float(row["v"]), float(row["w"]))
    except ValueError as exc:
        raise AnimationInputError(f"states.csv contains invalid numeric value: {exc}") from exc

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
```

- [ ] **Step 4: Run parser tests**

Run:

```bash
python -m pytest tests/python/test_animation_io.py -q
```

Expected:

```text
10 passed
```

- [ ] **Step 5: Commit state parser**

```bash
git add scripts/animation/io.py tests/python/test_animation_io.py
git commit -m "feat: parse animation state frames"
```

---

### Task 5: Adjacency Parser and NetworkX Graph

**Files:**

- Create: `scripts/animation/graph.py`
- Modify: `scripts/animation/io.py`
- Create: `tests/python/test_animation_graph.py`

- [ ] **Step 1: Add graph tests**

Create `tests/python/test_animation_graph.py`:

```python
import networkx as nx
import pytest

from scripts.animation.graph import build_graph_from_adjacency, compute_layout
from scripts.animation.model import AnimationInputError


def test_build_graph_from_adjacency_keeps_all_directed_edges(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "adjacency.csv").write_text(
        "i,j,Aij\n"
        "0,0,0\n"
        "0,1,1\n"
        "1,0,1\n"
        "1,1,0\n"
        "1,2,1\n"
        "2,0,0\n"
        "2,1,0\n"
        "2,2,0\n",
        encoding="utf-8",
    )

    graph_data = build_graph_from_adjacency(run_dir, n=3)

    assert isinstance(graph_data.graph, nx.DiGraph)
    assert sorted(graph_data.graph.nodes()) == [0, 1, 2]
    assert sorted(graph_data.graph.edges()) == [(0, 1), (1, 0), (1, 2)]
    assert graph_data.edge_count == 3


def test_build_graph_rejects_bad_header(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "adjacency.csv").write_text("i,j\n0,1\n", encoding="utf-8")

    with pytest.raises(AnimationInputError, match="adjacency.csv header"):
        build_graph_from_adjacency(run_dir, n=2)


def test_compute_circular_layout_is_deterministic():
    graph = nx.DiGraph()
    graph.add_nodes_from([0, 1, 2])

    first = compute_layout(graph, layout="circular", seed=123)
    second = compute_layout(graph, layout="circular", seed=999)

    assert first.keys() == second.keys()
    for node in first:
        assert first[node].tolist() == second[node].tolist()


def test_compute_layout_rejects_unknown_name():
    graph = nx.DiGraph()
    graph.add_node(0)

    with pytest.raises(AnimationInputError, match="unsupported layout"):
        compute_layout(graph, layout="grid", seed=123)
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/python/test_animation_graph.py -q
```

Expected:

```text
FAILED
```

The expected failure is import failure for `scripts.animation.graph`.

- [ ] **Step 3: Implement graph helpers**

Create `scripts/animation/graph.py`:

```python
from __future__ import annotations

from pathlib import Path

import networkx as nx

from .io import ADJACENCY_HEADER, _read_csv_rows
from .model import AnimationInputError, GraphData


def build_graph_from_adjacency(run_dir: Path, n: int) -> GraphData:
    rows = _read_csv_rows(run_dir / "adjacency.csv", ADJACENCY_HEADER)
    graph = nx.DiGraph()
    graph.add_nodes_from(range(n))

    try:
        for row in rows:
            i = int(row["i"])
            j = int(row["j"])
            aij = int(row["Aij"])
            if i < 0 or i >= n or j < 0 or j >= n:
                raise AnimationInputError(f"adjacency.csv index out of range: ({i}, {j}); expected 0..{n - 1}")
            if aij == 1:
                graph.add_edge(i, j)
            elif aij != 0:
                raise AnimationInputError(f"adjacency.csv Aij must be 0 or 1; got {aij}")
    except ValueError as exc:
        raise AnimationInputError(f"adjacency.csv contains invalid integer value: {exc}") from exc

    return GraphData(graph=graph, edge_count=graph.number_of_edges())


def compute_layout(graph: nx.DiGraph, layout: str, seed: int) -> dict[int, object]:
    if layout == "circular":
        return nx.circular_layout(graph)
    if layout == "spring":
        return nx.spring_layout(graph, seed=seed)
    raise AnimationInputError(f"unsupported layout: {layout}")
```

- [ ] **Step 4: Run graph and parser tests**

Run:

```bash
python -m pytest tests/python/test_animation_io.py tests/python/test_animation_graph.py -q
```

Expected:

```text
14 passed
```

- [ ] **Step 5: Commit graph helpers**

```bash
git add scripts/animation/graph.py tests/python/test_animation_graph.py
git commit -m "feat: build animation graph from adjacency"
```

---

### Task 6: Run Loader and Output Planning

**Files:**

- Modify: `scripts/animation/io.py`
- Modify: `scripts/animation/cli.py`
- Modify: `tests/python/test_animation_cli.py`

- [ ] **Step 1: Add fixture helper and loader tests**

Replace `tests/python/test_animation_cli.py` with:

```python
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.animation.cli import output_paths, parse_options
from scripts.animation.io import load_run
from scripts.animation.model import AnimationInputError


def write_tiny_run(run_dir: Path, include_adjacency: bool = True) -> None:
    run_dir.mkdir(parents=True)
    (run_dir / "metadata.properties").write_text(
        "\n".join(
            [
                "mode=single",
                "topology=ring",
                "N=3",
                "K=0.2",
                "p=",
                "k=1",
                "dt=0.1",
                "T=0.2",
                "saveInterval=0.1",
                "realization=1",
                "baseSeed=12345",
                "runSeed=42",
                "saveStates=true",
                f"saveAdjacency={'true' if include_adjacency else 'false'}",
                "topologyType=RING",
            ]
        ),
        encoding="utf-8",
    )
    (run_dir / "observables.csv").write_text(
        "t,mean_v,sigma_v,mean_w\n"
        "0.0,0.1,0.2,0.3\n"
        "0.1,0.2,0.1,0.4\n"
        "0.2,0.3,0.0,0.5\n",
        encoding="utf-8",
    )
    (run_dir / "states.csv").write_text(
        "t,i,v,w\n"
        "0.0,0,0.1,0.2\n"
        "0.0,1,0.2,0.3\n"
        "0.0,2,0.3,0.4\n"
        "0.1,0,0.2,0.3\n"
        "0.1,1,0.3,0.4\n"
        "0.1,2,0.4,0.5\n"
        "0.2,0,0.3,0.4\n"
        "0.2,1,0.4,0.5\n"
        "0.2,2,0.5,0.6\n",
        encoding="utf-8",
    )
    if include_adjacency:
        (run_dir / "adjacency.csv").write_text(
            "i,j,Aij\n"
            "0,0,0\n0,1,1\n0,2,1\n"
            "1,0,1\n1,1,0\n1,2,1\n"
            "2,0,1\n2,1,1\n2,2,0\n",
            encoding="utf-8",
        )


def test_cli_requires_run_dir():
    result = subprocess.run(
        [sys.executable, "scripts/animate_fhn.py"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "--run-dir" in result.stderr


def test_load_run_with_graph(tmp_path):
    run_dir = tmp_path / "run"
    write_tiny_run(run_dir)

    run = load_run(run_dir, require_graph=True)

    assert run.metadata.run_id() == "ring_k_01_K_0.20_seed_0001"
    assert run.states.frame_count == 3
    assert run.graph_data is not None
    assert run.graph_data.edge_count == 6


def test_load_run_without_adjacency_for_dashboard(tmp_path):
    run_dir = tmp_path / "run"
    write_tiny_run(run_dir, include_adjacency=False)

    run = load_run(run_dir, require_graph=False)

    assert run.graph_data is None


def test_load_run_requires_adjacency_for_network(tmp_path):
    run_dir = tmp_path / "run"
    write_tiny_run(run_dir, include_adjacency=False)

    with pytest.raises(AnimationInputError, match="adjacency.csv not found"):
        load_run(run_dir, require_graph=True)


def test_output_paths(tmp_path):
    run_dir = tmp_path / "run"
    write_tiny_run(run_dir)
    run = load_run(run_dir, require_graph=True)
    options = parse_options(
        [
            "--run-dir",
            str(run_dir),
            "--output-dir",
            str(tmp_path / "renders"),
        ]
    )

    paths = output_paths(run.metadata, options)

    assert paths.run_dir == tmp_path / "renders" / "ring_k_01_K_0.20_seed_0001"
    assert paths.network_mp4.name == "network.mp4"
    assert paths.dashboard_png.name == "dashboard_frame.png"
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/python/test_animation_cli.py -q
```

Expected:

```text
FAILED
```

The expected failures are missing `load_run`, `parse_options`, and `output_paths`.

- [ ] **Step 3: Implement `load_run`**

Append to `scripts/animation/io.py`:

```python
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
```

- [ ] **Step 4: Implement option parsing and output paths**

Replace `scripts/animation/cli.py` with:

```python
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from .model import Metadata, RenderOptions


@dataclass(frozen=True)
class PlannedOutputPaths:
    run_dir: Path
    network_mp4: Path
    network_png: Path
    dashboard_mp4: Path
    dashboard_png: Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="animate_fhn.py",
        description="Generate FitzHugh-Nagumo animations from motor output files.",
    )
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("renders"))
    parser.add_argument("--only", choices=("network", "dashboard", "all"), default="all")
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--dpi", type=int, default=140)
    parser.add_argument("--frame-stride", type=int, default=1)
    parser.add_argument("--representative-time", type=float)
    parser.add_argument("--directed-edges", action="store_true")
    parser.add_argument("--layout", choices=("circular", "spring"), default="circular")
    parser.add_argument("--edge-alpha", type=float)
    parser.add_argument("--edge-width", type=float, default=0.25)
    parser.add_argument("--node-size", type=float, default=18.0)
    parser.add_argument("--colormap", default="coolwarm")
    parser.add_argument("--overwrite", action="store_true")
    return parser


def parse_options(argv: list[str] | None = None) -> RenderOptions:
    args = build_parser().parse_args(argv)
    if args.fps <= 0:
        raise SystemExit("--fps must be positive")
    if args.dpi <= 0:
        raise SystemExit("--dpi must be positive")
    if args.frame_stride <= 0:
        raise SystemExit("--frame-stride must be positive")
    return RenderOptions(
        output_dir=args.output_dir,
        only=args.only,
        fps=args.fps,
        dpi=args.dpi,
        frame_stride=args.frame_stride,
        representative_time=args.representative_time,
        directed_edges=args.directed_edges,
        layout=args.layout,
        edge_alpha=args.edge_alpha,
        edge_width=args.edge_width,
        node_size=args.node_size,
        colormap=args.colormap,
        overwrite=args.overwrite,
    )


def output_paths(metadata: Metadata, options: RenderOptions) -> PlannedOutputPaths:
    run_output_dir = options.output_dir / metadata.run_id()
    return PlannedOutputPaths(
        run_dir=run_output_dir,
        network_mp4=run_output_dir / "network.mp4",
        network_png=run_output_dir / "network_frame.png",
        dashboard_mp4=run_output_dir / "dashboard.mp4",
        dashboard_png=run_output_dir / "dashboard_frame.png",
    )


def main(argv: list[str] | None = None) -> int:
    build_parser().parse_args(argv)
    return 0
```

- [ ] **Step 5: Run CLI tests**

Run:

```bash
python -m pytest tests/python/test_animation_cli.py -q
```

Expected:

```text
5 passed
```

- [ ] **Step 6: Commit loader/output planning**

```bash
git add scripts/animation/io.py scripts/animation/cli.py tests/python/test_animation_cli.py
git commit -m "feat: load animation run data"
```

---

### Task 7: Dashboard Renderer

**Files:**

- Create: `scripts/animation/render.py`
- Modify: `tests/python/test_animation_cli.py`

- [ ] **Step 1: Add dashboard render test**

Append to `tests/python/test_animation_cli.py`:

```python
from scripts.animation.render import render_dashboard


def test_render_dashboard_outputs_mp4_and_png(tmp_path):
    run_dir = tmp_path / "run"
    write_tiny_run(run_dir)
    run = load_run(run_dir, require_graph=False)
    options = parse_options(
        [
            "--run-dir",
            str(run_dir),
            "--output-dir",
            str(tmp_path / "renders"),
            "--fps",
            "2",
            "--dpi",
            "80",
            "--overwrite",
        ]
    )
    paths = output_paths(run.metadata, options)

    render_dashboard(run, options, paths)

    assert paths.dashboard_mp4.exists()
    assert paths.dashboard_mp4.stat().st_size > 0
    assert paths.dashboard_png.exists()
    assert paths.dashboard_png.stat().st_size > 0
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
python -m pytest tests/python/test_animation_cli.py::test_render_dashboard_outputs_mp4_and_png -q
```

Expected:

```text
FAILED
```

The expected failure is missing `scripts.animation.render`.

- [ ] **Step 3: Implement dashboard rendering**

Create `scripts/animation/render.py`:

```python
from __future__ import annotations

import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np

from .cli import PlannedOutputPaths
from .model import AnimationInputError, RenderOptions, RunData


def ensure_ffmpeg_available() -> None:
    if shutil.which("ffmpeg") is None:
        raise AnimationInputError("ffmpeg not found. Install ffmpeg before exporting MP4 animations.")


def selected_frame_indices(frame_count: int, frame_stride: int) -> list[int]:
    indices = list(range(0, frame_count, frame_stride))
    if indices[-1] != frame_count - 1:
        indices.append(frame_count - 1)
    return indices


def representative_frame_index(times: np.ndarray, representative_time: float | None) -> int:
    target = float(times[len(times) // 2] if representative_time is None else representative_time)
    return int(np.argmin(np.abs(times - target)))


def nearest_observable_index(observable_times: np.ndarray, t: float) -> int:
    return int(np.argmin(np.abs(observable_times - t)))


def render_dashboard(run: RunData, options: RenderOptions, paths: PlannedOutputPaths) -> None:
    ensure_ffmpeg_available()
    paths.run_dir.mkdir(parents=True, exist_ok=True)

    frame_indices = selected_frame_indices(run.states.frame_count, options.frame_stride)
    rep_index = representative_frame_index(run.states.t, options.representative_time)

    fig, axes = plt.subplots(3, 1, figsize=(9, 8), constrained_layout=True)
    fig.suptitle(_title(run, "Dashboard"))

    mean_axis, sigma_axis, snapshot_axis = axes
    mean_axis.plot(run.observables.t, run.observables.mean_v, color="#1f77b4")
    mean_axis.set_ylabel("<v(t)>")
    mean_axis.set_xlabel("t")
    mean_marker = mean_axis.axvline(run.states.t[0], color="black", linewidth=1)

    sigma_axis.plot(run.observables.t, run.observables.sigma_v, color="#d62728")
    sigma_axis.set_ylabel("sigma_v(t)")
    sigma_axis.set_xlabel("t")
    sigma_marker = sigma_axis.axvline(run.states.t[0], color="black", linewidth=1)

    node_indices = np.arange(run.states.n)
    snapshot_line, = snapshot_axis.plot(node_indices, run.states.v[0], color="#2ca02c", linewidth=1)
    snapshot_axis.set_ylabel("v_i(t)")
    snapshot_axis.set_xlabel("i")
    snapshot_axis.set_xlim(0, run.states.n - 1)
    vmin = float(np.min(run.states.v))
    vmax = float(np.max(run.states.v))
    if vmin == vmax:
        vmin -= 0.5
        vmax += 0.5
    snapshot_axis.set_ylim(vmin, vmax)
    time_text = snapshot_axis.text(0.02, 0.95, "", transform=snapshot_axis.transAxes, va="top")

    def update(frame_index: int):
        t = float(run.states.t[frame_index])
        mean_marker.set_xdata([t, t])
        sigma_marker.set_xdata([t, t])
        snapshot_line.set_ydata(run.states.v[frame_index])
        obs_index = nearest_observable_index(run.observables.t, t)
        time_text.set_text(
            f"t={t:.3f}, <v>={run.observables.mean_v[obs_index]:.4f}, sigma_v={run.observables.sigma_v[obs_index]:.4f}"
        )
        return mean_marker, sigma_marker, snapshot_line, time_text

    animation = FuncAnimation(fig, update, frames=frame_indices, blit=False)
    animation.save(paths.dashboard_mp4, writer="ffmpeg", fps=options.fps, dpi=options.dpi)
    update(rep_index)
    fig.savefig(paths.dashboard_png, dpi=options.dpi)
    plt.close(fig)


def _title(run: RunData, prefix: str) -> str:
    metadata = run.metadata
    if metadata.topology == "random":
        params = f"p={metadata.p_value:.2f}, K={metadata.k_value:.2f}"
    elif metadata.topology == "ring":
        params = f"k={metadata.ring_k:02d}, K={metadata.k_value:.2f}"
    else:
        params = f"K={metadata.k_value:.2f}"
    return f"{prefix} - {metadata.topology} ({params}), seed={metadata.realization:04d}"
```

- [ ] **Step 4: Run dashboard render test**

Run:

```bash
python -m pytest tests/python/test_animation_cli.py::test_render_dashboard_outputs_mp4_and_png -q
```

Expected:

```text
1 passed
```

If it fails with `ffmpeg not found`, install ffmpeg or document the local blocker before continuing.

- [ ] **Step 5: Run all Python tests**

Run:

```bash
python -m pytest tests/python -q
```

Expected:

```text
15 passed
```

- [ ] **Step 6: Commit dashboard renderer**

```bash
git add scripts/animation/render.py tests/python/test_animation_cli.py
git commit -m "feat: render FHN dashboard animation"
```

---

### Task 8: Network Renderer

**Files:**

- Modify: `scripts/animation/render.py`
- Modify: `tests/python/test_animation_cli.py`

- [ ] **Step 1: Add network render test**

Append to `tests/python/test_animation_cli.py`:

```python
from scripts.animation.render import render_network


def test_render_network_outputs_mp4_and_png(tmp_path):
    run_dir = tmp_path / "run"
    write_tiny_run(run_dir)
    run = load_run(run_dir, require_graph=True)
    options = parse_options(
        [
            "--run-dir",
            str(run_dir),
            "--output-dir",
            str(tmp_path / "renders"),
            "--fps",
            "2",
            "--dpi",
            "80",
            "--overwrite",
        ]
    )
    paths = output_paths(run.metadata, options)

    render_network(run, options, paths)

    assert paths.network_mp4.exists()
    assert paths.network_mp4.stat().st_size > 0
    assert paths.network_png.exists()
    assert paths.network_png.stat().st_size > 0
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
python -m pytest tests/python/test_animation_cli.py::test_render_network_outputs_mp4_and_png -q
```

Expected:

```text
FAILED
```

The expected failure is missing `render_network`.

- [ ] **Step 3: Implement network rendering**

Append to `scripts/animation/render.py`:

```python
import networkx as nx

from .graph import compute_layout


def render_network(run: RunData, options: RenderOptions, paths: PlannedOutputPaths) -> None:
    ensure_ffmpeg_available()
    if run.graph_data is None:
        raise AnimationInputError("adjacency.csv not found in run directory. Network animation requires --save-adjacency.")
    paths.run_dir.mkdir(parents=True, exist_ok=True)

    graph = run.graph_data.graph
    edge_count = run.graph_data.edge_count
    frame_indices = selected_frame_indices(run.states.frame_count, options.frame_stride)
    rep_index = representative_frame_index(run.states.t, options.representative_time)

    if options.layout == "spring" and (run.metadata.n > 200 or edge_count > 20000):
        print(
            f"WARNING: spring layout may be slow for N={run.metadata.n}, edge_count={edge_count}",
            flush=True,
        )
    if options.directed_edges and edge_count > 20000:
        print(
            f"WARNING: directed arrows may be illegible for edge_count={edge_count}",
            flush=True,
        )
    print(
        f"Rendering network: N={run.metadata.n}, edge_count={edge_count}, frames={len(frame_indices)}, output={paths.network_mp4}",
        flush=True,
    )

    positions = compute_layout(graph, options.layout, seed=run.metadata.run_seed)
    vmin = float(np.min(run.states.v))
    vmax = float(np.max(run.states.v))
    if vmin == vmax:
        vmin -= 0.5
        vmax += 0.5

    edge_alpha = options.edge_alpha
    if edge_alpha is None:
        edge_alpha = 0.08 if edge_count > 20000 else 0.20

    fig, axis = plt.subplots(figsize=(8, 8), constrained_layout=True)
    axis.set_axis_off()
    axis.set_title(_title(run, "Network"))

    nx.draw_networkx_edges(
        graph,
        positions,
        ax=axis,
        arrows=options.directed_edges,
        alpha=edge_alpha,
        width=options.edge_width,
        edge_color="#555555",
        arrowsize=4,
    )
    nodes = nx.draw_networkx_nodes(
        graph,
        positions,
        ax=axis,
        node_color=run.states.v[0],
        cmap=options.colormap,
        vmin=vmin,
        vmax=vmax,
        node_size=options.node_size,
        linewidths=0.0,
    )
    colorbar = fig.colorbar(nodes, ax=axis, shrink=0.75)
    colorbar.set_label("v_i(t)")
    time_text = axis.text(0.02, 0.98, "", transform=axis.transAxes, va="top")

    def update(frame_index: int):
        t = float(run.states.t[frame_index])
        nodes.set_array(run.states.v[frame_index])
        time_text.set_text(f"t={t:.3f}")
        return nodes, time_text

    animation = FuncAnimation(fig, update, frames=frame_indices, blit=False)
    animation.save(paths.network_mp4, writer="ffmpeg", fps=options.fps, dpi=options.dpi)
    update(rep_index)
    fig.savefig(paths.network_png, dpi=options.dpi)
    plt.close(fig)
```

- [ ] **Step 4: Run network render test**

Run:

```bash
python -m pytest tests/python/test_animation_cli.py::test_render_network_outputs_mp4_and_png -q
```

Expected:

```text
1 passed
```

- [ ] **Step 5: Run all Python tests**

Run:

```bash
python -m pytest tests/python -q
```

Expected:

```text
16 passed
```

- [ ] **Step 6: Commit network renderer**

```bash
git add scripts/animation/render.py tests/python/test_animation_cli.py
git commit -m "feat: render FHN network animation"
```

---

### Task 9: CLI Orchestration and Error Behavior

**Files:**

- Modify: `scripts/animation/cli.py`
- Modify: `tests/python/test_animation_cli.py`

- [ ] **Step 1: Add end-to-end CLI tests**

Append to `tests/python/test_animation_cli.py`:

```python
def test_cli_generates_all_outputs(tmp_path):
    run_dir = tmp_path / "run"
    output_dir = tmp_path / "renders"
    write_tiny_run(run_dir)

    result = subprocess.run(
        [
            sys.executable,
            "scripts/animate_fhn.py",
            "--run-dir",
            str(run_dir),
            "--output-dir",
            str(output_dir),
            "--fps",
            "2",
            "--dpi",
            "80",
            "--overwrite",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    run_output = output_dir / "ring_k_01_K_0.20_seed_0001"
    assert (run_output / "network.mp4").exists()
    assert (run_output / "network_frame.png").exists()
    assert (run_output / "dashboard.mp4").exists()
    assert (run_output / "dashboard_frame.png").exists()


def test_cli_dashboard_only_works_without_adjacency(tmp_path):
    run_dir = tmp_path / "run"
    output_dir = tmp_path / "renders"
    write_tiny_run(run_dir, include_adjacency=False)

    result = subprocess.run(
        [
            sys.executable,
            "scripts/animate_fhn.py",
            "--run-dir",
            str(run_dir),
            "--output-dir",
            str(output_dir),
            "--only",
            "dashboard",
            "--fps",
            "2",
            "--dpi",
            "80",
            "--overwrite",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    run_output = output_dir / "ring_k_01_K_0.20_seed_0001"
    assert not (run_output / "network.mp4").exists()
    assert (run_output / "dashboard.mp4").exists()


def test_cli_reports_missing_states(tmp_path):
    run_dir = tmp_path / "run"
    write_tiny_run(run_dir)
    (run_dir / "states.csv").unlink()

    result = subprocess.run(
        [
            sys.executable,
            "scripts/animate_fhn.py",
            "--run-dir",
            str(run_dir),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "states.csv not found" in result.stderr
    assert "--save-states" in result.stderr
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/python/test_animation_cli.py::test_cli_generates_all_outputs tests/python/test_animation_cli.py::test_cli_dashboard_only_works_without_adjacency tests/python/test_animation_cli.py::test_cli_reports_missing_states -q
```

Expected:

```text
FAILED
```

The expected failures are CLI no-op behavior and missing user-facing error mapping.

- [ ] **Step 3: Implement orchestration**

Replace `main` in `scripts/animation/cli.py` with:

```python
def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        options = parse_options(argv)
        require_graph = options.only in ("network", "all")
        from .io import load_run
        from .render import render_dashboard, render_network

        run = load_run(args.run_dir, require_graph=require_graph)
        paths = output_paths(run.metadata, options)
        planned = _planned_files(options.only, paths)

        if not options.overwrite:
            existing = [path for path in planned if path.exists()]
            if existing and len(existing) == len(planned):
                print(f"SKIP existing {paths.run_dir}")
                return 0
            if existing:
                names = ", ".join(str(path) for path in existing)
                raise AnimationInputError(f"partial outputs already exist without --overwrite: {names}")

        if options.only in ("network", "all"):
            render_network(run, options, paths)
        if options.only in ("dashboard", "all"):
            render_dashboard(run, options, paths)
        print(f"OK {paths.run_dir}")
        return 0
    except AnimationInputError as exc:
        message = str(exc)
        if "states.csv not found" in message:
            message += ". Regenerate the simulation with --save-states."
        if "adjacency.csv not found" in message:
            message += ". Regenerate the simulation with --save-adjacency or run with --only dashboard."
        parser.exit(1, f"ERROR: {message}\n")


def _planned_files(only: str, paths: PlannedOutputPaths) -> list[Path]:
    if only == "network":
        return [paths.network_mp4, paths.network_png]
    if only == "dashboard":
        return [paths.dashboard_mp4, paths.dashboard_png]
    return [paths.network_mp4, paths.network_png, paths.dashboard_mp4, paths.dashboard_png]
```

Also add the import near the top of `scripts/animation/cli.py`:

```python
from .model import AnimationInputError, Metadata, RenderOptions
```

- [ ] **Step 4: Run CLI tests**

Run:

```bash
python -m pytest tests/python/test_animation_cli.py -q
```

Expected:

```text
9 passed
```

- [ ] **Step 5: Run all Python tests**

Run:

```bash
python -m pytest tests/python -q
```

Expected:

```text
18 passed
```

- [ ] **Step 6: Commit CLI orchestration**

```bash
git add scripts/animation/cli.py tests/python/test_animation_cli.py
git commit -m "feat: orchestrate FHN animation CLI"
```

---

### Task 10: Verification, Smoke, and Documentation Closeout

**Files:**

- Modify: `docs/superpowers/plans/fhn-python-animations-implementation-plan.md` only if execution findings require plan corrections.

- [ ] **Step 1: Run full Python tests**

Run:

```bash
python -m pytest tests/python -q
```

Expected:

```text
18 passed
```

- [ ] **Step 2: Run existing Java tests**

Run:

```bash
mvn -q test
```

Expected:

```text
exit code 0
```

The Maven output includes existing sweep/smoke logs from the Java tests.

- [ ] **Step 3: Generate a fresh Java smoke run with states and adjacency**

Run:

```bash
mvn -q -DskipTests exec:java \
  -Dexec.args="single --topology ring --N 501 --K 0.2 --k 2 --dt 0.02 --T 0.2 --save-interval 0.02 --output-dir /tmp/tp5-fhn-animation-smoke --save-states --save-adjacency --overwrite"
```

Expected:

```text
OK /tmp/tp5-fhn-animation-smoke/runs/ring/k_02/K_0.20/seed_0001
```

- [ ] **Step 4: Render from the smoke run**

Run:

```bash
python scripts/animate_fhn.py \
  --run-dir /tmp/tp5-fhn-animation-smoke/runs/ring/k_02/K_0.20/seed_0001 \
  --output-dir /tmp/tp5-fhn-animation-renders \
  --fps 12 \
  --dpi 100 \
  --overwrite
```

Expected:

```text
OK /tmp/tp5-fhn-animation-renders/ring_k_02_K_0.20_seed_0001
```

- [ ] **Step 5: Verify smoke output files are nonempty**

Run:

```bash
ls -lh /tmp/tp5-fhn-animation-renders/ring_k_02_K_0.20_seed_0001
test -s /tmp/tp5-fhn-animation-renders/ring_k_02_K_0.20_seed_0001/network.mp4
test -s /tmp/tp5-fhn-animation-renders/ring_k_02_K_0.20_seed_0001/network_frame.png
test -s /tmp/tp5-fhn-animation-renders/ring_k_02_K_0.20_seed_0001/dashboard.mp4
test -s /tmp/tp5-fhn-animation-renders/ring_k_02_K_0.20_seed_0001/dashboard_frame.png
```

Expected:

```text
all test commands exit 0
```

- [ ] **Step 6: Check git status**

Run:

```bash
git status --short
```

Expected:

```text
only intended source/test/doc changes are listed
```

- [ ] **Step 7: Final commit**

```bash
git add .gitignore requirements.txt scripts tests
git commit -m "feat: add FHN Python animations"
```

## Self-Review Checklist

- Spec coverage:
  - Python CLI: Tasks 1, 6, 9.
  - NetworkX + Matplotlib: Tasks 5, 7, 8.
  - All `Aij=1` edges: Task 5 and Task 8.
  - Configurable directed edges: Task 1 parser and Task 8 renderer.
  - MP4 + PNG outputs: Tasks 7, 8, 9, 10.
  - Dashboard without adjacency: Task 9.
  - Missing-file errors: Tasks 3, 4, 5, 9.
  - Smoke reproducibility: Task 10.
- Placeholder scan: no unfinished markers or unspecified implementation steps should remain.
- Test style: tests assert public CLI/parser/output behavior, not private methods or exact rendering pixels.
- Scope: no Java motor changes are required.
