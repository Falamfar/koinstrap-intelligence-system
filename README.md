# koinstrap-decision-intelligence-system

## Project Overview

KoinStrap Intelligence Decision System is a hybrid data and cloud engineering platform designed to support strategic decision-making for cryptocurrency operations.

The system is built with modular architecture, enabling scalable integration of multiple data sources, including:

- External market data (CoinGecko, Twitter)
- Internal business data (transactions, user behavior, operational metrics)
- Structured data pipelines for normalization and storage in SQL
- Analytics and business intelligence dashboards for informed decision-making

This layered approach ensures flexibility, traceability, and the ability to extend the system over time.

---

## System Architecture & Layers

Layer 1 → Data Acquisition (External APIs: CoinGecko, Twitter)  
↓  
Layer 2 → Ingestion & Normalization (SQL tables, structured)  
↓  
Layer 3 → Analytics & Decision Support (Dashboards, reports)

**Note:** Layers are implemented modularly to allow future integration of internal data and advanced analytics.

---


---

## Current Progress

- ✅ Layer 2: Successfully ingested BTC and ETH market data from CoinGecko into MySQL table `raw_crypto_market_data`  
- ✅ Environment variables for API key and DB credentials configured  
- ✅ Table structure includes: `id`, `symbol`, `name`, `price_usd`, `volume_24h_usd`, `observed_at`  
- ✅ README updated to reflect SQL integration and new ingestion script  
- ✅ Layer 2 ingestion script **v1.2 stabilized** with:
  - Idempotency (prevents duplicate inserts)
  - Data validation (skips invalid records)
  - Transaction safety with rollback
  - Logging of skipped and duplicate records
  - Normalized timestamp for consistent data insertion
- ✅Automated ingestion every 5 minutes via cron job
- ✅Successfully computed metrics from raw_crypto_market_data and stored in crypto_metrics.
- ✅Automated metrics computation every 5 minutes via cron job.
  


---

## Next Steps



- Continue building analytics and decision support dashboards  
- Integrate Twitter data into the pipeline  
- Integrate internal KoinStrap business data  

---

## Changelog / Versioning

- **v1.0 – 2025-12-22**  
  - Added `ingest_coingecko_v1.py` to fetch BTC & ETH market data  
  - Switched storage from raw JSON files to MySQL table `raw_crypto_market_data`  
  - Updated project structure to include `sql/` folder and new table creation script  
  - Updated README to reflect SQL integration  
  - Added environment variables for API key and DB credentials  

- **v1.1 – 2026-01-19**  
  - Implemented idempotency to prevent duplicate inserts  
  - Added data validation for symbol, name, price, and volume  
  - Added transaction safety with rollback on failure  
  - Added logging for skipped/duplicate records  
  - Normalized timestamps to ensure consistent inserts  

---

## Notes for Recruiters

This project demonstrates:

- End-to-end system design  
- Data engineering and cloud engineering skills  
- Professional modular architecture and layered pipelines  
- Versioned workflow with Git and clean documentation  
- Production-ready use of secrets and database integration


