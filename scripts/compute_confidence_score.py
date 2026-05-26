"""
compute_confidence_score.py
-------------------------------
DAG-friendly script to compute confidence scores for crypto analysis rows.

Features:
- Reads crypto_analysis rows with missing or zero confidence_score
- Combines market signals (price spike, trend reversal, volume spike)
  and social sentiment (Reddit metrics)
- Applies configurable weights
- Inserts/updates confidence_score in crypto_analysis
- Returns count of rows updated
"""

import os
import logging
import psycopg2
import sys
from psycopg2 import Error
from psycopg2.extras import RealDictCursor 
from dotenv import load_dotenv
from datetime import datetime, timezone
from typing import Dict

# ---------------------------------------------------------
# 1️⃣ LOAD ENVIRONMENT VARIABLES
# ---------------------------------------------------------
ENV_PATH = "/app/config/.env"
load_dotenv(ENV_PATH)

DB_HOST = os.getenv("PG_HOST")
DB_USER = os.getenv("PG_USER")
DB_PASSWORD = os.getenv("PG_PASSWORD")
DB_NAME = os.getenv("PG_NAME")
DB_PORT = os.getenv("PG_PORT", 5432) 

# ---------------------------------------------------------
# 2️⃣ LOGGER CONFIGURATION
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# 3️⃣ CONFIDENCE WEIGHTS
# ---------------------------------------------------------
CONF_WEIGHTS = {
    "baseline": 50.0,
    "price_spike": 10,
    "trend_reversal": 15,
    "volume_spike": 5,
    "bullish_trend": 5,
    "bearish_trend": -5,
    "sentiment_pct_multiplier": 0.5,
    "social_activity_multiplier": 0.2
}

# ---------------------------------------------------------
# 4️⃣ DATABASE CONNECTION
# ---------------------------------------------------------
def get_db_connection():
    """Return PostgreSQL connection object."""
    try:
        conn = psycopg2.connect( 
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT
        )
        logger.info("Database connection established.")
        return conn
    except Error as e:
        logger.error("Database connection failed.", exc_info=True)
        raise

# ---------------------------------------------------------
# 5️⃣ HELPER: Clamp confidence to [0, 100]
# ---------------------------------------------------------
def clamp(value: float, min_value: float = 0, max_value: float = 100) -> float:
    return max(min_value, min(max_value, value))

# ---------------------------------------------------------
# 6️⃣ COMPUTE CONFIDENCE FOR SINGLE ROW
# ---------------------------------------------------------
def compute_confidence(row: Dict, sentiment_row: Dict = None) -> float:
    """
    Compute confidence score based on:
    - Market signals (price spike, trend reversal, volume spike)
    - Trend direction (Bullish/Bearish)
    - Optional social sentiment metrics
    """
    conf = CONF_WEIGHTS["baseline"]

    # Market signals
    if row.get('is_price_spike'): conf += CONF_WEIGHTS["price_spike"]
    if row.get('is_trend_reversal'): conf += CONF_WEIGHTS["trend_reversal"]
    if row.get('is_volume_spike'): conf += CONF_WEIGHTS["volume_spike"]

    # Trend signals
    trend = row.get('trend_signal')
    if trend == "Bullish": conf += CONF_WEIGHTS["bullish_trend"]
    elif trend == "Bearish": conf += CONF_WEIGHTS["bearish_trend"] 

    # Social sentiment metrics (optional)
    if sentiment_row:

        sent_pct = float(sentiment_row.get('change_in_sentiment_pct',0) or 0)  
        count_pct = float(sentiment_row.get('change_in_count_pct',0) or 0)  

        conf += sent_pct * CONF_WEIGHTS["sentiment_pct_multiplier"]
        conf += count_pct * CONF_WEIGHTS["social_activity_multiplier"]

    return clamp(conf)

# ---------------------------------------------------------
# 7️⃣ MAIN DAG-FRIENDLY FUNCTION
# ---------------------------------------------------------
def run_confidence(symbols: list = None) -> int:
    """
    Compute and update confidence scores for crypto_analysis rows.

    Args:
        symbols: optional list of symbols to process, default None = all

    Returns:
        updated_count: number of rows successfully updated
    """
    symbols = symbols or ["btc", "eth"]
    updated_count = 0

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor) 

    try:
        for symbol in symbols:
            # 1️⃣ Fetch analysis rows with missing/zero confidence
            cursor.execute("""
                SELECT *
                FROM crypto_analysis
                WHERE (confidence_score IS NULL OR confidence_score = 0)
                AND symbol = %s
                ORDER BY analysis_time ASC
            """, (symbol,))
            rows = cursor.fetchall()
            logger.info(f"Found {len(rows)} rows for {symbol} to compute confidence.")

            for row in rows:
                analysis_id = row['analysis_id']
                analysis_time = row['analysis_time']

                # 2️⃣ Fetch most recent social sentiment before analysis_time
                cursor.execute("""
                    SELECT *
                    FROM social_sentiment_metrics
                    WHERE symbol = %s AND window_end <= %s
                    ORDER BY window_end DESC
                    LIMIT 1
                """, (symbol, analysis_time))
                sentiment_row = cursor.fetchone()

                # 3️⃣ Compute confidence
                confidence = compute_confidence(row, sentiment_row)

                # 4️⃣ Update DB
                cursor.execute("""
                    UPDATE crypto_analysis
                    SET confidence_score = %s
                    WHERE analysis_id = %s
                """, (confidence, analysis_id))

                updated_count += 1
                logger.info(f"Updated analysis_id={analysis_id} | symbol={symbol} | confidence={confidence:.2f}")

        conn.commit()
        logger.info(f"All confidence scores updated. Total rows: {updated_count}")

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error("Error computing confidence scores. Transaction rolled back.", exc_info=True)
        raise
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
        logger.info("Database connection closed.")

    return updated_count

# ---------------------------------------------------------
# 8️⃣ ENTRY POINT FOR MANUAL RUN
# ---------------------------------------------------------
if __name__ == "__main__":
    updated = run_confidence()
    logger.info(f"Manual run complete. {updated} rows updated with confidence scores.")