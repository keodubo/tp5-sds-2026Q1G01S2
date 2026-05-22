from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from pathlib import Path

from .model import AnimationInputError, Metadata, RenderOptions


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
    parser.add_argument("--edge-width", type=float, default=0.8)
    parser.add_argument("--node-size", type=float, default=8.0)
    parser.add_argument("--colormap", default="coolwarm")
    parser.add_argument("--overwrite", action="store_true")
    return parser


def parse_options(argv: list[str] | None = None) -> RenderOptions:
    return _options_from_args(build_parser().parse_args(argv))


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
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        options = _options_from_args(args)
        from .io import load_run, read_metadata
        from .render import render_dashboard, render_network

        metadata = read_metadata(args.run_dir)
        paths = output_paths(metadata, options)
        network_available = options.only != "all" or (args.run_dir / "adjacency.csv").exists()
        planned = _planned_files(options.only, paths, network_available=network_available)

        if not options.overwrite:
            complete = [path for path in planned if path.exists() and path.stat().st_size > 0]
            existing = [path for path in planned if path.exists()]
            if len(complete) == len(planned):
                print(f"SKIP existing {paths.run_dir}")
                return 0
            if existing:
                names = ", ".join(str(path) for path in existing)
                raise AnimationInputError(f"partial outputs already exist without --overwrite: {names}")

        require_graph = options.only == "network"
        run = load_run(args.run_dir, require_graph=require_graph)
        if options.only == "all" and network_available:
            from .graph import build_graph_from_adjacency

            run = replace(run, graph_data=build_graph_from_adjacency(args.run_dir, run.metadata.n))
        elif options.only == "all":
            print(
                "SKIP network: adjacency.csv not found; regenerate with --save-adjacency to produce network outputs.",
                flush=True,
            )

        if options.only in ("network", "all"):
            if run.graph_data is not None:
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


def _options_from_args(args: argparse.Namespace) -> RenderOptions:
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


def _planned_files(
    only: str, paths: PlannedOutputPaths, *, network_available: bool = True
) -> list[Path]:
    if only == "network":
        return [paths.network_mp4, paths.network_png]
    if only == "dashboard":
        return [paths.dashboard_mp4, paths.dashboard_png]
    if not network_available:
        return [paths.dashboard_mp4, paths.dashboard_png]
    return [paths.network_mp4, paths.network_png, paths.dashboard_mp4, paths.dashboard_png]
