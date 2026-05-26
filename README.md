# Authorized Video Niche Collector

This repository contains a small Python CLI that populates a folder with videos
matching a niche such as `gym fails`.

The tool is designed for videos you own, licensed videos, or videos you have
permission to process. It does **not** scrape Instagram/Reels/TikTok, bypass
platform controls, or remove watermarks/attribution. Watermark removal can hide
ownership and creator attribution, so that workflow is intentionally unsupported.

## What it does

- Reads a JSON manifest of authorized video sources.
- Matches entries by niche phrase and keywords in the title, description, tags,
  and filename.
- Accepts local video files or direct media URLs.
- Rejects Instagram and TikTok URLs.
- Uses `ffmpeg` to copy the video stream while removing container metadata.
- Writes matching cleaned videos into an output folder.

## Requirements

- Python 3.10+
- `ffmpeg` on your PATH for metadata stripping

On Ubuntu/Debian:

```bash
sudo apt-get update && sudo apt-get install -y ffmpeg
```

## Manifest format

Create a manifest like `examples/manifest.example.json`:

```json
{
  "videos": [
    {
      "source": "/absolute/path/to/owned-gym-fail-clip.mp4",
      "title": "Gym fail compilation clip",
      "description": "A lifter misses a light warmup rep safely.",
      "tags": ["gym", "fails", "fitness"],
      "authorized": true
    }
  ]
}
```

Every item must include:

- `source`: a local video path or direct media URL.
- `authorized`: `true` only when you own or have permission to process the clip.

Optional fields used for matching:

- `title`
- `description`
- `tags`

## Usage

Preview matches without downloading or copying:

```bash
python3 video_niche_collector.py \
  --manifest examples/manifest.example.json \
  --niche "gym fails" \
  --keyword bench \
  --dry-run
```

Process matching videos into `videos/`:

```bash
python3 video_niche_collector.py \
  --manifest examples/manifest.example.json \
  --niche "gym fails" \
  --keyword bench \
  --output videos
```

If `ffmpeg` is unavailable, the program stops because it cannot guarantee
metadata removal. For local testing only, you can copy matched files without
metadata stripping:

```bash
python3 video_niche_collector.py \
  --manifest examples/manifest.example.json \
  --niche "gym fails" \
  --allow-copy-without-ffmpeg
```

## Notes

This is a metadata/text matcher, not a computer-vision classifier. For higher
accuracy, add good titles, descriptions, and tags to your manifest or extend the
program with an authorized video-analysis API.
