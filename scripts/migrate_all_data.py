import os
import mysql.connector
import psycopg2
from dotenv import load_dotenv

load_dotenv("/home/falamfar/koinstrap_platform/projects/koinstrap/koinstrap.env")

def get_connections():
    mysql_conn = mysql.connector.connect(
        host=os.getenv('MYSQL_HOST'),
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        database=os.getenv('MYSQL_DATABASE')
    )
    
    postgres_conn = psycopg2.connect(
        host=os.getenv("PG_HOST"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
        dbname=os.getenv("PG_NAME"),        # Matches 'PG_NAME' in your .env
        port=os.getenv("PG_PORT")
    )

    return mysql_conn, postgres_conn


def migrate_table(mysql_conn, pg_conn, table_name):
    m_cursor = mysql_conn.cursor()
    p_cursor = pg_conn.cursor() 

    print(f"--- 🚚 Migrating {table_name}... ---")

    # 1. Get the column names from Postgres to ensure the order is PERFECT
    p_cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}' ORDER BY ordinal_position")
    columns = [row[0] for row in p_cursor.fetchall()]
    column_str = ", ".join(columns)
    
    p_cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}' ORDER BY ordinal_position")
    columns = [row[0] for row in p_cursor.fetchall()]
    column_str = ", ".join(columns)

    # --- START OF CHANGE ---
    # 2. Get data from MySQL
    m_cursor.execute(f"SELECT {column_str} FROM {table_name}")  
    rows = m_cursor.fetchall()

    if not rows:
        print(f"⚠️ Skipping {table_name}: No data found.")
        return

    # 3. THE TRANSLATOR & DE-DUPLICATOR
    cleaned_rows = []
    seen_keys = set() 
    
    for row in rows:
        new_row = []
        for col_name, item in zip(columns, row):
            if item == '' or item is None:
                new_row.append('UNKNOWN' if col_name == 'symbol' else None)
            elif col_name.startswith('is_') and item in [0, 1]:
                new_row.append(bool(item))
            else:
                new_row.append(item)
        
        # --- NEW DUPLICATE CHECK ---
        if table_name == "crypto_analysis":
            try:
                # We identify which columns are for Time and Symbol
                time_idx = columns.index('analysis_time')
                sym_idx = columns.index('symbol')
                fingerprint = (new_row[time_idx], new_row[sym_idx])
                
                # If we've already added this specific Time+Symbol, skip the duplicate
                if fingerprint in seen_keys:
                    continue 
                seen_keys.add(fingerprint)
            except ValueError:
                pass 
        # ---------------------------
        
        cleaned_rows.append(tuple(new_row))
    
    # 4. The Insert
    placeholders = ", ".join(["%s"] * len(columns))
    insert_query = f"INSERT INTO {table_name} ({column_str}) VALUES ({placeholders})"    

    try:
        p_cursor.executemany(insert_query, cleaned_rows)  
        pg_conn.commit()
        print(f"✅ Successfully migrated {len(cleaned_rows)} rows")
    except Exception as e:
        pg_conn.rollback()
        print(f"❌ Error migrating {table_name}: {e}")



if __name__ == "__main__":
    m_conn, p_conn = get_connections()

    tables_to_migrate = [
        "raw_crypto_market_data",
        "crypto_metrics",
        "social_sentiment_metrics",
        "crypto_analysis"
    ]

    for table in tables_to_migrate:
        migrate_table(m_conn, p_conn, table)

    m_conn.close()
    p_conn.close()
    print("Migration completed.")

