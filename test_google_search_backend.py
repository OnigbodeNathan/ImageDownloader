import unittest

import google_search_backend as backend


class GoogleSearchBackendTests(unittest.TestCase):
    def setUp(self):
        self.client = backend.app.test_client()

    def test_search_requires_google_credentials(self):
        original_key = backend.GOOGLE_API_KEY
        original_cx = backend.GOOGLE_CX
        backend.GOOGLE_API_KEY = ""
        backend.GOOGLE_CX = ""
        try:
            response = self.client.post(
                "/search",
                json={"query": "test query", "num_results": 5, "skip_cache": True},
            )
            self.assertEqual(response.status_code, 400)
            body = response.get_json()
            self.assertIn("GOOGLE_API_KEY", str(body))
            self.assertIn("GOOGLE_CX", str(body))
        finally:
            backend.GOOGLE_API_KEY = original_key
            backend.GOOGLE_CX = original_cx


if __name__ == "__main__":
    unittest.main()
