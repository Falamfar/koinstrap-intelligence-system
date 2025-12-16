# koinstrap-decision-intelligence-system


## Project Overview

KoinStrap Intelligence Decision System is a hybrid data and cloud engineering platform designed to support strategic decision-making for cryptocurrency operations. 

The system is built with modular architecture, enabling scalable integration of multiple data sources, including:

- External market data (CoinGecko, Twitter)  
- Internal business data (transactions, user behavior, operational metrics)  
- Structured data pipelines for normalization and storage  
- Analytics and business intelligence dashboards for informed decision-making  

This layered approach ensures flexibility, traceability, and the ability to extend the system over time.

---

## System Architecture & Layers

Layer 1 → Data Acquisition (External APIs: CoinGecko, Twitter)
↓
Layer 3 → Raw Data Storage (Immutable JSON files, timestamped)
↓
Layer 2 → Ingestion & Normalization (Clean, structured tables)
↓
Layer 4 → Analytics & Decision Support (Dashboards, reports)


**Note:** Layers are implemented modularly to allow future integration of internal data and advanced analytics.

---

## Project Structure

koinstrap/
├── data/
│ ├── raw/
│ │ └── coingecko/ # Layer 3 raw JSON
│ │ └── backup/ # old fetch backups
│ ├── processed/
│ │ └── coingecko/ # Layer 2 structured CSVs
├── scripts/
│ ├── coingecko_fetch.py # Layer 1: External Data Module
│ └── coingecko_ingest.py # Layer 2: Ingestion & Normalization Module
├── .env # API keys (not committed)
├── requirements.txt
└── README.md


---

## Current Progress

- ✅ Layer 1: Successfully fetched BTC and ETH data from CoinGecko  
- ✅ Raw JSON stored in `data/raw/coingecko/`  
- ✅ Layer 2: Ingestion script prepared for normalization (CSV output ready)  
- Git repository initialized with `.gitignore` to exclude raw data and secrets  

---

## Next Steps

- Integrate Twitter data into the pipeline  
- Enhance Layer 2 ingestion to accommodate multiple data sources  
- Begin building analytics and decision support dashboards  
- Integrate internal KoinStrap business data  

---

## Environment Variables

- `COINGECKO_API_KEY` required for fetching CoinGecko data  
- Twitter API keys to be added when Layer 1 Twitter integration begins  

---

## Notes for Recruiters

This project demonstrates:

- End-to-end system design  
- Data engineering and cloud engineering skills  
- Modular architecture, layered pipelines, and scalable solutions  
- Professional documentation and workflow with Git version control
