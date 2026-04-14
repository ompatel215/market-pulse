import requests

HEADERS = {"User-Agent": "market-pulse/0.1"}

def scrape_subreddit(subreddit_name, limit=100, category="hot"):
    url = f"https://www.reddit.com/r/{subreddit_name}/{category}.json?limit={limit}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()

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

    return posts
