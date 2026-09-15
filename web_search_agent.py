import os
import importlib
from typing import Any, Dict, List

genai: Any = None
types: Any = None
try:
    genai = importlib.import_module("google.genai")
    types = importlib.import_module("google.genai.types")
except ImportError:
    pass

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> bool:
        return False

load_dotenv()

_configured_model = os.getenv("GEMINI_MODEL", "").strip()
GEMINI_MODEL = (
    "gemini-3.6-flash"
    if not _configured_model or _configured_model in {"gemini-2.5-flash", "models/gemini-2.5-flash"}
    else _configured_model.removeprefix("models/")
)
_CLIENT: Any = None
_CLIENT_KEY: str | None = None


def _gemini_client() -> Any:
    global _CLIENT, _CLIENT_KEY
    if genai is None:
        raise RuntimeError("Install the Gemini client with: pip install google-genai")
    api_key = os.getenv("GEMINI_API_KEY", "").strip().strip('"').strip("'").strip()
    if not api_key or api_key.lower() in {"your_gemini_api_key", "your_api_key", "replace_me"}:
        raise RuntimeError(
            "GEMINI_API_KEY is missing or still a placeholder. "
            "Set an active Gemini API key before searching."
        )
    if _CLIENT is None or _CLIENT_KEY != api_key:
        _CLIENT = genai.Client(api_key=api_key)
        _CLIENT_KEY = api_key
    return _CLIENT


def _generate_content(contents: str, config: Any) -> Any:
    """Generate content and recover once from a stale/closed client."""
    global _CLIENT
    try:
        return _gemini_client().models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=config,
        )
    except Exception as exc:
        if "client has been closed" not in str(exc).lower():
            raise
        _CLIENT = None
        return _gemini_client().models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=config,
        )


def web_search(query: str) -> str:
    """
    Searches the web and returns the summaries of top results.
    
    Args:
        query: The search query to be executed.
        
    Returns:
        A string containing the summaries of the top results.
    """
    try:
        response = _generate_content(
            query,
            types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
            ),
        )
        return response.text or ""
    except Exception as exc:
        return f"Error searching the web with Gemini: {exc}"


def search_results(query: str, count: int = 10) -> List[Dict[str, Any]]:
    """Return Gemini's grounded answer and cited sources as search results."""
    response = _generate_content(
        query,
        types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
        ),
    )
    grounding = getattr(response.candidates[0], "grounding_metadata", None)
    chunks = getattr(grounding, "grounding_chunks", None) or []
    results: List[Dict[str, Any]] = []
    for index, chunk in enumerate(chunks[:count], start=1):
        web = getattr(chunk, "web", None)
        if web is None:
            continue
        results.append({
            "title": getattr(web, "title", ""),
            "link": getattr(web, "uri", ""),
            "snippet": response.text or "",
            "result_id": f"gemini-{index}",
        })
    if not results:
        results.append({"title": "Gemini grounded answer", "link": "", "snippet": response.text or "", "result_id": "gemini-1"})
    return results


def run_agent_with_tools(question: str) -> Dict[str, Any]:
    """Answer a question using Gemini with Google Search grounding."""
    response = _generate_content(
        question,
        types.GenerateContentConfig(
            system_instruction=(
                "Answer using current web information. Cite the grounded sources "
                "when possible and distinguish facts from uncertainty."
            ),
            tools=[types.Tool(google_search=types.GoogleSearch())],
        ),
    )
    return {"final_response": response.text or "", "model": GEMINI_MODEL}


if __name__ == "__main__":
    result = run_agent_with_tools("Why did OKC Thunder lose game 1 of the NBA finals?")
    print(f"\nFinal Answer:\n{result['final_response']}")
