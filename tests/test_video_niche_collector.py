import json
import tempfile
import unittest
from pathlib import Path

from video_niche_collector import (
    VideoEntry,
    load_manifest,
    niche_score,
    reject_blocked_source,
    safe_stem,
)


class VideoNicheCollectorTests(unittest.TestCase):
    def test_niche_score_matches_phrase_and_keywords(self):
        entry = VideoEntry(
            source="/videos/clip.mp4",
            title="Gym fail during bench press",
            description="A harmless fitness mistake.",
            tags=("workout",),
            authorized=True,
        )

        self.assertGreaterEqual(niche_score(entry, "gym fails", ["bench"]), 3)

    def test_rejects_instagram_urls(self):
        with self.assertRaises(ValueError):
            reject_blocked_source("https://www.instagram.com/reel/example/")

    def test_rejects_instagram_subdomains(self):
        with self.assertRaises(ValueError):
            reject_blocked_source("https://cdn.instagram.com/example.mp4")

    def test_load_manifest_requires_authorization_flag(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest = Path(temp_dir) / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "videos": [
                            {
                                "source": "/tmp/example.mp4",
                                "title": "Example",
                                "tags": "gym",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            entries = load_manifest(manifest)

        self.assertEqual(len(entries), 1)
        self.assertFalse(entries[0].authorized)
        self.assertEqual(entries[0].tags, ("gym",))

    def test_safe_stem_removes_unsafe_characters(self):
        self.assertEqual(safe_stem("Gym fail: rep #1!", "fallback"), "Gym-fail-rep-1")


if __name__ == "__main__":
    unittest.main()
