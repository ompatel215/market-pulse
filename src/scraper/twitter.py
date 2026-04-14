import snscrape.modules.twitter as sntwitter
import logging

def scrape_twitter(query: str, limit: int = 100) -> list[dict]:
    """
    Scrapes tweets based on a query using snscrape.
    Returns a list of dictionaries compatible with the existing pipeline.
    """
    tweets = []
    try:
        scraper = sntwitter.TwitterSearchScraper(query)
        for i, tweet in enumerate(scraper.get_items()):
            if i >= limit:
                break
            
            # Construct dictionary with requested keys and compatibility keys for processor.py
            tweets.append({
                # Requested keys
                "source": "twitter",
                "content": tweet.content,
                "date": tweet.date,
                "likes": tweet.likeCount,
                "retweets": tweet.retweetCount,
                "username": tweet.user.username,
                
                # Compatibility keys for processor.py
                "id": str(tweet.id),
                "title": "",
                "body": tweet.content,
                "score": tweet.likeCount,
                "num_comments": tweet.retweetCount,
                "created_utc": tweet.date.timestamp(),
                "subreddit": f"t/{tweet.user.username}"
            })
    except Exception as e:
        logging.error(f"Error scraping Twitter: {e}")
        # Return empty list on failure to avoid crashing the app
        return []
        
    return tweets
