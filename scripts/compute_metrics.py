"""
compute_metrics.py
----------------------
DAG-friendly script to compute crypto metrics from raw data.

Features:
- Idempotent: avoids duplicate inserts for the same metric_time & symbol
- Computes price deltas (5m, 15m) and 1h aggregates
- Parameterized for symbols, time windows, and DB connection
- Logs all steps for monitoring and debugging
- Returns the count of metrics inserted
"""

import os
import logging
import psycopg2 
import sys
from psycopg2 import Error
from psycopg2.extras import RealDictCursor 
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from typing import List

# ---------------------------------------------------------
# 1️⃣ ENVIRONMENT CONFIGURATION
# ---------------------------------------------------------
ENV_PATH = "/app/config/.env"
load_dotenv(ENV_PATH)

DB_HOST = os.getenv("PG_HOST")
DB_USER = os.getenv("PG_USER")
DB_PASSWORD = os.getenv("PG_PASSWORD")
DB_NAME = os.getenv("PG_NAME")
DB_PORT = os.getenv("PG_PORT") 

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
# 3️⃣ DATABASE CONNECTION
# ---------------------------------------------------------
def get_db_connection():
    """Establish and return a PostgreSQL connection."""
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
# 4️⃣ HELPER FUNCTION: Clamp values
# ---------------------------------------------------------
def clamp(value, min_value=0, max_value=1e9):
    """Ensure numeric value stays in a reasonable range."""
    return max(min_value, min(max_value, value))

# ---------------------------------------------------------
# 5️⃣ MAIN METRICS FUNCTION (DAG-FRIENDLY)
# ---------------------------------------------------------


def run_compute_metrics(symbols=["btc", "eth"], price_delta_windows=[5, 15]):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor) 
    inserted_count = 0

    try:
        for symbol in symbols:
            # STEP 1: Find the LATEST timestamp available for this symbol in RAW data
            cursor.execute("""
                SELECT MAX(observed_at) as latest_time 
                FROM raw_crypto_market_data 
                WHERE symbol = %s
            """, (symbol,))
            res = cursor.fetchone()
            
            if not res or not res['latest_time']:
                logger.warning(f"No raw data found at all for {symbol}. Skipping.")
                continue
                
            
            metric_time = res['latest_time'].replace(second=0, microsecond=0)
            
            # Look back 70 mins from the DATA'S timestamp
            aggregate_window_start = metric_time - timedelta(minutes=70)

            # STEP 2: Fetch raw data around that specific timestamp
            cursor.execute("""
                SELECT observed_at, price_usd, volume_24h_usd
                FROM raw_crypto_market_data
                WHERE symbol = %s AND observed_at >= %s AND observed_at <= %s
                ORDER BY observed_at DESC
            """, (symbol, aggregate_window_start, metric_time))
            rows = cursor.fetchall()

            if not rows:
                logger.info(f"No rows found for {symbol} at target time {metric_time}")
                continue

          
            price_now = float(rows[0]["price_usd"])
            deltas = {}

            for delta_min in price_delta_windows:
                cutoff_time = metric_time - timedelta(minutes=delta_min)
                # Fuzzy look-back: find closest row <= cutoff
                price_before_row = next((r for r in rows if r["observed_at"] <= cutoff_time), None)
                
                if price_before_row:
                    price_before = float(price_before_row["price_usd"])
                    pct_change = ((price_now - price_before) / price_before) * 100
                    deltas[f"price_change_{delta_min}m"] = round(pct_change, 4)
                else:
                    deltas[f"price_change_{delta_min}m"] = 0.0

            # Aggregates
            prices = [float(r["price_usd"]) for r in rows]
            avg_price = sum(prices)/len(prices)
            
            # STEP 4: Insert (Using the Data's actual timestamp)
            insert_query = """
                INSERT INTO crypto_metrics (
                    metric_time, symbol, price_usd, price_change_5m, price_change_15m,
                    volume_24h_usd, avg_price_1h, min_price_1h, max_price_1h
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (metric_time, symbol) DO NOTHING 
            """
            cursor.execute(insert_query, (
                metric_time, symbol, price_now, 
                deltas.get("price_change_5m"), deltas.get("price_change_15m"),
                rows[0]["volume_24h_usd"], avg_price, min(prices), max(prices)
            ))
            
            if cursor.rowcount > 0:
                inserted_count += 1
                logger.info(f"🚀 SUCCESS: Computed metrics for {symbol} at {metric_time}")
            else:
                logger.info(f"😴 SKIPPED: Metrics for {symbol} at {metric_time} already exist.")

        conn.commit()

    except Exception as e:
        conn.rollback()
        logger.error(f"❌ DATABASE ERROR: {e}")
        raise
    finally:
        conn.close()
        logger.info(f"Process complete. Total metrics created: {inserted_count}")

    return inserted_count

if __name__ == "__main__":
    run_compute_metrics()