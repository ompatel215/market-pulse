from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import pandas as pd
import numpy as np

analyzer = SentimentIntensityAnalyzer()


# ── Sentiment ──────────────────────────────────────────────────────────────────

def analyze_posts(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["sentiment"] = df["text"].apply(lambda t: analyzer.polarity_scores(t)["compound"])
    # Convert created_utc to datetime for time-series work
    df["date"] = pd.to_datetime(df["created_utc"], unit="s", utc=True).dt.tz_localize(None).dt.normalize()
    return df


def summarize(df: pd.DataFrame) -> dict:
    if df.empty:
        return {}

    avg_sentiment = df["sentiment"].mean()
    # top_subreddit: strip the t/ prefix added by twitter stub, keep r/ for reddit
    sub_counts = df["subreddit"].value_counts()
    top_subreddit = sub_counts.idxmax()
    if not top_subreddit.startswith("t/"):
        top_subreddit = f"r/{top_subreddit}"

    bullish = (df["sentiment"] > 0.05).sum()
    bearish = (df["sentiment"] < -0.05).sum()
    neutral = len(df) - bullish - bearish

    return {
        "avg_sentiment": round(avg_sentiment, 3),
        "post_count": len(df),
        "top_subreddit": top_subreddit,
        "bullish": int(bullish),
        "bearish": int(bearish),
        "neutral": int(neutral),
    }


# ── Sentiment over time ────────────────────────────────────────────────────────

def sentiment_over_time(df: pd.DataFrame) -> pd.DataFrame:
    """Daily average sentiment + post count."""
    if df.empty or "date" not in df.columns:
        return pd.DataFrame(columns=["date", "sentiment", "post_count"])

    grouped = (
        df.groupby("date")
        .agg(sentiment=("sentiment", "mean"), post_count=("sentiment", "count"))
        .reset_index()
        .sort_values("date")
    )
    return grouped


# ── Topic Modeling (LDA) ───────────────────────────────────────────────────────

def extract_topics(df: pd.DataFrame, n_topics: int = 5, n_words: int = 6) -> list[dict]:
    """
    Run LDA on post text. Returns a list of dicts:
      [{"topic": 1, "label": "...", "words": [...], "weight": 0.xx}, ...]
    """
    texts = df["text"].dropna().tolist()
    if len(texts) < n_topics:
        return []

    try:
        vec = CountVectorizer(
            max_df=0.90,
            min_df=2,
            stop_words="english",
            max_features=500,
        )
        dtm = vec.fit_transform(texts)
        if dtm.shape[1] < n_topics:
            return []

        lda = LatentDirichletAllocation(
            n_components=n_topics,
            random_state=42,
            max_iter=15,
        )
        lda.fit(dtm)

        feature_names = vec.get_feature_names_out()
        topics = []
        doc_topics = lda.transform(dtm)
        topic_weights = doc_topics.mean(axis=0)

        for i, (component, weight) in enumerate(zip(lda.components_, topic_weights)):
            top_indices = component.argsort()[-n_words:][::-1]
            words = [feature_names[j] for j in top_indices]
            topics.append({
                "topic": i + 1,
                "words": words,
                "label": " · ".join(words[:3]),
                "weight": round(float(weight), 3),
            })

        # Sort by prevalence descending
        topics.sort(key=lambda x: x["weight"], reverse=True)
        return topics

    except Exception:
        return []
