"""
twitter_ingest.py

This script fetches tweets for BTC and ETH using snscrape, calculates sentiment using Vader,
aggregates metrics per time window, computes changes from the previous window, 
and stores everything in the twitter_sentiment_metrics table.
"""

import os
import mysql.connector
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone 
import pandas as pd 
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import snscrape.modules.twitter as sntwitter
import logging

# -----------------------------
# Load environment variables
# -----------------------------

load_dotenv("/home/falamfar/projects/koinstrap/config/.env")

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")


# -----------------------------
# Logging setup
# -----------------------------

LOG_FILE = "/home/falamfar/projects/koinstrap/logs/twitter_ingest.log" 

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.info("Twitter ingestion script started.")

# -----------------------------
# Database connection function
# -----------------------------

def get_db_connection():
    return mysql.connector.connect(
        host = DB_HOST,
        user = DB_USER,
        password = DB_PASSWORD,
        database = DB_NAME
    )
    
# -----------------------------
# Sentiment Analyzer
# -----------------------------

analyser = SentimentIntensityAnalyzer()


# -----------------------------
# Config
# -----------------------------

symbols = ["BTC", "ETH"]

window_minutes = 15 #aggregation window
now = datetime.utcnow().replace(tzinfo=timezone.utc)
window_start = now - timedelta(minutes=window_minutes)
window_end = now 

# -----------------------------
# Function to calculate sentiment
# -----------------------------

def get_sentiment(text):
    scores = analyzer.polarity_scores(text)
    return scores['compound'], scores['pos'], scores['neg'], scores ['neu']


# -----------------------------
# Connect to DB
# -----------------------------

conn = get_db_connection()
cursor = conn.cursor()

for symbol in symbols:
    logging.info(f"Processing tweets for {symbol}")

    # --- Fetch tweets from snscrape
    query = f"{symbol} lang:en since:{window_start.date()} until:{window_end.date()}"
    tweets = []
    for i, tweet in enumerate(sntwitter.TwitterSearchScraper(query).get_items()):
        if tweet.date.replace(tzinfo=timezone.utc) < window_start:
            continue 
        if tweet.date.replace(tzinfo=timezone.utc) > window_end:
            break
        tweets.append(tweet)

    tweet_count = len(tweet)

    if tweet_count == 0:
        logging.warning(f"No tweets found for {symbol} in the specified time window.")
        avg_sentiment = 0
        pos_ratio = neg_ratio = neu_ratio = 0
    else:
        sentiments = [get_sentiment(t.content) for t in tweets] 
        compound_scores = [s[0] for s in sentiments] 
        pos_scores = [s[1] for s in sentiments]
        neg_scores = [s[2] for s in sentiments]
        neu_scores = [s[3] for s in sentiments]

        avg_sentiment = sum(compound_scores) / tweet_count
        pos_ratio = sum(pos_scores) / tweet_count
        neg_ratio = sum(neg_scores) / tweet_count
        neu_ratio = sum(neu_scores) / tweet_count

    # --- Fetch previous window metrics to calculate changes 
    cursor.execute("""
        SELECT tweet_count, avg_sentiment
        FROM twitter_sentiment_metrics
        WHERE symbol = %s
        ORDER BY window_end DESC
        LIMIT 1
    """, (symbol,))
    prev = cursor.fetchone()

    if prev:
        change_in_count = tweet_count - prev['tweet_count']
        change_in_count_pct = (change_in_count / prev['tweet_count'] * 100) if prev['tweet_count'] else 0
        change_in_sentiment = avg_sentiment - prev['avg_sentiment']
        change_in_sentiment_pct = (change_in_sentiment / prev['avg_sentiment'] * 100) if prev['avg_sentiment'] else 0

    else:
        change_in_count = change_in_count_pct = change_in_sentiment_pct = change_in_sentiment_pct = 0

    
    # --- Insert into DB
    cursor.execute("""
        INSERT INTO twitter_sentiment_metrics (symbol, window_start, window_end, tweet_count, avg_sentiment, pos_ratio, neg_ratio, neu_ratio, change_in_count, change_in_count_pct, change_in_sentiment, change_in_sentiment_pct)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        symbol, window_start, window_end, tweet_count, avg_sentiment, pos_ratio, neg_ratio, neu_ratio, change_in_count, change_in_count_pct, change_in_sentiment, change_in_sentiment_pct))

conn.commit()
cursor.close()
conn.close()

logging.info("Twitter ingestion comlete") 

