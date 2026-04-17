CREATE TABLE IF NOT EXISTS signals_live (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    prediction_label VARCHAR(10),
    confidence_score FLOAT,
    james_narrative TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_symbol ON signals_live (symbol, created_at DESC); 