"""
reddit_ingest_dag_ready.py - DAG-ready Production version

Purpose:
- Fetch latest Reddit posts for selected crypto symbols
- Compute sentiment using VADER
- Aggregate metrics per rolling window
- Compute changes vs previous window
- Insert results into social_sentiment_metrics table
- Ensure idempotency
- Return processed counts for DAG downstream tasks
"""

import os
import logging
import requests
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv("/home/falamfar/koinstrap_platform/projects/koinstrap/config/.env")
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# -----------------------------
# Logging configuration
# -----------------------------
LOG_FILE = "/home/falamfar/koinstrap_platform/projects/koinstrap/logs/reddit_ingest.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("reddit_ingest")
logger.info("🚀 Starting Reddit ingestion script (DAG-ready)")

# -----------------------------
# Database connection
# -----------------------------
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        return conn
    except Error as e:
        logger.error("Database connection failed", exc_info=True)
        raise

# -----------------------------
# Sentiment Analyzer
# -----------------------------
analyzer = SentimentIntensityAnalyzer()

# -----------------------------
# Helper: clamp values
# -----------------------------
def clamp(value, min_value=-1e9, max_value=1e9):
    return max(min_value, min(max_value, value))

# -----------------------------
# Process a single symbol
# -----------------------------
def process_symbol(symbol, window_minutes=15, reddit_limit=50):
    logger.info(f"Processing {symbol.upper()}...")
    window_end = datetime.now(timezone.utc)
    window_start = window_end - timedelta(minutes=window_minutes)

    url = f"https://www.reddit.com/search.json?q={symbol}&sort=new&limit={reddit_limit}"
    headers = {"User-Agent": "koinstrap-intelligent-bot"}

    # Fetch posts
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            logger.warning(f"Reddit request failed for {symbol} with status {response.status_code}")
            return 0

        data = response.json()
        posts = data.get("data", {}).get("children", [])
    except Exception as e:
        logger.exception(f"Error fetching Reddit posts for {symbol}: {e}")
        return 0

    # Compute sentiment
    sentiments = []
    post_count = 0
    for post in posts:
        post_data = post["data"]
        created_utc = datetime.fromtimestamp(post_data["created_utc"], tz=timezone.utc)
        if created_utc < window_start:
            continue

        text = f"{post_data.get('title','')} {post_data.get('selftext','')}"
        sentiments.append(analyzer.polarity_scores(text)["compound"])
        post_count += 1

    # Aggregate metrics
    if post_count == 0:
        avg_sentiment = positive_ratio = negative_ratio = neutral_ratio = 0
    else:
        avg_sentiment = sum(sentiments) / post_count
        positive_ratio = len([s for s in sentiments if s > 0.05]) / post_count
        negative_ratio = len([s for s in sentiments if s < -0.05]) / post_count
        neutral_ratio = len([s for s in sentiments if -0.05 <= s <= 0.05]) / post_count

    # Insert into DB
    conn = cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Idempotency check
        cursor.execute("""
            SELECT 1 FROM social_sentiment_metrics
            WHERE symbol=%s AND window_start=%s
            LIMIT 1
        """, (symbol, window_start))

        if cursor.fetchone():
            logger.info(f"{symbol.upper()} already ingested for window starting {window_start}, skipping")
            return 0

        # Previous window for delta
        cursor.execute("""
            SELECT post_count, avg_sentiment
            FROM social_sentiment_metrics
            WHERE symbol=%s
            ORDER BY window_start DESC
            LIMIT 1
        """, (symbol,))
        previous = cursor.fetchone()

        if previous:
            change_in_count = post_count - previous["post_count"]
            change_in_count_pct = (change_in_count / previous["post_count"] * 100 if previous["post_count"] else 0)
            change_in_sentiment = avg_sentiment - previous["avg_sentiment"]
            change_in_sentiment_pct = (change_in_sentiment / abs(previous["avg_sentiment"]) if previous["avg_sentiment"] else 0)
        else:
            change_in_count = change_in_count_pct = change_in_sentiment = change_in_sentiment_pct = 0

        cursor.execute("""
            INSERT INTO social_sentiment_metrics(
                symbol, window_start, window_end, post_count, avg_sentiment,
                positive_ratio, negative_ratio, neutral_ratio,
                change_in_count, change_in_count_pct,
                change_in_sentiment, change_in_sentiment_pct,
                source
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'reddit')
        """, (
            symbol, window_start, window_end, post_count, avg_sentiment,
            positive_ratio, negative_ratio, neutral_ratio,
            clamp(change_in_count),
            clamp(change_in_count_pct, -100, 100),
            clamp(change_in_sentiment, -1, 1),
            clamp(change_in_sentiment_pct, -100, 100)
        ))

        conn.commit()
        logger.info(f"{symbol.upper()} inserted successfully with {post_count} posts")
        return post_count

    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception(f"Error processing {symbol}: {e}")
        return 0

    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# -----------------------------
# DAG-ready wrapper
# -----------------------------
def run_reddit_ingest(symbols=None, window_minutes=15, reddit_limit=50):
    symbols = symbols or ["btc", "eth"]
    results = {}
    for symbol in symbols:
        count = process_symbol(symbol, window_minutes, reddit_limit)
        results[symbol] = count
    logger.info(f"Reddit ingestion completed. Results: {results}")
    return results

# -----------------------------
# Entry point for local run
# -----------------------------
if __name__ == "__main__":
    run_reddit_ingest()