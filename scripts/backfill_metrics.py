import os 
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv("/home/falamfar/koinstrap_platform/projects/koinstrap/config/.env")

# ---------------------------------------------------------
#  DATABASE HELPER
# ---------------------------------------------------------
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("PG_HOST"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
        database=os.getenv("PG_NAME"),
        port=os.getenv("PG_PORT")
    )

# ---------------------------------------------------------
#  BACKFILL LOGIC
# ---------------------------------------------------------
def run_independent_backfill(symbols = ['btc', 'eth']):
    # Use the helper to ensure we have a valid connection
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT DISTINCT observed_at
        FROM raw_crypto_market_data r
        WHERE NOT EXISTS (
            SELECT 1 FROM crypto_metrics m
            WHERE m.metric_time = r.observed_at 
        ) 
        ORDER BY observed_at ASC 
    """) 

    missing_timestamps = cursor.fetchall()
    if not missing_timestamps:
        print("✅ No missing timestamps found. Everything already backfilled.")
        conn.close()
        return 

    print(f"📊 Found {len(missing_timestamps)} missing timestamps to process, starting...")    
    inserted_count = 0
    
    try:
        for ts_row in missing_timestamps:
            target_time = ts_row['observed_at']

            for symbol in symbols:
                # FIXED: Added the '=' sign
                lookback_start = target_time - timedelta(minutes=70)

                cursor.execute("""
                    SELECT observed_at, price_usd, volume_24h_usd
                    FROM raw_crypto_market_data 
                    WHERE symbol = %s AND observed_at >= %s AND observed_at <= %s
                    ORDER BY observed_at DESC
                """, (symbol, lookback_start, target_time))
                rows = cursor.fetchall()

                if not rows:
                    continue

                price_now = float(rows[0]["price_usd"])
                # FIXED: Simplified the volume check
                vol_now = float(rows[0]["volume_24h_usd"]) if rows[0]["volume_24h_usd"] else 0

                # Compute 5m and 15m Deltas
                deltas = {} 
                for delta_min in [5, 15]:
                    cutoff_time = target_time - timedelta(minutes=delta_min)

                    # FIXED: Added default 'None' so it doesn't crash if no data is found
                    price_before_row = next((r for r in rows if r["observed_at"] <= cutoff_time), None)

                    if price_before_row:
                        price_before = float(price_before_row["price_usd"])
                        pct_change = ((price_now - price_before) / price_before) * 100
                        deltas[delta_min] = round(pct_change, 4) 
                    else:
                        deltas[delta_min] = 0.0 

                # Aggregates
                prices = [float(r["price_usd"]) for r in rows]
                avg_price = sum(prices) / len(prices) # FIXED: Name consistency

                insert_query = """
                    INSERT INTO crypto_metrics (
                        metric_time, symbol, price_usd, price_change_5m, price_change_15m,
                        volume_24h_usd, avg_price_1h, min_price_1h, max_price_1h
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (metric_time, symbol) DO NOTHING
                """
                cursor.execute(insert_query, (
                    target_time, symbol, price_now, deltas[5], deltas[15], vol_now, 
                    avg_price, min(prices), max(prices)
                ))    

                if cursor.rowcount > 0:
                    inserted_count += 1

            # Commit periodically
            if inserted_count > 0 and inserted_count % 100 == 0:
                conn.commit()
                print(f"✅ Processed {inserted_count} rows so far...")   

        conn.commit()
        print(f"🎉 Finished! Total inserted rows: {inserted_count}")
    except Exception as e:
        conn.rollback()
        print(f"❌ Error occurred: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    run_independent_backfill()