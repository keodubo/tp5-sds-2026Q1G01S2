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
