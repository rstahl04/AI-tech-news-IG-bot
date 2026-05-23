from __future__ import annotations

from .headline import make_technology_headline, technology_topic
from .models import Article
from .text import sentence_case_trim


TOPIC_EXPLAINERS: dict[str, str] = {
    "AI body maps": "AI body maps use machine learning to spot patterns in complex biological data, helping researchers see links that are hard to catch manually.",
    "AI systems": "AI systems use data and models to recognize patterns, make predictions, or help people complete tasks more quickly.",
    "battery technology": "Battery technology is about storing more energy, charging faster, and making devices, cars, and grids more reliable.",
    "biotech": "Biotech applies engineering and computing ideas to biology, medicine, agriculture, and materials.",
    "clean energy technology": "Clean energy technology aims to produce, store, or use power with fewer emissions and less waste.",
    "fusion energy": "Fusion energy tries to copy the reaction that powers stars, with the goal of producing huge amounts of clean power.",
    "gene editing": "Gene editing lets scientists make targeted changes to DNA, opening new paths for medicine and agriculture.",
    "humanoid robots": "Humanoid robots are machines shaped to work in spaces designed for people, from factories to homes.",
    "machine learning": "Machine learning helps computers improve at a task by finding patterns in examples instead of following only hand-written rules.",
    "mobile manipulation robots": "Mobile manipulation robots combine movement with robotic arms, letting machines navigate a space and physically handle objects.",
    "next-generation chips": "Next-generation chips improve how computers process data, which can unlock faster AI, better devices, and lower power use.",
    "quantum batteries": "Quantum batteries explore whether quantum physics can change how energy is stored, charged, or released.",
    "quantum chips": "Quantum chips use qubits instead of ordinary bits, which could eventually help solve some problems classical computers struggle with.",
    "robots": "Robots combine sensors, software, and hardware so machines can move through the world and complete physical tasks.",
    "solid-state batteries": "Solid-state batteries replace flammable liquid electrolytes with solid materials, which could make batteries safer, denser, and longer lasting.",
    "space technology": "Space technology pushes advances in propulsion, satellites, robotics, and materials that can also affect life on Earth.",
}


DEFAULT_HASHTAGS: tuple[str, ...] = (
    "#technology",
    "#innovation",
    "#ai",
    "#futuretech",
    "#technews",
    "#reels",
)


def make_card_caption(article: Article, max_chars: int = 390) -> str:
    """Create the explanatory paragraph shown inside the image."""

    topic = technology_topic(article)
    intro = TOPIC_EXPLAINERS.get(
        topic,
        "This technology story points to a practical step forward in how new tools may be researched, built, or used.",
    )
    return sentence_case_trim(
        f"{intro} The source story is a current example of this technology moving from idea to impact.",
        max_chars=max_chars,
    )


def make_instagram_caption(article: Article, max_chars: int = 1200) -> str:
    """Create a longer caption to paste into the Instagram post body."""

    headline = make_technology_headline(article)
    explainer = make_card_caption(article, max_chars=520)
    parts = [
        "FOLLOW for tech explained simply every day 🧠🤖💫",
        "",
        headline,
        "",
        explainer,
        "",
        "Why people are watching: experts, researchers, and builders are racing to see "
        "whether this kind of technology can move from impressive demo to real-world use.",
        "",
        f"Via: {article.source}",
    ]
    if article.url:
        parts.append(article.url)
    parts.extend(["", " ".join(DEFAULT_HASHTAGS)])

    caption = "\n".join(parts).strip()
    if len(caption) <= max_chars:
        return caption

    clipped = sentence_case_trim(caption, max_chars=max_chars)
    return clipped.replace(" Why people are watching:", "\n\nWhy people are watching:")
