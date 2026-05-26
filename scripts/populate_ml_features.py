import psycopg2
import sys 
from psycopg2.extras import RealDictCursor
import os
import logging
from dotenv import load_dotenv

# 1. SETUP LOGGING
def setup_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:  # prevents duplicates in Airflow
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s"
        )

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)

        logger.addHandler(handler)

    return logger


logger = setup_logger(__name__)

ENV_PATH = "/app/config/.env"
load_dotenv(ENV_PATH)

def populate_features():
    logger.info("🏗️ Koin-Bot is building/updating the ML Feature table...")

    conn = None
    try:
        conn = psycopg2.connect(
            host=os.getenv("PG_HOST"),
            user=os.getenv("PG_USER"),
            password=os.getenv("PG_PASSWORD"),
            database=os.getenv("PG_NAME"),
            port=os.getenv("PG_PORT")
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)

      
        query = """
        WITH cleaned_sentiment AS (
            SELECT 
                symbol,
                date_trunc('minute', created_at) as sync_time,
                AVG(avg_sentiment) as final_sentiment,
                SUM(post_count) as total_posts
            FROM social_sentiment_metrics
            GROUP BY symbol, sync_time
        )
        SELECT 
            m.symbol, 
            m.metric_time, 
            m.price_usd, 
            m.price_change_5m, 
            m.price_change_15m, 
            m.volume_24h_usd,
            a.is_price_spike,
            a.is_trend_reversal,
            a.confidence_score,
            COALESCE(cs.total_posts, 0) as post_count,
            COALESCE(cs.final_sentiment, 0) as avg_sentiment
        FROM crypto_metrics m
        JOIN crypto_analysis a ON m.metric_time = a.metric_time_ref AND m.symbol = a.symbol
        LEFT JOIN cleaned_sentiment cs ON m.symbol = cs.symbol 
            AND m.metric_time = cs.sync_time
        ORDER BY m.symbol, m.metric_time ASC;
        """
        
        logger.info("📡 Gathering data snapshots...")
        cursor.execute(query)
        rows = cursor.fetchall()
        logger.info(f"📚 Found {len(rows)} potential snapshots.")

        # 3. THE TIME TRAVEL LOOP (Labeling)
        count = 0
        # Look 12 rows ahead (12 * 5 mins = 60 mins)
        for i in range(len(rows) - 12):
            current = rows[i]
            future = rows[i + 12]

            # Ensure we aren't comparing BTC to ETH
            if current['symbol'] != future['symbol']:
                continue 
            
            # Calculate the "Target" (What the AI is trying to predict)
            price_up = 1 if float(future['price_usd']) > float(current['price_usd']) else 0

            # 4. UPSERT LOGIC (Update if exists, Insert if new)
            insert_query = """
            INSERT INTO ml_features (
                symbol, feature_time, price_usd, price_change_5m, 
                price_change_15m, volume_24h_usd, post_count, 
                avg_sentiment, is_price_spike, is_trend_reversal, 
                confidence_score, price_up_next_60m
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (symbol, feature_time) 
            DO UPDATE SET 
                price_up_next_60m = EXCLUDED.price_up_next_60m,
                confidence_score = EXCLUDED.confidence_score,
                post_count = EXCLUDED.post_count,
                avg_sentiment = EXCLUDED.avg_sentiment,
                price_usd = EXCLUDED.price_usd;
            """ 

            cursor.execute(insert_query, (
                current['symbol'], current['metric_time'], current['price_usd'],
                current['price_change_5m'], current['price_change_15m'], 
                current['volume_24h_usd'], current.get('post_count') or 0,
                current.get('avg_sentiment') or 0, current['is_price_spike'],
                current['is_trend_reversal'], current['confidence_score'], price_up
            ))
            count += 1

        conn.commit()
        logger.info(f"✅ Success! Processed {count} snapshots into ml_features.")

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"❌ Error: {str(e)}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    populate_features()