-- Add server-calculated rolling return volatility to persisted analytics.
ALTER TABLE analytics_results
    ADD COLUMN IF NOT EXISTS volatility NUMERIC;
