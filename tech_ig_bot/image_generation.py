from __future__ import annotations

import hashlib
import logging
from io import BytesIO
from urllib.error import URLError
from urllib.parse import quote_plus, urlencode
from urllib.request import Request, urlopen

from PIL import Image

from .headline import technology_topic
from .models import Article

LOGGER = logging.getLogger(__name__)

POLLINATIONS_BASE_URL = "https://image.pollinations.ai/prompt/"
IMAGE_MODELS = ("flux", "turbo")

PROMPT_TEMPLATES: dict[str, str] = {
    "AI body maps": (
        "cinematic medical technology visualization, glowing human neural map, "
        "AI analyzing biological data, futuristic lab lighting, realistic, high detail"
    ),
    "AI systems": (
        "cinematic artificial intelligence command center, glowing neural network, "
        "human hands interacting with transparent data, realistic, dramatic lighting"
    ),
    "battery technology": (
        "futuristic battery cell glowing with green energy, clean laboratory prototype, "
        "macro photography, dramatic light, realistic technology editorial"
    ),
    "biotech": (
        "futuristic biotech laboratory, glowing microscope view, living cells and data overlays, "
        "realistic science photography, cinematic lighting"
    ),
    "clean energy technology": (
        "clean energy breakthrough, solar panels and wind turbines connected to glowing grid, "
        "sunrise, cinematic realistic technology photography"
    ),
    "fusion energy": (
        "fusion reactor core glowing like a tiny star, advanced energy laboratory, "
        "dramatic cinematic lighting, realistic science documentary style"
    ),
    "gene editing": (
        "CRISPR gene editing visualization, DNA strands glowing in a research lab, "
        "macro science photography, realistic and cinematic"
    ),
    "humanoid robots": (
        "humanoid robot hand with artificial muscle reaching toward a human hand, "
        "futuristic robotics lab, realistic, emotional cinematic lighting"
    ),
    "machine learning": (
        "machine learning system solving complex patterns, glowing data clusters over a workstation, "
        "realistic cinematic technology editorial"
    ),
    "mobile manipulation robots": (
        "mobile robot with robotic arm carefully handling objects in a warehouse, "
        "futuristic automation, realistic cinematic technology photography"
    ),
    "next-generation chips": (
        "macro photograph of next-generation computer chip, glowing circuits, wafer reflections, "
        "realistic semiconductor lab, cinematic lighting"
    ),
    "quantum batteries": (
        "quantum battery concept, glowing energy cells inside a futuristic laboratory, "
        "particles of light, realistic cinematic science image"
    ),
    "quantum chips": (
        "macro photograph of a glowing quantum photonic chip, lasers and fiber optics, "
        "advanced physics laboratory, realistic cinematic technology image"
    ),
    "robots": (
        "advanced robot learning a real-world task, sensors glowing, robotics lab, "
        "realistic cinematic technology photography"
    ),
    "solid-state batteries": (
        "solid-state battery prototype, layers of advanced materials glowing, electric vehicle lab, "
        "macro realistic cinematic technology image"
    ),
    "space technology": (
        "futuristic spacecraft technology, satellite propulsion test, Earth in background, "
        "realistic cinematic space engineering image"
    ),
}

DEFAULT_PROMPT = (
    "futuristic technology breakthrough, real-world prototype in a research lab, "
    "cinematic editorial photography, dramatic lighting, realistic, high detail"
)

NEGATIVE_PROMPT = "text, words, captions, logo, watermark, brand names, blurry, distorted, low quality"


def generate_story_image(
    article: Article,
    headline: str,
    size: tuple[int, int],
    timeout: float = 25.0,
) -> tuple[Image.Image | None, str, str]:
    """Fetch an AI-generated image related to the story, returning image/provider/prompt."""

    prompt = build_image_prompt(article, headline)
    seed = _seed(article, headline)
    for model in IMAGE_MODELS:
        params = urlencode(
            {
                "width": size[0],
                "height": size[1],
                "model": model,
                "nologo": "true",
                "enhance": "true",
                "seed": seed,
                "negative": NEGATIVE_PROMPT,
            }
        )
        url = f"{POLLINATIONS_BASE_URL}{quote_plus(prompt)}?{params}"
        try:
            request = Request(url, headers={"User-Agent": "TechInstagramBot/0.1"})
            with urlopen(request, timeout=timeout) as response:  # noqa: S310 - intentional image service call.
                data = response.read()
            image = Image.open(BytesIO(data)).convert("RGB")
            return image.resize(size, Image.Resampling.LANCZOS), f"pollinations:{model}", prompt
        except (OSError, URLError) as exc:
            LOGGER.warning("AI image generation failed with %s: %s", model, exc)
            continue

    LOGGER.warning("All AI image models failed, falling back to procedural art")
    return None, "procedural-fallback", prompt


def build_image_prompt(article: Article, headline: str) -> str:
    topic = technology_topic(article)
    visual = PROMPT_TEMPLATES.get(topic, DEFAULT_PROMPT)
    return (
        f"{visual}. Inspired by this news hook: {headline}. "
        "Instagram reels cover image, vertical 4:5 composition, strong focal point, "
        "high contrast, modern, cinematic teal and neon green color accents, "
        "consistent editorial tech style, no text, no logos, no watermark."
    )


def _seed(article: Article, headline: str) -> int:
    digest = hashlib.sha256(f"{article.url}|{article.title}|{headline}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16)
