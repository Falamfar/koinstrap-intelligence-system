# KoinStrap – Decision Intelligence System

## Project Overview

KoinStrap Decision Intelligence System is a **work-in-progress hybrid data and cloud engineering platform** designed to support strategic decision-making for cryptocurrency operations.

The goal of the system is not just to collect crypto prices, but to **transform raw market data into structured decision signals** that can later power dashboards, alerts, and automated intelligence workflows.

The project is intentionally built in **layers**, allowing it to grow incrementally from local development into a production-grade cloud system.

---

## System Philosophy

Most crypto tools stop at charts.

KoinStrap is designed to answer questions like:
- *Is the market behaving unusually right now?*
- *Is this a short-term spike or a real trend shift?*
- *When should the system alert a human or another service?*

To support this, the system follows a **decision-intelligence pipeline**, not just data ingestion.

---

## High-Level Architecture

Layer 1 → Data Acquisition  
External market data (CoinGecko)  

↓  

Layer 2 → Ingestion & Normalization  
Validated, structured storage in SQL  

↓  

Layer 3 → Metrics & Signals  
Derived metrics for trend, momentum, and change  

↓  

Layer 4 → Analytics & Decision Support  
Dashboards, alerts, and future automation  

Each layer is modular and independently extensible.

---

## Current Implementation Status

### ✅ Layer 1: Data Acquisition
- CoinGecko API integrated
- BTC and ETH market data pulled at fixed intervals

---

### ✅ Layer 2: Ingestion & Normalization
- Raw market data stored in MySQL table: `raw_crypto_market_data`
- Table fields include:
  - `id`
  - `symbol`
  - `name`
  - `price_usd`
  - `volume_24h_usd`
  - `observed_at`

**Ingestion pipeline features:**
- Idempotency (prevents duplicate inserts)
- Data validation (skips invalid records)
- Transaction safety with rollback
- Normalized timestamps
- Structured logging

📌 Ingestion runs automatically every 5 minutes via cron.

---

### ✅ Layer 3: Metrics & Signals

Raw prices alone are not decision-ready.

A dedicated metrics layer transforms raw market data into **interpretable decision signals**, stored in a separate table: `crypto_metrics`.

**Computed metrics include:**
- Price change over 5 minutes
- Price change over 15 minutes
- 1-hour rolling aggregates (avg, min, max)
- Robust handling of sparse or missing data

This logic is implemented in:
- `compute_metrics.py`

📌 Metrics computation runs automatically every 5 minutes via cron.

---

### ✅ Layer 4: Analytics & Decision Support

An interactive analytics layer has been implemented to surface decision-ready insights.

**Dashboard capabilities include:**
- Real-time BTC and ETH price metrics
- Clear visual separation between:
  - Raw values
  - Derived signals
- Short-term trend reversal indicators
- Hard-coded alert signals for:
  - Price spikes
  - Trend reversals
  - Unusual volume behavior
- Interactive line charts using Plotly
- Streamlit-based UI focused on clarity and signal visibility

This layer is designed for **human decision support first**, with automation planned later.

---

## What This Project Demonstrates

- End-to-end data pipeline design
- Separation of ingestion, metrics, and analytics layers
- Decision-focused analytics (not just visualization)
- SQL-backed metric computation
- Robust handling of sparse real-world data
- Automation with cron
- Clean, modular Python architecture
- Production-aware design without premature cloud complexity

---

## Project Status

🚧 **Actively evolving**

The system is currently running locally with:
- Automated ingestion
- Automated metrics computation
- Live analytics dashboard

Cloud deployment and alert delivery are intentionally deferred to preserve architectural clarity.

---

## Next Planned Steps

**Near-term**
- Twitter sentiment ingestion
- Internal KoinStrap business data integration
- Signal scoring and prioritization


**Mid-term**
- Cloud deployment (AWS / GCP)
- Containerization (Docker)
- Secure secrets management
- External alert delivery (email / webhook)

**Long-term**
- Automated decision triggers
- Advanced analytics and ML-based signals
- Fully productionized decision intelligence platform

---

## Notes for Recruiters & Reviewers

This project demonstrates:
- How real-world data platforms evolve incrementally
- Strong system design and architectural thinking
- Practical data engineering skills applied to decision intelligence
- Readiness for cloud and production environments

The repository intentionally reflects a **living system**, not a static demo.
