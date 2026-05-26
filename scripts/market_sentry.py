import os
import sys
import logging
import requests
import psycopg2 
from psycopg2.extras import RealDictCursor
from statistics import mean
from dotenv import load_dotenv 

# ==========================================
# STEP 1: PREPARING THE SENTRY'S TOOLS
# ==========================================

# Tell the script where to write down its "Diary" (Logs)
LOG_PATH = "/home/falamfar/koinstrap_platform/projects/koinstrap/logs/sentry.log"

# Open the "Safe" to get our secret keys (Database passwords and Discord link)
load_dotenv("/home/falamfar/koinstrap_platform/projects/koinstrap/config/.env")

# Set up the Diary so we can see what happened even if we weren't watching
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# ==========================================
# STEP 2: SETTING THE "ALARM" RULES
# ==========================================

PRICE_THRESHOLD = 3.0 # Alert if price moves 3% or more
VOLUME_THRESHOLD = 150.0 # Alert if volume jumps 150% (people are buying/selling like crazy)
SMA_PERIOD = 20 # Look at the last 20 check-ins to find the "Average" price
DISCORD_URL = os.getenv("DISCORD_ALERTS_URL") # Our megaphone link

# ==========================================
# STEP 3: THE MEGAPHONE FUNCTION
# ==========================================
def send_alert(message, symbol, anomaly_type, magnitude, current_val, previous_val):
    """This function picks up the megaphone and shouts."""
    # A. SHOUT ON DISCORD
    try:
        requests.post(DISCORD_URL, json={"content":message}, timeout=10) 
        logger.info(f"ALARM TRIPPED: {symbol} {anomaly_type}") 
    except Exception as e:
        logger.error(f"Failed to send alert: {e}")

    # B. WRITE IT DOWN IN THE HISTORY BOOK (Database)
    try: 
        conn = psycopg2.connect(
            dbname = os.getenv("PG_NAME"),
            user = os.getenv("PG_USER"),
            password = os.getenv("PG_PASSWORD"),
            host = os.getenv("PG_HOST"),
            port = os.getenv("PG_PORT")
        )
        cur = conn.cursor() 
        query = """
            INSERT INTO market_anomalies (symbol, anomaly_type, magnitude, current_value, previous_value)
            VALUES (%s, %s, %s, %s, %s)
        """
        cur.execute(query, (symbol, anomaly_type, magnitude, current_val, previous_val))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to write alert to database: {e}")

# ==========================================
# STEP 4: THE BRAIN (CHECKING THE DATA)
# ==========================================

def analyze_market_data():
    """This is the Sentry walking into the vault to look at the prices."""
    try:
        # Open the door to the Database bank
        conn = psycopg2.connect(
            dbname=os.getenv("PG_NAME"),
            user=os.getenv("PG_USER"),
            password=os.getenv("PG_PASSWORD"),
            host=os.getenv("PG_HOST"),
            port=os.getenv("PG_PORT")
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # We want to check BTC and ETH
        for symbol in ["BTC", "ETH"]:
            # Ask the database: "Give me the last 20 times you checked the price"
            cur.execute("""
                SELECT price_usd, volume_24h_usd FROM ml_features
                WHERE symbol =%s ORDER BY created_at DESC LIMIT %s 
            """, (symbol, SMA_PERIOD))  
            rows = cur.fetchall() 

            # If the bank just opened and we don't have 20 records yet, wait.
            if len(rows) < SMA_PERIOD:
                logger.warning(f"Waiting for more data for {symbol}...")
                continue 

            # Organize the data: [Current Price, Last Price, 3rd Last Price...]
            prices = [float(r['price_usd']) for r in rows]
            volumes = [float(r['volume_24h_usd']) for r in rows]

            # Grab the 'Now' price and the '5-minutes-ago' price
            curr_price = prices[0]
            prev_price = prices[1]
            curr_vol = volumes[0]
            prev_vol = volumes[1] 

            # Find the "Normal" price (The average of the last 20 checks)
            current_sma = mean(prices)

            # --- MATH CHECK 1: DID THE PRICE JUMP? ---
            # (New - Old) / Old = Percentage change

            price_change = ((curr_price - prev_price) / prev_price) * 100 

            if abs(price_change) >= PRICE_THRESHOLD:
                msg =  f" **PRICE SPIKE** | {symbol}\n It has moved {price_change: .2f}% "
                send_alert(msg, symbol, "Volatility", price_change, curr_price, prev_price) 

            # --- MATH CHECK 2: DID VOLUME GO CRAZY? ---  
            vol_change = ((curr_vol - prev_vol) / prev_vol) * 100 
            if abs(vol_change) >= VOLUME_THRESHOLD:
                msg =  f" **VOLUME SPIKE** | {symbol}\n More people are trading!"
                send_alert(msg, symbol, "Volume", vol_change, curr_vol, prev_vol) 

            # --- MATH CHECK 3: TREND REVERSAL (The Cross) ---
            # If it was BELOW average last time, but NOW it is ABOVE average...
            if prev_price < current_sma and curr_price > current_sma:
                msg =  f" **TREND REVERSAL**: UPWARDS | {symbol}\n price just crossed above average!"
                send_alert(msg, symbol, "Bullish Reversal", 0, curr_price, current_sma) 

            # If it was ABOVE average last time, but NOW it is BELOW average...
            elif prev_price > current_sma and curr_price < current_sma:
                msg = f" **TREND REVERSAL**: DOWNWARDS | {symbol}\n price just crossed below average!"
                send_alert(msg, symbol, "Bearish Reversal", 0, curr_price, current_sma)
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to analyze market data: {e}")

# ==========================================
# STEP 5: WAKE UP THE SENTRY
# ==========================================

if __name__ == "__main__":
    logger.info("Market Sentry is waking up and checking the vault...")
    analyze_market_data()
