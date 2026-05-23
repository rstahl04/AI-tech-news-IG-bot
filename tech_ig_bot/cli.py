from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .fetcher import collect_articles
from .models import Article, FeedSource
from .ranker import rank_articles
from .renderer import render_article_post
from .sources import build_bing_news_feed, default_sources


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Scrape tech news feeds, find exciting breakthroughs, and generate "
            "Instagram-ready image/caption assets."
        )
    )
    parser.add_argument(
        "--query",
        action="append",
        default=[],
        help="Extra Bing News RSS query to scan. Can be used more than once.",
    )
    parser.add_argument(
        "--feed",
        action="append",
        default=[],
        help="Extra RSS/Atom feed URL to scan. Can be used more than once.",
    )
    parser.add_argument(
        "--per-source",
        type=int,
        default=8,
        help="Maximum stories to read from each source.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=1,
        help="How many ranked stories to render.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory for generated PNG, caption, and metadata files.",
    )
    parser.add_argument(
        "--no-enrich",
        action="store_true",
        help="Skip fetching article pages and use feed summaries only.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print ranked candidates without rendering images.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        help="Logging verbosity.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level), format="%(levelname)s: %(message)s")

    sources = _build_sources(args.query, args.feed)
    articles = collect_articles(
        sources,
        per_source=args.per_source,
        enrich=not args.no_enrich,
    )
    ranked = rank_articles(articles, limit=args.top)

    if not ranked:
        parser.error("No articles were discovered. Try a custom --query or --feed.")

    if args.dry_run:
        _print_ranked(ranked)
        return 0

    for index, article in enumerate(ranked, start=1):
        paths = render_article_post(article, output_dir=args.output_dir, index=index)
        print(f"Generated {paths['image']}")
        print(f"Caption  {paths['caption']}")
        print(f"Metadata {paths['metadata']}")
    return 0


def _build_sources(queries: list[str], feeds: list[str]) -> list[FeedSource]:
    sources = default_sources(include_news_search=True)
    sources.extend(build_bing_news_feed(query) for query in queries)
    sources.extend(
        FeedSource(name=f"Custom feed {index}", url=url)
        for index, url in enumerate(feeds, start=1)
    )
    return sources


def _print_ranked(articles: list[Article]) -> None:
    for index, article in enumerate(articles, start=1):
        print(f"{index}. [{article.score}] {article.title}")
        print(f"   Source: {article.source}")
        print(f"   URL: {article.url}")


if __name__ == "__main__":
    raise SystemExit(main())
