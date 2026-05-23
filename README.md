# AI Tech News Instagram Bot

This project discovers exciting technology and science stories from public RSS/news
feeds, ranks the best breakthrough candidates, and turns them into Instagram-ready
post assets:

- a 1080x1350 PNG with a bold headline
- an in-image explainer box for a longer caption-style summary
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
for topics such as AI, robotics, quantum computing, batteries, fusion, and other
emerging technologies.

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

The PNG is designed for Instagram portrait posts. The separate caption file
contains a longer caption with source attribution and hashtags.

## Notes

- The scraper uses public RSS/Atom feeds and article pages. Some publishers may
  block automated requests or provide short summaries only.
- The ranking heuristic favors terms associated with breakthroughs, prototypes,
  records, AI, robotics, quantum computing, batteries, energy, biotech, and space.
- Always verify the generated copy and source article before posting.

## Tests

```bash
python3 -m unittest discover -s tests
```
