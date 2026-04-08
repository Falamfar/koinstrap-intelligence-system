"""
analyze_crypto_metrics.py
-----------------------------
DAG-friendly script to analyze crypto metrics and generate actionable signals.

Features:
- Reads latest metrics from crypto_metrics
- Computes price spike, trend reversal, and volume spike
- Generates trend signals (Bullish/Bearish/Neutral)
- Inserts into crypto_analysis table with idempotency
- Parameterized for symbols, thresholds, and logging
- Returns count of analysis rows inserted
"""

import os
import logging
import psycopg2
from psycopg2 import Error
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone
from decimal import Decimal
from dotenv import load_dotenv
from typing import List, Dict

# ---------------------------------------------------------
# 1️⃣ ENVIRONMENT CONFIGURATION
# ---------------------------------------------------------
load_dotenv("/home/falamfar/koinstrap_platform/projects/koinstrap/config/.env")

DB_HOST = os.getenv("PG_HOST")
DB_USER = os.getenv("PG_USER")
DB_PASSWORD = os.getenv("PG_PASSWORD")
DB_NAME = os.getenv("PG_NAME") 
DB_PORT = os.getenv("PG_PORT") 

# ---------------------------------------------------------
# 2️⃣ LOGGER CONFIGURATION
# ---------------------------------------------------------
logger = logging.getLogger("analyze_crypto_metrics")
logger.setLevel(logging.INFO)
if not logger.handlers:
    file_handler = logging.FileHandler("/home/falamfar/koinstrap_platform/projects/koinstrap/logs/analyze_metrics.log")
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

# ---------------------------------------------------------
# 3️⃣ CONSTANTS & THRESHOLDS
# ---------------------------------------------------------
PRICE_SPIKE_THRESHOLD = Decimal("0.005")  # 0.5% price move triggers spike
VOLUME_SPIKE_MULTIPLIER = Decimal("1.5")  # 50% increase in volume triggers spike

# ---------------------------------------------------------
# 4️⃣ DATABASE CONNECTION
# ---------------------------------------------------------
def get_db_connection():
    """Return a PostgreSQL database connection."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port = DB_PORT
        )
        logger.info("Database connection established.")
        return conn
    except Error as e:
        logger.error("Database connection failed.", exc_info=True)
        raise

# ---------------------------------------------------------
# 5️⃣ SIGNAL COMPUTATION HELPER
# ---------------------------------------------------------
def compute_signals(current_row: Dict, prev_row: Dict = None) -> Dict:
    """
    Compute trading signals based on current and previous metrics.

    Args:
        current_row: latest metric row from crypto_metrics
        prev_row: previous metric row for the same symbol (optional)

    Returns:
        dict with price spike, trend reversal, volume spike, trend signal
    """
    price_change_5m = current_row["price_change_5m"]
    price_change_15m = current_row["price_change_15m"]
    price_usd = current_row["price_usd"]
    volume = current_row["volume_24h_usd"]

    # Safety check
    if price_usd == 0:
        logger.warning(f"Price USD is zero for {current_row['symbol']}")
        return None

    # 1️⃣ Price spike
    pct_move = abs(price_change_5m / price_usd)
    is_price_spike = pct_move >= PRICE_SPIKE_THRESHOLD

    # 2️⃣ Trend reversal
    is_trend_reversal = (
        (price_change_5m > 0 and price_change_15m < 0) or
        (price_change_5m < 0 and price_change_15m > 0)
    )

    # 3️⃣ Volume spike (requires previous row)
    is_volume_spike = False
    if prev_row and prev_row.get("volume_24h_usd") and volume:
        if Decimal(volume) >= Decimal(prev_row["volume_24h_usd"]) * VOLUME_SPIKE_MULTIPLIER:
            is_volume_spike = True

    # 4️⃣ Trend signal
    if price_change_5m > 0:
        trend_signal = "Bullish"
    elif price_change_5m < 0:
        trend_signal = "Bearish"
    else:
        trend_signal = "Neutral"

    return {
        "is_price_spike": is_price_spike,
        "is_trend_reversal": is_trend_reversal,
        "is_volume_spike": is_volume_spike,
        "trend_signal": trend_signal
    }

# ---------------------------------------------------------
# 6️⃣ MAIN ANALYSIS FUNCTION (DAG-FRIENDLY)
# ---------------------------------------------------------
def run_analysis(symbols: List[str] = None) -> int:
    """
    Analyze latest metrics and insert signals into crypto_analysis.

    Args:
        symbols: list of coin symbols to analyze (default ["btc", "eth"])

    Returns:
        inserted_count: number of analysis rows inserted
    """
    symbols = symbols or ["btc", "eth"]
    inserted_count = 0

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    analysis_time = datetime.now(timezone.utc).replace(second=0, microsecond=0)

    insert_query = """
        INSERT INTO crypto_analysis (
            analysis_time, symbol, metric_time_ref, is_price_spike,
            is_trend_reversal, is_volume_spike, trend_signal, notes
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (analysis_time, symbol) 
        DO UPDATE SET
            is_price_spike=EXCLUDED.is_price_spike,
            is_trend_reversal=EXCLUDED.is_trend_reversal,
            is_volume_spike=EXCLUDED.is_volume_spike,
            trend_signal=EXCLUDED.trend_signal,
            notes=EXCLUDED.notes
    """

    try:
        for symbol in symbols:
            # 1️⃣ Fetch latest metric
            cursor.execute("""
                SELECT *
                FROM crypto_metrics
                WHERE symbol = %s
                ORDER BY metric_time DESC
                LIMIT 1
            """, (symbol,))
            current_row = cursor.fetchone()

            if not current_row:
                logger.warning(f"No metrics found for {symbol}")
                continue

            # 2️⃣ Fetch previous metric for volume spike comparison
            cursor.execute("""
                SELECT *
                FROM crypto_metrics
                WHERE symbol = %s AND metric_time < %s
                ORDER BY metric_time DESC
                LIMIT 1
            """, (symbol, current_row["metric_time"]))
            prev_row = cursor.fetchone()

            # 3️⃣ Compute signals
            signals = compute_signals(current_row, prev_row)
            if not signals:
                logger.warning(f"Signals could not be computed for {symbol}")
                continue

            # 4️⃣ Insert analysis
            notes = "Derived from latest metrics"
            cursor.execute(insert_query, (
                analysis_time,
                symbol,
                current_row["metric_time"],
                signals["is_price_spike"],
                signals["is_trend_reversal"],
                signals["is_volume_spike"],
                signals["trend_signal"],
                notes
            ))

            inserted_count += 1
            logger.info(f"Analysis stored for {symbol} at {analysis_time}")

        conn.commit()
        logger.info(f"All analysis committed successfully. Total inserted: {inserted_count}")

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error("Error analyzing metrics. Transaction rolled back.", exc_info=True)
        raise
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
        logger.info("Database connection closed.")

    return inserted_count

# ---------------------------------------------------------
# 7️⃣ ENTRY POINT FOR MANUAL RUN
# ---------------------------------------------------------
if __name__ == "__main__":
    inserted = run_analysis()
    logger.info(f"Manual run complete. {inserted} analysis rows inserted.")