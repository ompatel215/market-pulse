import requests
import logging
from datetime import datetime

HEADERS = {"User-Agent": "market-pulse/0.1 (CMPSC446 project)"}

def scrape_stocktwits(ticker: str, limit: int = 30) -> list[dict]:
    """
    Fetch messages from Stocktwits public API for a given ticker.
    No auth required. Returns up to 30 messages per call (API max).
    
    Notable: Stocktwits users self-label messages as Bullish/Bearish,
    stored in 'st_sentiment' — useful as ground truth vs VADER.
    """
    url = f"https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        messages = r.json().get("messages", [])
    except Exception as e:
        logging.warning(f"Stocktwits fetch failed for {ticker}: {e}")
        return []

    posts = []
    for msg in messages[:limit]:
        try:
            body = msg.get("body", "")
            created = msg.get("created_at", "")
            try:
                ts = datetime.strptime(created, "%Y-%m-%dT%H:%M:%SZ").timestamp()
            except Exception:
                import time
                ts = time.time()

            entities = msg.get("entities", {})
            st_sentiment_raw = entities.get("sentiment", {})
            st_sentiment = st_sentiment_raw.get("basic") if st_sentiment_raw else None

            likes = msg.get("likes", {}).get("total", 0) if isinstance(msg.get("likes"), dict) else 0

            posts.append({
                "id": f"st_{msg['id']}",
                "title": "",
                "body": body,
                "score": likes,
                "num_comments": 0,
                "created_utc": ts,
                "subreddit": "Stocktwits",
                "source": "stocktwits",
                "st_sentiment": st_sentiment,
            })
        except Exception:
            continue

    return posts
