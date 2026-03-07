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
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from typing import List

# ---------------------------------------------------------
# 1️⃣ ENVIRONMENT CONFIGURATION
# ---------------------------------------------------------
load_dotenv("/home/falamfar/koinstrap_platform/projects/koinstrap/config/.env")
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# ---------------------------------------------------------
# 2️⃣ LOGGER CONFIGURATION
# ---------------------------------------------------------
logger = logging.getLogger("compute_metrics")
logger.setLevel(logging.INFO)
if not logger.handlers:
    file_handler = logging.FileHandler("/home/falamfar/koinstrap_platform/projects/koinstrap/logs/compute_metrics.log")
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

# ---------------------------------------------------------
# 3️⃣ DATABASE CONNECTION
# ---------------------------------------------------------
def get_db_connection():
    """Establish and return a MySQL connection."""
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
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
def run_compute_metrics(symbols: List[str] = None, 
                        price_delta_windows: List[int] = [5, 15], 
                        aggregate_window_minutes: int = 60) -> int:
    """
    Compute metrics from raw_crypto_market_data and insert into crypto_metrics.

    Args:
        symbols: list of coin symbols to process
        price_delta_windows: list of delta windows in minutes (default [5, 15])
        aggregate_window_minutes: aggregation window for min/max/avg price

    Returns:
        inserted_count: number of metrics inserted
    """
    symbols = symbols or ["btc", "eth"]
    inserted_count = 0

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    metric_time = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    aggregate_window_start = metric_time - timedelta(minutes=aggregate_window_minutes)

    insert_query = """
        INSERT INTO crypto_metrics (
            metric_time, symbol, price_usd, price_change_5m, price_change_15m,
            volume_24h_usd, avg_price_1h, min_price_1h, max_price_1h
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    try:
        for symbol in symbols:
            # 1️⃣ Idempotency check: skip if already inserted
            cursor.execute("""
                SELECT COUNT(*) AS count
                FROM crypto_metrics
                WHERE metric_time = %s AND symbol = %s
            """, (metric_time, symbol))
            if cursor.fetchone()["count"] > 0:
                logger.info(f"Metrics already computed for {symbol} at {metric_time}, skipping.")
                continue

            # 2️⃣ Fetch raw data from last aggregate window
            cursor.execute("""
                SELECT observed_at, price_usd, volume_24h_usd
                FROM raw_crypto_market_data
                WHERE symbol = %s AND observed_at >= %s
                ORDER BY observed_at DESC
            """, (symbol, aggregate_window_start))
            rows = cursor.fetchall()

            if not rows:
                logger.warning(f"No raw data for {symbol} in the last {aggregate_window_minutes} minutes.")
                continue

            # 3️⃣ Make timestamps UTC aware if not
            for row in rows:
                if row["observed_at"].tzinfo is None:
                    row["observed_at"] = row["observed_at"].replace(tzinfo=timezone.utc)

            # 4️⃣ Extract latest price and volume
            price_now = rows[0]["price_usd"]
            volume_24h_usd = rows[0]["volume_24h_usd"]

            # 5️⃣ Compute price deltas for each window
            deltas = {}
            for delta_min in price_delta_windows:
                cutoff_time = metric_time - timedelta(minutes=delta_min)
                price_before = next((r["price_usd"] for r in rows if r["observed_at"] <= cutoff_time), price_now)
                deltas[f"price_change_{delta_min}m"] = clamp(price_now - price_before, -1e6, 1e6)

            # 6️⃣ Compute aggregates over the window
            prices = [r["price_usd"] for r in rows]
            avg_price = sum(prices)/len(prices)
            min_price = min(prices)
            max_price = max(prices)

            # 7️⃣ Insert metrics into crypto_metrics
            cursor.execute(insert_query, (
                metric_time,
                symbol,
                price_now,
                deltas.get("price_change_5m"),
                deltas.get("price_change_15m"),
                volume_24h_usd,
                avg_price,
                min_price,
                max_price
            ))

            inserted_count += 1
            logger.info(f"Metrics computed and stored for {symbol} at {metric_time}")

        conn.commit()
        logger.info(f"All metrics committed successfully. Total inserted: {inserted_count}")

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error("Error computing metrics. Transaction rolled back.", exc_info=True)
        raise
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
        logger.info("Database connection closed.")

    return inserted_count

# ---------------------------------------------------------
# 6️⃣ ENTRY POINT FOR MANUAL RUN
# ---------------------------------------------------------
if __name__ == "__main__":
    inserted = run_compute_metrics()
    logger.info(f"Manual run complete. {inserted} metrics inserted.")