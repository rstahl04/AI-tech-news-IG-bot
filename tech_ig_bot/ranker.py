from __future__ import annotations

from collections.abc import Iterable
import re
from datetime import datetime, timezone

from .headline import make_technology_headline, technology_focus_score, technology_topic
from .models import Article, parse_datetime


KEYWORD_WEIGHTS: dict[str, float] = {
    "breakthrough": 5.0,
    "first": 3.5,
    "new": 1.4,
    "prototype": 2.2,
    "launch": 1.8,
    "unveils": 2.0,
    "discovers": 3.0,
    "record": 2.8,
    "milestone": 3.0,
    "could": 1.0,
    "future": 1.0,
    "ai": 3.0,
    "artificial intelligence": 3.0,
    "machine learning": 2.0,
    "robot": 2.5,
    "robotics": 2.5,
    "quantum": 3.5,
    "fusion": 3.5,
    "battery": 3.0,
    "semiconductor": 2.5,
    "chip": 2.0,
    "biotech": 2.4,
    "gene editing": 3.2,
    "space": 2.0,
    "climate": 2.0,
    "renewable": 2.0,
    "energy storage": 3.0,
}


def score_article(article: Article, now: datetime | None = None) -> float:
    text = article.searchable_text.lower()
    score = 0.0

    for keyword, weight in KEYWORD_WEIGHTS.items():
        pattern = re.compile(r"\b" + re.escape(keyword) + r"\b")
        count = len(pattern.findall(text))
        title_bonus = 1.6 if pattern.search(article.title.lower()) else 1.0
        score += count * weight * title_bonus

    if article.summary:
        score += 1.0
    if article.content:
        score += 1.5

    score += technology_focus_score(article)
    score += _recency_score(article, now=now)
    return round(score, 3)


def rank_articles(articles: Iterable[Article], limit: int = 5) -> list[Article]:
    ranked = list(articles)
    for article in ranked:
        article.score = score_article(article)
    ranked.sort(key=lambda item: item.score, reverse=True)

    unique: list[Article] = []
    duplicates: list[Article] = []
    seen_keys: set[str] = set()
    seen_articles: list[Article] = []
    for article in ranked:
        article_key = _article_key(article)
        if article_key in seen_keys or any(_is_near_duplicate_story(article, seen) for seen in seen_articles):
            duplicates.append(article)
            continue
        seen_keys.add(article_key)
        seen_articles.append(article)
        unique.append(article)

    diversified = _diversify_by_topic(unique, limit)
    if len(diversified) < limit:
        diversified.extend(article for article in duplicates if article not in diversified)
    return diversified[:limit]


def _diversify_by_topic(articles: list[Article], limit: int) -> list[Article]:
    selected: list[Article] = []
    remaining = list(articles)
    topic_counts: dict[str, int] = {}

    for article in list(remaining):
        topic = _topic_key(article)
        if article.score < _diversity_quality_floor(articles) or topic in topic_counts:
            continue
        selected.append(article)
        remaining.remove(article)
        topic_counts[topic] = 1
        if len(selected) == limit:
            return selected

    max_per_topic = max(2, limit // 4)
    while remaining and len(selected) < limit:
        made_progress = False
        for article in list(remaining):
            topic = _topic_key(article)
            if topic_counts.get(topic, 0) >= max_per_topic and _has_underrepresented_topic(
                remaining,
                topic_counts,
                max_per_topic,
            ):
                continue
            selected.append(article)
            remaining.remove(article)
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
            made_progress = True
            if len(selected) == limit:
                break
        if not made_progress:
            selected.extend(remaining[: limit - len(selected)])
            break
    return selected


def _diversity_quality_floor(articles: list[Article]) -> float:
    if len(articles) < 6:
        return 0.0
    return max(8.0, articles[min(len(articles) - 1, 9)].score * 0.4)


def _has_underrepresented_topic(
    articles: list[Article],
    topic_counts: dict[str, int],
    max_per_topic: int,
) -> bool:
    return any(topic_counts.get(_topic_key(article), 0) < max_per_topic for article in articles)


def _topic_key(article: Article) -> str:
    topic = technology_topic(article)
    if topic in {"quantum chips", "quantum batteries"}:
        return "quantum"
    if topic in {"AI systems", "AI body maps", "machine learning"}:
        return "ai"
    if topic in {"robots", "humanoid robots", "mobile manipulation robots"}:
        return "robotics"
    if topic in {"battery technology", "solid-state batteries"}:
        return "battery"
    if topic in {"clean energy technology", "fusion energy"}:
        return "energy"
    if topic in {"biotech", "gene editing"}:
        return "biotech"
    if topic == "next-generation chips":
        return "chips"
    if topic == "space technology":
        return "space"
    return topic or "other"


def _article_key(article: Article) -> str:
    return f"{_headline_key(make_technology_headline(article))}|{_headline_key(article.title)}"


def _is_near_duplicate_story(article: Article, other: Article) -> bool:
    article_tokens = _story_tokens(article)
    other_tokens = _story_tokens(other)
    if not article_tokens or not other_tokens:
        return False
    intersection = article_tokens & other_tokens
    union = article_tokens | other_tokens
    if len(intersection) >= 4 and len(intersection) / len(union) >= 0.24:
        return True
    duplicate_signal_groups = (
        {"ai", "math", "breakthrough"},
        {"quantum", "teleportation", "computing"},
        {"dna", "battery", "sun"},
        {"carbon", "dioxide", "fuel"},
    )
    return any(group <= intersection for group in duplicate_signal_groups)


def _story_tokens(article: Article) -> set[str]:
    text = f"{article.title} {article.summary}".lower()
    raw_tokens = re.findall(r"[a-z0-9]+", text)
    stop_words = {
        "a", "an", "and", "are", "as", "by", "for", "from", "in", "is",
        "it", "new", "of", "on", "or", "the", "this", "to", "with",
        "could", "may", "might", "can", "will", "just", "major", "biggest",
    }
    tokens: set[str] = set()
    for token in raw_tokens:
        if token in stop_words or len(token) < 3:
            continue
        tokens.add(_normalize_story_token(token))
    return tokens


def _normalize_story_token(token: str) -> str:
    synonyms = {
        "maths": "math",
        "mathematics": "math",
        "mathematicians": "math",
        "artificial": "ai",
        "intelligence": "ai",
        "solar": "sun",
        "sunlight": "sun",
        "computers": "computing",
        "computer": "computing",
        "batteries": "battery",
        "robots": "robot",
    }
    return synonyms.get(token, token)


def _headline_key(headline: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", headline.lower()).strip()


def _recency_score(article: Article, now: datetime | None = None) -> float:
    published = parse_datetime(article.published)
    if published is None:
        return 0.0

    if now is None:
        now = datetime.now(timezone.utc)
    if published.tzinfo is None:
        published = published.replace(tzinfo=timezone.utc)

    age_hours = max((now - published).total_seconds() / 3600, 0)
    if age_hours <= 24:
        return 4.0
    if age_hours <= 72:
        return 2.0
    if age_hours <= 168:
        return 0.75
    return 0.0
