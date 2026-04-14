import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import sys
sys.path.append(".")
from src.scraper import scrape_subreddit
from src.processor import process_posts
from src.analyzer import analyze_posts, summarize

st.set_page_config(page_title="Market Pulse", layout="wide")

st.title("Market Pulse")
st.caption("Real-time Reddit sentiment tracker for market volatility detection")

# ticker input
col1, col2 = st.columns([3, 1])
with col1:
    ticker = st.text_input("Ticker", placeholder="e.g. TSLA, NVDA, AAPL", label_visibility="collapsed")
with col2:
    fetch = st.button("Fetch Sentiment", use_container_width=True)

st.divider()

SUBREDDITS = ["wallstreetbets", "investing", "stocks"]


@st.cache_data(show_spinner=False)
def fetch_and_analyze(ticker_upper):
    all_posts = []
    for sub in SUBREDDITS:
        all_posts.extend(scrape_subreddit(sub, limit=50))
    df = process_posts(all_posts)
    df = df[df["tickers"].apply(lambda t: ticker_upper in t)]
    if df.empty:
        return df, {}
    df = analyze_posts(df)
    stats = summarize(df)
    return df, stats


if fetch and not ticker:
    st.warning("Enter a ticker symbol first.")

if fetch and ticker:
    ticker_upper = ticker.upper()
    with st.spinner(f"Scraping Reddit for {ticker_upper}..."):
        df, stats = fetch_and_analyze(ticker_upper)

    if df.empty:
        st.info(f"No posts mentioning {ticker_upper} found.")
    else:
        # metrics row
        m1, m2, m3, m4 = st.columns(4)
        sentiment_val = stats["avg_sentiment"]
        sentiment_label = "Bullish" if sentiment_val > 0.05 else "Bearish" if sentiment_val < -0.05 else "Neutral"
        m1.metric("Avg Sentiment", f"{sentiment_val:+.2f}", sentiment_label)
        m2.metric("Posts Found", stats["post_count"])
        m3.metric("Top Subreddit", stats["top_subreddit"])
        m4.metric("Bullish / Bearish", f"{stats['bullish']} / {stats['bearish']}")

        st.divider()

        # charts
        chart1, chart2 = st.columns(2)

        with chart1:
            st.subheader("Sentiment Distribution")
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=df["sentiment"],
                nbinsx=20,
                marker_color="#00C896",
            ))
            fig.add_vline(x=0, line_dash="dash", line_color="gray", line_width=1)
            fig.update_layout(
                margin=dict(l=0, r=0, t=10, b=0),
                xaxis=dict(range=[-1, 1], title="Sentiment Score"),
                yaxis=dict(title="Posts"),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True)

        with chart2:
            st.subheader("Sentiment by Subreddit")
            sub_avg = df.groupby("subreddit")["sentiment"].mean().reset_index()
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(
                x=sub_avg["subreddit"],
                y=sub_avg["sentiment"],
                marker_color=["#00C896" if v >= 0 else "#EF4444" for v in sub_avg["sentiment"]],
            ))
            fig2.add_hline(y=0, line_dash="dash", line_color="gray", line_width=1)
            fig2.update_layout(
                margin=dict(l=0, r=0, t=10, b=0),
                yaxis=dict(range=[-1, 1], title="Avg Sentiment"),
                xaxis=dict(title=""),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig2, use_container_width=True)

        st.divider()

        # top posts
        st.subheader("Top Posts")
        top = (
            df[["subreddit", "text", "score", "num_comments", "sentiment"]]
            .sort_values("score", ascending=False)
            .head(10)
            .rename(columns={
                "subreddit": "Subreddit",
                "text": "Text",
                "score": "Score",
                "num_comments": "Comments",
                "sentiment": "Sentiment",
            })
        )
        st.dataframe(top, use_container_width=True, hide_index=True)

        st.divider()

        # raw data
        st.subheader("Raw Data")
        st.caption(f"{len(df)} posts mentioning {ticker_upper}")
        st.dataframe(
            df[["subreddit", "text", "tickers", "score", "num_comments", "sentiment"]],
            use_container_width=True,
            hide_index=True,
        )

else:
    # placeholder state before any fetch
    st.caption("Enter a ticker and click Fetch Sentiment to begin.")
