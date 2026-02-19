import requests
import mysql.connector
import os
import logging
import time
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv 
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


# -----------------------------------------
# LOAD ENVIRONMENT VARIABLES
# -----------------------------------------

load_dotenv("/home/falamfar/projects/koinstrap/config/.env")


DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# -----------------------------------------
# LOGGING CONFIGURATION
# -----------------------------------------


LOG_FILE = "/home/falamfar/projects/koinstrap/logs/reddit_ingest.log"
logging.basicConfig(
    filename = LOG_FILE,
    level = logging.INFO,
    format = "%(asctime)s - %(levelname)s - %(message)s"
)


logging.info("🚀 Starting Reddit ingestion script")

# -----------------------------------------
# DATABASE CONNECTION
# -----------------------------------------

def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

# -----------------------------------------
# SENTIMENT ANALYZER
# -----------------------------------------

analyzer = SentimentIntensityAnalyzer()

# -----------------------------------------
# CONFIG
# -----------------------------------------

SYMBOLS = ["btc", "eth"]
WINDOW_MINUTES = 15
REDDIT_LIMIT = 50  # how many recent posts to fetch

# -----------------------------------------
# MAIN PROCESS FUNCTION
# -----------------------------------------

def process_symbol(symbol):
    try:
        logging.info(f"processing {symbol.upper()}")

        # -----------------------------------------
        # 1️⃣ Calculate 15-minute window
        # -----------------------------------------

        window_end = datetime.now(timezone.utc)
        window_start = window_end - timedelta(minutes=WINDOW_MINUTES)

        # -----------------------------------------
        # 2️⃣ Fetch Reddit posts (public JSON endpoint)
        # ----------------------------------------- 

        url = f"https://www.reddit.com/search.json?q={symbol}&sort=new&limit={REDDIT_LIMIT}" 
        headers = {
            "User-Agent": "koinstrap-intelligent-bot"
        } 

        response = requests.get(url, headers=headers, timeout = 10)

        if response.status_code != 200:
            logging.warning(f"Reddit request failed for {symbol} with status {response.status_code}")
            return

        data = response.json()
        posts = data["data"]["children"] 

        sentiments = []
        post_count = 0 

        
        # -----------------------------------------
        # 3️⃣ Loop through posts and compute sentiment
        # -----------------------------------------

        for post in posts:
            post_data = post["data"]

            created_utc = datetime.fromtimestamp(
                post_data["created_utc"],
                tz=timezone.utc
            )

            # Only include posts inside our 15 min window
            if created_utc < window_start:
                continue

            title = post_data.get("title", "")
            body = post_data.get("selftext", "") 

            full_text = title + " " + body 

            sentiment_score = analyzer.polarity_scores(full_text)["compound"] 

            sentiments.append(sentiment_score)

            post_count += 1 


        
        # -----------------------------------------
        # 4️⃣ Aggregate metrics
        # -----------------------------------------

        if post_count == 0:
            avg_sentiment = 0
            positive_ratio = 0
            negative_ratio = 0
            neutral_ratio = 0

        else:
            avg_sentiment = sum(sentiments) / post_count

            positive_ratio = len([s for s in sentiments if s > 0.05]) / post_count
            negative_ratio = len([s for s in sentiments if s < -0.05]) / post_count
            neutral_ratio = len([s for s in sentiments if -0.05 <= s <= 0.05]) / post_count

        # -----------------------------------------
        # 5️⃣ Fetch previous window for change calculation
        # -----------------------------------------  

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT post_count, avg_sentiment
            FROM social_sentiment_metrics
            WHERE symbol = %s 
            ORDER BY window_start DESC
            LIMIT 1
        """, (symbol,))
        previous = cursor.fetchone() 


        if previous:
            change_in_count = post_count - previous["post_count"]
            if previous["post_count"] != 0:
                change_in_count_pct = (change_in_count / previous["post_count"]) * 100 
            else:
                change_in_count_pct = 0

            change_in_sentiment = avg_sentiment - previous["avg_sentiment"]

            if previous["avg_sentiment"] != 0:
                change_in_sentiment_pct = (change_in_sentiment / abs(previous["avg_sentiment"])) 
            else :
                change_in_sentiment_pct = 0
        else:
            change_in_count = 0
            change_in_count_pct = 0
            change_in_sentiment = 0
            change_in_sentiment_pct = 0

        # -----------------------------------------
        # 6️⃣ Insert into table
        # -----------------------------------------

        cursor.execute("""
            INSERT INTO social_sentiment_metrics(
                symbol,
                window_start,
                window_end,
                post_count,
                avg_sentiment,
                positive_ratio,
                negative_ratio,
                neutral_ratio,
                change_in_count,
                change_in_count_pct,
                change_in_sentiment,
                change_in_sentiment_pct,
                source
            ) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'reddit')
        """, (
            symbol,
            window_start,
            window_end,
            post_count,
            avg_sentiment,
            positive_ratio,
            negative_ratio,
            neutral_ratio,
            change_in_count,
            change_in_count_pct,
            change_in_sentiment,
            change_in_sentiment_pct
        ))

        conn.commit()

        logging.info(f"{symbol.upper()} inserted succesfully with {post_count} posts") 
        
        cursor.close()
        conn.close()

    except Exception as e:
        logging.exception(f"Error processing {symbol}: {e}")       

# -----------------------------------------
# ENTRY POINT
# -----------------------------------------

if __name__ == "__main__":
    for symbol in SYMBOLS:
        process_symbol(symbol)

    logging.info("✅ Reddit ingestion completed")




                




