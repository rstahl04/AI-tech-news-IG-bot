#!/usr/bin/env python3
"""Collect authorized niche videos into a cleaned output folder.

This tool intentionally does not scrape Instagram/TikTok or remove watermarks.
It works with local files or direct media URLs that you own or have permission
to use, then strips container metadata with ffmpeg before saving matched videos.
It can also export matching Instagram/TikTok URLs that you provide in the
manifest, without downloading them.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm", ".mkv"}
BLOCKED_HOSTS = {
    "instagram.com",
    "www.instagram.com",
    "m.instagram.com",
    "tiktok.com",
    "www.tiktok.com",
}


@dataclass(frozen=True)
class VideoEntry:
    """A single manifest item."""

    source: str
    page_url: str = ""
    title: str = ""
    description: str = ""
    tags: tuple[str, ...] = ()
    authorized: bool = False

    @property
    def searchable_text(self) -> str:
        return " ".join(
            part
            for part in (
                self.title,
                self.description,
                " ".join(self.tags),
                Path(urllib.parse.urlparse(self.source).path).stem,
                Path(urllib.parse.urlparse(self.page_url).path).stem,
            )
            if part
        )


def normalize_token(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "", value)
    if len(value) > 3 and value.endswith("s"):
        value = value[:-1]
    return value


def tokenize(value: str) -> set[str]:
    return {
        token
        for token in (normalize_token(part) for part in re.split(r"[^A-Za-z0-9]+", value))
        if token
    }


def niche_score(entry: VideoEntry, niche: str, keywords: Iterable[str]) -> int:
    """Score an entry with simple phrase and keyword matching."""

    searchable = entry.searchable_text.lower()
    score = 0
    if niche.lower() in searchable:
        score += 3

    entry_tokens = tokenize(searchable)
    keyword_tokens = tokenize(" ".join([niche, *keywords]))
    score += len(entry_tokens & keyword_tokens)
    return score


def load_manifest(path: Path) -> list[VideoEntry]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    records = payload.get("videos", payload) if isinstance(payload, dict) else payload
    if not isinstance(records, list):
        raise ValueError("Manifest must be a JSON list or an object with a 'videos' list.")

    entries: list[VideoEntry] = []
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            raise ValueError(f"Manifest item {index} must be an object.")
        source = str(record.get("source", "")).strip()
        if not source:
            raise ValueError(f"Manifest item {index} is missing a source.")
        tags = record.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]
        if not isinstance(tags, list):
            raise ValueError(f"Manifest item {index} tags must be a string or list.")
        entries.append(
            VideoEntry(
                source=source,
                page_url=str(record.get("page_url", record.get("url", ""))).strip(),
                title=str(record.get("title", "")).strip(),
                description=str(record.get("description", "")).strip(),
                tags=tuple(str(tag).strip() for tag in tags if str(tag).strip()),
                authorized=bool(record.get("authorized", False)),
            )
        )
    return entries


def is_url(source: str) -> bool:
    parsed = urllib.parse.urlparse(source)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def is_social_url(source: str) -> bool:
    if not is_url(source):
        return False
    host = urllib.parse.urlparse(source).hostname or ""
    host = host.lower()
    return host in BLOCKED_HOSTS or host.endswith(".instagram.com") or host.endswith(".tiktok.com")


def reject_blocked_source(source: str) -> None:
    if is_social_url(source):
        raise ValueError(
            "Instagram/TikTok scraping or downloading is not supported. "
            "Use local files or direct media URLs you are authorized to process."
        )


def social_export_url(entry: VideoEntry) -> str:
    """Return the first social URL provided for an entry, if any."""

    for candidate in (entry.page_url, entry.source):
        if is_social_url(candidate):
            return candidate
    return ""


def infer_extension(source: str, default: str = ".mp4") -> str:
    parsed_path = urllib.parse.urlparse(source).path if is_url(source) else source
    suffix = Path(parsed_path).suffix.lower()
    return suffix if suffix in VIDEO_EXTENSIONS else default


def safe_stem(value: str, fallback: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-._")
    return stem[:80] or fallback


def unique_output_path(folder: Path, stem: str, suffix: str) -> Path:
    candidate = folder / f"{stem}{suffix}"
    counter = 2
    while candidate.exists():
        candidate = folder / f"{stem}-{counter}{suffix}"
        counter += 1
    return candidate


def download_direct_url(source: str, destination: Path) -> None:
    request = urllib.request.Request(
        source,
        headers={
            "User-Agent": "authorized-video-niche-collector/1.0",
            "Accept": "video/*,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        content_type = response.headers.get("Content-Type", "")
        if content_type and not (
            content_type.startswith("video/") or content_type == "application/octet-stream"
        ):
            raise ValueError(f"URL did not return a video content type: {content_type}")
        with destination.open("wb") as output:
            shutil.copyfileobj(response, output)


def strip_metadata(input_path: Path, output_path: Path, allow_copy_without_ffmpeg: bool) -> bool:
    """Strip metadata with ffmpeg. Returns True when ffmpeg was used."""

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        if not allow_copy_without_ffmpeg:
            raise RuntimeError(
                "ffmpeg is required to strip metadata. Install ffmpeg or pass "
                "--allow-copy-without-ffmpeg to copy files without cleaning metadata."
            )
        shutil.copy2(input_path, output_path)
        return False

    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(input_path),
        "-map",
        "0",
        "-map_metadata",
        "-1",
        "-c",
        "copy",
        str(output_path),
    ]
    subprocess.run(command, check=True)
    return True


def collect_videos(
    manifest_path: Path,
    output_folder: Path,
    niche: str,
    keywords: Iterable[str],
    min_score: int,
    allow_copy_without_ffmpeg: bool,
    dry_run: bool,
) -> int:
    entries = load_manifest(manifest_path)
    output_folder.mkdir(parents=True, exist_ok=True)
    matched_count = 0

    with tempfile.TemporaryDirectory(prefix="video-niche-collector-") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        for index, entry in enumerate(entries, start=1):
            if not entry.authorized:
                print(f"SKIP {index}: not marked authorized=true")
                continue

            try:
                reject_blocked_source(entry.source)
            except ValueError as exc:
                print(f"SKIP {index}: {exc}")
                continue

            score = niche_score(entry, niche, keywords)
            if score < min_score:
                print(f"SKIP {index}: score {score} below threshold {min_score}")
                continue

            matched_count += 1
            suffix = infer_extension(entry.source)
            base_name = entry.title or Path(urllib.parse.urlparse(entry.source).path).stem
            output_path = unique_output_path(output_folder, safe_stem(base_name, f"video-{index}"), suffix)
            print(f"MATCH {index}: score {score} -> {output_path}")

            if dry_run:
                continue

            temp_input = temp_dir / f"input-{index}{suffix}"
            if is_url(entry.source):
                download_direct_url(entry.source, temp_input)
            else:
                source_path = Path(entry.source).expanduser()
                if not source_path.exists():
                    raise FileNotFoundError(f"Source file does not exist: {source_path}")
                shutil.copy2(source_path, temp_input)

            used_ffmpeg = strip_metadata(temp_input, output_path, allow_copy_without_ffmpeg)
            if not used_ffmpeg:
                print(f"WARN {index}: copied without metadata stripping because ffmpeg was unavailable")

    return matched_count


def export_matching_social_urls(
    manifest_path: Path,
    output_path: Path,
    niche: str,
    keywords: Iterable[str],
    min_score: int,
) -> int:
    """Write matching Instagram/TikTok URLs from the manifest to a text file."""

    entries = load_manifest(manifest_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    exported_urls: list[str] = []
    seen_urls: set[str] = set()

    for index, entry in enumerate(entries, start=1):
        if not entry.authorized:
            print(f"URL SKIP {index}: not marked authorized=true")
            continue

        url = social_export_url(entry)
        if not url:
            print(f"URL SKIP {index}: no Instagram/TikTok URL provided")
            continue

        score = niche_score(entry, niche, keywords)
        if score < min_score:
            print(f"URL SKIP {index}: score {score} below threshold {min_score}")
            continue

        if url in seen_urls:
            print(f"URL SKIP {index}: duplicate URL")
            continue

        seen_urls.add(url)
        exported_urls.append(url)
        print(f"URL MATCH {index}: score {score} -> {url}")

    output_path.write_text("\n".join(exported_urls) + ("\n" if exported_urls else ""), encoding="utf-8")
    return len(exported_urls)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Populate a folder with authorized videos matching a niche. "
            "Does not scrape social platforms or remove watermarks."
        )
    )
    parser.add_argument("--manifest", type=Path, required=True, help="Path to a JSON video manifest.")
    parser.add_argument("--niche", required=True, help="Niche phrase to match, for example 'gym fails'.")
    parser.add_argument(
        "--keyword",
        action="append",
        default=[],
        help="Extra keyword to match. May be provided multiple times.",
    )
    parser.add_argument("--output", type=Path, default=Path("videos"), help="Output folder.")
    parser.add_argument(
        "--urls-output",
        type=Path,
        help="Write matching Instagram/TikTok URLs from the manifest to this text file.",
    )
    parser.add_argument(
        "--urls-only",
        action="store_true",
        help="Only export matching URLs. Requires --urls-output and skips video processing.",
    )
    parser.add_argument("--min-score", type=int, default=1, help="Minimum niche match score.")
    parser.add_argument(
        "--allow-copy-without-ffmpeg",
        action="store_true",
        help="Copy matched files if ffmpeg is unavailable. Metadata may remain.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show matches without copying/downloading.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.min_score < 1:
        raise ValueError("--min-score must be at least 1")
    if args.urls_only and not args.urls_output:
        raise ValueError("--urls-only requires --urls-output")

    if args.urls_output:
        url_count = export_matching_social_urls(
            manifest_path=args.manifest,
            output_path=args.urls_output,
            niche=args.niche,
            keywords=args.keyword,
            min_score=args.min_score,
        )
        print(f"Done. Exported {url_count} matching Instagram/TikTok URL(s).")
        if args.urls_only:
            return 0

    matched = collect_videos(
        manifest_path=args.manifest,
        output_folder=args.output,
        niche=args.niche,
        keywords=args.keyword,
        min_score=args.min_score,
        allow_copy_without_ffmpeg=args.allow_copy_without_ffmpeg,
        dry_run=args.dry_run,
    )
    print(f"Done. Matched {matched} authorized video(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
