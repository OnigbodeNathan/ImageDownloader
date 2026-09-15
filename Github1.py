import argparse
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Sequence

import requests
from key_point_extractor import extract_key_points


# ====== CONFIGURATION ======
EXTRACTOR_OUTPUT = "extractor_output.json"
TOTAL_IMAGES_PER_QUERY = 10
IMAGES_PER_PAGE = 80
IMAGE_ORIENTATION = "landscape"
IMAGE_SIZE = "large"
IMAGE_COLOR = None
SAVE_FOLDER = "pexels_images"
REQUEST_TIMEOUT = 30


def _unique_queries(key_points: List[str]) -> List[str]:
    queries: List[str] = []
    seen = set()
    for key_point in key_points:
        query = str(key_point).strip()
        normalized_query = query.casefold()
        if query and normalized_query not in seen:
            seen.add(normalized_query)
            queries.append(query)
    return queries


def load_search_queries(output_file: str = EXTRACTOR_OUTPUT) -> List[str]:
    """Load unique search queries from key_point_extractor.py output."""
    output_path = Path(output_file)
    if not output_path.exists():
        raise FileNotFoundError(
            f"Extractor output not found: {output_path}. "
            "Run run_key_point_extractor.py first."
        )

    payload: Any = json.loads(output_path.read_text(encoding="utf-8"))
    records = payload if isinstance(payload, list) else [payload]
    all_key_points: List[str] = []

    for record in records:
        if not isinstance(record, dict):
            continue
        record_key_points = record.get("key_points", [])
        if isinstance(record_key_points, str):
            record_key_points = [record_key_points]
        if not isinstance(record_key_points, list):
            continue
        all_key_points.extend(str(key_point) for key_point in record_key_points)

    queries = _unique_queries(all_key_points)
    if not queries:
        raise ValueError(f"No key points found in {output_path}.")
    return queries


def load_queries_from_text(text: str) -> List[str]:
    """Extract image-search queries directly from source text."""
    queries = _unique_queries(extract_key_points(text))
    if not queries:
        raise ValueError("No key points could be extracted from the supplied text.")
    return queries


def download_images_for_query(query: str, headers: Dict[str, str]) -> None:
    query_folder = os.path.join(SAVE_FOLDER, query.replace(" ", "_"))
    os.makedirs(query_folder, exist_ok=True)

    print(f"\n🔹 Downloading up to {TOTAL_IMAGES_PER_QUERY} images for '{query}'...")

    page = 1
    downloaded_count = 0

    while downloaded_count < TOTAL_IMAGES_PER_QUERY:
        remaining_images = TOTAL_IMAGES_PER_QUERY - downloaded_count
        images_to_fetch = min(IMAGES_PER_PAGE, remaining_images)

        params = {
            "query": query,
            "per_page": images_to_fetch,
            "page": page,
            "orientation": IMAGE_ORIENTATION,
            "size": IMAGE_SIZE,
        }
        if IMAGE_COLOR:
            params["color"] = IMAGE_COLOR

        response = requests.get(
            "https://api.pexels.com/v1/search",
            params=params,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )

        if response.status_code == 200:
            images = response.json().get("photos", [])

            if not images:
                print(f"⚠️ No more images found for '{query}'. Stopping download.")
                break

            for img in images:
                downloaded_count += 1
                img_url = img["src"]["original"]
                img_path = os.path.join(query_folder, f"{query}_{downloaded_count}.jpg")

                try:
                    image_response = requests.get(img_url, timeout=REQUEST_TIMEOUT)
                    image_response.raise_for_status()
                    with open(img_path, "wb") as file:
                        file.write(image_response.content)
                    print(f"✅ Downloaded {downloaded_count} for '{query}': {img_path}")
                except Exception as e:
                    print(f"⚠️ Error downloading {img_url}: {e}")

                if downloaded_count >= TOTAL_IMAGES_PER_QUERY:
                    break

            page += 1
            time.sleep(1)

        else:
            print(f"❌ Error fetching images for '{query}': {response.status_code} {response.text}")
            break

    print(f"🎉 Finished downloading {downloaded_count} images for '{query}'!")


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract key points and download matching images from Pexels."
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument(
        "--input",
        default=EXTRACTOR_OUTPUT,
        help=f"Extractor JSON file (default: {EXTRACTOR_OUTPUT}).",
    )
    source.add_argument(
        "--query",
        help="Direct text to extract key points from and use as image queries.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    pexels_api_key = os.getenv("PEXELS_API_KEY")
    if not pexels_api_key:
        print(
            "PEXELS_API_KEY is not set. Set it to your active Pexels API key "
            "before running this script."
        )
        return 1

    try:
        search_queries = (
            load_queries_from_text(args.query)
            if args.query is not None
            else load_search_queries(args.input)
        )
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc))
        return 1

    os.makedirs(SAVE_FOLDER, exist_ok=True)
    headers = {"Authorization": pexels_api_key}
    print(f"Loaded {len(search_queries)} key-point queries from {EXTRACTOR_OUTPUT}.")

    for search_query in search_queries:
        download_images_for_query(search_query, headers)

    print("\n🚀 All downloads complete!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())