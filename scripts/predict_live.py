import psycopg2
from psycopg2.extras import RealDictCursor
import os
import joblib
import pandas as pd 
from dotenv import load_dotenv
import logging

# 1. SETUP LOGGING
LOG_FILE = "/home/falamfar/koinstrap_platform/projects/koinstrap/logs/live_predictions.log"
logger = logging.getLogger("live_predictor")
logger.setLevel(logging.INFO)

if not logger.handlers:
    stream_handler = logging.StreamHandler() 
    file_handler = logging.FileHandler(LOG_FILE) 
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    stream_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter) 
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)

load_dotenv("/home/falamfar/koinstrap_platform/projects/koinstrap/config/.env")

def make_live_prediction():
    logger.info("🤖 Koinstrap Robot is checking the latest features from the Feature Store...")
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("PG_NAME"),
            user=os.getenv("PG_USER"),
            password=os.getenv("PG_PASSWORD"),
            host=os.getenv("PG_HOST"),
            port=os.getenv("PG_PORT") 
        ) 

        # SIMPLIFIED QUERY: Read directly from the source of truth
        query = """
        SELECT DISTINCT ON (symbol)
            symbol,
            price_change_5m,
            price_change_15m,
            volume_24h_usd,
            post_count,
            avg_sentiment,
            confidence_score
        FROM ml_features
        ORDER BY symbol, feature_time DESC;
        """

        # Using pandas to read the sql
        df = pd.read_sql(query, conn)
        df = df.fillna(0)

        if df.empty:
            logger.warning("⚠️ ml_features table is empty. Ensure the populate_features DAG is running!")
            return

        # Load the Brain
        model_path = "/home/falamfar/koinstrap_platform/projects/koinstrap/scripts/koinstrap_brain.pkl"
        brain = joblib.load(model_path)

        # The features MUST match exactly what the model was trained on
        features = ['price_change_5m', 'price_change_15m', 'volume_24h_usd', 'post_count', 'avg_sentiment', 'confidence_score']

        for _, row in df.iterrows():
            # Extract only the features needed for the model
            input_data = row[features].values.reshape(1, -1)
            
            # Probability of price going UP
            prob_array = brain.predict_proba(input_data)
            probability_up = prob_array[0][1]

            direction = "🚀 UP" if probability_up > 0.50 else "📉 DOWN"
            
            msg = f"Symbol: {row['symbol'].upper()} | Prediction: {direction} | Certainty: {probability_up:.2%}"
            
            if probability_up > 0.70:
                logger.info(f"🔥 HIGH CONFIDENCE SIGNAL: {msg}")
            else:
                logger.info(msg)

        conn.close()

    except Exception as e:
        logger.error(f"❌ Error during live prediction: {str(e)}") 

if __name__ == "__main__":
    make_live_prediction() 