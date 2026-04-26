import re
import pandas as pd
import html as html_lib

STOPWORDS = {
    "A", "I", "AM", "PM", "CEO", "CFO", "CTO", "IPO", "ETF", "ATH", "ATL",
    "DD", "OP", "OC", "TL", "DR", "US", "UK", "EU", "IMO", "EOD", "EPS",
    "PE", "GDP", "CPI", "FED", "SEC", "NYSE", "NASDAQ", "SP", "YOY", "QOQ",
}

DOLLAR_TICKER_PATTERN = re.compile(r'\$([A-Z]{1,5})\b')
BARE_TICKER_PATTERN = re.compile(r'\b([A-Z]{2,5})\b')
URL_PATTERN = re.compile(r'http\S+|www\.\S+')
SPECIAL_CHARS_PATTERN = re.compile(r'[^a-zA-Z0-9\s\$]')


def clean_text(text: str) -> str:
    # Decode HTML entities first (&amp; &quot; &#39; etc.)
    text = html_lib.unescape(text)
    text = URL_PATTERN.sub("", text)
    text = SPECIAL_CHARS_PATTERN.sub(" ", text)
    text = re.sub(r'\s+', " ", text).strip()
    return text


def extract_tickers(text: str) -> list[str]:
    dollar_tickers = {t for t in DOLLAR_TICKER_PATTERN.findall(text) if t not in STOPWORDS}
    if dollar_tickers:
        return list(dollar_tickers)
    bare_tickers = {t for t in BARE_TICKER_PATTERN.findall(text) if t not in STOPWORDS}
    return list(bare_tickers)


def process_posts(posts: list[dict]) -> pd.DataFrame:
    records = []
    for post in posts:
        combined = f"{post.get('title', '')} {post.get('body', '')}".strip()
        cleaned = clean_text(combined)
        tickers = extract_tickers(combined)

        record = {
            "id": post["id"],
            "text": cleaned,
            "tickers": tickers,
            "score": post["score"],
            "num_comments": post["num_comments"],
            "created_utc": post["created_utc"],
            "subreddit": post["subreddit"],
        }
        # Carry through optional fields
        if "st_sentiment" in post:
            record["st_sentiment"] = post["st_sentiment"]
        if "source" in post:
            record["source"] = post["source"]

        records.append(record)

    return pd.DataFrame(records)
