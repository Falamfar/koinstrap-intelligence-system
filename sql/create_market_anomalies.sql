CREATE TABLE IF NOT EXISTS market_anomalies(
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    anomaly_type VARCHAR(50) NOT NULL,
    magnitude DECIMAL,
    current_value DECIMAL,
    previous_value DECIMAL,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
); 