# KoinStrap – Decision Intelligence System

## Project Overview

KoinStrap Decision Intelligence System is a **work-in-progress hybrid data and cloud engineering platform** designed to support strategic decision-making for cryptocurrency operations.

The goal of the system is not just to collect crypto prices, but to **transform raw market and social data into structured decision signals** that can later power dashboards, alerts, and automated intelligence workflows.

The project is intentionally built in **layers**, allowing it to evolve incrementally from local development into a production-grade cloud system.

---

## System Philosophy

Most crypto tools stop at charts.

KoinStrap is designed to answer questions like:

- Is the market behaving unusually right now?
- Is this a short-term spike or a real trend shift?
- Is social sentiment aligned with price movement?
- When should the system alert a human or another service?

To support this, the system follows a **decision-intelligence pipeline**, not just data ingestion.

---

## High-Level Architecture

Layer 1 → Market Data Acquisition (CoinGecko)  
Layer 2 → Social Data Acquisition (Reddit Public JSON Endpoints)  
Layer 3 → Ingestion & Normalization (MySQL)  
Layer 4 → Metrics & Signal Computation  
Layer 5 → Analytics & Decision Support Dashboard  

Each layer is modular and independently extensible.

---

# Current Implementation Status

## ✅ Accomplishments

### Layer 1 – Market Data Acquisition
- CoinGecko API fully integrated
- BTC and ETH market data pulled at fixed intervals
- Robust request handling with retries and logging

---

### Layer 2 – Social Data Acquisition (Reddit)
- Reddit public JSON endpoints integrated (no API keys required)
- Keyword-based search for BTC and ETH
- Basic NLP sentiment analysis using VADER
- Retry logic for network reliability
- Structured logging for observability

---

### Layer 3 – Ingestion & Normalization

#### Market Data Table
`raw_crypto_market_data`
- id
- symbol
- name
- price_usd
- volume_24h_usd
- observed_at

#### Social Sentiment Table
`social_sentiment_metrics`
- id
- symbol
- window_start
- window_end
- post_count
- avg_sentiment
- positive_ratio
- negative_ratio
- neutral_ratio
- change_in_count
- change_in_count_pct
- change_in_sentiment
- change_in_sentiment_pct
- source
- created_at

Ingestion pipeline features:
- Idempotent inserts
- Duplicate protection
- Transaction safety with rollback
- Normalized timestamps
- Structured logging
- Retry handling for external requests

📌 CoinGecko ingestion runs every 5 minutes via cron  
📌 Reddit ingestion runs on a controlled interval (longer window aggregation)

---

### Layer 4 – Metrics & Signals

Raw values are transformed into decision-ready signals.

#### Market Metrics
- 5-minute price change
- 15-minute price change
- 1-hour rolling aggregates (avg, min, max)
- Sparse data handling

#### Social Metrics
- Post count per time window
- Average sentiment score
- Positive / negative / neutral ratios
- Change in post volume between windows
- Change in sentiment between windows

This enables:
- Sentiment momentum tracking
- Social spike detection
- Cross-layer comparison (price vs sentiment)

---

### Layer 5 – Analytics & Decision Support

Interactive Streamlit dashboard implemented.

Features:
- Real-time BTC and ETH price metrics
- Social sentiment metrics display
- Clear separation of:
  - Raw data
  - Derived signals
- Short-term trend indicators
- Hard-coded alert signals for:
  - Price spikes
  - Trend reversals
  - Social activity surges
- Interactive Plotly visualizations

The dashboard is built for **human decision support first**, with structured backend logic for future extensibility.

---

# What This Project Demonstrates

- End-to-end data pipeline design
- Multi-source ingestion (market + social)
- Separation of ingestion, metrics, and analytics layers
- SQL-backed metric computation
- Social sentiment integration into financial intelligence
- Retry-safe ingestion scripts
- Logging and observability awareness
- Automation with cron
- Clean, modular Python architecture
- Production-aware thinking without premature cloud complexity

---

# Project Status

🚧 Actively evolving

The system currently runs locally with:

- Automated CoinGecko ingestion
- Automated Reddit ingestion
- Automated metric computation
- Live analytics dashboard
- Structured social sentiment storage

The architecture is cloud-ready but intentionally deployed locally during development to maintain clarity and control.

---

# Next Steps

### Near-Term
- Sentiment-to-price divergence detection logic
- Signal scoring and prioritization layer
- Internal KoinStrap business metrics integration
- Improved anomaly detection thresholds

### Mid-Term
- Cloud deployment (AWS or GCP)
- Docker containerization
- Secure secrets management
- External alert delivery (email / webhook)

---

# Notes for Recruiters & Reviewers

This project demonstrates:

- How real-world data platforms evolve incrementally
- Strong architectural thinking across multiple data sources
- Practical data engineering skills applied to decision intelligence
- Integration of financial and social sentiment signals
- Production-minded design decisions
- Structured automation and observability

The repository intentionally reflects a **living system**, not a static demo.
