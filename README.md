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


To achieve this, the system follows a **decision-intelligence pipeline**, combining **multi-source data ingestion, metrics computation, and AI reasoning**, rather than merely collecting data.

---

## High-Level Architecture

**Current Layers:**

1. Market Data Acquisition (CoinGecko)  
2. Social Data Acquisition (Reddit public endpoints)  
3. Ingestion & Normalization (PostgreSQL), Optimized for AI feature engineering and     cloud-readiness.  
4. Metrics & Signal Computation  

5. AI Insight & Recommendation Engine 

6. fully containerized, multi-service Docker architecture that is completely environment-agnostic and 100% ready for immediate cloud deployment.

**Planned/Next Evolution:**

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

---

### ✅ Layer 4 – Metrics & Feature Engineering (Optimized)
- Feature Store: Implemented ml_features as the centralized "Source of Truth" for all downstream intelligence.

- Real-Time Momentum: Engineered 5-minute and 15-minute price momentum and trend signals to capture micro-volatility.

- Synchronized Orchestration: Market and Social DAGs are now cross-aligned in Airflow to ensure data freshness every 5 minutes.

- All ingestion pipelines have been migrated from MySQL to PostgreSQL. This enables advanced indexing for AI training sets and ensures compatibility with production-grade cloud environments. Orchestration is fully handled via Airflow.*



  

---






### ✅ Layer 5 – AI Insight & Recommendation Engine ("James")
- Hybrid Intelligence: Merged a Random Forest Classifier (Probability/Quant) with Llama-3 via Groq (Narrative/Analyst).


- Context-Aware Reasoning: The system now distinguishes between "Neutral Social Sentiment" and "Missing Social Data," ensuring the AI doesn't hallucinate during low-volume periods.

- Predictive Certainty: Every insight is accompanied by a mathematical confidence score (e.g., "82% Probability of UP").

- FastAPI Integration: Developed a RESTful API (api.py) that serves real-time JSON packets to the KoinStrap mobile application.

---




### ✅ layer 6 -  Containerization with Docker for deployment to AWS/GCP.


---

## System Capabilities & Demonstrations

- End-to-End Data Pipeline Design: Architecture spanning from raw ingestion to live mobile delivery.

- Multi-Source Ingestion: Automated fetching and normalization of market data (CoinGecko) and high-velocity social signals (Reddit).

- Feature Engineering & ML Inference: Real-time computation of momentum metrics and sentiment scores, serving as inputs for a Random Forest Predictive Brain.

- Hybrid AI Narrative Engine: Integration of quantitative ML predictions with qualitative LLM reasoning (Llama-3.3 via Groq) to produce "James," a human-readable market analyst.

- Production API Layer: High-performance FastAPI implementation for standardized JSON data exchange with external mobile and web applications.

- Infrastructure & Networking: Advanced WSL2-to-Windows PortProxy configuration, enabling secure public access to internal Linux-hosted services.

- Automation & Orchestration: Fully scheduled operations via Apache Airflow, ensuring 5-minute data freshness and decision consistency.

- Observability & Reliability: Integrated logging, PostgreSQL transaction safety, and repository-level Secret Protection (push security).

- Containerization with Docker for deployment to AWS/GCP.

- Cloud-Ready Modular Python: Decoupled design following production standards, ready for Dockerization and AWS/GCP deployment.

---

## Project Status

- Operational Pipeline: End-to-end automation with local + Airflow orchestration running at 5-minute intervals.

- Production Data Streams: Robust, automated ingestion of CoinGecko (Financial) and Reddit (Sentiment) data.

- Live Intelligence: AI-driven narrative engine ("James") fully integrated, merging Random Forest predictions with Llama-3 reasoning.

- Deployment Ready: High-performance FastAPI delivery layer is active, serving JSON insights via a secure WSL2-to-Public-IP network bridge.

- Production-Ready & Cloud-Ready
KoinStrap has been completely evolved from a local python prototype into a **fully containerized, multi-service data architecture**. By decoupling the infrastructure into isolated microservices using **Docker** and **Docker Compose**, the platform is completely self-contained, environment-agnostic, and **100% ready for immediate cloud deployment.**


---

## Next Steps


- Cloud deployment (AWS/GCP/Azure)







## Notes for Reviewers

This repository serves as a comprehensive portfolio demonstrating advanced, end-to-end backend data engineering and applied artificial intelligence. It explicitly showcases:

* **Production-Grade Containerization & Isolation:** Full implementation of a multi-container architecture using Docker and Docker Compose. Every moving piece—the API, the database warehouse, and the automation layers—lives in its own secure, isolated network environment, completely eliminating local setup discrepancies.
* **100% Cloud-Ready Infrastructure:** A modern, infrastructure-as-code mindset. Because the entire ecosystem is packaged into a unified configuration, the platform is fully decoupled from local hardware and architected for immediate deployment to an enterprise cloud provider (AWS EC2 or a DigitalOcean Droplet) with a single command.
* **Automated Data Pipeline Orchestration:** Practical application of Apache Airflow to schedule, coordinate, and monitor concurrent data ingestion flows at strict 5-minute intervals, guaranteeing complete data freshness for predictive models.
* **Multi-Source Data Fusion & Analytics:** Automated extraction and normalization of high-velocity financial market telemetry (CoinGecko API) paired with unstructured public social sentiment data parsed via Natural Language Processing (VADER NLP).
* **Hybrid AI Inference & Decision Intelligence:** Integration of an end-to-end Machine Learning pipeline. The platform merges the quantitative precision of a local Random Forest Classifier with the qualitative, context-aware reasoning of Llama-3 (via Groq) to output high-conviction market analyst narratives ("James").
* **Observability & Failsafe Software Engineering:** A production-first design featuring strict error boundaries (pipelines fail loudly rather than swallowing bad data), optimized database session pooling to reduce connection overhead, and robust repository-level secret protection.
* **Continuous, Modular Evolution:** A living engineering project showcasing an incremental journey from loose local development scripts into a resilient, automated, and secure microservice platform.