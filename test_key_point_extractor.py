import unittest

from key_point_extractor import extract_key_points, extract_key_points_batch


class KeyPointExtractorTests(unittest.TestCase):
    def test_extracts_key_points_from_paragraph(self):
        paragraph = (
            "Machine learning helps businesses automate repetitive tasks. "
            "It can analyze large datasets quickly and find useful patterns. "
            "Developers use it to build smarter applications for customers."
        )

        points = extract_key_points(paragraph)

        self.assertIsInstance(points, list)
        self.assertGreaterEqual(len(points), 2)
        self.assertTrue(any("machine learning" in point.lower() for point in points))
        self.assertTrue(any("developers" in point.lower() for point in points) or any("applications" in point.lower() for point in points))

    def test_supports_large_input_and_batch_processing(self):
        paragraph = " ".join(
            [
                "Artificial intelligence improves decision making and simplifies complex workflows for teams."
                for _ in range(120)
            ]
        )

        points = extract_key_points(paragraph, max_words=1000)
        self.assertIsInstance(points, list)
        self.assertGreaterEqual(len(points), 1)

        batch_results = extract_key_points_batch([paragraph, "Cloud storage helps organizations keep data available and secure."])
        self.assertEqual(len(batch_results), 2)
        self.assertTrue(all(isinstance(item, list) for item in batch_results))

    def test_returns_only_top_four_points(self):
        paragraph = (
            "Machine learning helps businesses automate repetitive tasks. "
            "It can analyze large datasets quickly and find useful patterns. "
            "Developers use it to build smarter applications for customers. "
            "Cloud computing makes data storage easier and more scalable."
        )

        points = extract_key_points(paragraph)
        self.assertLessEqual(len(points), 4)

    def test_extracts_topic_clauses(self):
        paragraph = (
            "Marketing teams can expand reach when they use social analytics, "
            "and product teams can improve conversion by testing user workflows."
        )

        points = extract_key_points(paragraph)
        self.assertTrue(any("social analytics" in item.lower() for item in points))
        self.assertTrue(any("product teams" in item.lower() or "user workflows" in item.lower() for item in points))


if __name__ == "__main__":
    unittest.main()
