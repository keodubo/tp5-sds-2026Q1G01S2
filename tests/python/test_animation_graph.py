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


def test_build_graph_rejects_short_row(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "adjacency.csv").write_text("i,j,Aij\n0,1\n", encoding="utf-8")

    with pytest.raises(AnimationInputError, match="adjacency.csv contains invalid value"):
        build_graph_from_adjacency(run_dir, n=2)


def test_compute_circular_layout_is_deterministic():
    graph = nx.DiGraph()
    graph.add_nodes_from([0, 1, 2])

    first = compute_layout(graph, layout="circular", seed=123)
    second = compute_layout(graph, layout="circular", seed=999)

    assert first.keys() == second.keys()
    for node in first:
        assert first[node].tolist() == second[node].tolist()


def test_compute_spring_layout_is_deterministic_with_same_seed():
    graph = nx.DiGraph()
    graph.add_edges_from([(0, 1), (1, 2), (2, 0)])

    first = compute_layout(graph, layout="spring", seed=123)
    second = compute_layout(graph, layout="spring", seed=123)

    assert first.keys() == second.keys()
    for node in first:
        assert first[node].tolist() == second[node].tolist()


@pytest.mark.parametrize("seed", [6081439319154255393, -8485422715239165622])
def test_compute_spring_layout_accepts_java_long_seed(seed):
    graph = nx.DiGraph()
    graph.add_edges_from([(0, 1), (1, 2), (2, 0)])

    first = compute_layout(graph, layout="spring", seed=seed)
    second = compute_layout(graph, layout="spring", seed=seed)

    assert first.keys() == second.keys()
    for node in first:
        assert first[node].tolist() == second[node].tolist()


def test_compute_spring_layout_handles_tp_size_graph():
    graph = nx.cycle_graph(501, create_using=nx.DiGraph)

    positions = compute_layout(graph, layout="spring", seed=6081439319154255393)

    assert set(positions) == set(range(501))


def test_compute_layout_rejects_unknown_name():
    graph = nx.DiGraph()
    graph.add_node(0)

    with pytest.raises(AnimationInputError, match="unsupported layout"):
        compute_layout(graph, layout="grid", seed=123)
