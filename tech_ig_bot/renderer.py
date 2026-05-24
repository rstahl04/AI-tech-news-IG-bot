from __future__ import annotations

import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .caption import make_card_caption, make_instagram_caption
from .headline import make_technology_headline
from .image_generation import generate_story_image
from .models import Article
from .visuals import draw_story_visual

CANVAS_SIZE = (1080, 1350)
MARGIN = 64
HIGHLIGHT_GREEN = "#39ff14"
HIGHLIGHT_WORDS = {
    "ai",
    "artificial",
    "battery",
    "breakthrough",
    "built",
    "change",
    "cheaper",
    "chip",
    "chips",
    "climate",
    "computer",
    "computers",
    "computing",
    "dna",
    "energy",
    "faster",
    "future",
    "human",
    "humanoid",
    "major",
    "muscle",
    "prototype",
    "quantum",
    "record",
    "revolutionize",
    "robot",
    "robots",
    "scientists",
    "space",
    "stunned",
    "sunlight",
    "tech",
    "technology",
    "touch",
    "transform",
}
HIGHLIGHT_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "anyway",
    "be",
    "by",
    "can",
    "could",
    "for",
    "from",
    "good",
    "in",
    "is",
    "it",
    "just",
    "new",
    "next",
    "of",
    "on",
    "or",
    "set",
    "the",
    "this",
    "to",
    "vs",
    "what",
    "with",
}
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


def render_article_post(
    article: Article,
    output_dir: Path,
    index: int = 1,
    image_mode: str = "ai",
) -> dict[str, Path]:
    """Render an Instagram portrait post and companion text files."""

    output_dir.mkdir(parents=True, exist_ok=True)
    headline = make_technology_headline(article)
    slug = _slugify(headline)[:72] or f"post-{index}"
    base = output_dir / f"{index:02d}-{slug}"

    card_caption = make_card_caption(article)
    instagram_caption = make_instagram_caption(article)
    image, metadata = _build_image(article, card_caption, headline, image_mode=image_mode)
    highlighted_words = _highlighted_words(headline)

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
                **metadata,
                "highlighted_words": highlighted_words,
                "image": str(image_path),
                "caption": str(caption_path),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return {"image": image_path, "caption": caption_path, "metadata": metadata_path}


def _build_image(
    article: Article,
    card_caption: str,
    headline: str,
    image_mode: str = "ai",
) -> tuple[Image.Image, dict[str, str]]:
    prompt = ""
    image_provider = "procedural"
    visual_style = "procedural"

    if image_mode == "ai":
        generated, image_provider, prompt = generate_story_image(article, headline, CANVAS_SIZE)
        if generated is not None:
            image = generated
            visual_style = "ai-generated"
        else:
            image, visual_style = _procedural_background(article, headline)
    else:
        image, visual_style = _procedural_background(article, headline)
        image_provider = "procedural"

    draw = ImageDraw.Draw(image)
    _draw_readability_overlays(image)
    draw = ImageDraw.Draw(image)
    _draw_top_chrome(draw, article)
    _draw_headline(draw, headline)
    _draw_micro_explainer(draw, card_caption)
    _draw_footer(draw, article)

    return image, {
        "image_provider": image_provider,
        "image_prompt": prompt,
        "visual_style": visual_style,
    }


def _procedural_background(article: Article, headline: str) -> tuple[Image.Image, str]:
    image = Image.new("RGB", CANVAS_SIZE, "#0b1020")
    draw = ImageDraw.Draw(image)
    _draw_gradient(draw)
    _draw_decorative_shapes(draw)
    visual_style = draw_story_visual(image, article, headline)
    return image, visual_style


def _draw_readability_overlays(image: Image.Image) -> None:
    overlay = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    width, height = CANVAS_SIZE

    # Darken the top for source chrome and the bottom for the viral headline.
    for y in range(height):
        top_alpha = max(0, int(170 * (1 - y / 420))) if y < 420 else 0
        bottom_alpha = max(0, int(230 * ((y - 530) / (height - 530)))) if y > 530 else 0
        alpha = min(245, max(top_alpha, bottom_alpha))
        if alpha:
            draw.line((0, y, width, y), fill=(0, 0, 0, alpha))

    draw.rectangle((0, 0, width, height), outline=(255, 255, 255, 24), width=2)
    image.paste(Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB"))


def _draw_top_chrome(draw: ImageDraw.ImageDraw, article: Article) -> None:
    pill_font = _font(28, bold=True)
    source_font = _font(25, bold=True)
    draw.rounded_rectangle((MARGIN, 54, 445, 112), radius=29, fill=HIGHLIGHT_GREEN)
    draw.text((MARGIN + 24, 70), "REAL TECH NEWS", fill="#07111f", font=pill_font)

    source_line = article.source.upper()
    if article.display_date:
        source_line += f"  /  {article.display_date.upper()}"
    source_line = _truncate_for_width(draw, source_line, source_font, CANVAS_SIZE[0] - MARGIN * 2)
    draw.text((MARGIN, 136), source_line, fill="#dbeafe", font=source_font)


def _draw_headline(draw: ImageDraw.ImageDraw, headline: str) -> None:
    headline_font = _font(78, bold=True)
    box = (MARGIN, 745, CANVAS_SIZE[0] - MARGIN, 1095)
    _draw_wrapped_highlighted_text(
        draw,
        headline,
        box,
        headline_font,
        fill="#ffffff",
        highlight_fill=HIGHLIGHT_GREEN,
        line_spacing=10,
        shadow=True,
    )


def _draw_micro_explainer(draw: ImageDraw.ImageDraw, card_caption: str) -> None:
    font = _font(31)
    text = _first_sentence(card_caption, max_chars=155)
    box = (MARGIN, 1116, CANVAS_SIZE[0] - MARGIN, 1218)
    _draw_wrapped_text(draw, text, box, font, fill="#dbeafe", line_spacing=5, shadow=True)


def _draw_footer(draw: ImageDraw.ImageDraw, article: Article) -> None:
    footer_font = _font(25, bold=True)
    text = "FOLLOW FOR TECH EXPLAINED  /  VERIFY SOURCE BEFORE POSTING"
    if True:
        for offset in ((4, 4), (2, 2), (0, 5)):
            draw.text((MARGIN + offset[0], 1270 + offset[1]), text, fill=(0, 0, 0), font=footer_font)
        draw.text((MARGIN, 1270), text, fill="#ffffff", font=footer_font)


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


def _draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    box: tuple[int, int, int, int],
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: str,
    line_spacing: int = 0,
    shadow: bool = False,
) -> None:
    left, top, right, bottom = box
    max_width = right - left
    lines = _wrap_text(draw, text, font, max_width)
    line_height = _line_height(draw, font) + line_spacing
    highlight_words = {_normalize_highlight_word(word) for word in _highlighted_words(text)}

    y = top
    for line in lines:
        if y + line_height > bottom:
            if shadow:
                draw.text((left + 3, y + 3), "...", fill="#000000", font=font)
            draw.text((left, y), "...", fill=fill, font=font)
            return
        if shadow:
            for offset in ((4, 4), (2, 2), (0, 5)):
                draw.text((left + offset[0], y + offset[1]), line, fill=(0, 0, 0), font=font)
        draw.text((left, y), line, fill=fill, font=font)
        y += line_height


def _draw_wrapped_highlighted_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    box: tuple[int, int, int, int],
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: str,
    highlight_fill: str,
    line_spacing: int = 0,
    shadow: bool = False,
) -> None:
    left, top, right, bottom = box
    max_width = right - left
    lines = _wrap_text(draw, text, font, max_width)
    line_height = _line_height(draw, font) + line_spacing
    highlight_words = {_normalize_highlight_word(word) for word in _highlighted_words(text)}

    y = top
    for line in lines:
        if y + line_height > bottom:
            _draw_inline_highlighted_text(
                draw,
                "...",
                (left, y),
                font,
                fill=fill,
                highlight_fill=highlight_fill,
                highlight_words=highlight_words,
                shadow=shadow,
            )
            return
        _draw_inline_highlighted_text(
            draw,
            line,
            (left, y),
            font,
            fill=fill,
            highlight_fill=highlight_fill,
            highlight_words=highlight_words,
            shadow=shadow,
        )
        y += line_height


def _draw_inline_highlighted_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    position: tuple[int, int],
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: str,
    highlight_fill: str,
    highlight_words: set[str] | None = None,
    shadow: bool = False,
) -> None:
    x, y = position
    words = text.split()
    space_width = _text_width(draw, " ", font)
    for index, word in enumerate(words):
        word_fill = highlight_fill if _is_highlight_word(word, highlight_words) else fill
        if shadow:
            for offset in ((4, 4), (2, 2), (0, 5)):
                draw.text((x + offset[0], y + offset[1]), word, fill=(0, 0, 0), font=font)
        draw.text((x, y), word, fill=word_fill, font=font)
        x += _text_width(draw, word, font)
        if index < len(words) - 1:
            x += space_width


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


def _truncate_for_width(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    max_width: int,
) -> str:
    if _text_width(draw, text, font) <= max_width:
        return text
    words = text.split()
    while words and _text_width(draw, " ".join(words) + "...", font) > max_width:
        words.pop()
    return " ".join(words) + "..."


def _first_sentence(value: str, max_chars: int) -> str:
    value = value.strip()
    for marker in (". ", "! ", "? "):
        index = value.find(marker)
        if 0 < index <= max_chars:
            return value[: index + 1]
    if len(value) <= max_chars:
        return value
    return " ".join(value[:max_chars].split()[:-1]).rstrip(" ,;:-") + "..."


def _highlighted_words(text: str) -> list[str]:
    words: list[str] = []
    seen: set[str] = set()
    fallback_candidates: list[str] = []
    for word in text.split():
        normalized = _normalize_highlight_word(word)
        cleaned = word.strip(".,:;!?()[]{}\"'").strip()
        if not cleaned or normalized in seen:
            continue
        if normalized in HIGHLIGHT_WORDS:
            words.append(cleaned)
            seen.add(normalized)
            continue
        if _is_fallback_highlight_candidate(cleaned):
            fallback_candidates.append(cleaned)

    for word in sorted(fallback_candidates, key=_fallback_highlight_score, reverse=True):
        normalized = _normalize_highlight_word(word)
        if normalized in seen:
            continue
        words.append(word)
        seen.add(normalized)
        if len(words) >= 4:
            break
    return words


def _is_highlight_word(word: str, highlight_words: set[str] | None = None) -> bool:
    normalized = _normalize_highlight_word(word)
    if highlight_words is not None:
        return normalized in highlight_words
    return normalized in {_normalize_highlight_word(highlight) for highlight in _highlighted_words(word)}


def _is_fallback_highlight_candidate(word: str) -> bool:
    normalized = _normalize_highlight_word(word)
    return (
        len(normalized) >= 5
        and normalized not in HIGHLIGHT_STOP_WORDS
        and not normalized.isdigit()
    )


def _fallback_highlight_score(word: str) -> tuple[int, int]:
    normalized = _normalize_highlight_word(word)
    title_case_bonus = 2 if word[:1].isupper() else 0
    length_bonus = min(len(normalized), 12)
    return (title_case_bonus + length_bonus, len(normalized))


def _normalize_highlight_word(word: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", word.lower())


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
