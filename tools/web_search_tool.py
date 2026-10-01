"""
Live web search (DuckDuckGo, no API key needed) + headless page scraping.
"""
from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup


def search(query: str, max_results: int = 5):
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=max_results))
    return [{"title": r.get("title"), "url": r.get("href"), "snippet": r.get("body")} for r in results]


def scrape_page(url: str, max_chars: int = 4000):
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0 (UltronAgent)"})
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = " ".join(soup.get_text(separator=" ").split())
        return {"success": True, "url": url, "content": text[:max_chars]}
    except Exception as e:
        return {"success": False, "url": url, "error": str(e)}
