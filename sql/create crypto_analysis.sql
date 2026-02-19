CREATE TABLE IF NOT EXISTS crypto_analysis(
    analysis_id INT AUTO_INCREMENT PRIMARY KEY,
    analysis_time DATETIME NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    metric_time_ref DATETIME NOT NULL,
    is_price_spike BOOLEAN DEFAULT FALSE,
    is_trend_reversal BOOLEAN DEFAULT FALSE,
    is_volume_spike BOOLEAN DEFAULT FALSE,
    trend_signal VARCHAR(20),
    confidence_score DECIMAL (5,2),
    notes VARCHAR (255),
    UNIQUE KEY unique_analysis (analysis_time, symbol) 
);    


  