import logging

def scrape_twitter(query: str, limit: int = 100) -> list[dict]:
    """
    Twitter/X scraping via snscrape is no longer functional as of 2023
    (Twitter revoked the underlying API access snscrape relied on).
    This stub returns an empty list so the rest of the pipeline works cleanly.
    Sentiment analysis runs on Reddit data only.
    """
    logging.info("Twitter scraping disabled — API access revoked. Using Reddit only.")
    return []
