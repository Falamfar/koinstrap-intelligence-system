import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

from analyze_crypto_metrics import compute_signals

load_dotenv("/home/falamfar/koinstrap_platform/projects/koinstrap/config/.env")

def backfill_analysis():
    print("starting backfill analysis")

    conn = psycopg2.connect(
        host=os.getenv("PG_HOST"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
        database=os.getenv("PG_NAME"),
        port=os.getenv("PG_PORT")
    )

    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("TRUNCATE TABLE crypto_analysis;")

    cursor.execute("SELECT * FROM crypto_metrics ORDER BY symbol, metric_time ASC;")  
    all_metrics = cursor.fetchall()

    prev_row_map = {} # Memory to help detect Volume Spikes
    count = 0 

    for current_row in all_metrics:
        symbol = current_row['symbol']
        prev_row = prev_row_map.get(symbol)

        historical_time = current_row['metric_time']   

        signals = compute_signals(current_row, prev_row) 

        if signals:
            insert_query = """
            INSERT INTO crypto_analysis (
                analysis_time, symbol, metric_time_ref, is_price_spike,
                is_trend_reversal, is_volume_spike, trend_signal, notes
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (analysis_time, symbol) DO NOTHING;
            """

        
        cursor.execute(insert_query,(
            historical_time, 
            symbol,
            historical_time,  
            signals['is_price_spike'],
            signals['is_trend_reversal'],
            signals['is_volume_spike'],
            signals['trend_signal'],
            "Backfilled analysis based on historical metrics"
            )
        )
        count += 1
        
        # Update memory for the next loop
        prev_row_map[symbol] = current_row
    conn.commit()
    print(f"success😀 all {len(all_metrics)} metrics have been analyzed") 

if __name__ == "__main__":
    backfill_analysis() 

