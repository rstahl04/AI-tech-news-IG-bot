import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image

from tech_ig_bot.models import Article
from tech_ig_bot.renderer import CANVAS_SIZE, render_article_post


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
            paths = render_article_post(article, Path(directory))

            self.assertTrue(paths["image"].exists())
            self.assertTrue(paths["caption"].exists())
            self.assertTrue(paths["metadata"].exists())
            with Image.open(paths["image"]) as image:
                self.assertEqual(image.size, CANVAS_SIZE)


if __name__ == "__main__":
    unittest.main()
