CREATE TABLE ml_features(
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20),
    feature_time TIMESTAMP,
    price_usd NUMERIC,
    price_change_5m NUMERIC,
    price_change_15m NUMERIC,
    volume_24h_usd NUMERIC,
    post_count INT,
    avg_sentiment NUMERIC,
    is_price_spike BOOLEAN,
    is_trend_reversal BOOLEAN,
    confidence_score NUMERIC,
    price_up_next_60m INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);    



    