# KoinStrap – Decision Intelligence System

## Project Overview

The **KoinStrap Decision Intelligence System** is a **hybrid data and AI engineering platform** designed to empower strategic decision-making for cryptocurrency operations.  

The platform’s mission is not just to collect crypto prices, but to **transform raw market and social data into structured, actionable intelligence**. These insights are delivered via confidence scores, trend signals, and eventually AI-generated recommendations, supporting traders and stakeholders with **real-time decision guidance**.  

The system is built in **modular layers**, allowing incremental evolution from local development to **cloud-deployed production-grade infrastructure**.

---

## System Philosophy

Most crypto tools stop at charts and raw metrics.  

KoinStrap is designed to answer:

- Is the market behaving unusually right now?  
- Is a price spike short-term or part of a real trend shift?  
- Is social sentiment aligned with market movement?  
- When should the system trigger alerts or recommendations?  

To achieve this, the system follows a **decision-intelligence pipeline**, combining **multi-source data ingestion, metrics computation, and AI reasoning**, rather than merely collecting data.

---

## High-Level Architecture

**Current Layers:**

1. Market Data Acquisition (CoinGecko)  
2. Social Data Acquisition (Reddit public endpoints)  
3. Ingestion & Normalization (MySQL)  
4. Metrics & Signal Computation  
5. Analytics & Decision Dashboard  

**Planned/Next Evolution:**

6. AI Insight & Recommendation Layer – transforms signals into **human-readable insights and actionable recommendations**  
7. Cloud-Ready Orchestration & Deployment – automated, scalable, and production-ready  

The modular structure ensures **flexibility, extensibility, and easy cloud migration**.

---

## Current Implementation Status

### ✅ Layer 1 – Market Data Acquisition
- Fully integrated **CoinGecko API**  
- BTC and ETH market data fetched at controlled intervals  
- Robust request handling with retries and logging  

---

### ✅ Layer 2 – Social Data Acquisition
- **Reddit public JSON endpoints** integrated (no API keys required)  
- Keyword-based extraction for BTC and ETH discussions  
- Sentiment analysis with **VADER NLP**  
- Structured logging and retry logic for reliability  
- Integrated into the **confidence score computation**  

---

### ✅ Layer 3 – Ingestion & Normalization

**Market Data Table:** `raw_crypto_market_data`  
**Social Sentiment Table:** `social_sentiment_metrics`  

Pipeline features:  
- Idempotent inserts, duplicate protection  
- Transaction-safe with rollback  
- Normalized timestamps  
- Retry logic for external requests  
- Structured logging for observability  

**Milestone:** All ingestion pipelines are now **orchestrated via Airflow** (replacing cron), enabling scalable scheduling and laying the groundwork for cloud deployment. *(Screenshot attached in repo for reference)*  

---

### ✅ Layer 4 – Metrics & Signal Computation

**Market Metrics:**  
- 5m, 15m price change  
- 1-hour rolling aggregates (avg, min, max)  
- Sparse/missing data handling  

**Social Metrics:**  
- Post count per time window  
- Average sentiment score & sentiment ratios  
- Window-to-window changes (volume & sentiment)  

**Outcome:** Combines **price and social signals** into a **confidence score** that guides decision-making.

---

### ✅ Layer 5 – Analytics & Decision Support

- Interactive **Streamlit dashboard** for technical and non-technical stakeholders  
- Real-time BTC & ETH metrics  
- Clear separation of raw data vs derived signals  
- Short-term trend indicators  
- Alert signals for price spikes, trend reversals, and social activity surges  
- Plotly-based visualizations for exploration  

---

### 🚀 Next Evolution – AI Insight & Recommendation Layer

- Transform numeric signals into **human-readable insights**  
- Deliver **contextual recommendations** alongside confidence scores  
- Enable **real-time automated alerts** for traders  
- Goal: make KoinStrap a **decision-making companion**, not just a tracking tool  

---

## System Capabilities & Demonstrations

- End-to-end **data pipeline design**  
- Multi-source ingestion (market + social)  
- Feature engineering and metric computation  
- Social sentiment integration into financial intelligence  
- Automation with **Airflow orchestration**  
- Logging, observability, and production-ready architecture  
- Modular Python design, **cloud-ready infrastructure**  

---

## Project Status

- Active development with **local + Airflow orchestration**  
- Automated ingestion of CoinGecko and Reddit data  
- Confidence score computation fully functional  
- Real-time analytics dashboard deployed locally  
- Next milestones: AI insights integration, cloud deployment, and alert delivery  

---

## Next Steps

## Near-Term:

- AI layer for insights & recommendations

- Sentiment-to-price divergence detection

- Signal scoring and prioritization

## Mid-Term:

- Cloud deployment (AWS/GCP/Azure)

- Containerization with Docker

- Secure secrets management

- Real-time alerting via email/webhooks

## Notes for Reviewers

This repository demonstrates:

- Practical **data engineering and analytics** applied to crypto intelligence  
- Incremental, modular architecture evolution  
- Integration of **social sentiment + financial metrics** into actionable signals  
- **AI-driven insights and recommendation engine** for enhanced decision-making  
- Production-minded design, automation, and observability  
- Living system reflecting **continuous improvement, AI integration, and predictive intelligence**