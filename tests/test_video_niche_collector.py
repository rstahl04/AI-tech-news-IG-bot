import json
import tempfile
import unittest
from pathlib import Path

from video_niche_collector import (
    VideoEntry,
    export_matching_social_urls,
    load_manifest,
    niche_score,
    parse_manifest_data,
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

    def test_parse_manifest_data_accepts_payload(self):
        entries = parse_manifest_data(
            {
                "videos": [
                    {
                        "source": "https://www.instagram.com/reel/example/",
                        "title": "Gym fail",
                        "authorized": True,
                    }
                ]
            }
        )

        self.assertEqual(len(entries), 1)
        self.assertTrue(entries[0].authorized)
        self.assertEqual(entries[0].source, "https://www.instagram.com/reel/example/")

    def test_safe_stem_removes_unsafe_characters(self):
        self.assertEqual(safe_stem("Gym fail: rep #1!", "fallback"), "Gym-fail-rep-1")

    def test_exports_matching_social_urls(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            manifest = temp_path / "manifest.json"
            output = temp_path / "matched_urls.txt"
            manifest.write_text(
                json.dumps(
                    {
                        "videos": [
                            {
                                "source": "/tmp/owned.mp4",
                                "page_url": "https://www.instagram.com/reel/gym-fail-1/",
                                "title": "Gym fail",
                                "tags": ["gym", "fails"],
                                "authorized": True,
                            },
                            {
                                "source": "https://www.tiktok.com/@creator/video/123",
                                "title": "Treadmill gym fail",
                                "tags": ["fitness"],
                                "authorized": True,
                            },
                            {
                                "source": "https://www.instagram.com/reel/skip-this/",
                                "title": "Cooking tip",
                                "tags": ["food"],
                                "authorized": True,
                            },
                            {
                                "source": "https://www.instagram.com/reel/not-authorized/",
                                "title": "Gym fail",
                                "tags": ["gym"],
                                "authorized": False,
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            exported_count = export_matching_social_urls(
                manifest_path=manifest,
                output_path=output,
                niche="gym fails",
                keywords=["treadmill"],
                min_score=1,
            )

            exported_urls = output.read_text(encoding="utf-8").splitlines()

        self.assertEqual(exported_count, 2)
        self.assertEqual(
            exported_urls,
            [
                "https://www.instagram.com/reel/gym-fail-1/",
                "https://www.tiktok.com/@creator/video/123",
            ],
        )


if __name__ == "__main__":
    unittest.main()
