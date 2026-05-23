from __future__ import annotations

from urllib.parse import quote_plus

from .models import FeedSource


DEFAULT_FEEDS: tuple[FeedSource, ...] = (
    FeedSource("MIT Technology Review", "https://www.technologyreview.com/feed/"),
    FeedSource("The Verge", "https://www.theverge.com/rss/index.xml"),
    FeedSource("Ars Technica", "https://feeds.arstechnica.com/arstechnica/index"),
    FeedSource("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
    FeedSource("ScienceDaily Technology", "https://www.sciencedaily.com/rss/top/technology.xml"),
    FeedSource("Nature Technology", "https://www.nature.com/subjects/technology.rss"),
    FeedSource("Hacker News", "https://hnrss.org/frontpage?points=100"),
)

DEFAULT_QUERIES: tuple[str, ...] = (
    "exciting new technology breakthrough",
    "artificial intelligence breakthrough",
    "robotics breakthrough",
    "quantum computing breakthrough",
    "battery technology breakthrough",
)


def build_bing_news_feed(query: str) -> FeedSource:
    """Build a public Bing News RSS source for a discovery query."""

    encoded = quote_plus(query)
    return FeedSource(
        name=f"Bing News: {query}",
        url=f"https://www.bing.com/news/search?q={encoded}&format=rss",
    )


def default_sources(include_news_search: bool = True) -> list[FeedSource]:
    sources = list(DEFAULT_FEEDS)
    if include_news_search:
        sources.extend(build_bing_news_feed(query) for query in DEFAULT_QUERIES)
    return sources
