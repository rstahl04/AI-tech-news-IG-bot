from __future__ import annotations

from .headline import make_technology_headline
from .models import Article
from .text import sentence_case_trim


DEFAULT_HASHTAGS: tuple[str, ...] = (
    "#EmergingTech",
    "#Innovation",
    "#TechNews",
    "#FutureTech",
    "#Breakthrough",
    "#AI",
)


def make_card_caption(article: Article, max_chars: int = 390) -> str:
    """Create the explanatory paragraph shown inside the image."""

    base = article.content or article.summary
    if not base:
        base = (
            "This story is gaining attention because it points to a practical "
            "step forward in how new technology may be researched, built, or used."
        )
    return sentence_case_trim(base, max_chars=max_chars)


def make_instagram_caption(article: Article, max_chars: int = 1200) -> str:
    """Create a longer caption to paste into the Instagram post body."""

    explainer = make_card_caption(article, max_chars=650)
    parts = [
        make_technology_headline(article),
        "",
        f"Why it matters: {explainer}",
        "",
        f"Source: {article.source}",
    ]
    if article.url:
        parts.append(article.url)
    parts.extend(["", " ".join(DEFAULT_HASHTAGS)])

    caption = "\n".join(parts).strip()
    if len(caption) <= max_chars:
        return caption

    clipped = sentence_case_trim(caption, max_chars=max_chars)
    return clipped.replace(" Why it matters:", "\n\nWhy it matters:")
