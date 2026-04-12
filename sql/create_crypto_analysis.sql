 CREATE TABLE crypto_analysis (
    analysis_id SERIAL PRIMARY KEY,
    analysis_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    symbol VARCHAR(20) NOT NULL,
    metric_time_ref TIMESTAMP,          -- Which 'metric_time' this analysis is for
    is_price_spike BOOLEAN,             -- Postgres uses real BOOLEAN (True/False)
    is_trend_reversal BOOLEAN,
    is_volume_spike BOOLEAN,
    trend_signal VARCHAR(20),
    confidence_score NUMERIC,
    notes TEXT,
    UNIQUE (analysis_time, symbol)      -- Prevents duplicate analysis for the same time
);