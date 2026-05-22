from __future__ import annotations

import shutil

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import networkx as nx
import numpy as np

from .cli import PlannedOutputPaths
from .graph import compute_layout
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
    (snapshot_line,) = snapshot_axis.plot(node_indices, run.states.v[0], color="#2ca02c", linewidth=1)
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
            f"t={t:.3f}, <v>={run.observables.mean_v[obs_index]:.4f}, "
            f"sigma_v={run.observables.sigma_v[obs_index]:.4f}"
        )
        return mean_marker, sigma_marker, snapshot_line, time_text

    try:
        animation = FuncAnimation(fig, update, frames=frame_indices, blit=False)
        animation.save(paths.dashboard_mp4, writer="ffmpeg", fps=options.fps, dpi=options.dpi)
        update(rep_index)
        fig.savefig(paths.dashboard_png, dpi=options.dpi)
    finally:
        plt.close(fig)


def render_network(run: RunData, options: RenderOptions, paths: PlannedOutputPaths) -> None:
    ensure_ffmpeg_available()
    if run.graph_data is None:
        raise AnimationInputError(
            "adjacency.csv not found in run directory. Network animation requires --save-adjacency."
        )
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
        edge_alpha = 0.06 if edge_count > 20000 else 0.65

    fig, axis = plt.subplots(figsize=(8, 8), constrained_layout=True)
    axis.set_axis_off()
    axis.set_title(_title(run, "Network"))

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
    edge_draw_options = {"arrowsize": 4} if options.directed_edges else {}
    edges = nx.draw_networkx_edges(
        graph,
        positions,
        ax=axis,
        arrows=options.directed_edges,
        alpha=edge_alpha,
        width=options.edge_width,
        edge_color="#333333",
        **edge_draw_options,
    )
    if hasattr(edges, "set_zorder"):
        edges.set_zorder(3)
    elif isinstance(edges, list):
        for edge in edges:
            edge.set_zorder(3)
    colorbar = fig.colorbar(nodes, ax=axis, shrink=0.75)
    colorbar.set_label("v_i(t)")
    time_text = axis.text(0.02, 0.98, "", transform=axis.transAxes, va="top")

    def update(frame_index: int):
        t = float(run.states.t[frame_index])
        nodes.set_array(run.states.v[frame_index])
        time_text.set_text(f"t={t:.3f}")
        return nodes, time_text

    try:
        animation = FuncAnimation(fig, update, frames=frame_indices, blit=False)
        animation.save(paths.network_mp4, writer="ffmpeg", fps=options.fps, dpi=options.dpi)
        update(rep_index)
        fig.savefig(paths.network_png, dpi=options.dpi)
    finally:
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
