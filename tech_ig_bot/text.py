from __future__ import annotations

import html
import re
from html.parser import HTMLParser


WHITESPACE_RE = re.compile(r"\s+")


def clean_text(value: str) -> str:
    """Strip tags/entities and normalize whitespace."""

    if not value:
        return ""
    without_tags = re.sub(r"<[^>]+>", " ", value)
    unescaped = html.unescape(without_tags)
    return WHITESPACE_RE.sub(" ", unescaped).strip()


def sentence_case_trim(value: str, max_chars: int) -> str:
    """Trim text at a sentence boundary when possible."""

    value = clean_text(value)
    if len(value) <= max_chars:
        return value

    clipped = value[: max_chars + 1].strip()
    boundary = max(clipped.rfind("."), clipped.rfind("!"), clipped.rfind("?"))
    if boundary >= max_chars * 0.55:
        return clipped[: boundary + 1].strip()

    words = clipped[:max_chars].split()
    if len(words) <= 1:
        return clipped[:max_chars].rstrip() + "..."
    return " ".join(words[:-1]).rstrip(" ,;:-") + "..."


class ArticleHTMLExtractor(HTMLParser):
    """Small article-text extractor used to enrich feed summaries."""

    def __init__(self) -> None:
        super().__init__()
        self._capture_text = False
        self._ignore_depth = 0
        self._paragraph_parts: list[str] = []
        self._current_parts: list[str] = []
        self.meta_description = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {name.lower(): value or "" for name, value in attrs}
        tag = tag.lower()

        if tag in {"script", "style", "noscript", "svg"}:
            self._ignore_depth += 1
            return

        if tag == "meta":
            name = attrs_dict.get("name", "").lower()
            prop = attrs_dict.get("property", "").lower()
            if name == "description" or prop == "og:description":
                self.meta_description = clean_text(attrs_dict.get("content", ""))
            return

        if tag in {"p", "li"} and self._ignore_depth == 0:
            self._capture_text = True
            self._current_parts = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg"} and self._ignore_depth:
            self._ignore_depth -= 1
            return

        if tag in {"p", "li"} and self._capture_text:
            text = clean_text(" ".join(self._current_parts))
            if len(text) > 40:
                self._paragraph_parts.append(text)
            self._capture_text = False
            self._current_parts = []

    def handle_data(self, data: str) -> None:
        if self._capture_text and self._ignore_depth == 0:
            self._current_parts.append(data)

    def extract(self, max_chars: int = 1200) -> str:
        text = " ".join(self._paragraph_parts) or self.meta_description
        return sentence_case_trim(text, max_chars)


def extract_article_text(html_value: str, max_chars: int = 1200) -> str:
    parser = ArticleHTMLExtractor()
    parser.feed(html_value)
    return parser.extract(max_chars=max_chars)
