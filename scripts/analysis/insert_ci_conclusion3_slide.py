#!/usr/bin/env python3
"""Insert the conclusion-3 initial-condition slide into the TP5 presentation PDF."""
from __future__ import annotations

import argparse
import io
import shutil
from pathlib import Path

from matplotlib import font_manager
from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.pagesizes import landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT_DIR = Path(__file__).resolve().parents[2]
PAGE_SIZE = (720, 405)
DARK = HexColor("#344154")
BLUE = HexColor("#60c9e4")
LIGHT_BLUE = HexColor("#cfe1f5")
PALE_BLUE = HexColor("#e8eefb")
PERIWINKLE = HexColor("#9db7f1")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Insert the CI contrast slide into the presentation PDF.")
    parser.add_argument(
        "--input-pdf",
        type=Path,
        default=Path("SdS_TP5_2026Q1G01CS2_Presentación.pdf"),
    )
    parser.add_argument(
        "--output-pdf",
        type=Path,
        default=Path("SdS_TP5_2026Q1G01CS2_Presentación.pdf"),
    )
    parser.add_argument(
        "--figure",
        type=Path,
        default=Path("results/2026-06-11_ci-conclusion3_v1/slide_ci_sigma_vs_t.png"),
    )
    parser.add_argument(
        "--slide-pdf",
        type=Path,
        default=Path("tmp/ci-conclusion3/slide_ci_conclusion3.pdf"),
    )
    parser.add_argument("--insert-after-page", type=int, default=32)
    return parser


def register_fonts() -> None:
    regular = next(f.fname for f in font_manager.fontManager.ttflist if f.name == "DejaVu Sans")
    bold = next(f.fname for f in font_manager.fontManager.ttflist if f.name == "DejaVu Sans" and "Bold.ttf" in f.fname)
    pdfmetrics.registerFont(TTFont("DeckSans", regular))
    pdfmetrics.registerFont(TTFont("DeckSans-Bold", bold))


def hexagon(c: canvas.Canvas, cx: float, cy: float, r: float, color: Color, alpha: float = 1.0) -> None:
    import math

    points = []
    for idx in range(6):
        angle = math.radians(30 + 60 * idx)
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    path = c.beginPath()
    path.moveTo(*points[0])
    for point in points[1:]:
        path.lineTo(*point)
    path.close()
    c.saveState()
    c.setFillColor(color, alpha=alpha)
    c.setStrokeColor(white, alpha=0.0)
    c.drawPath(path, fill=1, stroke=0)
    c.restoreState()


def draw_chrome(c: canvas.Canvas) -> None:
    hexagon(c, -6, 357, 48, BLUE)
    hexagon(c, 54, 401, 38, LIGHT_BLUE)
    hexagon(c, 691, 385, 43, LIGHT_BLUE)
    hexagon(c, 733, 345, 38, PERIWINKLE)
    hexagon(c, 706, 40, 43, BLUE)
    hexagon(c, 662, -3, 38, PALE_BLUE)
    hexagon(c, 15, 38, 43, PERIWINKLE)
    hexagon(c, 58, -3, 38, LIGHT_BLUE)


def draw_text(c: canvas.Canvas, text: str, x: float, y: float, size: float, *, bold: bool = False) -> None:
    c.setFillColor(DARK)
    c.setFont("DeckSans-Bold" if bold else "DeckSans", size)
    c.drawString(x, y, text)


def draw_multiline(c: canvas.Canvas, lines: list[str], x: float, y: float, size: float, leading: float) -> None:
    c.setFillColor(DARK)
    c.setFont("DeckSans", size)
    for idx, line in enumerate(lines):
        c.drawString(x, y - idx * leading, line)


def build_slide_pdf(figure: Path, slide_pdf: Path) -> None:
    slide_pdf.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(slide_pdf), pagesize=landscape(PAGE_SIZE))
    draw_chrome(c)

    draw_text(c, "Resultados", 44, 366, 17, bold=True)
    draw_text(c, "Efecto de la condición inicial", 44, 315, 33, bold=True)

    c.drawImage(ImageReader(str(figure)), 36, 48, width=515, height=265, preserveAspectRatio=True, mask="auto")

    draw_text(c, "Parámetros fijos", 565, 270, 13, bold=True)
    draw_multiline(c, ["N = 501", "K = 0", "T = 500", "15 realizaciones"], 565, 248, 12.5, 18)

    draw_text(c, "Números clave", 565, 158, 13, bold=True)
    draw_multiline(
        c,
        [
            "σᵥ(0):",
            "2,9×10⁻² (angosta)",
            "vs 2,9×10⁻¹ (ancha)",
            "",
            "sincronizan:",
            "15/15 vs 0/15",
        ],
        565,
        136,
        11.2,
        16,
    )

    c.setFillColorRGB(0, 0, 0)
    c.setFont("DeckSans", 11)
    c.drawRightString(710, 12, "33")
    c.showPage()
    c.save()


def number_overlay(number: int) -> object:
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=landscape(PAGE_SIZE))
    c.setFillColor(white)
    c.rect(682, 4, 34, 24, fill=1, stroke=0)
    c.setFillColorRGB(0, 0, 0)
    c.setFont("DeckSans", 11)
    c.drawRightString(710, 12, str(number))
    c.save()
    packet.seek(0)
    return PdfReader(packet).pages[0]


def insert_slide(input_pdf: Path, output_pdf: Path, slide_pdf: Path, insert_after_page: int) -> bool:
    reader = PdfReader(str(input_pdf))
    if len(reader.pages) > insert_after_page:
        next_page_text = reader.pages[insert_after_page].extract_text() or ""
        if "Efecto de la condición inicial" in next_page_text:
            if input_pdf != output_pdf:
                shutil.copyfile(input_pdf, output_pdf)
            print("slide already present; not inserting a duplicate")
            return False

    slide = PdfReader(str(slide_pdf)).pages[0]
    writer = PdfWriter()

    for idx, page in enumerate(reader.pages, start=1):
        writer.add_page(page)
        if idx == insert_after_page:
            writer.add_page(slide)

    # Existing pages 33 and 34 become 34 and 35 after insertion.
    writer.pages[33].merge_page(number_overlay(34))
    writer.pages[34].merge_page(number_overlay(35))

    tmp = output_pdf.with_suffix(output_pdf.suffix + ".tmp")
    with tmp.open("wb") as f:
        writer.write(f)
    tmp.replace(output_pdf)
    return True


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    input_pdf = ROOT_DIR / args.input_pdf
    output_pdf = ROOT_DIR / args.output_pdf
    figure = ROOT_DIR / args.figure
    slide_pdf = ROOT_DIR / args.slide_pdf

    if not input_pdf.exists():
        raise SystemExit(f"ERROR: missing input PDF: {input_pdf}")
    if not figure.exists():
        raise SystemExit(f"ERROR: missing figure: {figure}")

    register_fonts()
    build_slide_pdf(figure, slide_pdf)
    inserted = insert_slide(input_pdf, output_pdf, slide_pdf, args.insert_after_page)
    print(f"slide_pdf: {args.slide_pdf}")
    print(f"updated_pdf: {args.output_pdf}")
    if inserted:
        print(f"inserted_slide_number: {args.insert_after_page + 1}")
    else:
        print(f"existing_slide_number: {args.insert_after_page + 1}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
