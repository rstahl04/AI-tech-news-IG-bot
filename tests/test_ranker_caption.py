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

    def test_ranker_prefers_unique_generated_headlines_for_batches(self) -> None:
        first = Article(
            source="Example",
            title="AI prototype breakthrough for office workflows",
            url="https://example.com/ai-1",
            summary="Researchers demonstrated an artificial intelligence prototype.",
        )
        duplicate_hook = Article(
            source="Example",
            title="Another AI prototype breakthrough for workplace machines",
            url="https://example.com/ai-2",
            summary="Researchers demonstrated another artificial intelligence prototype.",
        )
        unique = Article(
            source="Example",
            title="Scientists unveil solid-state battery breakthrough",
            url="https://example.com/battery",
            summary="A battery prototype stores more energy.",
        )

        ranked = rank_articles([first, duplicate_hook, unique], limit=3)

        self.assertIs(ranked[0], first)
        self.assertIs(ranked[1], unique)
        self.assertIs(ranked[2], duplicate_hook)

    def test_ranker_spreads_batch_across_tech_topics(self) -> None:
        ai_1 = Article("Example", "AI prototype breakthrough for office workflows", "https://example.com/ai-1", summary="Researchers demonstrated artificial intelligence.")
        ai_2 = Article("Example", "New AI system could transform engineering", "https://example.com/ai-2", summary="Researchers built an artificial intelligence prototype.")
        battery = Article("Example", "Scientists unveil solid-state battery breakthrough", "https://example.com/battery", summary="A battery prototype stores more energy.")
        robot = Article("Example", "Researchers demonstrate humanoid robot artificial muscle", "https://example.com/robot", summary="A humanoid robot prototype gains feedback.")

        ranked = rank_articles([ai_1, ai_2, battery, robot], limit=3)

        self.assertIn(battery, ranked[:3])
        self.assertIn(robot, ranked[:3])
        self.assertEqual(len(ranked), 3)

    def test_ranker_groups_related_quantum_topics_for_variety(self) -> None:
        quantum_computing = Article(
            "Example",
            "Quantum breakthrough could revolutionize teleportation and computing",
            "https://example.com/quantum-computing",
            summary="Researchers demonstrated quantum computing progress.",
        )
        quantum_chip = Article(
            "Example",
            "Prototype sets record for optical quantum information technology",
            "https://example.com/quantum-chip",
            summary="Scientists built a quantum chip prototype.",
        )
        battery = Article(
            "Example",
            "Scientists unveil DNA battery that charges directly from the sun",
            "https://example.com/battery",
            summary="A battery prototype stores more energy.",
        )

        ranked = rank_articles([quantum_computing, quantum_chip, battery], limit=2)

        self.assertIn(battery, ranked)
        self.assertEqual(len(ranked), 2)

    def test_ranker_filters_syndicated_versions_of_same_story(self) -> None:
        first = Article(
            "Example",
            "OpenAI's AI solves 80-year-old maths problem, marking major breakthrough",
            "https://example.com/ai-math-1",
            summary="Artificial intelligence made a mathematics breakthrough.",
        )
        duplicate = Article(
            "Example",
            "Mathematicians stunned by AI's biggest breakthrough in mathematics yet",
            "https://example.com/ai-math-2",
            summary="Experts say the AI math result is a breakthrough.",
        )
        battery = Article(
            "Example",
            "Scientists unveil DNA battery that charges directly from the sun",
            "https://example.com/battery",
            summary="A battery prototype stores more energy.",
        )

        ranked = rank_articles([first, duplicate, battery], limit=2)

        self.assertIn(battery, ranked)
        self.assertEqual(len(ranked), 2)
        self.assertFalse(first in ranked and duplicate in ranked)

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
