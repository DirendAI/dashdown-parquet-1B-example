#!/usr/bin/env python3
"""One-off generator for assets/social-card.png (the og:image link preview).

The card is committed to the repo (it changes rarely and shouldn't cost the
nightly build anything); rerun this script only when the headline or palette
changes:

    pip install pillow
    python .github/scripts/make_social_card.py

Needs the DejaVu fonts (preinstalled on Ubuntu runners and most Linux boxes).
Colors are the chart palette from dashdown.yaml so previews match the site.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
BG = "#0f172a"          # slate-900 — matches the dashboard's dark theme
FG = "#f8fafc"          # near-white headline
MUTED = "#94a3b8"       # slate-400 subtitle
AMBER = "#f59e0b"       # yellow-cab amber, brightened for the dark bg
# Series palette from dashdown.yaml: yellow cab, Uber, Lyft, green cab.
PALETTE = ["#d97706", "#4f6ef7", "#e8506e", "#2fa87c"]

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
OUT = Path(__file__).resolve().parents[2] / "assets" / "social-card.png"

# Stylized monthly-trips motif: the 2020 collapse and the long climb back,
# one line per service (relative heights, not real data).
SHAPES = [
    [0.62, 0.18, 0.24, 0.30, 0.34, 0.38, 0.42, 0.44, 0.46, 0.48, 0.50, 0.52],  # yellow
    [0.55, 0.30, 0.42, 0.52, 0.60, 0.66, 0.72, 0.76, 0.80, 0.84, 0.86, 0.88],  # uber
    [0.30, 0.14, 0.20, 0.26, 0.30, 0.33, 0.36, 0.38, 0.40, 0.41, 0.42, 0.43],  # lyft
    [0.18, 0.06, 0.08, 0.10, 0.11, 0.12, 0.12, 0.13, 0.13, 0.13, 0.14, 0.14],  # green
]


def main() -> None:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    bold = lambda s: ImageFont.truetype(str(FONT_DIR / "DejaVuSans-Bold.ttf"), s)
    reg = lambda s: ImageFont.truetype(str(FONT_DIR / "DejaVuSans.ttf"), s)

    # Line-chart motif across the lower half, behind the text.
    x0, x1, y0, y1 = 60, W - 60, 408, H - 96
    for shape, color in zip(SHAPES, PALETTE):
        pts = [
            (x0 + i * (x1 - x0) / (len(shape) - 1), y1 - v * (y1 - y0))
            for i, v in enumerate(shape)
        ]
        d.line(pts, fill=color, width=5, joint="curve")
        d.ellipse(
            [pts[-1][0] - 7, pts[-1][1] - 7, pts[-1][0] + 7, pts[-1][1] + 7],
            fill=color,
        )
    d.line([(x0, y1), (x1, y1)], fill="#1e293b", width=2)

    # Headline + subtitle.
    d.text((60, 72), "1.6 billion rides.", font=bold(76), fill=AMBER)
    d.text((60, 168), "One duck. Zero servers.", font=bold(76), fill=FG)
    d.text(
        (60, 286),
        "Every NYC yellow-cab, green-cab, Uber & Lyft trip since 2020 —",
        font=reg(31),
        fill=MUTED,
    )
    d.text(
        (60, 330),
        "DuckDB on raw TLC Parquet, rebuilt nightly. No warehouse, no ETL.",
        font=reg(31),
        fill=MUTED,
    )

    # Footer: site name, bottom-left.
    d.text((60, H - 64), "NYC Rides × DuckDB", font=bold(28), fill=MUTED)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, optimize=True)
    print(f"Wrote {OUT} ({OUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
