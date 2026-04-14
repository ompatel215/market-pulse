from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd

analyzer = SentimentIntensityAnalyzer()


def analyze_posts(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["sentiment"] = df["text"].apply(lambda t: analyzer.polarity_scores(t)["compound"])
    return df


def summarize(df: pd.DataFrame) -> dict:
    if df.empty:
        return {}

    avg_sentiment = df["sentiment"].mean()
    top_subreddit = df["subreddit"].value_counts().idxmax()

    bullish = (df["sentiment"] > 0.05).sum()
    bearish = (df["sentiment"] < -0.05).sum()
    neutral = len(df) - bullish - bearish

    return {
        "avg_sentiment": round(avg_sentiment, 3),
        "post_count": len(df),
        "top_subreddit": f"r/{top_subreddit}",
        "bullish": int(bullish),
        "bearish": int(bearish),
        "neutral": int(neutral),
    }
