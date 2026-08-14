import argparse
import csv
import json
import os
import re
import sys
import time 
import requests
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple


DEFAULT_RESULT_KEYS = [
    "image_path",
    "image_name",
    "key_points",
    "keypoint",
    "key_point",
    "features",
    "description",
    "metadata",
]


@dataclass
class SearchResult:
    source: str
    image_path: str
    result_id: str
    query: str
    matches: List[Dict[str, Any]]
    notes: str = ""


class BackendClient:
    """Client for communicating with Google Search Backend"""
    def __init__(self, backend_url: str, logger: Optional["ProcedureLogger"] = None):
        self.backend_url = backend_url.rstrip("/")
        self.logger = logger or ProcedureLogger(verbose=False)
    
    def health(self) -> bool:
        """Check if backend is running"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            self.logger.item(f"Backend health check failed: {e}")
            return False
    
    def web_search(self, query: str, num_results: int = 5, skip_cache: bool = False) -> List[Dict[str, Any]]:
        """Search the web using backend"""
        try:
            response = requests.post(
                f"{self.backend_url}/search",
                json={"query": query, "num_results": num_results, "skip_cache": skip_cache},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                wait_time = e.response.json().get("wait_seconds", 60)
                self.logger.item(f"Rate limited. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                return self.web_search(query, num_results, skip_cache)
            else:
                self.logger.item(f"Search failed: {e}")
                return []
        except Exception as e:
            self.logger.item(f"Search error: {e}")
            return []
    
    def image_search(self, query: str, num_results: int = 5, skip_cache: bool = False, download: bool = False) -> List[Dict[str, Any]]:
        """Search for images using backend"""
        try:
            response = requests.post(
                f"{self.backend_url}/image-search",
                json={"query": query, "num_results": num_results, "skip_cache": skip_cache, "download": download},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                wait_time = e.response.json().get("wait_seconds", 60)
                self.logger.item(f"Rate limited. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                return self.image_search(query, num_results, skip_cache, download)
            else:
                self.logger.item(f"Image search failed: {e}")
                return []
        except Exception as e:
            self.logger.item(f"Image search error: {e}")
            return []
    
    def list_cache(self) -> List[Dict[str, Any]]:
        """List all cached results"""
        try:
            response = requests.get(f"{self.backend_url}/cache", timeout=5)
            response.raise_for_status()
            return response.json().get("caches", [])
        except Exception as e:
            self.logger.item(f"Failed to list cache: {e}")
            return []
    
    def delete_cache(self, search_type: str, query: str) -> bool:
        """Delete a specific cached result"""
        try:
            response = requests.delete(f"{self.backend_url}/cache/{search_type}/{query}", timeout=5)
            return response.status_code == 200
        except Exception as e:
            self.logger.item(f"Failed to delete cache: {e}")
            return False
    
    def clear_all_cache(self) -> bool:
        """Clear all cached results"""
        try:
            response = requests.delete(f"{self.backend_url}/cache", timeout=5)
            return response.status_code == 200
        except Exception as e:
            self.logger.item(f"Failed to clear cache: {e}")
            return False
    
    def list_downloaded_media(self) -> List[Dict[str, Any]]:
        """List all downloaded media files"""
        try:
            response = requests.get(f"{self.backend_url}/downloaded-media", timeout=5)
            response.raise_for_status()
            return response.json().get("downloaded_files", [])
        except Exception as e:
            self.logger.item(f"Failed to list downloads: {e}")
            return []
    
    def clear_downloaded_media(self) -> bool:
        """Delete all downloaded media files"""
        try:
            response = requests.delete(f"{self.backend_url}/downloaded-media", timeout=5)
            return response.status_code == 200
        except Exception as e:
            self.logger.item(f"Failed to clear downloads: {e}")
            return False


class ProcedureLogger:
    def __init__(self, verbose: bool = True):
        self.verbose = verbose

    def log(self, message: str):
        if self.verbose:
            print(message)

    def section(self, title: str):
        if self.verbose:
            print(f"\n=== {title} ===")

    def item(self, message: str):
        if self.verbose:
            print(f"  - {message}")


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (int, float, bool)):
        return str(value)
    return str(value).strip()


def flatten_key_points(raw: Any) -> List[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return []
        return [part.strip() for part in re.split(r"[\n,;|]+", text) if part.strip()]
    if isinstance(raw, (list, tuple, set)):
        values: List[str] = []
        for item in raw:
            values.extend(flatten_key_points(item))
        return values
    if isinstance(raw, dict):
        values = []
        for key, value in raw.items():
            if key.lower() in {"key_points", "keypoint", "key_point", "features"}:
                values.extend(flatten_key_points(value))
            elif isinstance(value, (str, int, float, bool)) and normalize_text(value):
                values.append(normalize_text(value))
        return values
    return [normalize_text(raw)]


def coerce_image_path(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    candidate = normalize_text(value)
    return candidate or fallback


def parse_json_file(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def parse_csv_file(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader)


def parse_text_file(path: Path) -> List[str]:
    with path.open("r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip()]


def load_extractor_results(path: str | Path) -> List[Dict[str, Any]]:
    source_path = Path(path)
    if not source_path.exists():
        raise FileNotFoundError(f"Extractor result file not found: {source_path}")

    if source_path.is_dir():
        records: List[Dict[str, Any]] = []
        for child in sorted(source_path.iterdir()):
            if child.is_file() and child.suffix.lower() in {".json", ".csv", ".txt"}:
                records.extend(load_extractor_results(child))
        return records

    suffix = source_path.suffix.lower()

    if suffix == ".json":
        payload = parse_json_file(source_path)
        if isinstance(payload, list):
            return [normalize_extractor_record(item, source=str(source_path)) for item in payload]
        if isinstance(payload, dict):
            if any(key in payload for key in ["results", "items", "records", "data"]):
                nested = payload.get("results") or payload.get("items") or payload.get("records") or payload.get("data")
                if isinstance(nested, list):
                    return [normalize_extractor_record(item, source=str(source_path)) for item in nested]
            return [normalize_extractor_record(payload, source=str(source_path))]
        return [{"source": str(source_path), "image_path": str(source_path), "key_points": [str(payload)]}]

    if suffix == ".csv":
        rows = parse_csv_file(source_path)
        normalized_rows: List[Dict[str, Any]] = []
        for row in rows:
            normalized_rows.append(normalize_extractor_record(row, source=str(source_path)))
        return normalized_rows

    if suffix == ".txt":
        lines = parse_text_file(source_path)
        return [{"source": str(source_path), "image_path": str(source_path), "key_points": lines}]

    raise ValueError(f"Unsupported extractor output format: {source_path}")


def normalize_extractor_record(item: Dict[str, Any], source: str) -> Dict[str, Any]:
    if not isinstance(item, dict):
        return {"source": source, "image_path": source, "key_points": flatten_key_points(item)}

    image_path = ""
    image_name = ""
    for key in ["image_path", "path", "image", "file_path", "source_file"]:
        if key in item:
            image_path = coerce_image_path(item.get(key))
            break
    if not image_path:
        for key in ["image_name", "filename", "name"]:
            if key in item:
                image_name = coerce_image_path(item.get(key))
                break

    key_points: List[str] = []
    for key in DEFAULT_RESULT_KEYS:
        if key in item:
            key_points.extend(flatten_key_points(item.get(key)))

    if not key_points and "content" in item:
        key_points.extend(flatten_key_points(item.get("content")))

    if not key_points:
        for value in item.values():
            if isinstance(value, (str, int, float, bool)):
                key_points.extend(flatten_key_points(value))

    return {
        "source": source,
        "image_path": image_path or image_name,
        "image_name": image_name or Path(image_path).name if image_path else "",
        "key_points": list(dict.fromkeys(key_points)),
        "metadata": {k: v for k, v in item.items() if k not in {"image_path", "path", "image", "file_path", "source_file"}},
    }


def collate_extractor_results(records: Iterable[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        image_path = coerce_image_path(record.get("image_path"), record.get("image_name", ""))
        if not image_path:
            image_path = record.get("source", "unknown")
        grouped.setdefault(image_path, []).append(record)
    return grouped


def search_for_key_point(result_record: Dict[str, Any], backend_client: BackendClient, logger: ProcedureLogger, search_type: str = "web", download_images: bool = False) -> List[Dict[str, Any]]:
    image_path = coerce_image_path(result_record.get("image_path"), result_record.get("image_name", "unknown"))
    key_points = result_record.get("key_points", [])

    logger.section(f"Searching for result: {image_path}")
    logger.item(f"Key points collected: {len(key_points)}")

    all_hits: List[Dict[str, Any]] = []
    for idx, key_point in enumerate(key_points):
        logger.item(f"Running {search_type} search #{idx + 1} for key point: {key_point}")
        
        if search_type == "image":
            matches = backend_client.image_search(key_point, num_results=5, download=download_images)
        else:
            matches = backend_client.web_search(key_point, num_results=5)
        
        if matches:
            logger.item(f"Found {len(matches)} results for query '{key_point}'")
        else:
            logger.item(f"No results found for '{key_point}'")
        
        all_hits.append({
            "query": key_point,
            "matches": matches,
        })

    return all_hits


def run_search_for_collated_results(collated: Dict[str, List[Dict[str, Any]]], backend_client: BackendClient, logger: ProcedureLogger, search_type: str = "web", download_images: bool = False) -> Dict[str, List[Dict[str, Any]]]:
    search_outputs: Dict[str, List[Dict[str, Any]]] = {}
    logger.section("Collated search execution")
    logger.item(f"Total unique images to process: {len(collated)}")
    logger.item(f"Search type: {search_type}")
    if download_images:
        logger.item(f"Image downloading: enabled")

    for image_id, records in collated.items():
        logger.item(f"Processing image: {image_id}")
        results_for_image: List[Dict[str, Any]] = []
        for record in records:
            search_result = search_for_key_point(record, backend_client, logger, search_type=search_type, download_images=download_images)
            results_for_image.append({
                "source": record.get("source", image_id),
                "image_path": image_id,
                "searches": search_result,
            })
        search_outputs[image_id] = results_for_image
    return search_outputs


def print_summary(search_outputs: Dict[str, List[Dict[str, Any]]], logger: ProcedureLogger):
    logger.section("Search summary")
    total_results = 0
    total_queries = 0
    for image_key, image_results in search_outputs.items():
        total_results += len(image_results)
        for entry in image_results:
            total_queries += len(entry.get("searches", []))
            for search in entry.get("searches", []):
                matches = search.get("matches", [])
                logger.item(f"{image_key} | '{search.get('query')}' -> {len(matches)} matches")
    logger.item(f"Processed images: {len(search_outputs)}")
    logger.item(f"Processed records: {total_results}")
    logger.item(f"Executed queries: {total_queries}")



def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search key-point extractions using Google Search API via backend server.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start backend server (Terminal 1)
  set GOOGLE_API_KEY=your_api_key
  set GOOGLE_CX=your_cx_id
  python google_search_backend.py --port 5000
  
  # Run searches (Terminal 2)
  python key_point_search_tool.py --input extractor_output.json --backend-url http://localhost:5000
  
  # Search with image downloads
  python key_point_search_tool.py --input extractor_output.json --backend-url http://localhost:5000 --search-type image --download-images
  
  # View and manage cache/downloads
  python key_point_search_tool.py --backend-url http://localhost:5000 --list-cache
  python key_point_search_tool.py --backend-url http://localhost:5000 --clear-cache
  python key_point_search_tool.py --backend-url http://localhost:5000 --list-downloads
  python key_point_search_tool.py --backend-url http://localhost:5000 --clear-downloads
        """
    )
    
    parser.add_argument("--input", help="Extractor output JSON/CSV/TXT file or directory.")
    parser.add_argument("--backend-url", default="http://127.0.0.1:5000", help="Backend server URL (default: http://127.0.0.1:5000)")
    parser.add_argument("--search-type", choices=["web", "image"], default="web", help="Search type: web or image search (default: web)")
    parser.add_argument("--download-images", action="store_true", help="Download images to local folder (only for image search)")
    parser.add_argument("--max-results", type=int, default=None, help="Optional limit for how many records to process.")
    parser.add_argument("--skip-cache", action="store_true", help="Skip cached results and fetch fresh data")
    
    # Cache management options
    parser.add_argument("--list-cache", action="store_true", help="List all cached search results")
    parser.add_argument("--clear-cache", action="store_true", help="Clear all cached search results")
    parser.add_argument("--delete-cache", nargs=2, metavar=("TYPE", "QUERY"), help="Delete specific cached result (TYPE: web/image, QUERY: search query)")
    
    # Download management options
    parser.add_argument("--list-downloads", action="store_true", help="List all downloaded media files")
    parser.add_argument("--clear-downloads", action="store_true", help="Delete all downloaded media files")
    
    parser.add_argument("--quiet", action="store_true", help="Hide detailed procedure output.")
    
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    logger = ProcedureLogger(verbose=not args.quiet)
    
    # Initialize backend client
    logger.section("Backend Setup")
    logger.item(f"Backend URL: {args.backend_url}")
    backend_client = BackendClient(args.backend_url, logger)
    
    if not backend_client.health():
        logger.item("❌ Backend server is not running or not accessible")
        logger.item(f"Start it with: python google_search_backend.py --port 5000")
        return 1
    
    logger.item("✓ Backend server is running")
    
    # Handle cache management commands
    if args.list_cache:
        logger.section("Cached Search Results")
        caches = backend_client.list_cache()
        if not caches:
            logger.item("No cached results found")
        else:
            for cache in caches:
                logger.item(f"[{cache['search_type']}] {cache['query']} ({cache['result_count']} results) - {cache['cached_at']}")
        return 0
    
    if args.clear_cache:
        logger.section("Clearing Cache")
        if backend_client.clear_all_cache():
            logger.item("✓ All cached results cleared")
        else:
            logger.item("❌ Failed to clear cache")
        return 0
    
    if args.delete_cache:
        search_type, query = args.delete_cache
        logger.section("Deleting Cache Entry")
        if backend_client.delete_cache(search_type, query):
            logger.item(f"✓ Deleted cache for [{search_type}] {query}")
        else:
            logger.item(f"❌ Failed to delete cache for [{search_type}] {query}")
        return 0
    
    # Handle download management commands
    if args.list_downloads:
        logger.section("Downloaded Media Files")
        files = backend_client.list_downloaded_media()
        if not files:
            logger.item("No downloaded files found")
        else:
            total_size = 0
            for file in files:
                logger.item(f"{file['filename']} ({file['size_mb']}MB)")
                total_size += file['size']
            logger.item(f"Total size: {round(total_size / (1024*1024), 2)}MB")
        return 0
    
    if args.clear_downloads:
        logger.section("Clearing Downloads")
        if backend_client.clear_downloaded_media():
            logger.item("✓ All downloaded files cleared")
        else:
            logger.item("❌ Failed to clear downloads")
        return 0
    
    # Handle search operations
    if not args.input:
        logger.item("Error: --input is required for search operations")
        return 1
    
    logger.section("Loading extractor output")
    all_records = load_extractor_results(args.input)
    if args.max_results is not None:
        all_records = all_records[:args.max_results]
    logger.item(f"Loaded {len(all_records)} extractor records")

    collated = collate_extractor_results(all_records)
    logger.item(f"Grouped into {len(collated)} unique image groups")

    logger.section("Running search instances")
    search_outputs = run_search_for_collated_results(
        collated, 
        backend_client, 
        logger, 
        search_type=args.search_type,
        download_images=args.download_images and args.search_type == "image"
    )
    print_summary(search_outputs, logger)

    if not args.quiet:
        logger.section("Result JSON preview")
        print(json.dumps({k: v for k, v in search_outputs.items()}, indent=2, ensure_ascii=False)[:4000])

    return 0


if __name__ == "__main__":
    sys.exit(main())
