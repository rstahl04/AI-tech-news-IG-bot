import unittest

from web_niche_collector import matching_social_urls, parse_social_url_lines, split_keywords


class WebNicheCollectorTests(unittest.TestCase):
    def test_parse_social_url_lines_accepts_notes_after_pipe(self):
        entries = parse_social_url_lines(
            "https://www.instagram.com/reel/example/ | gym fail bench press",
            assumed_context="gym fails",
        )

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].source, "https://www.instagram.com/reel/example/")
        self.assertTrue(entries[0].authorized)
        self.assertIn("bench", entries[0].searchable_text)

    def test_parse_social_url_lines_rejects_non_social_url(self):
        with self.assertRaises(ValueError):
            parse_social_url_lines("https://example.com/video.mp4 | gym fail")

    def test_matching_social_urls_deduplicates_matches(self):
        entries = parse_social_url_lines(
            "\n".join(
                [
                    "https://www.instagram.com/reel/example/ | gym fail",
                    "https://www.instagram.com/reel/example/ | gym fail",
                    "https://www.tiktok.com/@creator/video/123 | cooking",
                ]
            ),
            assumed_context="",
        )

        matches, messages = matching_social_urls(entries, "gym fails", [], 1)

        self.assertEqual(matches, ["https://www.instagram.com/reel/example/"])
        self.assertTrue(any("duplicate" in message for message in messages))

    def test_split_keywords_supports_commas_and_newlines(self):
        self.assertEqual(split_keywords("bench, treadmill\nsquat"), ["bench", "treadmill", "squat"])


if __name__ == "__main__":
    unittest.main()
