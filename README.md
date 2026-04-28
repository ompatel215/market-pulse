# Market Pulse
CMPSC 446 Final Project

## Overview
Real-time market sentiment analysis dashboard that aggregates data from Reddit, Google News, and Stocktwits to quantify market sentiment and overlay it against stock price history. Uses VADER sentiment analysis and LDA topic modeling to surface insights about public market perception.

## Features
- Live scraping from Reddit (10 subreddits), Google News (RSS), and Stocktwits
- VADER sentiment scoring with Bullish/Bearish/Neutral classification
- LDA topic modeling to surface trending themes per ticker
- Dual-axis chart overlaying sentiment vs. stock price (via yfinance)
- Source breakdown, sentiment distribution, and top posts by engagement
- VADER accuracy validation against Stocktwits user-labeled sentiment
- Pre-scraped CSV cache for fast, reliable demo loading

## Setup
1. Clone the repo.
2. Install dependencies: `pip install -r requirements.txt`
3. Run the dashboard: `streamlit run app.py`

> No API keys required. Reddit is accessed via the public JSON API.

## Dataset Generation
To regenerate the pre-scraped dataset:
```bash
python scrape_dataset.py
```
This scrapes Reddit, Google News, and Stocktwits for NVDA, TSLA, AAPL, AMD, and SPY, then saves results to `data/dataset.csv` and `data/stock_prices.csv`.

## Project Structure
```
market-pulse/
├── app.py                  # Streamlit dashboard (main entry point)
├── scrape_dataset.py       # Batch scraper for pre-populating CSV cache
├── src/
│   ├── processor.py        # Text cleaning and ticker extraction
│   ├── analyzer.py         # VADER sentiment, LDA topic modeling, accuracy metrics
│   ├── stock.py            # yfinance stock price fetching
│   └── scraper/
│       ├── reddit.py       # Reddit public JSON API scraper
│       ├── news.py         # Google News RSS scraper
│       ├── stocktwits.py   # Stocktwits API scraper
│       └── twitter.py      # Twitter stub (disabled — API revoked 2023)
├── data/
│   ├── dataset.csv         # Pre-scraped posts with sentiment scores
│   └── stock_prices.csv    # Historical OHLCV data for tracked tickers
├── notebooks/
│   └── exploration.ipynb   # EDA notebook (placeholder)
└── requirements.txt
```

## Tech Stack
| Category | Library |
|----------|---------|
| Dashboard | Streamlit |
| Sentiment Analysis | vaderSentiment |
| Topic Modeling | scikit-learn (LDA) |
| Visualization | Plotly |
| Stock Data | yfinance |
| Data Processing | Pandas, NumPy |
| Web Scraping | requests |

## Team
- Om Patel
- Nirmal Nelson
- Abel Prasad
