from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

STANDARD_WARNING = (
    "GOVERNMENT WARNING: (1) ACCORDING TO THE SURGEON GENERAL, WOMEN SHOULD NOT DRINK "
    "ALCOHOLIC BEVERAGES DURING PREGNANCY BECAUSE OF THE RISK OF BIRTH DEFECTS. "
    "(2) CONSUMPTION OF ALCOHOLIC BEVERAGES IMPAIRS YOUR ABILITY TO DRIVE A CAR OR "
    "OPERATE MACHINERY, AND MAY CAUSE HEALTH PROBLEMS."
)


def draw_label(path: Path, brand: str, abv: str, warning: str) -> None:
    image = Image.new("RGB", (1200, 1800), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    lines = [
        f"BRAND NAME: {brand}",
        "CLASS/TYPE: WHISKEY",
        f"ALCOHOL CONTENT: {abv}",
        "NET CONTENTS: 750 ML",
        warning,
    ]

    y = 80
    for line in lines:
        draw.multiline_text((80, y), line, fill="black", font=font, spacing=6)
        y += 120 if len(line) < 90 else 220

    image.save(path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic alcohol label images.")
    parser.add_argument("--output", default="sample_labels", help="Output directory")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    draw_label(output_dir / "label-good.png", "STONE'S THROW", "45% ALC/VOL", STANDARD_WARNING)
    draw_label(output_dir / "label-warning-fail.png", "STONE'S THROW", "45% Alc./Vol.", "Government Warning missing")
    draw_label(output_dir / "label-brand-variant.png", "Stone’s Throw", "45% ALC/VOL", STANDARD_WARNING)


if __name__ == "__main__":
    main()
