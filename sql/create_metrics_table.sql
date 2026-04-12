CREATE TABLE crypto_metrics (
    id SERIAL PRIMARY KEY,
    metric_time TIMESTAMP NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    price_usd NUMERIC,
    price_change_5m NUMERIC,
    price_change_15m NUMERIC,
    volume_24h_usd NUMERIC,
    avg_price_1h NUMERIC,
    min_price_1h NUMERIC,
    max_price_1h NUMERIC,
    CONSTRAINT unique_metrics_time_symbol UNIQUE (metric_time, symbol)
);