import requests
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
import html
import re
import logging

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def _clean_title(title: str) -> str:
    """Strip HTML entities, source suffix, and special chars from headline."""
    # Decode HTML entities (&amp; &quot; etc.)
    title = html.unescape(title)
    # Strip source suffix e.g. " - CNBC" or " | Bloomberg"
    title = re.sub(r'\s[-|]\s[\w\s]+$', '', title).strip()
    return title

def scrape_google_news(ticker: str, limit: int = 50) -> list[dict]:
    """
    Fetch news headlines for a ticker from Google News RSS.
    Returns posts compatible with processor.py pipeline.
    """
    query = f"{ticker} stock"
    url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        root = ET.fromstring(r.text)
        items = root.findall(".//item")
    except Exception as e:
        logging.warning(f"Google News fetch failed for {ticker}: {e}")
        return []

    posts = []
    for i, item in enumerate(items[:limit]):
        try:
            title = _clean_title(item.find("title").text or "")
            pubdate_str = item.find("pubDate").text
            try:
                ts = parsedate_to_datetime(pubdate_str).timestamp()
            except Exception:
                import time
                ts = time.time()

            link = item.find("link").text or ""

            posts.append({
                "id": f"news_{ticker}_{i}",
                "title": title,
                "body": "",
                "score": 0,
                "num_comments": 0,
                "created_utc": ts,
                "subreddit": "Google News",
                "url": link,
                "source": "google_news",
            })
        except Exception:
            continue

    return posts
