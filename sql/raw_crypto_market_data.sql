CREATE TABLE raw_crypto_market_data (
    id SERIAL PRIMARY KEY,              -- The unique ID for every price check
    symbol VARCHAR(20) NOT NULL,        -- e.g., 'BTC'
    name VARCHAR(100),                  -- e.g., 'Bitcoin'
    price_usd NUMERIC NOT NULL,         -- The actual price at that moment
    volume_24h_usd NUMERIC,             -- Total trading volume
    observed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- When the API gave us this data
);