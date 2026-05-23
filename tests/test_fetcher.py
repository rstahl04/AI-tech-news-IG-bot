import unittest

from tech_ig_bot.fetcher import parse_feed_xml


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


if __name__ == "__main__":
    unittest.main()
