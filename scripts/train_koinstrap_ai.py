import psycopg2
import pandas as pd 
import os
import logging
from dotenv import load_dotenv
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib 


logger = logging.getLogger("train_ai")
logger.setLevel(logging.INFO) 

if not logger.handlers:
    file_handler = logging.FileHandler("/home/falamfar/koinstrap_platform/projects/koinstrap/logs/train_ai.log")
    stream_handler = logging.StreamHandler()
    
    formatter = logging.Formatter( "%(asctime)s | %(levelname)s | %(message)s") 
    file_handler.setFormatter (formatter)
    stream_handler.setFormatter(formatter) 

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

load_dotenv("/home/falamfar/koinstrap_platform/projects/koinstrap/config/.env")

def train_model():
    logger.info("Starting model training...") 
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("PG_NAME"),
            user=os.getenv("PG_USER"),
            password=os.getenv("PG_PASSWORD"),
            host=os.getenv("PG_HOST"),
            port=os.getenv("PG_PORT") 
        )

        logger.info("connecting to database to fetch features")
        query = "SELECT * FROM ml_features"
        df = pd.read_sql (query, conn) 
        conn.close()

        df = df.fillna(0)

        logger.info(f"successfully loaded {len(df)} rows of data")



        features = ['price_change_5m', 'price_change_15m', 'volume_24h_usd', 'post_count', 'avg_sentiment', 'confidence_score']

        X = df[features]
        y = df['price_up_next_60m']

        # Split into Study (80%) and Exam (20%)
        x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42) 
        logger.info(f"data split into Training (80%) and Testing (20%) sets")  


        # TRAINING THE BRAIN
        logger.info("building the random forest (100 treees)...")
        model = RandomForestClassifier(n_estimators=100, random_state=42)

        logger.info("training started (fitting the model)")
        model.fit(x_train, y_train) 
        logger.info("training completed") 

        #  EVALUATION 
        predictions = model.predict(x_test)
        score = accuracy_score(y_test, predictions)  
        logger.info(f"FINAL EXAM SCORE: {score * 100:.4f}%")

        #  SAVING THE BRAIN 
        model_path = 'koinstrap_brain.pkl'
        joblib.dump(model, model_path)
        logger.info(f"model saved to {model_path}")

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}", exc_info=True)

if __name__ == "__main__":
    train_model()

