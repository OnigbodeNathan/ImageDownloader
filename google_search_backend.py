import os
import time
import json
import requests
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify
import argparse


app = Flask(__name__)

# Configuration
# Prefer environment variables so the app never silently uses a stale or invalid key.
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
GOOGLE_CX = os.environ.get("GOOGLE_CX", "")
MAX_FILE_SIZE = 30 * 1024 * 1024  # 30MB
DOWNLOAD_DIR = Path("downloaded_media")
CACHE_DIR = Path("search_cache")

# Rate limiting: 2 requests per minute
REQUEST_HISTORY = []
MAX_REQUESTS_PER_MINUTE = 2

# Initialize directories
DOWNLOAD_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)


class RateLimiter:
    """Enforce 2 requests per minute"""
    def __init__(self, max_requests=2, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = []
    
    def is_allowed(self):
        now = time.time()
        # Remove old requests outside the window
        self.requests = [req_time for req_time in self.requests if now - req_time < self.window_seconds]
        
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        return False
    
    def wait_time(self):
        """Return seconds to wait before next request is allowed"""
        if not self.requests:
            return 0
        oldest = min(self.requests)
        wait = self.window_seconds - (time.time() - oldest)
        return max(0, wait)


rate_limiter = RateLimiter(max_requests=MAX_REQUESTS_PER_MINUTE, window_seconds=60)


def rate_limit_request(f):
    """Decorator to enforce rate limiting"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not rate_limiter.is_allowed():
            wait_time = rate_limiter.wait_time()
            return jsonify({
                "error": "Rate limit exceeded. Too many requests.",
                "wait_seconds": round(wait_time, 2)
            }), 429
        return f(*args, **kwargs)
    return decorated_function


def google_api_error(message: str, status_code: int = 500, details: Any | None = None):
    """Return a standardized JSON error payload for Google API issues."""
    payload = {"error": message}
    if details is not None:
        payload["details"] = details
    return jsonify(payload), status_code


def filter_ad_urls(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter out ad-related results"""
    ad_keywords = ["ads", "shopping", "googleads", "amazon.com", "ebay.com", "aliexpress", "promoted"]
    filtered = []
    
    for item in items:
        url = item.get("link", "").lower()
        title = item.get("title", "").lower()
        
        # Skip if URL or title contains ad keywords
        if any(keyword in url or keyword in title for keyword in ad_keywords):
            continue
        
        filtered.append(item)
    
    return filtered


def download_media(url: str, query: str) -> Dict[str, Any]:
    """Download media file with size limit"""
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        content_length = int(response.headers.get("content-length", 0))
        
        # Check size limit
        if content_length > MAX_FILE_SIZE:
            return {
                "success": False,
                "error": f"File too large: {content_length / (1024*1024):.2f}MB (max: 30MB)",
                "url": url
            }
        
        # Download file
        response = requests.get(url, timeout=10, stream=True)
        response.raise_for_status()
        
        # Generate filename
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        filename = parsed_url.path.split("/")[-1] or "image.jpg"
        
        # Add query prefix for organization
        safe_query = "".join(c for c in query if c.isalnum() or c in "-_")[:30]
        filename = f"{safe_query}_{filename}"
        
        file_path = DOWNLOAD_DIR / filename
        
        # Write file
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        return {
            "success": True,
            "file_path": str(file_path),
            "file_size": file_path.stat().st_size,
            "url": url
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "url": url
        }


def get_cache_path(query: str, search_type: str = "web") -> Path:
    """Generate cache file path for a query"""
    safe_name = "".join(c for c in query if c.isalnum() or c in "-_")
    return CACHE_DIR / f"{search_type}_{safe_name}.json"


def load_cache(query: str, search_type: str = "web") -> Dict[str, Any] | None:
    """Load cached results if available"""
    cache_path = get_cache_path(query, search_type)
    if cache_path.exists():
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def save_cache(query: str, results: Dict[str, Any], search_type: str = "web"):
    """Save search results to cache"""
    cache_path = get_cache_path(query, search_type)
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Cache save error: {e}")


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "api_configured": bool(GOOGLE_API_KEY and GOOGLE_CX),
        "timestamp": datetime.now().isoformat()
    })


@app.route("/search", methods=["POST"])
@rate_limit_request
def search_web():
    """Search the web using Google Custom Search API"""
    data = request.json or {}
    query = data.get("query", "").strip()
    num_results = min(int(data.get("num_results", 5)), 10)
    skip_cache = data.get("skip_cache", False)
    
    if not query:
        return jsonify({"error": "Query is required"}), 400
    
    if not GOOGLE_API_KEY or not GOOGLE_CX:
        return google_api_error(
            "Google API credentials are missing. Set GOOGLE_API_KEY and GOOGLE_CX environment variables before searching.",
            status_code=400,
            details={"required": ["GOOGLE_API_KEY", "GOOGLE_CX"]},
        )
    
    # Check cache first
    if not skip_cache:
        cached = load_cache(query, "web")
        if cached:
            return jsonify({
                "results": cached["results"],
                "query": query,
                "cached": True,
                "cached_at": cached.get("cached_at")
            })
    
    # Perform search
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "q": query,
            "key": GOOGLE_API_KEY,
            "cx": GOOGLE_CX,
            "num": num_results,
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Filter ads
        items = filter_ad_urls(data.get("items", []))
        
        # Format results
        results = []
        for idx, item in enumerate(items[:num_results]):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "score": round(1.0 - (idx * 0.1), 4),
                "index": idx
            })
        
        # Cache results
        cache_data = {
            "query": query,
            "results": results,
            "cached_at": datetime.now().isoformat()
        }
        save_cache(query, cache_data, "web")
        
        return jsonify({
            "results": results,
            "query": query,
            "cached": False,
            "total_results": len(results)
        })
    
    except requests.exceptions.RequestException as e:
        details = {"request_error": str(e)}
        return google_api_error(
            "Google Custom Search request failed. Verify that your API key and Search Engine ID are valid and that the project has Custom Search JSON API access enabled.",
            status_code=403 if isinstance(e, requests.exceptions.HTTPError) else 500,
            details=details,
        )
    except ValueError as e:
        return google_api_error("Google response was not valid JSON.", status_code=500, details={"detail": str(e)})


@app.route("/image-search", methods=["POST"])
@rate_limit_request
def search_images():
    """Search for images using Google Custom Search API"""
    data = request.json or {}
    query = data.get("query", "").strip()
    num_results = min(int(data.get("num_results", 5)), 10)
    skip_cache = data.get("skip_cache", False)
    download = data.get("download", False)
    
    if not query:
        return jsonify({"error": "Query is required"}), 400
    
    if not GOOGLE_API_KEY or not GOOGLE_CX:
        return google_api_error(
            "Google API credentials are missing. Set GOOGLE_API_KEY and GOOGLE_CX environment variables before searching.",
            status_code=400,
            details={"required": ["GOOGLE_API_KEY", "GOOGLE_CX"]},
        )
    
    # Check cache first
    if not skip_cache:
        cached = load_cache(query, "image")
        if cached:
            return jsonify({
                "results": cached["results"],
                "query": query,
                "cached": True,
                "cached_at": cached.get("cached_at")
            })
    
    # Perform image search
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "q": query,
            "key": GOOGLE_API_KEY,
            "cx": GOOGLE_CX,
            "searchType": "image",
            "num": num_results,
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Filter ads
        items = filter_ad_urls(data.get("items", []))
        
        # Format results
        results = []
        for idx, item in enumerate(items[:num_results]):
            image_url = item.get("link", "")
            result = {
                "title": item.get("title", ""),
                "url": image_url,
                "image_url": image_url,
                "snippet": item.get("snippet", ""),
                "score": round(1.0 - (idx * 0.1), 4),
                "index": idx,
                "downloaded": False,
                "file_path": None
            }
            
            # Optionally download images
            if download:
                download_result = download_media(image_url, query)
                result["downloaded"] = download_result["success"]
                if download_result["success"]:
                    result["file_path"] = download_result["file_path"]
                else:
                    result["download_error"] = download_result.get("error")
            
            results.append(result)
        
        # Cache results
        cache_data = {
            "query": query,
            "results": results,
            "cached_at": datetime.now().isoformat()
        }
        save_cache(query, cache_data, "image")
        
        return jsonify({
            "results": results,
            "query": query,
            "cached": False,
            "total_results": len(results)
        })
    
    except requests.exceptions.RequestException as e:
        details = {"request_error": str(e)}
        return google_api_error(
            "Google Custom Search request failed. Verify that your API key and Search Engine ID are valid and that the project has Custom Search JSON API access enabled.",
            status_code=403 if isinstance(e, requests.exceptions.HTTPError) else 500,
            details=details,
        )
    except ValueError as e:
        return google_api_error("Google response was not valid JSON.", status_code=500, details={"detail": str(e)})


@app.route("/cache", methods=["GET"])
def list_cache():
    """List all cached search results"""
    try:
        caches = []
        for cache_file in sorted(CACHE_DIR.glob("*.json")):
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                caches.append({
                    "file": cache_file.name,
                    "query": data.get("query"),
                    "search_type": cache_file.name.split("_")[0],
                    "cached_at": data.get("cached_at"),
                    "result_count": len(data.get("results", []))
                })
        return jsonify({"caches": caches})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/cache/<search_type>/<query>", methods=["DELETE"])
def delete_cache(search_type: str, query: str):
    """Delete a specific cached result"""
    try:
        cache_path = get_cache_path(query, search_type)
        if cache_path.exists():
            cache_path.unlink()
            return jsonify({"message": f"Cache deleted for query: {query}"})
        return jsonify({"error": "Cache not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/cache", methods=["DELETE"])
def clear_all_cache():
    """Clear all cached results"""
    try:
        count = 0
        for cache_file in CACHE_DIR.glob("*.json"):
            cache_file.unlink()
            count += 1
        return jsonify({"message": f"Cleared {count} cached searches"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/downloaded-media", methods=["GET"])
def list_downloaded_media():
    """List all downloaded media files"""
    try:
        files = []
        for media_file in sorted(DOWNLOAD_DIR.glob("*")):
            if media_file.is_file():
                files.append({
                    "filename": media_file.name,
                    "size": media_file.stat().st_size,
                    "size_mb": round(media_file.stat().st_size / (1024*1024), 2),
                    "path": str(media_file)
                })
        return jsonify({"downloaded_files": files, "total_count": len(files)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/downloaded-media", methods=["DELETE"])
def clear_downloaded_media():
    """Delete all downloaded media files"""
    try:
        count = 0
        total_size = 0
        for media_file in DOWNLOAD_DIR.glob("*"):
            if media_file.is_file():
                total_size += media_file.stat().st_size
                media_file.unlink()
                count += 1
        return jsonify({
            "message": f"Deleted {count} files",
            "total_size_freed_mb": round(total_size / (1024*1024), 2)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Google Search Backend Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to (default: 5000)")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    
    args = parser.parse_args()
    
    print(f"Starting Google Search Backend Server")
    print(f"Host: {args.host}:{args.port}")
    print(f"API Key configured: {bool(GOOGLE_API_KEY)}")
    print(f"CX configured: {bool(GOOGLE_CX)}")
    print(f"Download directory: {DOWNLOAD_DIR.absolute()}")
    print(f"Cache directory: {CACHE_DIR.absolute()}")
    
    app.run(host=args.host, port=args.port, debug=args.debug)
