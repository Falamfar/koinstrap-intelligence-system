import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from datetime import timedelta 

load_dotenv("/home/falamfar/koinstrap_platform/projects/koinstrap/config/.env")

conn = psycopg2.connect(
    host=os.getenv("PG_HOST"),
    user=os.getenv("PG_USER"),
    password=os.getenv("PG_PASSWORD"),
    database=os.getenv("PG_NAME"),
    port=os.getenv("PG_PORT")
)

cursor = conn.cursor(cursor_factory=RealDictCursor)

def backfill_1():
    print("starting back aware backfill")

    cursor.execute("SELECT * FROM raw_crypto_market_data  ORDER BY symbol, observed_at ASC") 
    all_raw_data = cursor.fetchall() 

    history = {}
    last_time = {} #new memory to track the last time we saw a price

    for row in all_raw_data:
        sym = row['symbol'] 
        price = float(row['price_usd'])
        time = row['observed_at']
        vol = float(row['volume_24h_usd']) if row ['volume_24h_usd'] else 0 

        if sym not in history:
            history[sym] = [] 

    # --- THE GAP DETECTOR ---   
        if sym in last_time:
            minutes_passed = (time - last_time[sym]).total_seconds() / 60.0
            if minutes_passed > 10:
                history[sym] = [] # Wipe the bucket, the old data is stale

        history[sym].append(price)
        last_time[sym] = time # Update the last seen time for this symbol    

        if len(history[sym]) > 12:
        # Remove the oldest entry (first one)
            history[sym].pop(0) 

        # Only do math if we have at least 2 points that are "close" in time
        p_5m = ((price - history[sym][-2])) / history[sym][-2] * 100 if len(history[sym]) >= 2 else 0
        p_15m = ((price - history[sym][-4])) / history[sym][-4] * 100 if len(history[sym]) >= 4 else 0

        avg_1h = sum(history[sym]) / len(history[sym]) 
        min_1h = min(history[sym])
        max_1h = max(history[sym])

        insert_query = """
            INSERT INTO crypto_metrics (
                metric_time, symbol, price_usd, price_change_5m, price_change_15m, volume_24h_usd, avg_price_1h, min_price_1h, max_price_1h
            )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (metric_time, symbol) DO NOTHING;
        """
        cursor.execute(insert_query, (time, sym, price, p_5m, p_15m, vol, avg_1h, min_1h, max_1h)) 

    conn.commit()

    print(f"cleanly blackfilled {len(all_raw_data)} rows. Gaps were handled")

if __name__ == "__main__":
    backfill_1()
    cursor.close()
    conn.close()