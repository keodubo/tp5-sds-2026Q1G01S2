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
    parse_options(argv)
    return 0
