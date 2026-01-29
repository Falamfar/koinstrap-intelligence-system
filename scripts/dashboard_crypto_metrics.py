import streamlit as st
import os
import mysql.connector
from dotenv import load_dotenv 
from datetime import timezone 
from datetime import datetime
import plotly.graph_objects as go

load_dotenv("/home/falamfar/projects/koinstrap/config/.env")

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME") 

def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

st.set_page_config(page_title="koinstrap intelligence dashboard")


st.title("🧠Koinstrap crypto Intelligence")

st.write("live decision metrics from the koinstrap decision intelligence system")

conn = get_db_connection()
cursor = conn.cursor(dictionary=True)
symbols = ["btc", "eth"]

def fmt(value, decimals = 2):
    return f"{value:.{decimals}f}" if value is not None else "N/A"

def fmt_change(value) : 
    if value is None:   
        return "N/A"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f}" 

def alert_label(flag):
    if flag:
        return "🔕yes"
    else: 
        return "✅ No"    



latest_metrics = {}
history = {}


 
 # --- GET LATEST METRIC ---
for symbol in symbols:
    cursor.execute(
        """
        SELECT *
        FROM crypto_metrics
        WHERE symbol = %s
        ORDER BY metric_time DESC
        LIMIT 1
        """,
        (symbol,)
    )

    row = cursor.fetchone() 
    latest_metrics[symbol] = row

    # ---  GET LAST N METRICS PER SYMBOL (robust for plotting)

    N = 12

    cursor.execute(
        """
        SELECT metric_time, price_usd 
        FROM crypto_metrics
        WHERE symbol = %s 
        ORDER BY metric_time ASC 
        LIMIT %s
        """,
        (symbol, N)
    )



    history[symbol] = cursor.fetchall()

cursor.close()
conn.close()

# --------------------------------------------------
# DISPLAY LATEST METRICS USING STREAMLIT METRIC
# --------------------------------------------------
st.subheader("Latest Metrics")

for symbol in symbols:
    row = latest_metrics[symbol]




    if row:
        st.subheader(f"📊{symbol.upper()} latest Metrics")

        col1,col2,col3, col4 = st.columns(4)

       

        col1.metric(
            label= "price (USD)",
            value=f"${fmt(row['price_usd'])}",
            delta=fmt_change(row["price_change_5m"])
        ) 

        col2.metric(
            label="price change (5m)",
            value=fmt_change(row['price_change_5m'])
        )

        col3.metric( 
            label = "price change (15m)",
            value = fmt_change(row['price_change_15m'])

        )

        col4.metric(
            label = "24h volume (usd)",
            value = f"${fmt(row['volume_24h_usd'], 0)}"
        )

    # Columns for alerts    

    alert_col1, alert_col2, alert_col3 = st.columns(3)
    alert_col1.markdown(f"**price spike:** {alert_label(row.get('is_price_spike'))}")
    alert_col2.markdown(f"**trend reversal:** {alert_label(row.get('is_trend_reversal'))}")
    alert_col3.markdown(f"**volume spike:**{alert_label(row.get('is_volume_spike'))}")




    # Timestamp (explicit UTC)

    metric_time = row['metric_time']
    metric_time_utc = metric_time.replace(tzinfo=timezone.utc)
    st.caption(f"Last updated: {metric_time_utc.strftime('%Y-%m-%d %H:%M UTC')}")


    st.divider()

else:
    st.write(f"no metrics found for {symbol.upper()}")    


# --------------------------------------------------
# PLOTLY LINE CHART FOR LAST 1 HOUR
# --------------------------------------------------

st.subheader ("📈 Price Trend (last ~hour / last {} points)".format(N)) 

fig = go.Figure() #create empty figure

for symbol in symbols: 
    rows = history.get(symbol, [])  

    # fallback if no data
    if not rows:
        latest_row = latest_metrics.get(symbol)
        if latest_row :
            rows = [latest_row]
        else:
            continue

    # Extract times and prices     
    times = [r['metric_time'] for r in rows]
    prices = [r['price_usd'] for r in rows]    

    # Extract alert points
    price_spikes = [r['price_usd'] if r.get('is_price_spike') else None for r in rows]
    trend_reversals = [r['price_usd'] if r.get('is_trend_reversal') else None for r in rows]
    volume_spikes = [r['price_usd'] if r.get('is_volume_spike') else None for r in rows]

    # Ensure datetime objects
    times = [
        t if isinstance(t, datetime) else datetime.fromisoformat(str(t))
        for t in times
    ]
    times = [
        t if isinstance(t, datetime) else datetime.fromisoformat(str(t))
        for t in times
    ]

    #overlay alerts as markers
    fig.add_trace(go.Scatter(x=times, y = price_spikes, mode = "markers", marker = dict(color="red", size = 12, symbol = "triangle-up"), name = f"{symbol.upper()} price spike")) 
    fig.add_trace(go.Scatter(x=times, y =trend_reversals, mode = "markers", marker = dict(color = "orange", size = 12, symbol = "diamond"), name = f"{symbol.upper()} trend reversal " ))
    fig.add_trace(go.Scatter(x=times, y =volume_spikes, mode = "markers", marker = dict(color = "blue", size = 12, symbol = "star"), name = f"{symbol.upper()} volume spike "))


    
    # Add a line + marker trace for each coin
    fig.add_trace(
        go.Scatter(
            x=times,
            y=prices,
            mode="lines+markers", #Draw both line and points
            name=symbol.upper() 
            
            )
    
    )




# Customize chart layout

fig.update_layout(
    title = "Crypto Price Trends (Last 1 Hour)",
    xaxis_title = "Time",
    yaxis_title = "price (USD)",
    legend_title = "Coin",
    template = "plotly_dark"
)


# Show the chart in Streamlit

st.plotly_chart(fig, width='stretch')







