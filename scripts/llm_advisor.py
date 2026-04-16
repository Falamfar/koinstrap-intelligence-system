import os
import sys
import psycopg2
import logging
from psycopg2.extras import RealDictCursor
from groq import Groq
from dotenv import load_dotenv

# Setup logging
log_format = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

file_handler = logging.FileHandler("/home/falamfar/koinstrap_platform/projects/koinstrap/logs/koinstrap_ai.log", mode="a")
file_handler.setFormatter(log_format) 

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_format)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

load_dotenv("/home/falamfar/koinstrap_platform/projects/koinstrap/config/.env")

def get_market_context(symbol):
    conn = None 
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("PG_NAME"),
            user=os.getenv("PG_USER"),
            password=os.getenv("PG_PASSWORD"),
            host=os.getenv("PG_HOST"),
            port=os.getenv("PG_PORT") 
        ) 
        logging.info(f"Connected to Postgres. Fetching {symbol} features...")

        # Updated Query: Includes post_count to help AI distinguish between 'Neutral' and 'No Data'
        query = """
        SELECT 
            symbol,
            price_usd AS current_price,
            avg_sentiment AS sentiment,
            price_change_5m AS mom_5m,
            price_change_15m AS trend_15m,
            post_count
        FROM ml_features 
        WHERE symbol = %s 
          AND price_change_5m IS NOT NULL
        ORDER BY feature_time DESC 
        LIMIT 1;
        """

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (symbol,))
            data = cur.fetchone()
            if not data:
                logging.warning(f"No data found for symbol: {symbol}")
                return None
            
            return data

    except Exception as e:
        logging.error(f"DATABASE ERROR: {str(e)}") 
        return None

    finally:
        if conn:
            conn.close() 

def generate_recommendation(data):
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        # Logic to handle cases where sentiment is 0 because of 0 posts
        if data['post_count'] > 0:
            social_info = f"Hourly Sentiment: {data['sentiment']} (based on {data['post_count']} posts)"
        else:
            social_info = "Hourly Sentiment: No recent social activity/posts found."

        prompt = f"""
        ASSET : {data['symbol'].upper()}
        CURRENT_PRICE : ${data['current_price']}
        {social_info}
        5m Momentum : {data['mom_5m']}%
        15m Trend : {data['trend_15m']}% 
        Task : provide a two sentence market insight for a trader. 
        If sentiment is missing, focus strictly on the price momentum and trend.
        """

        logging.info(f"Requesting AI insight from Groq for {data['symbol'].upper()}")

        chat_completion = client.chat.completions.create(
            messages = [
                {"role": "system", "content": "You are a senior crypto technical analyst."},
                {"role": "user", "content": prompt} 
            ],
            model ="llama-3.3-70b-versatile",
            temperature=0.5
        ) 

        return chat_completion.choices[0].message.content

    except Exception as e:
        logging.error(f"AI API ERROR: {str(e)}") 
        return "Insight generation failed"

if __name__ == "__main__":
    logging.info("Starting Koinstrap Advisor pipeline...")

    for coin in ["btc", "eth"]:
        market_data = get_market_context(coin) 

        if market_data: 
            insight = generate_recommendation(market_data) 
            logging.info(f"AI Insight for {coin.upper()}: {insight}")
        else:
            logging.error(f"Failed to retrieve market data for {coin.upper()}")