import unittest

from tech_ig_bot.headline import make_technology_headline, technology_focus_score
from tech_ig_bot.models import Article


class HeadlineTest(unittest.TestCase):
    def test_business_title_is_rewritten_around_technology(self) -> None:
        article = Article(
            source="News",
            title=(
                "Locus Robotics Acquires Nexera Robotics, Advancing a Patented "
                "Breakthrough in Mobile Manipulation"
            ),
            url="https://example.com/story",
            summary="The work focuses on mobile manipulation for warehouse robots.",
        )

        headline = make_technology_headline(article)

        self.assertEqual(headline, "Mobile Manipulation Robots Take a Step Toward Real-World Use")
        self.assertNotIn("Acquires", headline)
        self.assertLess(technology_focus_score(article), 0)

    def test_company_makes_breakthrough_keeps_the_topic_not_company(self) -> None:
        article = Article(
            source="News",
            title="Xanadu makes quantum computing breakthrough",
            url="https://example.com/quantum",
        )

        headline = make_technology_headline(article)

        self.assertEqual(headline, "A Breakthrough in Quantum Computing Points to Real-World Impact")

    def test_marketing_and_fame_items_are_penalized(self) -> None:
        marketing = Article(
            source="News",
            title="Ferrari is using IBM’s AI to create F1 superfans",
            url="https://example.com/fans",
        )
        hall_of_fame = Article(
            source="News",
            title="Two space shuttle-era spacewalkers enter Astronaut Hall of Fame",
            url="https://example.com/fame",
        )

        self.assertLess(technology_focus_score(marketing), 0)
        self.assertLess(technology_focus_score(hall_of_fame), 0)

    def test_breakthrough_award_is_not_treated_like_research_news(self) -> None:
        article = Article(
            source="News",
            title=(
                "IQVIA SmartSolve eQMS Wins 2024 MedTech Breakthrough Award "
                "Best Use of Artificial Intelligence in Healthcare"
            ),
            url="https://example.com/award",
        )

        self.assertLess(technology_focus_score(article), -20)

    def test_lab_to_market_headline_keeps_technology_topic(self) -> None:
        article = Article(
            source="News",
            title="Solid-State Battery Breakthroughs: From Lab to Road-Ready",
            url="https://example.com/battery",
        )

        headline = make_technology_headline(article)

        self.assertEqual(
            headline,
            "Solid-State Batteries Are Moving From Lab Promise to Road-Ready",
        )


if __name__ == "__main__":
    unittest.main()
