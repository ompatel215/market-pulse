import requests
import time
import logging

# Reddit's JSON API requires a descriptive User-Agent per their API rules.
# Using a generic "python-requests" UA returns 403 on some endpoints.
HEADERS = {
    "User-Agent": "market-pulse:v0.1 (by /u/abelprasad; CMPSC446 project)"
}

def scrape_subreddit(subreddit_name: str, limit: int = 100, category: str = "hot") -> list[dict]:
    """
    Fetch posts from a subreddit using Reddit's public JSON API (no auth required).
    Returns a list of post dicts compatible with processor.py.
    """
    url = f"https://www.reddit.com/r/{subreddit_name}/{category}.json?limit={limit}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logging.warning(f"Reddit HTTP error for r/{subreddit_name}: {e}")
        return []
    except requests.exceptions.RequestException as e:
        logging.warning(f"Reddit request failed for r/{subreddit_name}: {e}")
        return []

    posts = []
    for post in response.json()["data"]["children"]:
        data = post["data"]
        posts.append({
            "id": data["id"],
            "title": data["title"],
            "body": data.get("selftext", ""),
            "score": data["score"],
            "num_comments": data["num_comments"],
            "created_utc": data["created_utc"],
            "subreddit": subreddit_name,
            "url": data["url"],
        })

    # Be polite — small delay between subreddit calls
    time.sleep(0.5)
    return posts
