import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image

from tech_ig_bot.models import Article
from tech_ig_bot.renderer import CANVAS_SIZE, _highlighted_words, render_article_post


class RendererTest(unittest.TestCase):
    def test_render_article_post_writes_instagram_assets(self) -> None:
        article = Article(
            source="MIT Technology Review",
            title="AI breakthrough gives robots a faster way to learn new tasks",
            url="https://example.com/ai-robots",
            summary=(
                "Researchers built a prototype system that helps robots adapt to new "
                "environments with fewer demonstrations."
            ),
            score=42.0,
        )

        with TemporaryDirectory() as directory:
            paths = render_article_post(article, Path(directory), image_mode="procedural")

            self.assertTrue(paths["image"].exists())
            self.assertTrue(paths["caption"].exists())
            self.assertTrue(paths["metadata"].exists())
            metadata = json.loads(paths["metadata"].read_text(encoding="utf-8"))
            self.assertEqual(metadata["image_provider"], "procedural")
            self.assertEqual(metadata["visual_style"], "robot")
            self.assertIn("Robots", metadata["highlighted_words"])
            self.assertIn("Faster", metadata["highlighted_words"])
            with Image.open(paths["image"]) as image:
                self.assertEqual(image.size, CANVAS_SIZE)

    def test_rendered_visuals_change_by_topic(self) -> None:
        quantum = Article(
            source="Science Wire",
            title="Researchers demonstrate quantum chip breakthrough",
            url="https://example.com/quantum",
            summary="Scientists built a prototype qubit processor.",
        )
        battery = Article(
            source="Science Wire",
            title="Scientists unveil solid-state battery breakthrough",
            url="https://example.com/battery",
            summary="The prototype battery stores more energy for future devices.",
        )

        with TemporaryDirectory() as directory:
            output_dir = Path(directory)
            quantum_paths = render_article_post(quantum, output_dir, index=1, image_mode="procedural")
            battery_paths = render_article_post(battery, output_dir, index=2, image_mode="procedural")

            quantum_metadata = json.loads(quantum_paths["metadata"].read_text(encoding="utf-8"))
            battery_metadata = json.loads(battery_paths["metadata"].read_text(encoding="utf-8"))
            self.assertEqual(quantum_metadata["visual_style"], "quantum")
            self.assertEqual(battery_metadata["visual_style"], "battery")
            self.assertNotEqual(
                quantum_paths["image"].read_bytes(),
                battery_paths["image"].read_bytes(),
            )

    def test_headline_highlighting_falls_back_to_strong_words(self) -> None:
        highlighted = _highlighted_words("What Is a Wormhole Good For Anyway")

        self.assertIn("Wormhole", highlighted)
        self.assertNotIn("What", highlighted)
        self.assertNotIn("Anyway", highlighted)

    def test_metadata_highlights_headline_not_description(self) -> None:
        article = Article(
            source="Science Wire",
            title="Prototype sets record for optical quantum information technology",
            url="https://example.com/simple-quantum",
            summary="Battery robots scientists sunlight touch.",
        )

        with TemporaryDirectory() as directory:
            paths = render_article_post(article, Path(directory), image_mode="procedural")
            metadata = json.loads(paths["metadata"].read_text(encoding="utf-8"))

        self.assertIn("Prototype", metadata["highlighted_words"])
        self.assertIn("Quantum", metadata["highlighted_words"])
        self.assertNotIn("Battery", metadata["highlighted_words"])
        self.assertNotIn("Robots", metadata["highlighted_words"])


if __name__ == "__main__":
    unittest.main()
