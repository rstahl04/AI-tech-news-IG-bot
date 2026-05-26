#!/usr/bin/env python3
"""Browser UI for exporting authorized Instagram/TikTok URLs by niche."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.parse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Iterable

from video_niche_collector import (
    VideoEntry,
    is_social_url,
    niche_score,
    parse_manifest_data,
    social_export_url,
)


DEFAULT_SAMPLE_URLS = """https://www.instagram.com/reel/example-owned-gym-fail/ | Gym fail bench press
https://www.tiktok.com/@youraccount/video/1234567890 | Treadmill gym fail"""


def split_keywords(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"[,\n]+", value) if part.strip()]


def parse_social_url_lines(lines: str, assumed_context: str = "") -> list[VideoEntry]:
    """Parse quick-entry pasted text into authorized manifest entries.

    Accepted formats:
    - https://www.instagram.com/reel/example/
    - https://www.tiktok.com/@creator/video/123 | gym fail treadmill
    - gym fail treadmill https://www.instagram.com/reel/example/
    - A copied text block containing multiple social URLs.
    """

    entries: list[VideoEntry] = []
    url_pattern = re.compile(r"https?://\S+")
    context_lines: list[str] = []

    for raw_line in lines.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        matches = list(url_pattern.finditer(line))
        if not matches:
            context_lines.append(line)
            continue

        notes = url_pattern.sub(" ", line).strip(" |,-")
        if "|" in line:
            parts = [part.strip() for part in line.split("|", 1)]
            if parts[0].startswith("http"):
                notes = parts[1]
            elif parts[1].startswith("http"):
                notes = parts[0]

        context = " ".join(part for part in (notes, " ".join(context_lines), assumed_context) if part)
        context_lines.clear()

        for match in matches:
            url = clean_pasted_url(match.group(0))
            if not is_social_url(url):
                continue

            entries.append(
                VideoEntry(
                    source=url,
                    title=context,
                    description=context,
                    tags=tuple(split_keywords(context)),
                    authorized=True,
                )
            )

    if not entries:
        raise ValueError(
            "No Instagram/TikTok links were found. Paste one or more reel/video URLs first; "
            "this site filters pasted links but does not search those platforms automatically."
        )
    return entries


def clean_pasted_url(value: str) -> str:
    return value.rstrip(".,;)]}>\"'")


def matching_social_urls(
    entries: Iterable[VideoEntry],
    niche: str,
    keywords: Iterable[str],
    min_score: int,
) -> tuple[list[str], list[str]]:
    matches: list[str] = []
    messages: list[str] = []
    seen: set[str] = set()

    for index, entry in enumerate(entries, start=1):
        if not entry.authorized:
            messages.append(f"Skipped item {index}: not marked authorized=true.")
            continue

        url = social_export_url(entry)
        if not url:
            messages.append(f"Skipped item {index}: no Instagram/TikTok URL found.")
            continue

        score = niche_score(entry, niche, keywords)
        if score < min_score:
            messages.append(f"Skipped item {index}: score {score} below threshold {min_score}.")
            continue

        if url in seen:
            messages.append(f"Skipped item {index}: duplicate URL.")
            continue

        seen.add(url)
        matches.append(url)
        messages.append(f"Matched item {index}: score {score}.")

    return matches, messages


def render_page(
    *,
    niche: str = "gym fails",
    keywords: str = "",
    urls: str = DEFAULT_SAMPLE_URLS,
    manifest: str = "",
    assume_matching: bool = True,
    min_score: int = 1,
    matches: list[str] | None = None,
    messages: list[str] | None = None,
    error: str = "",
) -> bytes:
    matches = matches or []
    messages = messages or []
    escaped_matches = "\n".join(matches)
    match_links = "\n".join(
        f'<li><a href="{html.escape(url, quote=True)}" target="_blank" rel="noreferrer">{html.escape(url)}</a></li>'
        for url in matches
    )
    message_items = "\n".join(f"<li>{html.escape(message)}</li>" for message in messages)
    checked = "checked" if assume_matching else ""
    html_body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Video Niche URL Collector</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 2rem auto; max-width: 980px; padding: 0 1rem; line-height: 1.5; }}
    textarea, input {{ box-sizing: border-box; font: inherit; width: 100%; }}
    textarea {{ min-height: 9rem; }}
    label {{ display: block; font-weight: 700; margin-top: 1rem; }}
    button {{ background: #111827; border: 0; border-radius: 0.5rem; color: white; cursor: pointer; font: inherit; margin-top: 1rem; padding: 0.75rem 1rem; }}
    .hint, .policy {{ color: #4b5563; }}
    .notice {{ background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 0.75rem; color: #1e3a8a; padding: 1rem; }}
    .grid {{ display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); }}
    .box {{ background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 0.75rem; padding: 1rem; }}
    .error {{ background: #fef2f2; border-color: #fecaca; color: #991b1b; }}
    .results textarea {{ min-height: 6rem; }}
    .checkbox {{ align-items: center; display: flex; gap: 0.5rem; margin-top: 1rem; }}
    .checkbox input {{ width: auto; }}
  </style>
</head>
<body>
  <h1>Video Niche URL Collector</h1>
  <p class="policy">Paste Instagram/TikTok URLs you already have permission to track or collect through authorized means. This page filters and exports links only; it does not scrape platforms, download videos, or remove watermarks.</p>
  <div class="notice">
    <strong>Important:</strong> This is not an Instagram/TikTok search engine. Paste links first, then the site finds the matching links from what you pasted.
  </div>
  {"<div class='box error'><strong>Error:</strong> " + html.escape(error) + "</div>" if error else ""}
  <form method="post" action="/export">
    <div class="grid">
      <div>
        <label for="niche">Niche</label>
        <input id="niche" name="niche" value="{html.escape(niche, quote=True)}" required>
      </div>
      <div>
        <label for="keywords">Extra keywords</label>
        <input id="keywords" name="keywords" value="{html.escape(keywords, quote=True)}" placeholder="bench, treadmill">
      </div>
      <div>
        <label for="min_score">Minimum score</label>
        <input id="min_score" name="min_score" type="number" min="1" value="{min_score}">
      </div>
    </div>

    <label for="urls">Paste Instagram/TikTok links or copied text</label>
    <p class="hint">You can paste one URL per line, multiple URLs in a text block, or notes after a pipe: <code>URL | gym fail treadmill</code>.</p>
    <textarea id="urls" name="urls">{html.escape(urls)}</textarea>

    <div class="checkbox">
      <input id="assume_matching" name="assume_matching" type="checkbox" value="1" {checked}>
      <label for="assume_matching" style="margin:0;">Treat pasted quick-list URLs as matching this niche</label>
    </div>

    <label for="manifest">Optional JSON manifest</label>
    <p class="hint">If provided, the manifest is used instead of the quick URL list.</p>
    <textarea id="manifest" name="manifest" placeholder='{{"videos":[{{"source":"https://www.instagram.com/reel/example/","title":"gym fail","tags":["gym"],"authorized":true}}]}}'>{html.escape(manifest)}</textarea>

    <button type="submit">Find matching URLs</button>
  </form>

  <section class="box results">
    <h2>Matching URLs ({len(matches)})</h2>
    <textarea readonly>{html.escape(escaped_matches)}</textarea>
    <ol>{match_links}</ol>
  </section>

  <section class="box">
    <h2>Run log</h2>
    <ul>{message_items}</ul>
  </section>
</body>
</html>
"""
    return html_body.encode("utf-8")


class NicheCollectorRequestHandler(BaseHTTPRequestHandler):
    server_version = "VideoNicheCollector/1.0"

    def do_GET(self) -> None:
        if self.path in {"/", "/index.html"}:
            self.send_html(render_page())
            return
        if self.path == "/healthz":
            self.send_response(HTTPStatus.OK)
            self.end_headers()
            self.wfile.write(b"ok\n")
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        if self.path != "/export":
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        length = int(self.headers.get("Content-Length", "0"))
        form = urllib.parse.parse_qs(self.rfile.read(length).decode("utf-8"), keep_blank_values=True)
        niche = form_value(form, "niche", "gym fails")
        keywords_text = form_value(form, "keywords", "")
        urls_text = form_value(form, "urls", "")
        manifest_text = form_value(form, "manifest", "")
        assume_matching = form_value(form, "assume_matching", "") == "1"
        min_score = parse_min_score(form_value(form, "min_score", "1"))

        matches: list[str] = []
        messages: list[str] = []
        error = ""

        try:
            if manifest_text.strip():
                entries = parse_manifest_data(json.loads(manifest_text))
            else:
                assumed_context = " ".join([niche, keywords_text]) if assume_matching else ""
                entries = parse_social_url_lines(urls_text, assumed_context=assumed_context)
            matches, messages = matching_social_urls(entries, niche, split_keywords(keywords_text), min_score)
        except Exception as exc:  # Keep browser errors user-readable.
            error = str(exc)

        self.send_html(
            render_page(
                niche=niche,
                keywords=keywords_text,
                urls=urls_text,
                manifest=manifest_text,
                assume_matching=assume_matching,
                min_score=min_score,
                matches=matches,
                messages=messages,
                error=error,
            ),
            status=HTTPStatus.BAD_REQUEST if error else HTTPStatus.OK,
        )

    def log_message(self, format: str, *args: object) -> None:
        sys.stderr.write("%s - - [%s] %s\n" % (self.client_address[0], self.log_date_time_string(), format % args))

    def send_html(self, body: bytes, status: HTTPStatus = HTTPStatus.OK) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def form_value(form: dict[str, list[str]], key: str, default: str = "") -> str:
    values = form.get(key)
    return values[0] if values else default


def parse_min_score(value: str) -> int:
    try:
        min_score = int(value)
    except ValueError:
        return 1
    return max(1, min_score)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the browser UI for the video niche URL collector.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind.")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    server = ThreadingHTTPServer((args.host, args.port), NicheCollectorRequestHandler)
    print(f"Open http://{args.host}:{args.port} in your browser.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
