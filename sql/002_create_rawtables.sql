Use Koinstrap;

CREATE TABLE raw_crypto_market_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(10),
    name VARCHAR(50),
    price_usd DECIMAL(18,8),
    volume_24h_usd DECIMAL(18,8),
    observed_at DATETIME
    );