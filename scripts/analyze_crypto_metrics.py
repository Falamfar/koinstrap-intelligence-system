"""
analyze_crypto_metrics.py

This script reads the metrics from crypto_metrics table
and computes actionable insights like short-term price changes,
volatility, and signals.
"""

import os
import logging
import mysql.connector
from datetime import datetime, timezone
from dotenv import load_dotenv 

# --------------------------------------------------
# ENVIRONMENT SETUP
# --------------------------------------------------

load_dotenv("/home/falamfar/projects/koinstrap/config/.env")

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# --------------------------------------------------
# LOGGING SETUP
# --------------------------------------------------

LOG_FILE =  "/home/falamfar/projects/koinstrap/logs/analyze_metrics.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
)

logging.info("starting crypto metrics analysis")

def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

# --------------------------------------------------
# ANALYTICS FUNCTION
# --------------------------------------------------    

def analyze_metrics():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    now = datetime.now(timezone.utc)

    symbols = ["btc", "eth"] 

    try:
        for symbol in symbols:
            #  Read latest metrics from SQL
            cursor.execute(
                """
                SELECT *
                FROM crypto_metrics
                WHERE symbol = %s
                ORDER BY metric_time DESC
                LIMIT 10
                """,
                (symbol,)
            )

            rows = cursor.fetchall()

            if not rows:
                logging.warning(f"No metrics found for {symbol}")
                continue

            #  Extract values into Python lists for calculation    

            prices = [row['price_usd'] for row in rows]
            volumes = [row['volume_24h_usd'] for row in rows]
            metric_times = [row['metric_time'] for row in rows] 

            price_now = prices[0]
            volume_now = volumes[0]

            #  Compute simple short-term trend
            # Difference between latest price and oldest in this batch

            price_change = price_now - prices[-1] if len(prices) > 1 else 0

            # Compute volatility (simple example: max-min over last 10 points)
            price_volatility = max(prices) - min(prices) 

            # Compute percentage change for alerting
            price_pct_change = (price_change / prices[-1]) * 100 if prices[-1]  else 0 

            # log insights

            logging.info(
                f"{symbol.upper()} | Current price: ${price_now: .2f} |"
                f"price change: ${price_change: .2f} |"
                f"percentage change : ${price_pct_change: .2f} | "
                f"votality (last 10 points) : ${price_volatility: .2f} |"
                f"volume : ${volume_now : .2f}"

            )



    except Exception as e:
        logging.exception(f" metrics analysis failed: {e}")

    finally:
        cursor.close()
        conn.close()



# --------------------------------------------------
# ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":
    analyze_metrics()
