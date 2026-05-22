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
