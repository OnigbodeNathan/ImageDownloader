import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Sequence

from key_point_extractor import extract_key_points
from web_search_agent import search_results


def load_input(path: str) -> str:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"Input file not found: {source}")
    if source.suffix.lower() == ".json":
        payload = json.loads(source.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return "\n".join(json.dumps(item, ensure_ascii=False) for item in payload)
        return json.dumps(payload, ensure_ascii=False)
    return source.read_text(encoding="utf-8")


def search_one_key_point(
    key_point: str,
    count: int = 5,
) -> Dict[str, Any]:
    """Search one extracted key point through the web search agent."""
    try:
        matches = search_results(key_point, count=count)
        return {"query": key_point, "matches": matches, "error": None}
    except Exception as exc:
        return {"query": key_point, "matches": [], "error": str(exc)}


def search_key_points(
    text: str,
    count: int = 5,
    on_progress: Callable[[int, int, str], None] | None = None,
) -> Dict[str, Any]:
    """Extract key points, then search each one sequentially in order."""
    key_points = extract_key_points(text)
    searches: List[Dict[str, Any]] = []
    total = len(key_points)

    for index, key_point in enumerate(key_points, start=1):
        if on_progress is not None:
            on_progress(index, total, key_point)
        searches.append(search_one_key_point(key_point, count))

    return {"key_points": key_points, "search_type": "gemini", "searches": searches}


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search extracted key points with Gemini Google Search grounding.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", help="Text, JSON, or extractor output file.")
    source.add_argument("--query", help="Direct text to extract and search.")
    parser.add_argument("--count", type=int, default=5, help="Results per key point.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    if args.count < 1 or args.count > 20:
        raise SystemExit("--count must be between 1 and 20")
    text = args.query if args.query is not None else load_input(args.input)
    def report_progress(index: int, total: int, key_point: str) -> None:
        print(f"Searching key point {index}/{total}: {key_point}", file=sys.stderr)

    output = search_key_points(text, args.count, on_progress=report_progress)
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
