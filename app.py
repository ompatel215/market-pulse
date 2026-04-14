import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

st.set_page_config(page_title="Market Pulse", layout="wide")

st.title("Market Pulse")
st.caption("Real-time Reddit sentiment tracker for market volatility detection")

# --- Ticker Input ---
col1, col2 = st.columns([3, 1])
with col1:
    ticker = st.text_input("Ticker", placeholder="e.g. TSLA, NVDA, AAPL", label_visibility="collapsed")
with col2:
    fetch = st.button("Fetch Sentiment", use_container_width=True)

st.divider()

# --- Mock Data ---
dates = pd.date_range(end=pd.Timestamp.now(), periods=48, freq="h")
np.random.seed(42)
sentiment = np.clip(np.cumsum(np.random.normal(0, 0.05, 48)), -1, 1)
mentions = np.random.randint(5, 80, 48)

# --- Metrics Row ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("Current Sentiment", "0.42", "+0.11 vs yesterday")
m2.metric("Mention Volume (24h)", "1,284", "+38%")
m3.metric("Anomaly Flags", "2", "last 7 days")
m4.metric("Top Subreddit", "r/wallstreetbets")

st.divider()

# --- Charts ---
chart1, chart2 = st.columns(2)

with chart1:
    st.subheader("Sentiment Over Time (48h)")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=sentiment,
        mode="lines",
        line=dict(color="#00C896", width=2),
        fill="tozeroy",
        fillcolor="rgba(0,200,150,0.1)",
    ))
    fig.add_hline(y=0, line_dash="dash", line_color="gray", line_width=1)
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        yaxis=dict(range=[-1, 1], title="Sentiment Score"),
        xaxis=dict(title=""),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

with chart2:
    st.subheader("Mention Volume (48h)")
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=dates, y=mentions,
        marker_color="#4F8EF7",
    ))
    fig2.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        yaxis=dict(title="Posts / hr"),
        xaxis=dict(title=""),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# --- Anomaly Flags ---
st.subheader("Anomaly Flags")
anomalies = pd.DataFrame([
    {"Timestamp": "2026-04-12 14:00", "Type": "Sentiment Spike", "Z-Score": "+2.8σ", "Direction": "Bullish"},
    {"Timestamp": "2026-04-11 09:00", "Type": "Mention Surge",   "Z-Score": "+3.1σ", "Direction": "Bearish"},
])
st.dataframe(anomalies, use_container_width=True, hide_index=True)

st.divider()

# --- Top Posts ---
st.subheader("Top Posts")
posts = pd.DataFrame([
    {"Title": "TSLA to the moon after earnings beat",    "Subreddit": "r/wallstreetbets", "Score": 4200, "Sentiment": 0.87,  "Time": "2h ago"},
    {"Title": "Why I'm still holding TSLA long-term",    "Subreddit": "r/investing",      "Score": 1800, "Sentiment": 0.61,  "Time": "5h ago"},
    {"Title": "Sold my TSLA bags, here's why",           "Subreddit": "r/stocks",         "Score": 1100, "Sentiment": -0.62, "Time": "8h ago"},
    {"Title": "TSLA overvalued at current levels — DD",  "Subreddit": "r/investing",      "Score": 890,  "Sentiment": -0.74, "Time": "12h ago"},
    {"Title": "Riding the TSLA wave this week",          "Subreddit": "r/wallstreetbets", "Score": 670,  "Sentiment": 0.55,  "Time": "18h ago"},
])
st.dataframe(posts, use_container_width=True, hide_index=True)
