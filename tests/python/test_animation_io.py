from pathlib import Path

import pytest

from scripts.animation.io import read_metadata, read_observables, read_states
from scripts.animation.model import AnimationInputError, Metadata


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


def test_random_run_id_keeps_small_probabilities_distinct():
    metadata = Metadata(
        mode="single",
        topology="random",
        n=501,
        k_value=0.1,
        p_value=0.0001,
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

    assert metadata.run_id() == "random_p_1.0000e-4_K_0.10_seed_0001"


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


def test_read_metadata_rejects_invalid_boolean(tmp_path):
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
                "saveStates=yes",
                "saveAdjacency=true",
                "topologyType=RING",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(AnimationInputError, match="metadata.properties contains invalid value"):
        read_metadata(run_dir)


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


def test_read_observables_rejects_short_row(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "observables.csv").write_text(
        "t,mean_v,sigma_v,mean_w\n"
        "0.0,0.1,0.2\n",
        encoding="utf-8",
    )

    with pytest.raises(AnimationInputError, match="observables.csv contains invalid value"):
        read_observables(run_dir)


def test_read_observables_rejects_long_row(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "observables.csv").write_text(
        "t,mean_v,sigma_v,mean_w\n"
        "0.0,0.1,0.2,0.3,EXTRA\n",
        encoding="utf-8",
    )

    with pytest.raises(AnimationInputError, match="observables.csv contains invalid row"):
        read_observables(run_dir)


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


def test_read_states_rejects_short_row(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "states.csv").write_text(
        "t,i,v,w\n"
        "0.0,0,0.1\n",
        encoding="utf-8",
    )

    with pytest.raises(AnimationInputError, match="states.csv contains invalid value"):
        read_states(run_dir, n=1)


def test_read_states_rejects_duplicate_time_and_index(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "states.csv").write_text(
        "t,i,v,w\n"
        "0.0,0,0.1,0.2\n"
        "0.0,0,0.3,0.4\n"
        "0.1,0,0.5,0.6\n",
        encoding="utf-8",
    )

    with pytest.raises(AnimationInputError, match="duplicate state row"):
        read_states(run_dir, n=1)


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
