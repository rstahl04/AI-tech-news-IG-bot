from __future__ import annotations

from collections.abc import Iterable
import re
from datetime import datetime, timezone

from .headline import technology_focus_score
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
    return ranked[:limit]


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
