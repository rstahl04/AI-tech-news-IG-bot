import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tech_ig_bot.web import load_recent_posts, parse_generate_options, render_index


class WebTest(unittest.TestCase):
    def test_parse_generate_options_bounds_and_multiline_values(self) -> None:
        options = parse_generate_options(
            "query=quantum+breakthrough%0Arobotics&feed=https%3A%2F%2Fexample.com%2Frss.xml"
            "&per_source=99&top=0&enrich=on"
        )

        self.assertEqual(options.queries, ["quantum breakthrough", "robotics"])
        self.assertEqual(options.feeds, ["https://example.com/rss.xml"])
        self.assertEqual(options.per_source, 20)
        self.assertEqual(options.top, 1)
        self.assertTrue(options.enrich)

    def test_load_recent_posts_reads_generated_metadata(self) -> None:
        with TemporaryDirectory() as directory:
            output_dir = Path(directory)
            run_dir = output_dir / "web" / "run-0001"
            run_dir.mkdir(parents=True)
            image_path = run_dir / "01-story.png"
            caption_path = run_dir / "01-story.caption.txt"
            metadata_path = run_dir / "01-story.json"
            image_path.write_bytes(b"fake image")
            caption_path.write_text("A caption for Instagram.", encoding="utf-8")
            metadata_path.write_text(
                json.dumps(
                    {
                        "title": "AI breakthrough story",
                        "source": "Example",
                        "url": "https://example.com/story",
                        "score": 12.5,
                    }
                ),
                encoding="utf-8",
            )

            posts = load_recent_posts(output_dir)

            self.assertEqual(len(posts), 1)
            self.assertEqual(posts[0].title, "AI breakthrough story")
            self.assertEqual(posts[0].caption, "A caption for Instagram.")

    def test_render_index_includes_form_and_post_actions(self) -> None:
        page = render_index([], Path("output"))

        self.assertIn("Generate explainer assets", page)
        self.assertIn("No posts generated yet", page)


if __name__ == "__main__":
    unittest.main()
