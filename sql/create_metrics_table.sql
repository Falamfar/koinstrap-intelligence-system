CREATE TABLE crypto_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(10),
    metric_time DATETIME,
    price_usd DECIMAL(18,8),
    price_change_5m DECIMAL(18,8),
    price_change_15m DECIMAL(18,8),
    volume_24h_usd DECIMAL(18,8)
);
