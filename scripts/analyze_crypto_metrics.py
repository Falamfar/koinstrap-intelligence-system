"""
analyze_crypto_metrics.py

Purpose:
- Reads the clean metrics from crypto_metrics table
- Computes actionable insights / alerts like price spikes, trend reversals, volume spikes
- Stores these insights in a separate table crypto_analysis
- This allows the dashboard to read **decision-ready data** instead of raw metrics
"""

# --------------------------------------------------
# 1️⃣ Import Libraries
# --------------------------------------------------
import os                    # To read environment variables (like DB credentials)
import logging               # To log info, warnings, and errors
import mysql.connector       # To connect and query MySQL database
from datetime import datetime, timezone  # For timestamps and timezone handling
from dotenv import load_dotenv           # To read .env file safely
from decimal import Decimal              # For precise decimal calculations (money)

# --------------------------------------------------
# 2️⃣ Load Environment Variables
# --------------------------------------------------
load_dotenv("/home/falamfar/projects/koinstrap/config/.env")
# .env file contains DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
# Keeps sensitive info out of your code

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# --------------------------------------------------
# 3️⃣ Logging Setup
# --------------------------------------------------
LOG_FILE = "/home/falamfar/projects/koinstrap/logs/analyze_metrics.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,                 # Log INFO, WARNING, ERROR
    format="%(asctime)s %(levelname)s:%(message)s"
)

logging.info("Starting analyze_crypto_metrics...")  # Let us know script started

# --------------------------------------------------
# 4️⃣ Database Connection Function
# --------------------------------------------------
def get_db_connection():
    """
    Returns a connection object to MySQL.
    We use this function every time we need to talk to the DB.
    """
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

# --------------------------------------------------
# 5️⃣ Main Analysis Function
# --------------------------------------------------
def analyze_metrics():
    """
    This is the main function that computes actionable insights.
    Steps:
    1. Connect to DB
    2. For each coin:
       a. Get latest metric
       b. Compute price spike, trend reversal, volume spike
       c. Compute simple trend signal and confidence score
    3. Insert insights into crypto_analysis table
    """

    conn = get_db_connection()   # Step 1: Connect to DB
    cursor = conn.cursor(dictionary=True)  # We want results as dictionary, not tuple

    # Step 2a: Timestamp for analysis
    analysis_time = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    # This is **when** we performed the analysis. Useful to track history.

    symbols = ["btc", "eth"]  # List of coins to analyze

    # --------------------------------------------------
    # 2b: SQL Insert Template
    # --------------------------------------------------
    insert_query = """
        INSERT INTO crypto_analysis (
            analysis_time,
            symbol,
            metric_time_ref,
            is_price_spike,
            is_trend_reversal,
            is_volume_spike,
            trend_signal,
            confidence_score,
            notes
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            is_price_spike=VALUES(is_price_spike),
            is_trend_reversal=VALUES(is_trend_reversal),
            is_volume_spike=VALUES(is_volume_spike),
            trend_signal=VALUES(trend_signal),
            confidence_score=VALUES(confidence_score),
            notes=VALUES(notes)
    """
    """
    Baby Explanation:
    - %s are placeholders for Python variables
    - ON DUPLICATE KEY UPDATE ensures we don't insert duplicates for same coin/time
    """

    try:
        # Step 3: Loop through all coins
        for symbol in symbols:

            # Step 3a: Fetch the latest metric row for this coin
            cursor.execute("""
                SELECT *
                FROM crypto_metrics
                WHERE symbol = %s
                ORDER BY metric_time DESC
                LIMIT 1
            """, (symbol,))

            row = cursor.fetchone()  # Get the first/latest row
            if not row:
                logging.warning(f"No metrics found for {symbol}")
                continue  # Skip this coin if no data

            # Step 3b: Compute Signals / Insights

            # 1️⃣ Price Spike: absolute 5-min price change >= 0.5% of current price
            is_price_spike = abs(row['price_change_5m'] / row['price_usd']) >= Decimal('0.005')

            # 2️⃣ Trend Reversal: 5m move opposite to 15m move
            is_trend_reversal = (row['price_change_5m'] > 0 and row['price_change_15m'] < 0) \
                                or (row['price_change_5m'] < 0 and row['price_change_15m'] > 0)

            # 3️⃣ Volume Spike: current volume > 1.5x avg volume
            # For now, using volume_24h_usd as reference if avg_volume not in metrics
            avg_volume_1h = row['volume_24h_usd']
            is_volume_spike = row['volume_24h_usd'] > Decimal(avg_volume_1h) * Decimal('1.5')

            # 4️⃣ Trend Signal: simple heuristic
            if row['price_change_5m'] > 0:
                trend_signal = "Bullish"
            elif row['price_change_5m'] < 0:
                trend_signal = "Bearish"
            else:
                trend_signal = "Neutral"

            # 5️⃣ Confidence Score: absolute 5-min % change
            confidence_score = float(abs(row['price_change_5m'] / row['price_usd']) * 100)

            # Notes: optional short info for humans or dashboard
            notes = "Derived from last metrics"

            # Step 3c: Insert insights into crypto_analysis table
            cursor.execute(insert_query, (
                analysis_time,
                symbol,
                row['metric_time'],  # Reference metric timestamp
                is_price_spike,
                is_trend_reversal,
                is_volume_spike,
                trend_signal,
                confidence_score,
                notes
            ))

            logging.info(f"Analysis stored for {symbol} at {analysis_time}")

        # Step 4: Commit all inserts
        conn.commit()

    except Exception as e:
        conn.rollback()  # If error, undo all changes
        logging.exception(f"Error in analyze_metrics: {e}")

    finally:
        cursor.close()
        conn.close()  # Always close DB connection to avoid leaks

# --------------------------------------------------
# 6️⃣ Entry Point
# --------------------------------------------------
if __name__ == "__main__":
    analyze_metrics()



    
