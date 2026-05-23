import unittest

from tech_ig_bot.caption import make_card_caption, make_instagram_caption
from tech_ig_bot.models import Article
from tech_ig_bot.ranker import rank_articles


class RankerCaptionTest(unittest.TestCase):
    def test_ranker_prefers_breakthrough_story(self) -> None:
        ordinary = Article(
            source="Example",
            title="Company updates its app settings screen",
            url="https://example.com/app",
            summary="The release includes small interface changes.",
        )
        breakthrough = Article(
            source="Example",
            title="Quantum battery breakthrough sets new energy storage record",
            url="https://example.com/battery",
            summary="Researchers unveiled a prototype that could change future grids.",
        )

        ranked = rank_articles([ordinary, breakthrough], limit=2)

        self.assertIs(ranked[0], breakthrough)
        self.assertGreater(ranked[0].score, ranked[1].score)

    def test_ranker_prefers_technology_over_acquisition_framing(self) -> None:
        company_story = Article(
            source="Example",
            title=(
                "Locus Robotics Acquires Nexera Robotics, Advancing a Patented "
                "Breakthrough in Mobile Manipulation"
            ),
            url="https://example.com/acquisition",
            summary="The acquisition expands a company portfolio around warehouse robotics.",
        )
        technology_story = Article(
            source="Example",
            title="New robot hand learns delicate tasks from a single demonstration",
            url="https://example.com/robot-hand",
            summary=(
                "Researchers built a robotics prototype that could make mobile "
                "manipulation more useful in factories and homes."
            ),
        )

        ranked = rank_articles([company_story, technology_story], limit=2)

        self.assertIs(ranked[0], technology_story)

    def test_caption_includes_explainer_source_and_hashtags(self) -> None:
        article = Article(
            source="Science Wire",
            title="Robotics breakthrough helps warehouse arms learn faster",
            url="https://example.com/robotics",
            summary="A new machine learning method lets robots learn from fewer demonstrations.",
        )

        card_caption = make_card_caption(article)
        instagram_caption = make_instagram_caption(article)

        self.assertIn("Robots combine sensors", card_caption)
        self.assertIn("FOLLOW for tech explained simply", instagram_caption)
        self.assertIn("Why people are watching:", instagram_caption)
        self.assertIn("Via: Science Wire", instagram_caption)
        self.assertIn("#technology", instagram_caption)


if __name__ == "__main__":
    unittest.main()
