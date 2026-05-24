import unittest

from unittest.mock import patch

from tech_ig_bot.fetcher import collect_articles, parse_feed_xml
from tech_ig_bot.models import Article, FeedSource


class FetcherTest(unittest.TestCase):
    def test_parse_rss_feed_item(self) -> None:
        xml = """<?xml version="1.0"?>
        <rss version="2.0">
          <channel>
            <item>
              <title>New quantum chip reaches a record milestone</title>
              <link>https://example.com/quantum-chip</link>
              <description>&lt;p&gt;Researchers demonstrated a faster prototype.&lt;/p&gt;</description>
              <pubDate>Sat, 23 May 2026 12:00:00 +0000</pubDate>
            </item>
          </channel>
        </rss>
        """

        articles = parse_feed_xml(xml, "Example Feed")

        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0].source, "Example Feed")
        self.assertEqual(articles[0].title, "New quantum chip reaches a record milestone")
        self.assertEqual(articles[0].summary, "Researchers demonstrated a faster prototype.")

    def test_collect_articles_dedupes_bing_redirects_to_same_story(self) -> None:
        articles = [
            Article(
                source="A",
                title="Scientists unveil DNA battery",
                url="https://www.bing.com/news/apiclick.aspx?url=https%3A%2F%2Fexample.com%2Fstory",
            ),
            Article(
                source="B",
                title="Scientists unveil DNA battery",
                url="https://example.com/story/",
            ),
        ]

        with patch("tech_ig_bot.fetcher.fetch_feed", return_value=articles):
            collected = collect_articles([FeedSource("Test", "https://example.com/feed")], enrich=False)

        self.assertEqual(len(collected), 1)


if __name__ == "__main__":
    unittest.main()
