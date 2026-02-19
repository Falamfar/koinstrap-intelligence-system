CREATE TABLE social_sentiment_metrics(
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    window_start DATETIME NOT NULL,
    window_end DATETIME NOT NULL,
    post_count INT NOT NULL,
    avg_sentiment FLOAT,
    positive_ratio FLOAT,
    negative_ratio FLOAT,
    neutral_ratio FLOAT,
    change_in_count INT, 
    change_in_count_pct FLOAT,
    change_in_sentiment FLOAT,
    change_in_sentiment_pct FLOAT,
    source VARCHAR(50) DEFAULT 'reddit',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (symbol, window_start)
); 
