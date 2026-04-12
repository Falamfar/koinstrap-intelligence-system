CREATE TABLE social_sentiment_metrics (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    post_count INT,
    avg_sentiment NUMERIC,
    positive_ratio NUMERIC,
    negative_ratio NUMERIC,
    neutral_ratio NUMERIC,
    change_in_count INT, 
    change_in_count_pct NUMERIC,
    change_in_sentiment NUMERIC,
    change_in_sentiment_pct NUMERIC,
    source VARCHAR(50) DEFAULT 'reddit',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (symbol, window_start)
);