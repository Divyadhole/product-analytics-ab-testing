DROP VIEW IF EXISTS experiment_summary;
CREATE VIEW experiment_summary AS
SELECT
    variant,
    COUNT(*) AS users,
    SUM(purchased) AS purchasers,
    ROUND(1.0 * SUM(purchased) / COUNT(*), 4) AS conversion_rate,
    ROUND(SUM(revenue), 2) AS revenue,
    ROUND(SUM(revenue) / COUNT(*), 2) AS revenue_per_user,
    ROUND(SUM(revenue) / NULLIF(SUM(purchased), 0), 2) AS average_order_value
FROM user_funnel
GROUP BY variant;

DROP VIEW IF EXISTS segment_results;
CREATE VIEW segment_results AS
SELECT
    device,
    variant,
    COUNT(*) AS users,
    SUM(purchased) AS purchasers,
    ROUND(100.0 * SUM(purchased) / COUNT(*), 2) AS conversion_pct,
    ROUND(SUM(revenue) / COUNT(*), 2) AS revenue_per_user
FROM user_funnel
GROUP BY device, variant
ORDER BY device, variant;

DROP VIEW IF EXISTS daily_experiment_results;
CREATE VIEW daily_experiment_results AS
SELECT
    DATE(a.assigned_at) AS experiment_date,
    a.variant,
    COUNT(*) AS assigned_users,
    SUM(f.purchased) AS purchasers,
    ROUND(100.0 * SUM(f.purchased) / COUNT(*), 2) AS conversion_pct,
    ROUND(SUM(f.revenue) / COUNT(*), 2) AS revenue_per_user
FROM assignments a
JOIN user_funnel f USING (user_id)
GROUP BY DATE(a.assigned_at), a.variant
ORDER BY experiment_date, a.variant;

DROP VIEW IF EXISTS acquisition_results;
CREATE VIEW acquisition_results AS
SELECT
    acquisition_channel,
    variant,
    COUNT(*) AS users,
    SUM(purchased) AS purchasers,
    ROUND(100.0 * SUM(purchased) / COUNT(*), 2) AS conversion_pct,
    ROUND(SUM(revenue) / COUNT(*), 2) AS revenue_per_user
FROM user_funnel
GROUP BY acquisition_channel, variant
ORDER BY acquisition_channel, variant;
