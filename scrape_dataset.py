"""
Batch scraper — saves a combined Reddit + Google News dataset to data/dataset.csv
Run once before the demo: python scrape_dataset.py
"""
import time
import pandas as pd
from pathlib import Path
import sys
sys.path.append(".")

from src.scraper.reddit import scrape_subreddit
from src.scraper.news import scrape_google_news
from src.scraper.stocktwits import scrape_stocktwits
from src.processor import process_posts
from src.analyzer import analyze_posts
from src.stock import fetch_stock_prices

TICKERS = ["NVDA", "TSLA", "AAPL", "AMD", "SPY"]

SUBREDDITS = [
    "wallstreetbets", "investing", "stocks", "StockMarket", "options",
    "Superstonk", "pennystocks", "Daytrading", "ValueInvesting", "SecurityAnalysis",
]

LIMIT_PER_SUB = 50  # posts per subreddit per category

Path("data").mkdir(exist_ok=True)


def scrape_all():
    print("=" * 60)
    print("Market Pulse — Batch Dataset Scraper")
    print("=" * 60)

    # ── Reddit ────────────────────────────────────────────────
    print(f"\n[1/2] Scraping {len(SUBREDDITS)} subreddits...")
    all_reddit = []
    for sub in SUBREDDITS:
        for category in ["hot", "new"]:
            try:
                posts = scrape_subreddit(sub, limit=LIMIT_PER_SUB, category=category)
                all_reddit.extend(posts)
                print(f"  r/{sub} [{category}]: {len(posts)} posts")
            except Exception as e:
                print(f"  r/{sub} [{category}]: FAILED — {e}")

    # ── Google News ───────────────────────────────────────────
    print(f"\n[2/3] Scraping Google News for {TICKERS}...")
    all_news = []
    for ticker in TICKERS:
        try:
            news = scrape_google_news(ticker, limit=75)
            all_news.extend(news)
            print(f"  {ticker}: {len(news)} headlines")
        except Exception as e:
            print(f"  {ticker}: FAILED — {e}")
        time.sleep(0.5)

    # ── Stocktwits ────────────────────────────────────────────
    print(f"\n[3/3] Scraping Stocktwits for {TICKERS}...")
    all_stocktwits = []
    for ticker in TICKERS:
        try:
            posts = scrape_stocktwits(ticker, limit=30)
            all_stocktwits.extend(posts)
            labeled = sum(1 for p in posts if p.get("st_sentiment"))
            print(f"  {ticker}: {len(posts)} messages ({labeled} user-labeled)")
        except Exception as e:
            print(f"  {ticker}: FAILED — {e}")
        time.sleep(0.5)

    all_posts = all_reddit + all_news + all_stocktwits
    print(f"\nTotal raw posts: {len(all_posts)}")

    # ── Process + deduplicate ─────────────────────────────────
    df = process_posts(all_posts)
    df = df.drop_duplicates(subset=["id"])
    print(f"After dedup: {len(df)} posts")

    # ── Sentiment ─────────────────────────────────────────────
    df = analyze_posts(df)

    # ── Filter to tickers of interest ─────────────────────────
    ticker_rows = []
    for ticker in TICKERS:
        t_df = df[df["tickers"].apply(lambda t: ticker in t)].copy()
        t_df["query_ticker"] = ticker
        ticker_rows.append(t_df)
        print(f"  {ticker}: {len(t_df)} matching posts")

    combined = pd.concat(ticker_rows, ignore_index=True)
    combined = combined.drop_duplicates(subset=["id", "query_ticker"])

    # ── Save posts dataset ────────────────────────────────────
    out_path = Path("data/dataset.csv")
    combined.to_csv(out_path, index=False)
    print(f"\n✓ Saved {len(combined)} rows → {out_path}")

    # ── Save stock prices ─────────────────────────────────────
    print("\nFetching stock prices...")
    stock_frames = []
    for ticker in TICKERS:
        s = fetch_stock_prices(ticker, period="3mo")
        if not s.empty:
            s["ticker"] = ticker
            stock_frames.append(s)
            print(f"  {ticker}: {len(s)} days")

    if stock_frames:
        stocks = pd.concat(stock_frames, ignore_index=True)
        stocks.to_csv("data/stock_prices.csv", index=False)
        print(f"✓ Saved stock prices → data/stock_prices.csv")

    # ── Summary stats ─────────────────────────────────────────
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for ticker in TICKERS:
        t_df = combined[combined["query_ticker"] == ticker]
        if t_df.empty:
            continue
        avg = t_df["sentiment"].mean()
        bull = (t_df["sentiment"] > 0.05).sum()
        bear = (t_df["sentiment"] < -0.05).sum()
        mood = "BULLISH" if avg > 0.05 else "BEARISH" if avg < -0.05 else "NEUTRAL"
        print(f"  {ticker:5s} | {len(t_df):3d} posts | avg={avg:+.3f} | {mood} | 🟢{bull} 🔴{bear}")

    print("\nDone. Run 'streamlit run app.py' to launch the dashboard.")


if __name__ == "__main__":
    scrape_all()
