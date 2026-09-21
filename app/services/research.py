import requests

from ..config import TAVILY_API_KEY


def search_web(query: str, max_results: int = 5) -> list[dict]:
    if not TAVILY_API_KEY:
        return []
    response = requests.post(
        "https://api.tavily.com/search",
        json={
            "api_key": TAVILY_API_KEY,
            "query": query,
            "search_depth": "advanced",
            "max_results": max_results,
            "include_answer": True,
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    results = []
    for item in data.get("results", []):
        results.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "content": item.get("content", ""),
        })
    return results
