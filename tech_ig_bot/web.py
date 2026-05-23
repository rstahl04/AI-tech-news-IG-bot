from __future__ import annotations

import argparse
import html
import json
import logging
import mimetypes
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

from .caption import make_instagram_caption
from .fetcher import collect_articles
from .headline import make_technology_headline
from .models import Article, FeedSource
from .ranker import rank_articles
from .renderer import render_article_post
from .sources import build_bing_news_feed, default_sources

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class WebPost:
    title: str
    source: str
    url: str
    score: float
    image_path: Path
    caption_path: Path
    metadata_path: Path
    caption: str


@dataclass(slots=True)
class GenerateOptions:
    queries: list[str]
    feeds: list[str]
    per_source: int
    top: int
    enrich: bool


def parse_generate_options(form_body: str) -> GenerateOptions:
    values = parse_qs(form_body, keep_blank_values=True)
    queries = _lines(values.get("query", [""])[0])
    feeds = _lines(values.get("feed", [""])[0])
    per_source = _bounded_int(values.get("per_source", ["4"])[0], default=4, low=1, high=20)
    top = _bounded_int(values.get("top", ["1"])[0], default=1, low=1, high=6)
    enrich = values.get("enrich", [""])[0] == "on"
    return GenerateOptions(
        queries=queries,
        feeds=feeds,
        per_source=per_source,
        top=top,
        enrich=enrich,
    )


def generate_posts(options: GenerateOptions, output_dir: Path) -> list[WebPost]:
    sources = _build_sources(options.queries, options.feeds)
    articles = collect_articles(
        sources,
        per_source=options.per_source,
        enrich=options.enrich,
    )
    ranked = rank_articles(articles, limit=options.top)
    if not ranked:
        return []

    run_dir = output_dir / "web" / _next_run_name(output_dir / "web")
    posts: list[WebPost] = []
    for index, article in enumerate(ranked, start=1):
        paths = render_article_post(article, output_dir=run_dir, index=index)
        posts.append(
            WebPost(
                title=make_technology_headline(article),
                source=article.source,
                url=article.url,
                score=article.score,
                image_path=paths["image"],
                caption_path=paths["caption"],
                metadata_path=paths["metadata"],
                caption=make_instagram_caption(article),
            )
        )
    return posts


def load_recent_posts(output_dir: Path, limit: int = 12) -> list[WebPost]:
    web_root = output_dir / "web"
    if not web_root.exists():
        return []

    metadata_files = sorted(
        web_root.glob("**/*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    posts: list[WebPost] = []
    for metadata_path in metadata_files[:limit]:
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue

        image_path = metadata_path.with_suffix(".png")
        caption_path = metadata_path.with_suffix(".caption.txt")
        if not image_path.exists() or not caption_path.exists():
            continue

        posts.append(
            WebPost(
                title=str(metadata.get("title", image_path.stem)),
                source=str(metadata.get("source", "")),
                url=str(metadata.get("url", "")),
                score=float(metadata.get("score", 0.0)),
                image_path=image_path,
                caption_path=caption_path,
                metadata_path=metadata_path,
                caption=caption_path.read_text(encoding="utf-8").strip(),
            )
        )
    return posts


def render_index(
    posts: list[WebPost],
    output_dir: Path,
    notice: str = "",
    error: str = "",
) -> str:
    post_cards = "\n".join(_render_post_card(post, output_dir) for post in posts)
    if not post_cards:
        post_cards = """
        <section class="empty">
          <h2>No posts generated yet</h2>
          <p>Use the form to discover current technology stories and create Instagram assets.</p>
        </section>
        """

    notice_html = f'<div class="notice">{html.escape(notice)}</div>' if notice else ""
    error_html = f'<div class="error">{html.escape(error)}</div>' if error else ""

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Tech News Instagram Bot</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #08111f;
      --panel: #111c33;
      --text: #f8fafc;
      --muted: #aab6ce;
      --accent: #00f5d4;
      --accent-2: #7c3aed;
      --danger: #fda4af;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at top right, rgba(124, 58, 237, 0.35), transparent 35rem),
        radial-gradient(circle at 10% 20%, rgba(0, 245, 212, 0.20), transparent 28rem),
        var(--bg);
      color: var(--text);
    }}
    main {{ width: min(1180px, calc(100% - 32px)); margin: 0 auto; padding: 44px 0 64px; }}
    header {{ margin-bottom: 28px; }}
    .eyebrow {{ color: var(--accent); font-weight: 800; letter-spacing: 0.12em; text-transform: uppercase; }}
    h1 {{ margin: 10px 0 12px; font-size: clamp(2.2rem, 5vw, 4.5rem); line-height: 0.96; }}
    .subtitle {{ color: var(--muted); max-width: 760px; font-size: 1.12rem; line-height: 1.6; }}
    .layout {{ display: grid; grid-template-columns: minmax(300px, 420px) 1fr; gap: 24px; align-items: start; }}
    .panel, .card, .empty {{
      background: rgba(17, 28, 51, 0.86);
      border: 1px solid rgba(255, 255, 255, 0.10);
      border-radius: 28px;
      box-shadow: 0 24px 80px rgba(0, 0, 0, 0.26);
    }}
    .panel {{ padding: 24px; position: sticky; top: 24px; }}
    label {{ display: block; color: #dbeafe; font-weight: 750; margin: 18px 0 8px; }}
    textarea, input {{
      width: 100%;
      border: 1px solid rgba(255, 255, 255, 0.14);
      border-radius: 16px;
      background: rgba(8, 17, 31, 0.88);
      color: var(--text);
      padding: 13px 14px;
      font: inherit;
    }}
    textarea {{ min-height: 96px; resize: vertical; }}
    .row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
    .checkbox {{ display: flex; gap: 10px; align-items: center; margin-top: 18px; color: var(--muted); }}
    .checkbox input {{ width: auto; }}
    button, .button {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      border: 0;
      border-radius: 999px;
      background: var(--accent);
      color: #06111f;
      font-weight: 850;
      padding: 13px 18px;
      cursor: pointer;
      text-decoration: none;
      font: inherit;
    }}
    button.primary {{ width: 100%; margin-top: 22px; font-size: 1.03rem; }}
    .notice, .error {{ margin-bottom: 18px; padding: 14px 16px; border-radius: 18px; }}
    .notice {{ background: rgba(0, 245, 212, 0.12); color: #bffdf3; }}
    .error {{ background: rgba(253, 164, 175, 0.14); color: var(--danger); }}
    .results {{ display: grid; gap: 22px; }}
    .card {{ display: grid; grid-template-columns: minmax(220px, 340px) 1fr; gap: 22px; padding: 20px; }}
    .card img {{ width: 100%; border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.12); }}
    .meta {{ color: var(--accent); font-size: 0.88rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.08em; }}
    .card h2 {{ margin: 8px 0 8px; font-size: clamp(1.35rem, 2.3vw, 2rem); }}
    .source {{ color: var(--muted); margin-bottom: 14px; }}
    .caption {{
      width: 100%;
      min-height: 190px;
      white-space: pre-wrap;
      color: #e5edf9;
      background: rgba(8, 17, 31, 0.65);
      border-radius: 18px;
      padding: 14px;
      line-height: 1.5;
      overflow: auto;
    }}
    .actions {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 14px; }}
    .secondary {{ background: rgba(255, 255, 255, 0.12); color: var(--text); }}
    .empty {{ padding: 34px; color: var(--muted); }}
    @media (max-width: 900px) {{
      .layout, .card {{ grid-template-columns: 1fr; }}
      .panel {{ position: static; }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <div class="eyebrow">Breakthrough Radar</div>
      <h1>Generate Instagram posts from emerging tech news.</h1>
      <p class="subtitle">
        Scrape public technology feeds, rank exciting breakthroughs, and create a polished
        Instagram image plus a long caption you can review before posting.
      </p>
    </header>
    {notice_html}
    {error_html}
    <section class="layout">
      <form class="panel" method="post" action="/generate">
        <h2>Generate posts</h2>
        <label for="query">Extra search topics, one per line</label>
        <textarea id="query" name="query" placeholder="space propulsion breakthrough&#10;humanoid robot prototype"></textarea>
        <label for="feed">Extra RSS feeds, one per line</label>
        <textarea id="feed" name="feed" placeholder="https://example.com/rss.xml"></textarea>
        <div class="row">
          <div>
            <label for="top">Posts</label>
            <input id="top" name="top" type="number" min="1" max="6" value="1">
          </div>
          <div>
            <label for="per_source">Stories/source</label>
            <input id="per_source" name="per_source" type="number" min="1" max="20" value="4">
          </div>
        </div>
        <label class="checkbox">
          <input type="checkbox" name="enrich">
          Fetch article pages for richer captions. This is slower.
        </label>
        <button class="primary" type="submit">Generate Instagram assets</button>
      </form>
      <section class="results">
        {post_cards}
      </section>
    </section>
  </main>
  <script>
    async function copyCaption(id) {{
      const text = document.getElementById(id).innerText;
      await navigator.clipboard.writeText(text);
      const button = document.querySelector(`[data-copy="${{id}}"]`);
      const old = button.innerText;
      button.innerText = "Copied";
      setTimeout(() => button.innerText = old, 1200);
    }}
  </script>
</body>
</html>"""


class TechNewsHandler(BaseHTTPRequestHandler):
    output_dir = Path("output")

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            posts = load_recent_posts(self.output_dir)
            self._send_html(render_index(posts, self.output_dir))
            return
        if parsed.path.startswith("/generated/"):
            self._send_generated_file(parsed.path.removeprefix("/generated/"))
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/generate":
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        body = self.rfile.read(_content_length(self.headers.get("Content-Length"))).decode(
            "utf-8",
            errors="replace",
        )
        try:
            options = parse_generate_options(body)
            posts = generate_posts(options, self.output_dir)
            if not posts:
                page = render_index(
                    load_recent_posts(self.output_dir),
                    self.output_dir,
                    error="No articles were discovered. Try a custom topic or feed.",
                )
            else:
                page = render_index(
                    posts,
                    self.output_dir,
                    notice=f"Generated {len(posts)} post asset set.",
                )
        except Exception as exc:  # pragma: no cover - keeps browser errors friendly.
            LOGGER.exception("Generation failed")
            page = render_index(
                load_recent_posts(self.output_dir),
                self.output_dir,
                error=f"Generation failed: {exc}",
            )
        self._send_html(page)

    def log_message(self, format: str, *args: object) -> None:
        LOGGER.info("%s - %s", self.address_string(), format % args)

    def _send_html(self, body: str) -> None:
        encoded = body.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_generated_file(self, relative_url_path: str) -> None:
        relative_path = Path(unquote(relative_url_path))
        root = self.output_dir.resolve()
        file_path = (root / relative_path).resolve()
        if not _is_relative_to(file_path, root) or not file_path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "Generated file not found")
            return

        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        data = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def run_server(host: str, port: int, output_dir: Path) -> None:
    handler_class = type(
        "ConfiguredTechNewsHandler",
        (TechNewsHandler,),
        {"output_dir": output_dir},
    )
    server = ThreadingHTTPServer((host, port), handler_class)
    print(f"Open http://{host}:{port} in your browser")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server")
    finally:
        server.server_close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Tech News Instagram Bot website.")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind.")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory where generated web assets are written.",
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
    run_server(args.host, args.port, args.output_dir)
    return 0


def _render_post_card(post: WebPost, output_dir: Path) -> str:
    caption_id = "caption-" + quote(post.metadata_path.stem, safe="")
    image_url = _generated_url(post.image_path, output_dir)
    caption_url = _generated_url(post.caption_path, output_dir)
    metadata_url = _generated_url(post.metadata_path, output_dir)
    title = html.escape(post.title)
    source = html.escape(post.source)
    article_url = html.escape(post.url)
    caption = html.escape(post.caption)
    source_link = (
        f'<a class="button secondary" href="{article_url}" target="_blank" rel="noreferrer">Open source</a>'
        if article_url
        else ""
    )

    return f"""
    <article class="card">
      <a href="{image_url}" target="_blank"><img src="{image_url}" alt="{title}"></a>
      <div>
        <div class="meta">Score {post.score:.2f}</div>
        <h2>{title}</h2>
        <div class="source">{source}</div>
        <div id="{caption_id}" class="caption">{caption}</div>
        <div class="actions">
          <button class="secondary" type="button" data-copy="{caption_id}" onclick="copyCaption('{caption_id}')">Copy caption</button>
          <a class="button" href="{image_url}" download>Download image</a>
          <a class="button secondary" href="{caption_url}" download>Download caption</a>
          <a class="button secondary" href="{metadata_url}" download>Metadata</a>
          {source_link}
        </div>
      </div>
    </article>
    """


def _build_sources(queries: list[str], feeds: list[str]) -> list[FeedSource]:
    sources = default_sources(include_news_search=True)
    sources.extend(build_bing_news_feed(query) for query in queries)
    sources.extend(
        FeedSource(name=f"Custom feed {index}", url=url)
        for index, url in enumerate(feeds, start=1)
    )
    return sources


def _lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def _bounded_int(value: str, default: int, low: int, high: int) -> int:
    try:
        parsed = int(value)
    except ValueError:
        return default
    return min(max(parsed, low), high)


def _next_run_name(root: Path) -> str:
    root.mkdir(parents=True, exist_ok=True)
    existing = [
        int(path.name.removeprefix("run-"))
        for path in root.glob("run-*")
        if path.name.removeprefix("run-").isdigit()
    ]
    return f"run-{(max(existing) if existing else 0) + 1:04d}"


def _generated_url(path: Path, output_dir: Path) -> str:
    relative = path.resolve().relative_to(output_dir.resolve())
    return "/generated/" + quote(relative.as_posix())


def _content_length(value: str | None) -> int:
    if value is None:
        return 0
    try:
        return max(int(value), 0)
    except ValueError:
        return 0


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


if __name__ == "__main__":
    raise SystemExit(main())
