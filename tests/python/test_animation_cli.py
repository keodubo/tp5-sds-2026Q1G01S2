import subprocess
import sys
from pathlib import Path

import pytest

from scripts.animation.cli import output_paths, parse_options
from scripts.animation.io import load_run
from scripts.animation.model import AnimationInputError
from scripts.animation.render import render_dashboard, render_network


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


@pytest.mark.parametrize(
    ("option", "message"),
    [
        ("--fps", "--fps must be positive"),
        ("--dpi", "--dpi must be positive"),
        ("--frame-stride", "--frame-stride must be positive"),
    ],
)
def test_cli_rejects_non_positive_integer_options(option, message):
    result = subprocess.run(
        [
            sys.executable,
            "scripts/animate_fhn.py",
            "--run-dir",
            "/tmp/nonexistent",
            option,
            "0",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert message in result.stderr


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
