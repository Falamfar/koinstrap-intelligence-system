import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

# Import your validated signal logic
from analyze_crypto_metrics import compute_signals

load_dotenv("/home/falamfar/koinstrap_platform/projects/koinstrap/config/.env")

def backfill_analysis():
    print("🚀 Starting Market Analysis Backfill...")
    conn = psycopg2.connect(
        host=os.getenv("PG_HOST"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
        database=os.getenv("PG_NAME"),
        port=os.getenv("PG_PORT")
    )
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # 1. Clean the table first as we discussed
    cursor.execute("TRUNCATE TABLE crypto_analysis;")
    conn.commit()

    # 2. Get all metrics in chronological order
    cursor.execute("SELECT * FROM crypto_metrics ORDER BY symbol, metric_time ASC;")  
    all_metrics = cursor.fetchall()

    prev_row_map = {} 
    count = 0 

    insert_query = """
        INSERT INTO crypto_analysis (
            analysis_time, symbol, metric_time_ref, is_price_spike,
            is_trend_reversal, is_volume_spike, trend_signal, notes
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """

    for current_row in all_metrics:
        symbol = current_row['symbol']
        prev_row = prev_row_map.get(symbol)
        historical_time = current_row['metric_time']   

        signals = compute_signals(current_row, prev_row) 

        if signals:
            cursor.execute(insert_query, (
                historical_time, 
                symbol,
                historical_time,  
                signals['is_price_spike'],
                signals['is_trend_reversal'],
                signals['is_volume_spike'],
                signals['trend_signal'],
                "Backfilled Market Analysis"
            ))
            count += 1
        
        prev_row_map[symbol] = current_row

        if count % 500 == 0:
            conn.commit()
            print(f"✅ Analyzed {count} rows...")

    conn.commit()
    cursor.close()
    conn.close()
    print(f"🎉 Phase 1 Complete: {count} market signals stored.")

if __name__ == "__main__":
    backfill_analysis()    