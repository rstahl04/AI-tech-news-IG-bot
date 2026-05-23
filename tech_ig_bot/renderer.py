from __future__ import annotations

import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .caption import make_card_caption, make_instagram_caption
from .headline import make_technology_headline
from .models import Article

CANVAS_SIZE = (1080, 1350)
MARGIN = 72
FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/Library/Fonts/Arial.ttf",
)
FONT_BOLD_CANDIDATES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/Library/Fonts/Arial Bold.ttf",
)


def render_article_post(article: Article, output_dir: Path, index: int = 1) -> dict[str, Path]:
    """Render a square-ish Instagram portrait post and companion text files."""

    output_dir.mkdir(parents=True, exist_ok=True)
    headline = make_technology_headline(article)
    slug = _slugify(headline)[:72] or f"post-{index}"
    base = output_dir / f"{index:02d}-{slug}"

    card_caption = make_card_caption(article)
    instagram_caption = make_instagram_caption(article)
    image = _build_image(article, card_caption, headline)

    image_path = base.with_suffix(".png")
    caption_path = base.with_suffix(".caption.txt")
    metadata_path = base.with_suffix(".json")

    image.save(image_path)
    caption_path.write_text(instagram_caption + "\n", encoding="utf-8")
    metadata_path.write_text(
        json.dumps(
            {
                "title": headline,
                "original_title": article.title,
                "source": article.source,
                "url": article.url,
                "published": article.published,
                "score": article.score,
                "image": str(image_path),
                "caption": str(caption_path),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return {"image": image_path, "caption": caption_path, "metadata": metadata_path}


def _build_image(article: Article, card_caption: str, headline: str) -> Image.Image:
    image = Image.new("RGB", CANVAS_SIZE, "#0b1020")
    draw = ImageDraw.Draw(image)
    _draw_gradient(draw)
    _draw_decorative_shapes(draw)

    label_font = _font(34, bold=True)
    source_font = _font(30)
    headline_font = _font(72, bold=True)
    body_font = _font(40)
    footer_font = _font(26)

    draw.rounded_rectangle((MARGIN, 70, 690, 132), radius=30, fill="#00f5d4")
    draw.text((MARGIN + 28, 88), "STOP SCROLLING", fill="#08111f", font=label_font)

    source_line = f"REAL TECH NEWS / {article.source.upper()}"
    if article.display_date:
        source_line += f"  |  {article.display_date.upper()}"
    draw.text((MARGIN, 162), source_line, fill="#c8d3ff", font=source_font)

    headline_box = (MARGIN, 245, CANVAS_SIZE[0] - MARGIN, 665)
    _draw_wrapped_text(
        draw,
        headline,
        headline_box,
        headline_font,
        fill="#ffffff",
        line_spacing=12,
    )

    caption_box = (MARGIN, 750, CANVAS_SIZE[0] - MARGIN, 1210)
    draw.rounded_rectangle(caption_box, radius=42, fill="#f7f9ff")
    draw.text(
        (caption_box[0] + 42, caption_box[1] + 38),
        "Why this matters",
        fill="#101828",
        font=_font(34, bold=True),
    )
    _draw_wrapped_text(
        draw,
        card_caption,
        (caption_box[0] + 42, caption_box[1] + 96, caption_box[2] - 42, caption_box[3] - 38),
        body_font,
        fill="#273041",
        line_spacing=8,
    )

    draw.text(
        (MARGIN, 1260),
        "Source-linked tech explainer - verify before posting",
        fill="#98a2b3",
        font=footer_font,
    )
    return image


def _draw_gradient(draw: ImageDraw.ImageDraw) -> None:
    width, height = CANVAS_SIZE
    for y in range(height):
        ratio = y / height
        red = int(11 + ratio * 35)
        green = int(16 + ratio * 18)
        blue = int(32 + ratio * 70)
        draw.line((0, y, width, y), fill=(red, green, blue))


def _draw_decorative_shapes(draw: ImageDraw.ImageDraw) -> None:
    draw.ellipse((690, 90, 1160, 560), fill="#1e3a8a")
    draw.ellipse((760, 170, 1090, 500), fill="#7c3aed")
    draw.ellipse((-160, 560, 260, 980), fill="#0f766e")
    draw.line((72, 705, 1008, 705), fill="#00f5d4", width=5)


def _draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    box: tuple[int, int, int, int],
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: str,
    line_spacing: int = 0,
) -> None:
    left, top, right, bottom = box
    max_width = right - left
    lines = _wrap_text(draw, text, font, max_width)
    line_height = _line_height(draw, font) + line_spacing

    y = top
    for line in lines:
        if y + line_height > bottom:
            draw.text((left, y), "...", fill=fill, font=font)
            return
        draw.text((left, y), line, fill=fill, font=font)
        y += line_height


def _wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []

    for word in words:
        candidate = " ".join([*current, word])
        if _text_width(draw, candidate, font) <= max_width or not current:
            current.append(word)
            continue
        lines.append(" ".join(current))
        current = [word]

    if current:
        lines.append(" ".join(current))
    return lines


def _text_width(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
) -> int:
    left, _, right, _ = draw.textbbox((0, 0), text, font=font)
    return right - left


def _line_height(
    draw: ImageDraw.ImageDraw,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
) -> int:
    _, top, _, bottom = draw.textbbox((0, 0), "Ag", font=font)
    return bottom - top


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = FONT_BOLD_CANDIDATES if bold else FONT_CANDIDATES
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def _slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")
