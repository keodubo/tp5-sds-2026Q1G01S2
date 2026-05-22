from __future__ import annotations

from pathlib import Path

import networkx as nx

from .io import ADJACENCY_HEADER, _read_csv_rows, _read_int
from .model import AnimationInputError, GraphData


def build_graph_from_adjacency(run_dir: Path, n: int) -> GraphData:
    path = run_dir / "adjacency.csv"
    rows = _read_csv_rows(path, ADJACENCY_HEADER)
    graph = nx.DiGraph()
    graph.add_nodes_from(range(n))

    for row_number, row in enumerate(rows, start=2):
        i = _read_int(row, "i", path, row_number)
        j = _read_int(row, "j", path, row_number)
        aij = _read_int(row, "Aij", path, row_number)
        if i < 0 or i >= n or j < 0 or j >= n:
            raise AnimationInputError(
                f"adjacency.csv index out of range: ({i}, {j}); expected 0..{n - 1}"
            )
        if aij == 1:
            graph.add_edge(i, j)
        elif aij != 0:
            raise AnimationInputError(f"adjacency.csv Aij must be 0 or 1; got {aij}")

    return GraphData(graph=graph, edge_count=graph.number_of_edges())


def compute_layout(graph: nx.DiGraph, layout: str, seed: int) -> dict[int, object]:
    if layout == "circular":
        return nx.circular_layout(graph)
    if layout == "spring":
        return nx.spring_layout(graph, seed=_networkx_seed(seed))
    raise AnimationInputError(f"unsupported layout: {layout}")


def _networkx_seed(seed: int) -> int:
    # NetworkX delegates integer seeds to NumPy, whose accepted range differs from Java long.
    return seed % (2**32)
