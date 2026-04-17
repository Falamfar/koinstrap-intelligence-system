import os
import sys
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv

LOG_PATH = "/home/falamfar/koinstrap_platform/projects/koinstrap/logs/api.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, mode="a"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

load_dotenv("/home/falamfar/koinstrap_platform/projects/koinstrap/config/.env")
app = FastAPI(title = "Koinstrap Ai Insight API")

def get_db_connection():
    conn = psycopg2.connect(
        dbname=os.getenv("PG_NAME"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
        host=os.getenv("PG_HOST"),
        port=os.getenv("PG_PORT")
    )
    return conn 
    
# ---  API ENDPOINTS ---    
@app.get("/")
def home():
    """Health check endpoint."""
    logger.info("Root endpoint accessed")
    return {
        "status": "online",
        "message": "Koinstrap AI insight API is active. Use /API/insight/{symbol} for data."
    }

@app.get("/api/insight/{symbol}")
def get_james_insight(symbol: str):
    """
    Fetches the latest AI-generated insight for a specific cryptocurrency.
    This is the primary endpoint for the mobile app developer.
    """
    symbol = symbol.upper()
    logger.info(f"incoming request for symbol: {symbol}")
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Query retrieves only the most recent entry for the given asset
        query = """
            SELECT symbol, prediction_label, confidence_score, james_narrative, created_at
            FROM signals_live
            WHERE symbol = %s
            ORDER BY created_at DESC
            LIMIT 1
        """
        cur.execute(query, (symbol,))
        result = cur.fetchone()

        cur.close()
        conn.close()

        if not result:
            logger.warning(f"No insight found for symbol: {symbol}")
            raise HTTPException(status_code=404, detail=f"No insight found for symbol: {symbol}")

        logger.info(f"Insight retrieved successfully for symbol: {symbol}")
        return {
            "status": "success",
            "data": result,
            "legal_notice": "AI analysis is for informational purposes only. Not financial advice."
        }

    except Exception as e:
        logger.error(f"Error occurred while fetching insight for symbol: {symbol}. Error: {e}")
        return {
            "status": "error",
            "message": "Internal Server Error"
        }



