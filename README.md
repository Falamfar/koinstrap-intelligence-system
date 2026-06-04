# KoinStrap – Decision Intelligence System

## Project Overview

The **KoinStrap Decision Intelligence System** is a **hybrid data and AI engineering platform** designed to empower strategic decision-making for cryptocurrency operations.  

The platform’s mission is not just to collect crypto prices, but to **transform raw market and social data into structured, actionable intelligence**. These insights are delivered via confidence scores, trend signals, and AI-generated recommendations, supporting traders and stakeholders with **real-time decision guidance**.  

The system is built in **modular layers**, allowing incremental evolution from local development to **cloud-deployed production-grade infrastructure**.

---

## System Philosophy

Most crypto tools stop at charts and raw metrics.  

KoinStrap is designed to answer:

- Is the market behaving unusually right now?  
- Is a price spike short-term or part of a real trend shift?  
- Is social sentiment aligned with market movement?  


To achieve this, the system follows a **decision-intelligence pipeline**, combining **multi-source data ingestion, metrics computation, and AI reasoning**, rather than merely collecting data.

---

## High-Level Architecture

**Current Layers:**

1. Market Data Acquisition (Coingecko WebSockets API)  
2. Social Data Acquisition (Reddit public endpoints)  
3. Ingestion & Normalization (PostgreSQL), Optimized for AI feature engineering and cloud production.  
4. Metrics & Signal Computation  
5. AI Insight & Recommendation Engine 
6. Fully containerized, multi-service Docker architecture that is completely environment-agnostic.
7. Cloud Orchestration & Deployment – Fully deployed production environment on AWS EC2.

The modular structure ensures **flexibility, extensibility, and seamless cloud operations**.

---

## Current Implementation Status

### ✅ Layer 1 – Market Data Acquisition
- Fully migrated to the **Coingecko WebSocket API** for streaming telemetry.
- BTC and ETH market data fetched continuously in real time.
- Robust network connection handling with automated reconnection and logging.  

---

### ✅ Layer 2 – Social Data Acquisition
- **Reddit public JSON endpoints** integrated (no API keys required).  
- Keyword-based extraction for BTC and ETH discussions.  
- Sentiment analysis with **VADER NLP**.  
- Structured logging and retry logic for reliability.  
- Integrated into the **confidence score computation**.  

---

### ✅ Layer 3 – Ingestion & Normalization

**Market Data Table:** Live tick tables tracking high-velocity price parameters.  
**Social Sentiment Table:** `social_sentiment_metrics`  

Pipeline features:  
- Idempotent inserts, duplicate protection.  
- Transaction-safe with rollback.  
- Normalized timestamps.  
- Retry logic for external requests.  
- Structured logging for observability.  

---

### ✅ Layer 4 – Metrics & Feature Engineering (Optimized)
- Feature Store: Implemented ml_features as the centralized "Source of Truth" for all downstream intelligence.
- Real-Time Momentum: Engineered 5-minute and 15-minute price momentum and trend signals to capture micro-volatility.
- Synchronized Orchestration: Ingestion and processing DAGs are cross-aligned to match incoming high-velocity data.
- Core database engine successfully migrated from MySQL to PostgreSQL to handle advanced indexing for training sets and production cloud queries.

---

### ✅ Layer 5 – AI Insight & Recommendation Engine ("James")
- Hybrid Intelligence: Merged a Random Forest Classifier (Probability/Quant) with Llama-3 via Groq (Narrative/Analyst).
- Context-Aware Reasoning: The system distinguishes between "Neutral Social Sentiment" and "Missing Social Data," preventing LLM hallucinations during low-volume periods.
- Predictive Certainty: Every insight is accompanied by a mathematical confidence score.
- FastAPI Integration: High-performance backend routing (`api.py`) serving live JSON packages to external UI platforms.

---

### ✅ Layer 6 – Containerization with Docker
- Multi-container architecture using Docker and Docker Compose.
- Decoupled into isolated microservices (FastAPI, PostgreSQL database warehouse, Apache Airflow orchestration layers).
- Environment-agnostic environment mapping for immediate cold-booting on remote infrastructure.

---

### ✅ Layer 7 – Cloud Orchestration & Deployment
- Production environment fully deployed and live on an **AWS EC2 instance**.
- Orchestration fully handled via **Apache Airflow**, executing automated tasks via the `DockerOperator`.
- Implemented ephemeral task container creation to maximize EC2 resource efficiency.
- Secure production-level secret management using Airflow Variables and isolated host container mapping, abstracting tokens entirely out of source control.

---

## System Capabilities & Demonstrations

- **End-to-End Data Pipeline Design:** Architecture spanning from raw WebSocket ingestion to live cloud API delivery.
- **Multi-Source Ingestion:** Automated fetching and normalization of financial telemetry (Coingecko) and high-velocity social signals (Reddit).
- **Feature Engineering & ML Inference:** Real-time computation of momentum metrics and sentiment scores serving a Random Forest Predictive Brain.
- **Hybrid AI Narrative Engine:** Integration of quantitative ML predictions with qualitative LLM reasoning to produce "James," a human-readable market analyst.
- **Production API Layer:** Low-latency FastAPI implementation using raw `psycopg2` and `RealDictCursor` for optimized JSON data exchange.
- **Automation & Orchestration:** Fully scheduled operations via Apache Airflow, ensuring strict data freshness and decision consistency.
- **Observability & Reliability:** Integrated logging, PostgreSQL transaction safety, and repository-level Secret Protection.

---

## Project Status

- **Operational Pipeline:** End-to-end cloud automation with Airflow orchestration running on scheduled cron intervals.
- **Production Data Streams:** Robust, automated streaming of financial and unstructured sentiment data.
- **Live Intelligence:** AI-driven narrative engine ("James") fully integrated, merging quantitative predictions with automated qualitative reasoning.
- **Deployment Validated:** High-performance FastAPI delivery layer is actively listening on Port 8000 of the EC2 public interface, serving real-time JSON packets securely across the web.

---

## Notes for Reviewers

This repository serves as a comprehensive portfolio demonstrating advanced, end-to-end backend data engineering and applied artificial intelligence. It explicitly showcases:

* **Production-Grade Containerization & Isolation:** Full implementation of a multi-container architecture using Docker and Docker Compose. Every moving piece lives in its own secure, isolated network environment.
* **Live Cloud Infrastructure:** Deployed directly onto AWS EC2 with an infrastructure-as-code mindset, completely decoupled from local development environments.
* **Automated Data Pipeline Orchestration:** Practical application of Apache Airflow to schedule, coordinate, and monitor concurrent workflow execution tasks securely.
* **Multi-Source Data Fusion & Analytics:** Automated extraction and normalization of high-velocity financial market telemetry paired with unstructured text parsed via Natural Language Processing (VADER NLP).
* **Hybrid AI Inference & Decision Intelligence:** Integration of an end-to-end Machine Learning pipeline merging a local Random Forest Classifier with the qualitative, context-aware reasoning of Llama-3 (via Groq) to output high-conviction market analyst narratives ("James").
* **Observability & Failsafe Software Engineering:** A production-first design featuring strict error boundaries, optimized database queries, and repository-level secret protection.
