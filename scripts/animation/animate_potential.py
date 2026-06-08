#!/usr/bin/env python3
"""Circular-network potential animation for TP5 Sistema 2 (FitzHugh-Nagumo).

Consumes the text output of the Java engine (states.csv + metadata.properties)
and renders the N neurons placed on a circle, coloured by their membrane
potential v_i(t), with a shared colour bar. As the network synchronises every
node converges to the same colour.

Runs fully independently of the simulation: animation speed and post-processing
do not depend on simulation speed (TP5 requirement). Exports MP4, GIF and PNG.

Usage:
    python3 scripts/animation/animate_potential.py \
        --run-dir tmp/anim-source-runs/runs/complete/K_0.50/seed_0001 \
        --output-dir outputs/2026-06-08_potential-animations_v1 \
        --label completa_K0.50 --title "Red completa - K=0.50"
"""
from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter


# --------------------------------------------------------------------------- IO
@dataclass(frozen=True)
class Run:
    topology: str
    n: int
    k_value: float
    p_value: float | None
    ring_k: int | None
    save_interval: float
    total_time: float
    times: np.ndarray  # (F,)
    v: np.ndarray  # (F, N)


def read_metadata(run_dir: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in (run_dir / "metadata.properties").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    return values


def load_run(run_dir: Path) -> Run:
    meta = read_metadata(run_dir)
    n = int(meta["N"])
    states_path = run_dir / "states.csv"
    if not states_path.exists():
        raise SystemExit(f"ERROR: states.csv not found in {run_dir} (re-run engine with --save-states)")

    # The engine writes exactly N rows (i = 0..N-1, in order) per saved time.
    # Load only the time and v columns, then reshape to (frames, N).
    data = np.loadtxt(states_path, delimiter=",", skiprows=1, usecols=(0, 2))
    if data.shape[0] % n != 0:
        raise SystemExit(f"ERROR: states row count {data.shape[0]} not divisible by N={n}")
    frames = data.shape[0] // n
    t_flat = data[:, 0].reshape(frames, n)
    v = data[:, 1].reshape(frames, n)
    times = t_flat[:, 0].copy()
    return Run(
        topology=meta["topology"],
        n=n,
        k_value=float(meta["K"]),
        p_value=float(meta["p"]) if meta.get("p") else None,
        ring_k=int(meta["k"]) if meta.get("k") else None,
        save_interval=float(meta["saveInterval"]),
        total_time=float(meta["T"]),
        times=times,
        v=v,
    )


# ---------------------------------------------------------------------- helpers
def default_title(run: Run) -> str:
    if run.topology == "random":
        return rf"Red aleatoria,  $p = {run.p_value:g},\ K = {run.k_value:.2f}$"
    if run.topology == "ring":
        return rf"Red anillo,  $k = {run.ring_k},\ K = {run.k_value:.2f}$"
    return rf"Red completa,  $K = {run.k_value:.2f}$"


def frame_indices(total: int, stride: int) -> list[int]:
    idx = list(range(0, total, stride))
    if idx[-1] != total - 1:
        idx.append(total - 1)
    return idx


# ------------------------------------------------------------------- rendering
def build_figure(run: Run, vmin: float, vmax: float, cmap: str, node_size: float, title: str):
    theta = 2.0 * np.pi * np.arange(run.n) / run.n
    xs, ys = np.cos(theta), np.sin(theta)

    fig, ax = plt.subplots(figsize=(7.2, 7.6))
    ax.set_aspect("equal")
    ax.set_xlim(-1.18, 1.18)
    ax.set_ylim(-1.18, 1.18)
    ax.set_axis_off()

    scatter = ax.scatter(
        xs, ys, c=run.v[0], cmap=cmap, vmin=vmin, vmax=vmax,
        s=node_size, linewidths=0.0, zorder=3,
    )
    cbar = fig.colorbar(scatter, ax=ax, shrink=0.82, pad=0.02)
    cbar.set_label(r"potencial  $v_i$", fontsize=12)

    ax.set_title(title, fontsize=15, pad=14)
    ax.text(0.015, 0.985, f"$N = {run.n}$\nFitzHugh-Nagumo", transform=ax.transAxes,
            ha="left", va="top", fontsize=10.5, color="#666666")
    info = ax.text(
        0.5, -0.02, "", transform=ax.transAxes, ha="center", va="top", fontsize=14,
    )
    fig.subplots_adjust(left=0.02, right=0.98, top=0.93, bottom=0.06)
    return fig, scatter, info


def info_text(run: Run, frame: int) -> str:
    v = run.v[frame]
    return (rf"$t = {run.times[frame]:.1f}$"
            rf"$\quad\quad\sigma_v = {v.std():.4f}$"
            rf"$\quad\quad\langle v\rangle = {v.mean():+.3f}$")


def render(run: Run, args: argparse.Namespace, out: Path, title: str) -> dict:
    mp4_dir = out / "mp4"
    gif_dir = out / "gif"
    png_dir = out / "png"
    for d in (mp4_dir, gif_dir, png_dir):
        d.mkdir(parents=True, exist_ok=True)
    total = run.v.shape[0]
    result: dict[str, object] = {}

    # ---- MP4: cover full run, playback speed ~= time_per_second (sim units / s)
    if "mp4" in args.formats:
        stride = max(1, round(args.time_per_second / (run.save_interval * args.mp4_fps)))
        idx = frame_indices(total, stride)
        fig, scatter, info = build_figure(run, args.vmin, args.vmax, args.colormap, args.node_size, title)

        def update(fi: int):
            scatter.set_array(run.v[fi])
            info.set_text(info_text(run, fi))
            return scatter, info

        anim = FuncAnimation(fig, update, frames=idx, blit=False)
        mp4_path = mp4_dir / f"{args.label}.mp4"
        anim.save(str(mp4_path), writer="ffmpeg", fps=args.mp4_fps, dpi=args.dpi_mp4)
        plt.close(fig)
        speed = run.save_interval * stride * args.mp4_fps
        result["mp4"] = (mp4_path, len(idx), len(idx) / args.mp4_fps, speed)

    # ---- GIF: compact looping preview of the full evolution
    if "gif" in args.formats:
        target = max(2, args.gif_seconds * args.gif_fps)
        stride = max(1, round(total / target))
        idx = frame_indices(total, stride)
        fig, scatter, info = build_figure(run, args.vmin, args.vmax, args.colormap, args.node_size, title)

        def update_gif(fi: int):
            scatter.set_array(run.v[fi])
            info.set_text(info_text(run, fi))
            return scatter, info

        anim = FuncAnimation(fig, update_gif, frames=idx, blit=False)
        gif_path = gif_dir / f"{args.label}.gif"
        anim.save(str(gif_path), writer=PillowWriter(fps=args.gif_fps), dpi=args.dpi_gif)
        plt.close(fig)
        speed = run.save_interval * stride * args.gif_fps
        result["gif"] = (gif_path, len(idx), len(idx) / args.gif_fps, speed)

    # ---- PNG stills: initial, representative (transient) and final (for slides / PDF)
    if "png" in args.formats:
        rep_fi = int(np.argmin(np.abs(run.times - args.rep_time)))
        for tag, fi in (("inicio", 0), ("medio", rep_fi), ("final", total - 1)):
            fig, scatter, info = build_figure(run, args.vmin, args.vmax, args.colormap, args.node_size, title)
            scatter.set_array(run.v[fi])
            info.set_text(info_text(run, fi))
            png_path = png_dir / f"{args.label}_{tag}.png"
            fig.savefig(str(png_path), dpi=args.dpi_mp4)
            plt.close(fig)
            result[f"png_{tag}"] = png_path

    return result


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Circular potential animation (FHN, TP5 Sistema 2).")
    p.add_argument("--run-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--label", required=True, help="filename stem, e.g. completa_K0.50")
    p.add_argument("--title", default=None, help="plot title; defaults to topology + params")
    p.add_argument("--formats", default="mp4,gif,png", help="comma list: mp4,gif,png")
    p.add_argument("--vmin", type=float, default=-2.0)
    p.add_argument("--vmax", type=float, default=2.0)
    p.add_argument("--colormap", default="coolwarm")
    p.add_argument("--node-size", type=float, default=38.0)
    p.add_argument("--time-per-second", type=float, default=4.0,
                   help="MP4 playback: simulation time units shown per real second (4 = x4)")
    p.add_argument("--mp4-fps", type=int, default=20)
    p.add_argument("--dpi-mp4", type=int, default=110)
    p.add_argument("--gif-seconds", type=float, default=18.0, help="approx GIF duration")
    p.add_argument("--gif-fps", type=int, default=12)
    p.add_argument("--dpi-gif", type=int, default=80)
    p.add_argument("--rep-time", type=float, default=40.0,
                   help="sim time for the representative 'medio' still (shows the transient)")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    args.formats = [f.strip() for f in args.formats.split(",") if f.strip()]
    t0 = time.time()
    run = load_run(args.run_dir)
    title = args.title or default_title(run)
    print(f"Loaded {args.run_dir}: N={run.n}, frames={run.v.shape[0]}, "
          f"T={run.total_time:g}, load={time.time()-t0:.1f}s", flush=True)
    result = render(run, args, args.output_dir, title)
    for key, val in result.items():
        if isinstance(val, tuple):
            path, nframes, dur, speed = val
            print(f"  {key:4s} -> {path.name}: {nframes} frames, {dur:.1f}s, x{speed:.0f} ({speed:g} u/s)", flush=True)
        else:
            print(f"  {key:9s} -> {val.name}", flush=True)
    print(f"DONE {args.label} in {time.time()-t0:.1f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
