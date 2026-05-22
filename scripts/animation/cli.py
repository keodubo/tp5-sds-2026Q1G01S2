from __future__ import annotations

import argparse
from pathlib import Path


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


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    parser.parse_args(argv)
    return 0
