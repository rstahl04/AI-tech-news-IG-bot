import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tech_ig_bot.models import Article
from tech_ig_bot.web import (
    GenerationJob,
    WebPost,
    generation_job_payload,
    load_recent_posts,
    parse_generate_options,
    render_index,
    render_job_page,
)


class WebTest(unittest.TestCase):
    def test_parse_generate_options_bounds_and_multiline_values(self) -> None:
        options = parse_generate_options(
            "query=quantum+breakthrough%0Arobotics&feed=https%3A%2F%2Fexample.com%2Frss.xml"
            "&per_source=99&top=0&enrich=on"
        )

        self.assertEqual(options.queries, ["quantum breakthrough", "robotics"])
        self.assertEqual(options.feeds, ["https://example.com/rss.xml"])
        self.assertEqual(options.per_source, 99)
        self.assertEqual(options.top, 1)
        self.assertTrue(options.enrich)

    def test_parse_generate_options_accepts_batch_counts(self) -> None:
        options = parse_generate_options("top=10&per_source=25")

        self.assertEqual(options.top, 10)
        self.assertEqual(options.per_source, 25)

    def test_parse_generate_options_caps_extreme_batches(self) -> None:
        options = parse_generate_options("top=999&per_source=999")

        self.assertEqual(options.top, 50)
        self.assertEqual(options.per_source, 100)

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

        self.assertIn("Generate viral tech assets", page)
        self.assertIn("No posts generated yet", page)

    def test_render_job_page_includes_progress_polling(self) -> None:
        job = GenerationJob(
            id="abc123",
            options=parse_generate_options("top=10&per_source=8"),
            output_dir=Path("output"),
        )

        page = render_job_page(job)

        self.assertIn("Your posts are being made one at a time", page)
        self.assertIn("/job/${jobId}/status", page)
        self.assertIn("progress-bar", page)

    def test_generation_job_payload_contains_partial_posts(self) -> None:
        with TemporaryDirectory() as directory:
            output_dir = Path(directory)
            image_path = output_dir / "web" / "run-0001" / "01-story.png"
            caption_path = output_dir / "web" / "run-0001" / "01-story.caption.txt"
            metadata_path = output_dir / "web" / "run-0001" / "01-story.json"
            image_path.parent.mkdir(parents=True)
            image_path.write_bytes(b"fake image")
            caption_path.write_text("Caption text", encoding="utf-8")
            metadata_path.write_text("{}", encoding="utf-8")
            post = WebPost(
                title="AI breakthrough story",
                source="Example",
                url="https://example.com/story",
                score=12.5,
                image_path=image_path,
                caption_path=caption_path,
                metadata_path=metadata_path,
                caption="Caption text",
            )
            job = GenerationJob(
                id="abc123",
                options=parse_generate_options("top=2"),
                output_dir=output_dir,
                status="generating",
                message="Generating 1/2",
                total=2,
                completed=1,
                posts=[post],
            )

            payload = generation_job_payload(job, output_dir)

            self.assertEqual(payload["percent"], 50)
            self.assertIn("AI breakthrough story", str(payload["posts_html"]))


if __name__ == "__main__":
    unittest.main()
