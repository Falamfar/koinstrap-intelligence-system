"""
compute_metrics.py

Computes decision metrics from raw_crypto_market_data
and stores them in crypto_metrics.
"""

import os
import logging
import mysql.connector
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# --------------------------------------------------
# ENVIRONMENT SETUP
# --------------------------------------------------

# Load environment variables from our .env file
# This includes DB credentials like host, user, password, and database name

load_dotenv(dotenv_path="config/.env")

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# --------------------------------------------------
# LOGGING SETUP
# --------------------------------------------------

# File where all logs will be written
LOG_FILE = "logs/compute_metrics.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    
)

logging.info("starting metrics computation script....")

# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------

# Function to connect to mysql.
def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

# --------------------------------------------------
# METRICS COMPUTATION
# --------------------------------------------------

def compute_metrics():
    """
    Main function to compute crypto metrics:
    - Reads raw_crypto_market_data from MySQL
    - Computes price changes and aggregates
    - Writes results into crypto_metrics table
    """
    # Connect to database
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Create a timestamp for this metrics computation
    # Rounded to nearest minute
    metric_time = datetime.now(timezone.utc).replace(second=0, microsecond=0)

    # Define reference times for calculating price changes
    five_min_ago = metric_time - timedelta(minutes=5)
    fifteen_min_ago = metric_time - timedelta(minutes=15)
    one_hour_ago = metric_time - timedelta(hours=1)

    # List of coins we want to compute metrics for
    symbols = ['btc', 'eth']

    # SQL query template for inserting metrics
    # Placeholders %s will be filled by Python variables
    insert_query = """
        INSERT INTO crypto_metrics (
            metric_time,
            price_usd,
            price_change_5m,
            price_change_15m,
            volume_24h_usd,
            avg_price_1h,
            min_price_1h,
            max_price_1h
        ) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """


    try:
         # Loop through each symbol (coin)
        for symbol in symbols:
            # Fetch all raw data for this coin in the last 1 hour 
            cursor.execute("""
        
                SELECT observed_at, price_usd, volume_24h_usd
                FROM raw_crypto_market_data
                WHERE symbol = %s 
                AND observed_at >= %s
                ORDER BY observed_at DESC
            """,
            (symbol, one_hour_ago)
            ) 

            # Fetch all rows returned by SQL
            # Each row is a dictionary because of dictionary=True 
            rows = cursor.fetchall()

            # If no data, skip and log
            if not rows:
                logging.warning(f"No data found for {symbol} in the last hour.")

                continue

            # Make DB timestamps UTC-aware to avoid naive/aware conflict
            for row in rows:
                if row['observed_at'].tzinfo is None:
                    row['observed_at'] = row['observed_at'].replace(tzinfo=timezone.utc)    

            # Extract a list of all prices for easier calculation
            prices = [row['price_usd'] for row in rows]

            
            # Latest price and volume = first row (DESC order = newest first)
            price_now = prices[0]
            volume_24h_usd = rows[0]['volume_24h_usd']
            
            # Initialize variables for past prices
            price_5m = None
            price_15m = None
            
            # Loop through historical rows to find 5min and 15min old prices
            for row in rows:
                if row['observed_at'] <= five_min_ago and price_5m is None:
                    price_5m = row['price_usd']
                if row['observed_at'] <= fifteen_min_ago:
                    price_15m = row['price_usd']
                    break  # No need to continue once we have both prices    



            # Compute price changes (current - past) 
            price_change_5m = price_now - price_5m if price_5m else None       
            price_change_15m = price_now - price_15m if price_15m else None

            
            # Compute 1-hour aggregates
            avg_price_1h = sum(prices) / len(prices) 
            min_price_1h = min(prices)
            max_price_1h = max(prices)

            # Insert metrics into crypto_metrics table
            cursor.execute(
                insert_query,
                (
                    metric_time,
                    price_now,
                    price_change_5m,
                    price_change_15m,
                    volume_24h_usd,
                    avg_price_1h,
                    min_price_1h,
                    max_price_1h
                )
            )

            # Log success for this coin
            logging.info(f"Metrics computed and stored for {symbol} at {metric_time}.")
        
        # Commit all changes to SQL
        conn.commit()

    except Exception as e:
        # Rollback changes if anything goes wrong  
        conn.rollback()
        logging.error(f"Error computing metrics: {e}")  


    finally:
        # Always close cursor and connection (cleanup)
        cursor.close()
        conn.close()  

# --------------------------------------------------
# ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":
    compute_metrics()









