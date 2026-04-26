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
    df["date"] = pd.to_datetime(df["created_utc"], unit="s", utc=True).dt.tz_localize(None).dt.normalize()
    return df


def _format_source(name: str) -> str:
    """Format source name cleanly for display."""
    NON_REDDIT = {"Google News", "Stocktwits", "news", "stocktwits"}
    if name in NON_REDDIT:
        return name.title().replace("_", " ")
    if name.startswith("t/"):
        return name
    return f"r/{name}"


def summarize(df: pd.DataFrame) -> dict:
    if df.empty:
        return {}

    avg_sentiment = df["sentiment"].mean()
    sub_counts = df["subreddit"].value_counts()
    top_subreddit = _format_source(sub_counts.idxmax())

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
            # Strip leftover HTML artifacts
            token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z]+\b",
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

        # Words to exclude from topic display (too generic to be meaningful)
        SKIP_WORDS = {"stock", "stocks", "price", "today", "market", "share",
                      "shares", "trading", "trade", "amp", "nasdaq", "nyse"}

        for i, (component, weight) in enumerate(zip(lda.components_, topic_weights)):
            top_indices = component.argsort()[::-1]
            words = [
                feature_names[j] for j in top_indices
                if feature_names[j].lower() not in SKIP_WORDS
            ][:n_words]
            topics.append({
                "topic": i + 1,
                "words": words,
                "label": " · ".join(words[:3]),
                "weight": round(float(weight), 3),
            })

        topics.sort(key=lambda x: x["weight"], reverse=True)
        return topics

    except Exception:
        return []


# ── VADER vs Stocktwits accuracy ───────────────────────────────────────────────

def vader_accuracy(df: pd.DataFrame) -> dict:
    """
    Compare VADER compound score against Stocktwits user-labeled sentiment.
    Only rows with 'st_sentiment' == 'Bullish' or 'Bearish' are evaluated.
    """
    if "st_sentiment" not in df.columns or "sentiment" not in df.columns:
        return {}

    labeled = df[df["st_sentiment"].isin(["Bullish", "Bearish"])].copy()
    if len(labeled) < 5:
        return {}

    labeled["vader_label"] = labeled["sentiment"].apply(
        lambda v: "Bullish" if v > 0.05 else ("Bearish" if v < -0.05 else "Neutral")
    )
    directional = labeled[labeled["vader_label"] != "Neutral"]
    if directional.empty:
        return {}

    correct = (directional["vader_label"] == directional["st_sentiment"]).sum()
    accuracy = correct / len(directional)

    bull_true = directional[directional["st_sentiment"] == "Bullish"]
    bull_correct = (bull_true["vader_label"] == "Bullish").sum()
    bear_true = directional[directional["st_sentiment"] == "Bearish"]
    bear_correct = (bear_true["vader_label"] == "Bearish").sum()

    return {
        "total_labeled": len(labeled),
        "evaluated": len(directional),
        "correct": int(correct),
        "accuracy": round(float(accuracy), 3),
        "bullish_recall": round(float(bull_correct / len(bull_true)) if len(bull_true) else 0, 3),
        "bearish_recall": round(float(bear_correct / len(bear_true)) if len(bear_true) else 0, 3),
    }
