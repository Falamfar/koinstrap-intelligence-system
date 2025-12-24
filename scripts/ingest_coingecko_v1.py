import os
import logging 
import requests
import mysql.connector
from datetime import datetime, timezone
from dotenv import load_dotenv

#load environment variables from .env file

load_dotenv(dotenv_path="config/.env")
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

#logging configuration

LOG_FILE = "logs/ingest_coingecko_v1.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s"
)


#coingecko configuration

COINS = ["bitcoin", "ethereum"] 
VS_CURRENCY = "usd" 
COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets" 

HEADERS = {
    "Accept": "application/json",
    "x-cg-demo-api-key": COINGECKO_API_KEY
}

PARAMS = {
    "vs_currency": VS_CURRENCY,
    "ids": ",".join(COINS)
}

#database connection
def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

#ingestion logic
def ingest_market_data():
    logging.info("fetching market data from CoinGecko...")

    response = requests.get(
        COINGECKO_URL,
        headers=HEADERS,
        params=PARAMS,
        timeout=10
    )

    if response.status_code != 200:
        logging.error(f"CoinGecko API error: {response.status_code}")
        raise Exception(f"CoinGecko API error: {response.status_code}")

    data = response.json()
    if not data:
        logging.warning("No data received from CoinGecko API")
        return


    conn = get_db_connection()        
    cursor = conn.cursor()

    insert_query = """
        INSERT INTO raw_crypto_market_data 
        (symbol, name, price_usd, volume_24h_usd, observed_at)
        VALUES (%s, %s, %s, %s, %s)
    """

    now = datetime.now(timezone.utc)

    for coin in data:
        record = (
            coin.get("symbol"),
            coin.get("name"),
            coin.get("current_price"),
            coin.get("total_volume"),
            now
        )

        cursor.execute(insert_query, record)

    conn.commit()
    cursor.close()
    conn.close()
    logging.info(f"successfully ingested {len(data)} records at {now}")
   

#Entry point    
if __name__ == "__main__":
    try:
        ingest_market_data()
        logging.info("ingestion completed successfully.")
    except Exception as e:
        logging.exception(f"ingestion failed: {e}")



        