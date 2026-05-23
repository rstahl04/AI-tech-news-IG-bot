from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class FeedSource:
    """RSS or Atom feed to scan for candidate technology stories."""

    name: str
    url: str


@dataclass(slots=True)
class Article:
    """Normalized story discovered from a feed or news search."""

    source: str
    title: str
    url: str
    summary: str = ""
    published: str = ""
    content: str = ""
    score: float = 0.0

    @property
    def searchable_text(self) -> str:
        return " ".join(
            value
            for value in (self.title, self.summary, self.content)
            if value
        )

    @property
    def display_date(self) -> str:
        parsed = parse_datetime(self.published)
        if parsed is None:
            return self.published
        return parsed.strftime("%b %-d, %Y")


def parse_datetime(value: str) -> datetime | None:
    """Best-effort parser for common RSS and Atom date formats."""

    if not value:
        return None

    formats = (
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d",
    )
    for fmt in formats:
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None
