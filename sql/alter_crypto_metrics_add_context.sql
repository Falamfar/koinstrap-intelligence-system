ALTER TABLE crypto_metrics
ADD COLUMN avg_price_1h DECIMAL(18,8),
ADD COLUMN min_price_1h DECIMAL(18,8),
ADD COLUMN max_price_1h DECIMAL(18,8);
