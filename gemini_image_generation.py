import base64
import os
import re
from pathlib import Path
from typing import Callable, Sequence

from google import genai
from google.genai import interactions as genai_interactions


DEFAULT_GEMINI_IMAGE_MODEL = "gemini-3.1-flash-lite-image"
ProgressCallback = Callable[[str], None]


def _safe_name(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_")
    return cleaned[:80] or "gemini_image"


def generate_gemini_images(
    queries: Sequence[str],
    api_key: str,
    destination: str | Path = "gemini_images",
    images_per_query: int = 5,
    model: str | None = None,
    on_progress: ProgressCallback | None = None,
) -> int:
    """Generate and save images for each query, returning the number saved."""
    normalized_key = api_key.strip().strip('"').strip("'").strip()
    if not normalized_key:
        raise ValueError("A Gemini API key is required to generate images.")
    if images_per_query < 1:
        raise ValueError("images_per_query must be at least 1.")

    image_queries = [query.strip() for query in queries if query.strip()]
    if not image_queries:
        raise ValueError("At least one non-empty image prompt is required.")

    image_model = (
        model or os.getenv("GEMINI_IMAGE_MODEL", "").strip() or DEFAULT_GEMINI_IMAGE_MODEL
    )
    client = genai.Client(api_key=normalized_key)
    root = Path(destination)
    root.mkdir(parents=True, exist_ok=True)
    downloaded = 0

    def report(message: str) -> None:
        if on_progress is not None:
            on_progress(message)

    for query in image_queries:
        query_folder = root / _safe_name(query)
        query_folder.mkdir(parents=True, exist_ok=True)
        report(f"Generating {images_per_query} Gemini image(s) for '{query}'...")

        for index in range(1, images_per_query + 1):
            interaction = client.interactions.create(
                model=image_model,
                input=(
                    "Create one polished, original image based on this visual brief. "
                    "Return an image, not a written description: "
                    f"{query}"
                ),
            )
            if not isinstance(interaction, genai_interactions.Interaction):
                raise RuntimeError("Gemini returned a streaming response; a completed image response is required.")
            output_image = interaction.output_image
            if output_image is None or not output_image.data:
                status = getattr(interaction, "status", "unknown")
                raise RuntimeError(
                    f"Gemini returned no image for '{query}' "
                    f"(model {image_model}, status {status})."
                )

            image_bytes = base64.b64decode(output_image.data, validate=True)
            extension = {
                "image/jpeg": ".jpg",
                "image/webp": ".webp",
                "image/gif": ".gif",
                "image/bmp": ".bmp",
                "image/tiff": ".tiff",
                "image/heic": ".heic",
                "image/heif": ".heif",
            }.get(output_image.mime_type or "", ".png")
            image_path = query_folder / f"{_safe_name(query)}_{index}{extension}"
            image_path.write_bytes(image_bytes)
            downloaded += 1
            report(f"Saved Gemini image {downloaded}: {image_path}")

    return downloaded
