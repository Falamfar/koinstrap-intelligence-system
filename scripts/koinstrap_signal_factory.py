import os
import sys
import psycopg2
import logging
import joblib
import pandas as pd 
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn") 
warnings.filterwarnings("ignore", message=".*pandas only supports SQLAlchemy connectable.*")
from psycopg2.extras import RealDictCursor
from groq import Groq
from dotenv import load_dotenv
from sqlalchemy import create_engine

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

import pathlib
BASE_DIR = str(pathlib.Path(__file__).resolve().parent.parent)

ENV_PATH = "/app/config/.env"
load_dotenv(ENV_PATH)

def get_latest_features():
    """Fetch the absolute latest pre-joined features for all symbols."""
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("PG_NAME"),
            user=os.getenv("PG_USER"),
            password=os.getenv("PG_PASSWORD"),
            host=os.getenv("PG_HOST"),
            port=os.getenv("PG_PORT")
        )
        query = """
        SELECT DISTINCT ON (symbol)
            symbol, price_usd, avg_sentiment, price_change_5m, 
            price_change_15m, volume_24h_usd, post_count, confidence_score
        FROM ml_features
        ORDER BY symbol, feature_time DESC;
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df.fillna(0)
    except Exception as e:
        logger.error(f"DB Error: {e}")
        return None
      

       

def generate_signals(row):
    """The core engine: Predict first, then explain."""
    try:
        # 1. THE BRAIN (Prediction)
        model_path = os.path.join(BASE_DIR, "scripts", "koinstrap_brain.pkl")
        brain = joblib.load(model_path)

        feature_cols = ['price_change_5m', 'price_change_15m', 'volume_24h_usd', 'post_count', 'avg_sentiment','confidence_score'] 
        input_data = pd.DataFrame([row[feature_cols]])

        prob_up = brain.predict_proba(input_data)[0][1]
        direction = "BULLISH" if prob_up > 0.5 else "BEARISH"

        # 2. THE VOICE (LLM Insight)
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        social_context = f"{row['avg_sentiment']} sentiment from {row['post_count']} posts" if row['post_count'] > 0 else "No recent social data available"


        prompt = f"""
        ASSET: {row['symbol'].upper()}
        PRICE: ${row['price_usd']}
        PREDICTION: {direction} ({prob_up:.2%} probability of price increase in the next hour)
        METRICS: 5m momentum: {row['price_change_5m']}%, 15m trend: {row['price_change_15m']}%
        SOCIAL: {social_context} 

        TASK: As James (Koinstrap's AI), provide a concise 2-sentence alert for a customer. 
        Focus on explaining WHY the prediction probability is what it is based on the metrics.
        """
        chat = client.chat.completions.create(
            messages = [{"role":"system", "content": "You are James, the highly intelligent Koinstrap AI Advisor."},
                        {"role":"user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.4 
        )

        return {
            "symbol": row['symbol'].upper(),
            "prediction": direction,
            "certainty": f"{prob_up:.2%}",
            "insight": chat.choices[0].message.content
        } 

    except Exception as e:
        logger.error(f"signal generation error for {row['symbol']}: {e}")
        return None

def save_signal_to_live_db(signal):
    """Save the generated signal to the signals_live table."""
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("PG_NAME"),
            user=os.getenv("PG_USER"),
            password=os.getenv("PG_PASSWORD"),
            host=os.getenv("PG_HOST"),
            port=os.getenv("PG_PORT")
        )
        cur = conn.cursor()

        clean_confidence = float(signal['certainty'].strip('%')) / 100.0
        query = """
        INSERT INTO signals_live (symbol, prediction_label, confidence_score, james_narrative)
        VALUES (%s, %s, %s, %s);
        """
        cur.execute(query, (
            signal['symbol'],
            signal['prediction'],
            clean_confidence,
            signal['insight']
        ))
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"✅ Successfully pushed {signal['symbol']} signal to Live UI table.")
    except Exception as e:
        logger.error(f"Error saving signal to live DB for {signal['symbol']}: {e}")


if __name__ == "__main__":
    logger.info("james is genarating the master signals...")
    data = get_latest_features() 

    # CRITICAL SECURITY CHECK: If database fails or returns no features, KILL THE PIPELINE
    if data is None or data.empty:
        logger.error("❌ CRITICAL FAILURE: No feature data could be retrieved from ml_features table!")
        # Raising an unhandled exception forces Python to exit with code 1, turning Airflow RED
        raise ValueError("Pipeline halted: Missing critical market features data.")

    # If data exists, proceed normally
    for _, row in data.iterrows():
        signal = generate_signals(row)  
        if signal:
            logger.info(f"----FINAL SIGNAL: {signal['symbol']}----")
            logger.info(f"Prediction: {signal['prediction']} with {signal['certainty']} certainty")
            logger.info(f"james says: {signal['insight']}") 
            save_signal_to_live_db(signal)
               

