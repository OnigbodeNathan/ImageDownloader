import re
from pathlib import Path
from typing import Any, Callable, Dict, List
from urllib.parse import quote

import requests


GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"
REQUEST_TIMEOUT = 30
ProgressCallback = Callable[[str], None]


def _safe_name(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_")
    return cleaned[:80] or "google_image"


def search_google_images(
    query: str,
    api_key: str,
    search_engine_id: str,
    count: int = 10,
) -> List[Dict[str, Any]]:
    """Return Google Custom Search image results for a query."""
    if not api_key.strip() or not search_engine_id.strip():
        raise ValueError("A Google API key and Programmable Search Engine ID are required.")
    response = requests.get(
        GOOGLE_SEARCH_URL,
        params={
            "key": api_key,
            "cx": search_engine_id,
            "q": query,
            "searchType": "image",
            "num": min(max(count, 1), 10),
            "safe": "active",
        },
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    items = response.json().get("items", [])
    return [
        {
            "title": item.get("title", query),
            "link": item.get("link", ""),
            "thumbnail": item.get("image", {}).get("thumbnailLink", ""),
            "source_page": item.get("image", {}).get("contextLink", ""),
        }
        for item in items
        if item.get("link")
    ]


def download_google_images(
    queries: List[str],
    api_key: str,
    search_engine_id: str,
    destination: str = "google_images",
    images_per_query: int = 10,
    on_progress: ProgressCallback | None = None,
) -> int:
    """Search and download Google image results, returning successful downloads."""
    root = Path(destination)
    root.mkdir(parents=True, exist_ok=True)
    downloaded = 0

    def report(message: str) -> None:
        if on_progress is not None:
            on_progress(message)

    for query in queries:
        query_folder = root / _safe_name(query)
        query_folder.mkdir(parents=True, exist_ok=True)
        report(f"Searching Google Images for '{query}'...")
        results = search_google_images(query, api_key, search_engine_id, images_per_query)
        for index, result in enumerate(results, start=1):
            try:
                image_response = requests.get(result["link"], timeout=REQUEST_TIMEOUT)
                image_response.raise_for_status()
                image_path = query_folder / f"{_safe_name(query)}_{index}.jpg"
                image_path.write_bytes(image_response.content)
                downloaded += 1
                report(f"Downloaded Google image {downloaded}: {image_path}")
            except requests.RequestException as exc:
                report(f"Skipped Google image '{result.get('title', query)}': {exc}")
    return downloaded