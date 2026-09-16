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

    def test_scales_default_result_count_with_sentence_count(self):
        self.assertEqual(len(extract_key_points("One useful topic appears here.")), 1)
        self.assertEqual(
            len(extract_key_points("First useful topic appears. Second useful topic appears.")),
            2,
        )
        paragraph = " ".join(
            f"Sentence {index} contains a distinct relevant topic." for index in range(1, 7)
        )
        self.assertEqual(len(extract_key_points(paragraph)), 3)

    def test_prefers_relevant_multi_word_phrases(self):
        paragraph = (
            "The campaign needs striking coastal landscape photography for its homepage. "
            "The team will review the assets tomorrow."
        )
        points = extract_key_points(paragraph)
        self.assertTrue(any("coastal landscape photography" in point.lower() for point in points))

    def test_extracts_topic_clauses(self):
        paragraph = (
            "Marketing teams can expand reach when they use social analytics, "
            "and product teams can improve conversion by testing user workflows."
        )

        points = extract_key_points(paragraph)
        self.assertTrue(any("social analytics" in item.lower() for item in points))


if __name__ == "__main__":
    unittest.main()
