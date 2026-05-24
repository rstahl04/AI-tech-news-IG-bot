import unittest

from tech_ig_bot.image_generation import build_image_prompt
from tech_ig_bot.models import Article


class ImageGenerationTest(unittest.TestCase):
    def test_prompt_is_topic_specific_and_excludes_text(self) -> None:
        article = Article(
            source="Science Wire",
            title="Researchers demonstrate quantum chip breakthrough",
            url="https://example.com/quantum",
            summary="Scientists built a prototype qubit processor.",
        )

        prompt = build_image_prompt(article, "A Prototype Just Set a Quantum Computing Record")

        self.assertIn("quantum", prompt.lower())
        self.assertIn("no text", prompt.lower())
        self.assertIn("no logos", prompt.lower())
        self.assertIn("consistent editorial tech style", prompt.lower())


if __name__ == "__main__":
    unittest.main()
