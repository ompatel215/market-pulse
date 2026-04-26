import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import sys

sys.path.append(".")
from src.scraper import scrape_subreddit, scrape_twitter
from src.processor import process_posts
from src.analyzer import analyze_posts, summarize, sentiment_over_time, extract_topics
from src.stock import fetch_stock_prices

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Market Pulse",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Minimal CSS tweaks ─────────────────────────────────────────────────────────
st.markdown("""
<style>
    .metric-label { font-size: 0.8rem !important; }
    .stMetric { background: #0f172a; border-radius: 8px; padding: 12px; }
    div[data-testid="stMetricValue"] { font-size: 1.6rem !important; }
    .topic-chip {
        display: inline-block;
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 20px;
        padding: 4px 12px;
        margin: 3px;
        font-size: 0.82rem;
        color: #94a3b8;
    }
    .bullish { color: #10b981 !important; }
    .bearish { color: #ef4444 !important; }
    .neutral { color: #94a3b8 !important; }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("## 📈 Market Pulse")
st.caption("Reddit sentiment tracker with stock price overlay · CMPSC 446 Final Project")

# ── Input row ──────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    ticker = st.text_input(
        "Ticker",
        placeholder="e.g. TSLA, NVDA, AAPL",
        label_visibility="collapsed",
    )
with col2:
    period = st.selectbox(
        "Period",
        ["1wk", "1mo", "3mo"],
        index=1,
        label_visibility="collapsed",
    )
with col3:
    fetch = st.button("🔍 Analyze", use_container_width=True, type="primary")

st.divider()

SUBREDDITS = ["wallstreetbets", "investing", "stocks", "StockMarket", "options"]
PERIOD_REDDIT_LIMIT = {"1wk": 25, "1mo": 50, "3mo": 100}


# ── Data fetching (cached) ─────────────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=600)
def fetch_and_analyze(ticker_upper: str, period: str):
    all_posts = []

    for sub in SUBREDDITS:
        for category in ["hot", "new"]:
            try:
                posts = scrape_subreddit(
                    sub,
                    limit=PERIOD_REDDIT_LIMIT.get(period, 50),
                    category=category,
                )
                all_posts.extend(posts)
            except Exception:
                continue

    # Twitter stub — returns [] gracefully
    all_posts.extend(scrape_twitter(f"${ticker_upper}", limit=50))

    if not all_posts:
        return pd.DataFrame(), {}, pd.DataFrame(), pd.DataFrame(), []

    df = process_posts(all_posts)
    # Deduplicate by id
    df = df.drop_duplicates(subset=["id"])

    ticker_df = df[df["tickers"].apply(lambda t: ticker_upper in t)]

    if ticker_df.empty:
        return ticker_df, {}, pd.DataFrame(), pd.DataFrame(), []

    ticker_df = analyze_posts(ticker_df)
    stats = summarize(ticker_df)
    time_df = sentiment_over_time(ticker_df)
    stock_df = fetch_stock_prices(ticker_upper, period=period)
    topics = extract_topics(ticker_df)

    return ticker_df, stats, time_df, stock_df, topics


# ── Main ───────────────────────────────────────────────────────────────────────
if fetch and not ticker:
    st.warning("Enter a ticker symbol first.")

elif fetch and ticker:
    ticker_upper = ticker.strip().upper()

    with st.spinner(f"Scraping Reddit & fetching {ticker_upper} data…"):
        df, stats, time_df, stock_df, topics = fetch_and_analyze(ticker_upper, period)

    if df.empty:
        st.info(
            f"No posts mentioning **{ticker_upper}** found across r/wallstreetbets, "
            "r/investing, r/stocks, r/StockMarket, and r/options. "
            "Try a more widely discussed ticker."
        )
    else:
        # ── KPI row ────────────────────────────────────────────────────────────
        avg = stats["avg_sentiment"]
        if avg > 0.05:
            mood, mood_class, mood_delta = "Bullish 🟢", "bullish", f"+{avg:.3f}"
        elif avg < -0.05:
            mood, mood_class, mood_delta = "Bearish 🔴", "bearish", f"{avg:.3f}"
        else:
            mood, mood_class, mood_delta = "Neutral ⚪", "neutral", f"{avg:.3f}"

        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Overall Sentiment", mood, mood_delta)
        k2.metric("Posts Analyzed", stats["post_count"])
        k3.metric("Bullish", stats["bullish"])
        k4.metric("Bearish", stats["bearish"])
        k5.metric("Most Active", stats["top_subreddit"])

        st.divider()

        # ── Chart 1: Sentiment + Stock Price overlay ───────────────────────────
        st.subheader("Sentiment vs. Stock Price")

        if not time_df.empty and not stock_df.empty:
            fig = make_subplots(specs=[[{"secondary_y": True}]])

            # Stock price (candlestick)
            fig.add_trace(
                go.Scatter(
                    x=stock_df["date"],
                    y=stock_df["close"],
                    name="Close Price",
                    line=dict(color="#6366f1", width=2),
                    fill="tozeroy",
                    fillcolor="rgba(99,102,241,0.08)",
                ),
                secondary_y=False,
            )

            # Sentiment line
            sentiment_colors = [
                "#10b981" if v > 0.05 else "#ef4444" if v < -0.05 else "#94a3b8"
                for v in time_df["sentiment"]
            ]
            fig.add_trace(
                go.Scatter(
                    x=time_df["date"],
                    y=time_df["sentiment"],
                    name="Avg Sentiment",
                    mode="lines+markers",
                    line=dict(color="#f59e0b", width=2),
                    marker=dict(color=sentiment_colors, size=7, line=dict(width=1, color="#0f172a")),
                ),
                secondary_y=True,
            )

            # Zero line on sentiment axis
            fig.add_hline(y=0, line_dash="dot", line_color="rgba(148,163,184,0.3)",
                          secondary_y=True)

            fig.update_layout(
                height=340,
                margin=dict(l=0, r=0, t=10, b=0),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", y=1.08, x=0),
                hovermode="x unified",
            )
            fig.update_yaxes(title_text=f"{ticker_upper} Close ($)", secondary_y=False,
                             gridcolor="rgba(51,65,85,0.4)")
            fig.update_yaxes(title_text="Sentiment Score", range=[-1, 1],
                             secondary_y=True, gridcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

        elif not time_df.empty:
            # No stock data — just sentiment over time
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=time_df["date"], y=time_df["sentiment"],
                mode="lines+markers",
                line=dict(color="#f59e0b", width=2),
                fill="tozeroy",
                fillcolor="rgba(245,158,11,0.1)",
                name="Avg Sentiment",
            ))
            fig.add_hline(y=0, line_dash="dot", line_color="rgba(148,163,184,0.4)")
            fig.update_layout(
                height=300, margin=dict(l=0, r=0, t=10, b=0),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(range=[-1, 1], title="Sentiment Score"),
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption("⚠️ Stock price data unavailable for this ticker.")
        else:
            st.info("Not enough posts across different dates to build a time-series chart.")

        st.divider()

        # ── Chart 2: Sentiment Distribution + Subreddit breakdown ─────────────
        ch1, ch2 = st.columns(2)

        with ch1:
            st.subheader("Sentiment Distribution")
            fig2 = go.Figure()
            fig2.add_trace(go.Histogram(
                x=df["sentiment"],
                nbinsx=25,
                marker=dict(
                    color=df["sentiment"].apply(
                        lambda v: "#10b981" if v > 0.05 else "#ef4444" if v < -0.05 else "#94a3b8"
                    ),
                    line=dict(width=0),
                ),
                name="Posts",
            ))
            fig2.add_vline(x=0, line_dash="dash", line_color="rgba(148,163,184,0.5)", line_width=1)
            fig2.add_vline(x=avg, line_dash="dot", line_color="#f59e0b", line_width=2,
                           annotation_text=f"avg {avg:+.2f}", annotation_position="top")
            fig2.update_layout(
                height=280, margin=dict(l=0, r=0, t=10, b=0),
                xaxis=dict(range=[-1, 1], title="VADER Compound Score"),
                yaxis=dict(title="Posts"),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
            )
            st.plotly_chart(fig2, use_container_width=True)

        with ch2:
            st.subheader("Avg Sentiment by Subreddit")
            sub_avg = (
                df.groupby("subreddit")["sentiment"]
                .agg(["mean", "count"])
                .reset_index()
                .rename(columns={"mean": "sentiment", "count": "posts"})
                .sort_values("sentiment", ascending=True)
            )
            colors = ["#10b981" if v >= 0.05 else "#ef4444" if v < -0.05 else "#94a3b8"
                      for v in sub_avg["sentiment"]]
            fig3 = go.Figure()
            fig3.add_trace(go.Bar(
                x=sub_avg["sentiment"],
                y=sub_avg["subreddit"],
                orientation="h",
                marker_color=colors,
                text=sub_avg["posts"].apply(lambda n: f"{n} posts"),
                textposition="outside",
            ))
            fig3.add_vline(x=0, line_dash="dash", line_color="rgba(148,163,184,0.5)", line_width=1)
            fig3.update_layout(
                height=280, margin=dict(l=0, r=20, t=10, b=0),
                xaxis=dict(range=[-1, 1], title="Avg Sentiment"),
                yaxis=dict(title=""),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
            )
            st.plotly_chart(fig3, use_container_width=True)

        st.divider()

        # ── LDA Topics ────────────────────────────────────────────────────────
        st.subheader("🧠 Discovered Topics  *(LDA)*")
        if topics:
            topic_cols = st.columns(min(len(topics), 5))
            for col, topic in zip(topic_cols, topics):
                with col:
                    pct = round(topic["weight"] * 100, 1)
                    st.markdown(f"**Topic {topic['topic']}** &nbsp; `{pct}%`")
                    chips = "".join(
                        f'<span class="topic-chip">{w}</span>' for w in topic["words"]
                    )
                    st.markdown(chips, unsafe_allow_html=True)
        else:
            st.caption("Not enough posts to run topic modeling (need ≥ 10 posts with varied vocabulary).")

        st.divider()

        # ── Top Posts ─────────────────────────────────────────────────────────
        st.subheader("Top Posts by Score")
        top = (
            df[["subreddit", "text", "score", "num_comments", "sentiment"]]
            .sort_values("score", ascending=False)
            .head(10)
            .copy()
        )
        top["sentiment"] = top["sentiment"].apply(lambda v: f"{v:+.3f}")
        st.dataframe(
            top.rename(columns={
                "subreddit": "Source", "text": "Text",
                "score": "Score", "num_comments": "Comments", "sentiment": "Sentiment",
            }),
            use_container_width=True,
            hide_index=True,
        )

else:
    # ── Empty state ───────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center; padding: 60px 0; color: #475569;">
        <div style="font-size: 3rem;">📊</div>
        <p style="font-size: 1.1rem; margin-top: 12px;">Enter a ticker symbol and click <strong>Analyze</strong> to start.</p>
        <p style="font-size: 0.85rem;">Pulls from r/wallstreetbets · r/investing · r/stocks · r/StockMarket · r/options</p>
        <p style="font-size: 0.85rem;">Runs VADER sentiment analysis + LDA topic modeling · Overlays stock price from Yahoo Finance</p>
    </div>
    """, unsafe_allow_html=True)
