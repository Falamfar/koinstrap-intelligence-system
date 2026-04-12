import psycopg2
from psycopg2.extras import RealDictCursor
import os
import logging
from dotenv import load_dotenv

# 1. SETUP THE DIARY (Logging)

LOG_FILE = "/home/falamfar/koinstrap_platform/projects/koinstrap/logs/populate_ml.log"
logger = logging.getLogger("populate_ml")
logger.setLevel(logging.INFO)

if not logger.handlers:
    stream_handler = logging.StreamHandler()
    file_handler = logging.FileHandler(LOG_FILE) 

formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
stream_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

logger.addHandler(stream_handler)
logger.addHandler(file_handler)

load_dotenv("/home/falamfar/koinstrap_platform/projects/koinstrap/config/.env")

def populate_features():
    logger.info("🏗️ Koin-Bot is building the UNIQUE ML Feature table...")

    try:
        conn = psycopg2.connect(
            host=os.getenv("PG_HOST"),
            user=os.getenv("PG_USER"),
            password=os.getenv("PG_PASSWORD"),
            database=os.getenv("PG_NAME"),
            port=os.getenv("PG_PORT")
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # 2. CLEAR THE TOY BOX (Fresh Start)
        logger.info ("📈 Adding new snapshots to the existing collection...") 
        

        # 3. THE "DISTINCT" QUERY
        # We use DISTINCT ON to make sure we only get ONE row per minute
        query = """
        SELECT DISTINCT ON (m.symbol, date_trunc('minute', m.metric_time))
            m.symbol, 
            m.metric_time, 
            m.price_usd, 
            m.price_change_5m, 
            m.price_change_15m, 
            m.volume_24h_usd,
            a.is_price_spike,
            a.is_trend_reversal,
            a.confidence_score,
            s.post_count,
            s.avg_sentiment
        FROM crypto_metrics m
        JOIN crypto_analysis a ON m.metric_time = a.metric_time_ref AND m.symbol = a.symbol
        LEFT JOIN social_sentiment_metrics s ON m.symbol = s.symbol 
            AND s.window_end <= m.metric_time 
            AND s.window_end > m.metric_time - INTERVAL '1 hour'
        ORDER BY m.symbol, date_trunc('minute', m.metric_time), m.metric_time ASC;
        """
        
        logger.info("📡 Gathering unique data snapshots...")
        cursor.execute(query)
        rows = cursor.fetchall()
        logger.info(f"📚 Found {len(rows)} unique time snapshots.")

        # 4. THE TIME TRAVEL LOOP (Answer Key)
        count = 0
        # We look 12 rows ahead (12 * 5 mins = 60 mins)
        for i in range(len(rows) - 12):
            current = rows[i]
            future = rows[i + 12]

            if current['symbol'] != future['symbol']:
                continue 
            
            # Is the future price higher than current?
            price_up = 1 if float(future['price_usd']) > float(current['price_usd']) else 0

            insert_query = """
            INSERT INTO ml_features (
                symbol, feature_time, price_usd, price_change_5m, 
                price_change_15m, volume_24h_usd, post_count, 
                avg_sentiment, is_price_spike, is_trend_reversal, 
                confidence_score, price_up_next_60m
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT( symbol, feature_time) DO NOTHING;
            """ 
            cursor.execute(insert_query, (
                current['symbol'], current['metric_time'], current['price_usd'],
                current['price_change_5m'], current['price_change_15m'], 
                current['volume_24h_usd'], current.get('post_count', 0) or 0,
                current.get('avg_sentiment', 0) or 0, current['is_price_spike'],
                current['is_trend_reversal'], current['confidence_score'], price_up
            ))
            count += 1

        conn.commit()
        logger.info(f"✅ Success! Saved {count} honest examples to ml_features.")

    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    populate_features()