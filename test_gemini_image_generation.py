import base64
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from google.genai import interactions

from gemini_image_generation import generate_gemini_images
from interface import WorkflowApp


class GeminiImageGenerationTests(unittest.TestCase):
    @patch("gemini_image_generation.genai.Client")
    def test_saves_requested_number_of_generated_images(self, client_factory):
        image_bytes = b"test-image-data"
        image_data = base64.b64encode(image_bytes).decode("ascii")
        client = Mock()
        client_factory.return_value = client
        client.interactions.create.return_value = interactions.Interaction(
            status="completed",
            output_image=interactions.ImageContent(data=image_data, mime_type="image/jpeg"),
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            count = generate_gemini_images(
                ["playstation 5"],
                " test-key ",
                destination=temporary_directory,
                images_per_query=5,
            )

            image_paths = list(Path(temporary_directory).rglob("*.jpg"))
            self.assertEqual(count, 5)
            self.assertEqual(len(image_paths), 5)
            self.assertTrue(all(path.read_bytes() == image_bytes for path in image_paths))

        client_factory.assert_called_once_with(api_key="test-key")
        self.assertEqual(client.interactions.create.call_count, 5)

    @patch("gemini_image_generation.genai.Client")
    def test_reports_when_gemini_returns_no_image(self, client_factory):
        client = Mock()
        client_factory.return_value = client
        client.interactions.create.return_value = interactions.Interaction(
            status="completed",
            output_image=None,
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            with self.assertRaisesRegex(RuntimeError, "Gemini returned no image"):
                generate_gemini_images(
                    ["playstation 5"],
                    "test-key",
                    destination=temporary_directory,
                    images_per_query=1,
                )

    def test_rejects_empty_key_without_calling_gemini(self):
        with patch("gemini_image_generation.genai.Client") as client_factory:
            with self.assertRaisesRegex(ValueError, "API key is required"):
                generate_gemini_images(["playstation 5"], "  ")
            client_factory.assert_not_called()

    @patch("gemini_image_generation.generate_gemini_images", return_value=5)
    def test_interface_runs_gemini_generation_for_selected_key_points(self, generate_images):
        app = WorkflowApp.__new__(WorkflowApp)
        app.root = Mock()
        app.root.after.side_effect = lambda *args: args[-1]()
        app.status = Mock()
        app.download_button = Mock()
        app._ui_log = Mock()

        app._run_workflow(
            ["playstation 5"],
            use_pexels=False,
            use_gemini=True,
            gemini_key="test-key",
            use_google=False,
            google_key="",
            google_engine_id="",
        )

        generate_images.assert_called_once_with(
            ["playstation 5"],
            "test-key",
            images_per_query=5,
            on_progress=app._ui_log,
        )
        app.status.configure.assert_called_once_with(
            text="Complete: 5 image(s) generated or downloaded."
        )


if __name__ == "__main__":
    unittest.main()
