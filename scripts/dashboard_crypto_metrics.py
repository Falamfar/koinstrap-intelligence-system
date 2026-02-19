# -----------------------------
# 🧠 Koinstrap Crypto Intelligence Dashboard (Updated)
# -----------------------------

import streamlit as st
import os
import mysql.connector
from dotenv import load_dotenv
from datetime import timezone, datetime
import plotly.graph_objects as go

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv("/home/falamfar/projects/koinstrap/config/.env")

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# -----------------------------
# Database connection function
# -----------------------------
def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

# -----------------------------
# Streamlit page config
# -----------------------------
st.set_page_config(page_title="Koinstrap Intelligence Dashboard")
st.title("🧠 Koinstrap Crypto Intelligence")
st.write("Live decision metrics from the Koinstrap Decision Intelligence System")

# -----------------------------
# Symbols to track
# -----------------------------
symbols = ["btc", "eth"]

# -----------------------------
# Helper formatting functions
# -----------------------------
def fmt(value, decimals=2):
    """Format numeric value or fallback to N/A"""
    return f"{value:.{decimals}f}" if value is not None else "N/A"

def fmt_change(value):
    """Format change values with sign + or -"""
    if value is None:
        return "N/A"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f}"

def alert_label(value):
    """Show alert emojis based on boolean flag"""
    return "🔕 Yes" if value else "✅ No"

# -----------------------------
# Connect to DB and fetch combined metrics + analysis
# -----------------------------
conn = get_db_connection()
cursor = conn.cursor(dictionary=True)

latest_data = {}  # store latest combined info
history_data = {}  # store last N points for plotting
N = 12  # last N points

for symbol in symbols:
    # -----------------------------
    # INNER JOIN crypto_metrics + crypto_analysis
    # Only select relevant columns:
    # metrics: price_usd, price_change_5m, price_change_15m, volume_24h_usd
    # analysis: trend_signal, confidence_score, alerts
    # -----------------------------
    cursor.execute("""
        SELECT 
            m.metric_time,
            m.price_usd,
            m.price_change_5m,
            m.price_change_15m,
            m.volume_24h_usd,
            a.analysis_time,
            a.trend_signal,
            a.confidence_score,
            a.is_price_spike,
            a.is_trend_reversal,
            a.is_volume_spike
        FROM crypto_metrics m
        INNER JOIN crypto_analysis a
            ON a.symbol = m.symbol
            AND a.analysis_time >= m.metric_time
        WHERE m.symbol = %s
        ORDER BY a.analysis_time DESC
        LIMIT 1
    """, (symbol,))
    latest_data[symbol] = cursor.fetchone()

    # Fetch last N points for plotting price trends
    cursor.execute("""
        SELECT m.metric_time, m.price_usd
        FROM crypto_metrics m
        WHERE m.symbol = %s
        ORDER BY m.metric_time ASC
        LIMIT %s
    """, (symbol, N))
    history_data[symbol] = cursor.fetchall()

cursor.close()
conn.close()

# -----------------------------
# Display latest metrics
# -----------------------------
st.subheader("Latest Metrics + Analysis")

for symbol in symbols:
    row = latest_data.get(symbol)

    if row:
        st.subheader(f"📊 {symbol.upper()} Latest Analysis + Metrics")

        col1, col2, col3, col4 = st.columns(4)

        # 1️⃣ Trend Signal with Confidence
        col1.metric(
            label="Trend Signal",
            value=row.get("trend_signal", "N/A"),
            delta=f"{fmt(row.get('confidence_score', 0))}%"
        )

        # 2️⃣ Price in USD
        col2.metric(
            label="Price (USD)",
            value=f"${fmt(row.get('price_usd'))}",
            delta=fmt_change(row.get('price_change_5m'))
        )

        # 3️⃣ Price change 15m
        col3.metric(
            label="Price Change 15m",
            value=fmt_change(row.get('price_change_15m'))
        )

        # 4️⃣ 24h Volume
        col4.metric(
            label="24h Volume (USD)",
            value=f"${fmt(row.get('volume_24h_usd'), 0)}"
        )

        # Alerts (price spike, trend reversal, volume spike)
        alert_col1, alert_col2, alert_col3 = st.columns(3)
        alert_col1.markdown(f"**Price Spike:** {alert_label(row.get('is_price_spike'))}")
        alert_col2.markdown(f"**Trend Reversal:** {alert_label(row.get('is_trend_reversal'))}")
        alert_col3.markdown(f"**Volume Spike:** {alert_label(row.get('is_volume_spike'))}")

        # Timestamp
        metric_time_utc = row['metric_time'].replace(tzinfo=timezone.utc)
        st.caption(f"Last updated: {metric_time_utc.strftime('%Y-%m-%d %H:%M UTC')}")

        st.divider()

# -----------------------------
# Plot Price Trend
# -----------------------------
st.subheader(f"📈 Price Trend (Last ~{N} points)")

fig = go.Figure()

for symbol in symbols:
    rows = history_data.get(symbol, [])

    if not rows:
        latest_row = latest_data.get(symbol)
        if latest_row:
            rows = [latest_row]
        else:
            continue

    times = [r['metric_time'] for r in rows]
    prices = [r['price_usd'] for r in rows]

    fig.add_trace(go.Scatter(
        x=times,
        y=prices,
        mode='lines+markers',
        name=symbol.upper(),
        line=dict(width=2),
        marker=dict(size=6)
    ))

fig.update_layout(
    title="Crypto Price Trends (Last ~Hour)",
    xaxis_title="Time",
    yaxis_title="Price (USD)",
    legend_title="Coin",
    template="plotly_dark"
)

st.plotly_chart(fig, use_container_width=True)
