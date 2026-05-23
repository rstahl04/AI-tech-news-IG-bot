from __future__ import annotations

import re

from .models import Article
from .text import clean_text, sentence_case_trim


NOISE_TERMS = (
    "hall of fame",
    "superfans",
    "fan engagement",
    "sports fans",
)


BUSINESS_TERMS = (
    "acquires",
    "acquisition",
    "raises",
    "funding",
    "ipo",
    "stock",
    "shares",
    "earnings",
    "revenue",
    "appoints",
    "award",
    "awards",
    "best use of",
    "partnership",
    "partners with",
    "press release",
    "wins",
)

TECH_TOPICS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bmobile manipulation\b", re.I), "mobile manipulation robots"),
    (re.compile(r"\bsolid[- ]state batter(?:y|ies)\b", re.I), "solid-state batteries"),
    (re.compile(r"\bquantum (?:chip|processor|comput(?:er|ing))\b", re.I), "quantum chips"),
    (re.compile(r"\bquantum batter(?:y|ies)\b", re.I), "quantum batteries"),
    (re.compile(r"\bhumanoid robots?\b", re.I), "humanoid robots"),
    (re.compile(r"\brobotics?\b|\brobots?\b", re.I), "robots"),
    (re.compile(r"\bai body map\b|\bbody map\b", re.I), "AI body maps"),
    (re.compile(r"\bartificial intelligence\b|\bai\b", re.I), "AI systems"),
    (re.compile(r"\bmachine learning\b", re.I), "machine learning"),
    (re.compile(r"\bfusion\b", re.I), "fusion energy"),
    (re.compile(r"\bbatter(?:y|ies)\b|\benergy storage\b", re.I), "battery technology"),
    (re.compile(r"\bsemiconductors?\b|\bchips?\b", re.I), "next-generation chips"),
    (re.compile(r"\bgene editing\b|\bcrispr\b", re.I), "gene editing"),
    (re.compile(r"\bbiotech\b|\bbiology\b", re.I), "biotech"),
    (re.compile(r"\bspace\b|\bpropulsion\b|\brocket\b", re.I), "space technology"),
    (re.compile(r"\bsolar\b|\brenewable\b|\bclimate\b", re.I), "clean energy technology"),
)


def make_technology_headline(article: Article, max_chars: int = 92) -> str:
    """Create a social headline focused on the technology, not the company wrapper."""

    title = _clean_source_title(article.title)
    context = " ".join(part for part in (title, article.summary, article.content) if part)
    topic = _extract_topic(context)
    title_lower = title.lower()

    if topic and _is_business_title(title_lower):
        verb = _verb(topic, singular="takes", plural="take")
        return _title_case(sentence_case_trim(f"{topic} {verb} a step toward real-world use", max_chars))

    lab_to_market = re.search(r"from lab to ([a-z -]+)", title, flags=re.I)
    if topic and lab_to_market:
        destination = clean_text(lab_to_market.group(1)).rstrip(".")
        return _title_case(
            sentence_case_trim(
                f"{topic} {_verb(topic, singular="is", plural="are")} moving from lab promise to {destination}",
                max_chars,
            )
        )

    breakthrough_topic = _extract_breakthrough_topic(title)
    if breakthrough_topic:
        return _title_case(
            sentence_case_trim(
                f"A breakthrough in {breakthrough_topic} points to real-world impact",
                max_chars,
            )
        )

    reveal_match = re.search(r"\b(?:new )?(ai|artificial intelligence).*\breveals?\b(.+)", title, re.I)
    if reveal_match:
        return _title_case(sentence_case_trim(f"AI reveals {clean_text(reveal_match.group(2))}", max_chars))

    if topic and "breakthrough" in title_lower:
        return _title_case(sentence_case_trim(f"{topic} breakthrough points to real-world impact", max_chars))

    if topic and _starts_with_company_style(title):
        return _title_case(sentence_case_trim(f"{topic} could be the bigger story behind this news", max_chars))

    return sentence_case_trim(title, max_chars)


def technology_focus_score(article: Article) -> float:
    """Positive score for technology substance, negative for business-first framing."""

    title = article.title.lower()
    text = article.searchable_text.lower()
    score = 0.0

    if _extract_topic(text):
        score += 5.0
    if "breakthrough" in title and "award" not in title:
        score += 2.0
    matched_business_terms = sum(1 for term in BUSINESS_TERMS if term in title)
    if matched_business_terms:
        score -= 18.0 * matched_business_terms
    score -= 25.0 * sum(1 for term in NOISE_TERMS if term in title)
    if re.search(r"\b(?:uses|using)\b.*\b(?:ai|artificial intelligence)\b", title) and not re.search(
        r"\b(?:breakthrough|prototype|research|discovers?|reveals?|demonstrates?)\b",
        title,
    ):
        score -= 10.0
    if _is_business_title(title):
        score -= 10.0
    if _starts_with_company_style(article.title) and "breakthrough" not in title:
        score -= 4.0
    return score


def technology_topic(article: Article) -> str:
    """Return the main technology topic detected in an article."""

    return _extract_topic(article.searchable_text)


def _extract_topic(text: str) -> str:
    for pattern, topic in TECH_TOPICS:
        if pattern.search(text):
            return topic
    return ""


def _extract_breakthrough_topic(title: str) -> str:
    if re.search(r"breakthrough\s+awards?\b|breakthrough\s+award\b", title, flags=re.I):
        return ""

    match = re.search(
        r"\b(?:makes|announces|unveils|reports|achieves|claims)\s+(.+?)\s+breakthroughs?\b",
        title,
        flags=re.I,
    )
    if match:
        topic = clean_text(match.group(1))
        return re.sub(r"^(a|an|new|major|huge|first)\s+", "", topic, flags=re.I).lower()

    match = re.search(r"breakthroughs?\s+(?:in|for)\s+([^,:;-]+)", title, flags=re.I)
    if match:
        return clean_text(match.group(1)).lower()

    match = re.search(r"([^,:;-]+)\s+breakthroughs?", title, flags=re.I)
    if match:
        topic = clean_text(match.group(1))
        topic = re.sub(r"^(new|major|huge|first)\s+", "", topic, flags=re.I)
        return topic.lower()
    return ""


def _clean_source_title(title: str) -> str:
    title = clean_text(title)
    title = re.sub(r"\s+[-|]\s+(?:[^-|]{2,40})$", "", title)
    title = re.sub(r"\s+", " ", title)
    return title.strip(" -")


def _is_business_title(title_lower: str) -> bool:
    return any(term in title_lower for term in BUSINESS_TERMS)


def _starts_with_company_style(title: str) -> bool:
    first_words = title.split()[:3]
    if not first_words:
        return False
    capitalized = sum(1 for word in first_words if word[:1].isupper())
    return capitalized >= 2


def _verb(topic: str, singular: str, plural: str) -> str:
    singular_topics = {
        "battery technology",
        "biotech",
        "clean energy technology",
        "fusion energy",
        "machine learning",
        "space technology",
    }
    return plural if topic.endswith("s") and topic not in singular_topics else singular


def _title_case(value: str) -> str:
    small_words = {"a", "an", "and", "as", "at", "for", "in", "of", "on", "or", "the", "to"}
    words = value.split()
    titled: list[str] = []
    for index, word in enumerate(words):
        if word.isupper():
            titled.append(word)
        elif index > 0 and word.lower() in small_words:
            titled.append(word.lower())
        else:
            titled.append("-".join(part[:1].upper() + part[1:] for part in word.split("-")))
    return " ".join(titled)
