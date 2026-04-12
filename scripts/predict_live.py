import psycopg2
from psycopg2.extras import RealDictCursor
import os
import joblib
import pandas as pd 
from dotenv import load_dotenv
import logging
from pathlib import Path 

LOG_FILE = "/home/falamfar/koinstrap_platform/projects/koinstrap/logs/live_predictions.log"

logger = logging.getLogger("live_predictor")
logger.setLevel(logging.INFO)

if not logger.handlers:
    stream_handler = logging.StreamHandler() 
    file_handler= logging.FileHandler(LOG_FILE) 

    formatter = logging.Formatter ("%(asctime)s | %(levelname)s | %(message)s")
    stream_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter) 
 
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)

load_dotenv("/home/falamfar/koinstrap_platform/projects/koinstrap/config/.env")

def make_live_prediction():
    logger.info("robot is waking up to check the markets")
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("PG_NAME"),
            user=os.getenv("PG_USER"),
            password=os.getenv("PG_PASSWORD"),
            host=os.getenv("PG_HOST"),
            port=os.getenv("PG_PORT") 
        ) 

        query = """
        SELECT DISTINCT ON (m.symbol)
            m.symbol, m.metric_time, m.price_usd, m.price_change_5m,
            m.price_change_15m, m.volume_24h_usd, a.confidence_score, s.post_count, 
            s.avg_sentiment
        FROM crypto_metrics m
        JOIN crypto_analysis a ON m.metric_time = a.metric_time_ref AND m.symbol = a.symbol 
        LEFT JOIN social_sentiment_metrics s ON m.symbol = s.symbol 
        WHERE m.metric_time >= NOW() - INTERVAL '30 minutes'
        ORDER BY m.symbol, m.metric_time DESC;
        """

        df = pd.read_sql(query, conn)
        df = df.fillna(0)

        if df.empty:
            logger.warning("No data found for live prediction.")
            return

        # Wake up the Owl (Brain)
        model_path = "/home/falamfar/koinstrap_platform/projects/koinstrap/scripts/koinstrap_brain.pkl"
        brain = joblib.load(model_path)

        features = ['price_change_5m', 'price_change_15m', 'volume_24h_usd', 'post_count', 'avg_sentiment', 'confidence_score']

        # "Finger points to each row one by one"
        for index, row in df.iterrows():

            # Put the data in a tiny labeled table so the Brain is happy
            input_df = pd.DataFrame([row[features]], columns=features) 

            # The Owl hoots his guess
            prediction = brain.predict(input_df)[0] 
            prob_array = brain.predict_proba(input_df)
            probability = prob_array[0][1].item()   

            direction = "😀up" if prediction == 1 else "😥down"
          

            logger.info(f"Live prediction for {row['symbol'].upper()} is likely going  {direction} (confidence: {probability:.2%})")
        conn.close()

    except Exception as e:
        logger.error(f"Error occurred during live prediction: {str(e)}") 

if __name__ == "__main__":
    make_live_prediction()