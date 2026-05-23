from __future__ import annotations

import logging
from collections.abc import Iterable
from urllib.error import URLError
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from .models import Article, FeedSource
from .text import clean_text, extract_article_text

LOGGER = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (compatible; TechInstagramBot/0.1; "
    "+https://example.invalid/tech-instagram-bot)"
)


def fetch_url(url: str, timeout: float = 15.0) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - user-supplied URLs are intended.
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def parse_feed_xml(xml_text: str, source_name: str, limit: int = 10) -> list[Article]:
    root = ElementTree.fromstring(xml_text)
    articles: list[Article] = []

    rss_items = root.findall(".//item")
    atom_entries = root.findall(".//{http://www.w3.org/2005/Atom}entry")
    entries = rss_items or atom_entries

    for entry in entries[:limit]:
        article = _parse_rss_item(entry, source_name)
        if article is None:
            article = _parse_atom_entry(entry, source_name)
        if article is not None:
            articles.append(article)

    return articles


def fetch_feed(source: FeedSource, per_source: int = 8, timeout: float = 15.0) -> list[Article]:
    try:
        xml_text = fetch_url(source.url, timeout=timeout)
        return parse_feed_xml(xml_text, source.name, limit=per_source)
    except (ElementTree.ParseError, OSError, URLError) as exc:
        LOGGER.warning("Could not fetch %s: %s", source.name, exc)
        return []


def fetch_article_content(article: Article, timeout: float = 10.0) -> Article:
    try:
        html_text = fetch_url(article.url, timeout=timeout)
    except (OSError, URLError) as exc:
        LOGGER.debug("Could not enrich %s: %s", article.url, exc)
        return article

    extracted = extract_article_text(html_text)
    if extracted:
        article.content = extracted
    return article


def collect_articles(
    sources: Iterable[FeedSource],
    per_source: int = 8,
    enrich: bool = True,
) -> list[Article]:
    articles: list[Article] = []
    seen_urls: set[str] = set()

    for source in sources:
        for article in fetch_feed(source, per_source=per_source):
            if article.url in seen_urls:
                continue
            seen_urls.add(article.url)
            articles.append(fetch_article_content(article) if enrich else article)

    return articles


def _parse_rss_item(entry: ElementTree.Element, source_name: str) -> Article | None:
    title = _find_text(entry, "title")
    link = _find_text(entry, "link")
    if not title or not link:
        return None

    summary = (
        _find_text(entry, "description")
        or _find_text(entry, "{http://purl.org/rss/1.0/modules/content/}encoded")
    )
    published = _find_text(entry, "pubDate") or _find_text(entry, "published")
    return Article(
        source=source_name,
        title=clean_text(title),
        url=clean_text(link),
        summary=clean_text(summary),
        published=clean_text(published),
    )


def _parse_atom_entry(entry: ElementTree.Element, source_name: str) -> Article | None:
    title = _find_text(entry, "{http://www.w3.org/2005/Atom}title")
    link = _atom_link(entry)
    if not title or not link:
        return None

    summary = (
        _find_text(entry, "{http://www.w3.org/2005/Atom}summary")
        or _find_text(entry, "{http://www.w3.org/2005/Atom}content")
    )
    published = (
        _find_text(entry, "{http://www.w3.org/2005/Atom}published")
        or _find_text(entry, "{http://www.w3.org/2005/Atom}updated")
    )
    return Article(
        source=source_name,
        title=clean_text(title),
        url=clean_text(link),
        summary=clean_text(summary),
        published=clean_text(published),
    )


def _find_text(entry: ElementTree.Element, path: str) -> str:
    found = entry.find(path)
    if found is None or found.text is None:
        return ""
    return found.text


def _atom_link(entry: ElementTree.Element) -> str:
    for link in entry.findall("{http://www.w3.org/2005/Atom}link"):
        rel = link.attrib.get("rel", "alternate")
        href = link.attrib.get("href")
        if href and rel == "alternate":
            return href
    return ""
