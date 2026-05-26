"""
ingest_coingecko_dag.py
-----------------------
DAG-friendly, production-ready ingestion module for CoinGecko market data.

Features:
- Encapsulated function for Airflow `python_callable`
- Parameterized symbols & vs_currency
- Idempotent insertion into raw_crypto_market_data
- Full logging and error handling
- Returns number of records processed (for monitoring)
"""

import os
import logging
import requests
import psycopg2 
import sys
from psycopg2 import Error 
from datetime import datetime, timezone
from dotenv import load_dotenv
from typing import List, Dict

#setup logging

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
# 1️⃣ ENVIRONMENT CONFIGURATION
# ---------------------------------------------------------
ENV_PATH = "/app/config/.env"  

load_dotenv(ENV_PATH)

COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")
DB_HOST = os.getenv("PG_HOST")
DB_USER = os.getenv("PG_USER")
DB_PASSWORD = os.getenv("PG_PASSWORD")
DB_NAME = os.getenv("PG_NAME") 
DB_PORT = os.getenv("PG_PORT")



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
            database=DB_NAME
        )
        logger.info("Database connection established.")
        return conn
    except Error as e:
        logger.error("Database connection failed.", exc_info=True)
        raise

# ---------------------------------------------------------
# 4️⃣ VALIDATION
# ---------------------------------------------------------
def is_valid_record(coin: Dict) -> bool:
    """Ensure required fields exist and numeric values are valid."""
    if not coin.get("symbol") or not coin.get("name"):
        return False
    if coin.get("current_price") is None or coin.get("current_price") < 0:
        return False
    if coin.get("total_volume") is None or coin.get("total_volume") < 0:
        return False
    return True

# ---------------------------------------------------------
# 5️⃣ API FETCH WITH RETRIES
# ---------------------------------------------------------
def fetch_market_data(symbols: List[str], vs_currency: str = "usd", max_retries: int = 3) -> List[Dict]:
    """Fetch market data from CoinGecko with retry logic."""
    url = "https://api.coingecko.com/api/v3/coins/markets"
    headers = {
        "Accept": "application/json",
        "x-cg-demo-api-key": COINGECKO_API_KEY
    }
    params = {"vs_currency": vs_currency, "ids": ",".join(symbols)}

    attempt = 0
    while attempt < max_retries:
        try:
            logger.info(f"Fetching market data (attempt {attempt + 1}) for {symbols}")
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            logger.warning(f"API returned status code {response.status_code}")
        except Exception as e:
            logger.error("API request failed.", exc_info=True)
        attempt += 1

    raise Exception("Max retries reached. CoinGecko fetch failed.")

# ---------------------------------------------------------
# 6️⃣ INGESTION FUNCTION (DAG-FRIENDLY)
# ---------------------------------------------------------
def run_ingest(symbols: List[str] = None, vs_currency: str = "usd") -> int:
    """
    Fetch market data and insert into raw_crypto_market_data.

    Returns:
        inserted (int): number of records processed
    """
    symbols = symbols or ["bitcoin", "ethereum"]
    inserted = 0

    data = fetch_market_data(symbols, vs_currency)
    if not data:
        logger.warning("No data returned from CoinGecko.")
        return inserted

    conn = get_db_connection()
    cursor = conn.cursor()
    observed_at = datetime.now(timezone.utc).replace(second=0, microsecond=0)

    insert_query = """
        INSERT INTO raw_crypto_market_data
        (symbol, name, price_usd, volume_24h_usd, observed_at)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (symbol, observed_at)
        DO UPDATE SET
        price_usd = EXCLUDED.price_usd,
        volume_24h_usd = EXCLUDED.volume_24h_usd
    """

    try:
        for coin in data:
            if not is_valid_record(coin):
                logger.warning(f"Invalid record skipped: {coin}")
                continue
            record = (
                coin["symbol"],
                coin["name"],
                coin["current_price"],
                coin["total_volume"],
                observed_at
            )
            cursor.execute(insert_query, record)
            inserted += 1

        conn.commit()
        logger.info(f"Ingestion successful. {inserted} records processed.")

    except Exception as e:
        conn.rollback()
        logger.error("Ingestion failed. Transaction rolled back.", exc_info=True)
        raise
    finally:
        cursor.close()
        conn.close()
        logger.info("Database connection closed.")

    return inserted

# ---------------------------------------------------------
# 7️⃣ ENTRY POINT FOR MANUAL RUN
# ---------------------------------------------------------
if __name__ == "__main__":
    inserted_count = run_ingest()
    logger.info(f"Manual run complete. {inserted_count} records ingested.")