# AI Tech News Instagram Bot

This project discovers current technology and science stories from public RSS/news
feeds, favors expert/research-backed breakthroughs, and turns them into Instagram-ready
posts modeled after viral educational technology pages:

- a 1080x1350 PNG with a scroll-stopping technology headline
- AI-generated topic artwork related to the headline, with an offline procedural fallback
- an in-image quick explainer box for mobile-friendly learning
- a separate `.caption.txt` file ready to paste into Instagram
- a `.json` metadata file with source URL, score, and output paths

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
```

## Generate a post

```bash
tech-ig-bot --top 3 --output-dir output
```

The default run scans curated technology/science feeds plus Bing News RSS queries
for topics such as AI, robotics, quantum computing, batteries, fusion, expert
commentary, research prototypes, and other emerging technologies.

Add your own discovery terms or RSS feeds:

```bash
tech-ig-bot \
  --query "space propulsion breakthrough" \
  --query "humanoid robot prototype" \
  --feed "https://example.com/rss.xml" \
  --top 2
```

Preview ranked stories without creating images:

```bash
tech-ig-bot --dry-run --no-enrich
```

Generate without external AI image generation, using the offline fallback instead:

```bash
tech-ig-bot --image-mode procedural --top 1 --output-dir output
```

## Use the website

Start the local website:

```bash
python3 -m tech_ig_bot.web
```

Then open:

```text
http://127.0.0.1:8000
```

The website lets you:

- enter extra search topics or RSS feeds
- choose how many Instagram posts to generate
- preview the generated image
- copy the long caption
- download the PNG, caption text, and metadata

If you installed the package, you can also start it with:

```bash
tech-ig-bot-web
```

## Output

For each selected story, the bot writes files like:

```text
output/
  01-ai-breakthrough-gives-robots-a-faster-way-to-learn.png
  01-ai-breakthrough-gives-robots-a-faster-way-to-learn.caption.txt
  01-ai-breakthrough-gives-robots-a-faster-way-to-learn.json
```

The metadata includes `image_provider`, `image_prompt`, and `visual_style` so you can see whether the post used AI image generation or the fallback renderer.

The PNG is designed for Instagram portrait posts with a viral, learn-something-new technology explainer style. Each image uses an AI image-generation request related to the story topic and headline, so quantum, robotics, battery, biotech, chip, space, clean-energy, and AI posts do not all look the same. If the image service is unavailable, the renderer falls back to deterministic procedural artwork. The separate caption file contains a follow-style hook, plain-language explanation, source attribution, and hashtags such as #technology and #reels.

## Notes

- The scraper uses public RSS/Atom feeds and article pages. Some publishers may
  block automated requests or provide short summaries only.
- The ranking heuristic favors expert/research signals, breakthroughs, prototypes,
  records, AI, robotics, quantum computing, batteries, energy, biotech, and space,
  while pushing down acquisitions, awards, marketing posts, and unrelated gaming/news noise.
- Always verify the generated copy and source article before posting.

## Tests

```bash
python3 -m unittest discover -s tests
```
