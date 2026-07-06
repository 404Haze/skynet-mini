"""
DuckDuckGo web search tool for skynet-mini.

Provides a clean wrapper around the duckduckgo-search package.
No API key required.
"""

from ddgs import DDGS


def web_search(query: str, max_results: int = 5) -> dict:
    """
    Search the web using DuckDuckGo and return results.

    Args:
        query: The search query string.
        max_results: Maximum number of results to return (default 5, max 10).

    Returns:
        A dict with 'status' and either 'results' (list of {title, url, snippet})
        or 'error_message' on failure.
    """
    max_results = min(max_results, 10)

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))

        if not results:
            return {
                "status": "success",
                "results": [],
                "message": "No results found for this query.",
            }

        formatted = []
        for r in results:
            formatted.append({
                "title": r.get("title", "Untitled"),
                "url": r.get("href", ""),
                "snippet": r.get("body", ""),
            })

        return {
            "status": "success",
            "results": formatted,
        }

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Search failed: {str(e)}",
        }
