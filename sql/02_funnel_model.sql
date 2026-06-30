DROP VIEW IF EXISTS user_funnel;
CREATE VIEW user_funnel AS
WITH event_flags AS (
    SELECT
        user_id,
        MAX(event_name = 'session_start') AS started_session,
        MAX(event_name = 'product_view') AS viewed_product,
        MAX(event_name = 'add_to_cart') AS added_to_cart,
        MAX(event_name = 'purchase') AS purchased
    FROM events
    GROUP BY user_id
)
SELECT
    u.user_id,
    u.acquisition_channel,
    u.device,
    u.country,
    a.variant,
    e.started_session,
    e.viewed_product,
    e.added_to_cart,
    e.purchased,
    COALESCE(o.revenue, 0) AS revenue
FROM users u
JOIN assignments a USING (user_id)
JOIN event_flags e USING (user_id)
LEFT JOIN (
    SELECT user_id, SUM(revenue) AS revenue FROM orders GROUP BY user_id
) o USING (user_id);

DROP VIEW IF EXISTS funnel_summary;
CREATE VIEW funnel_summary AS
SELECT
    variant,
    COUNT(*) AS sessions,
    SUM(viewed_product) AS product_views,
    SUM(added_to_cart) AS carts,
    SUM(purchased) AS purchases,
    ROUND(100.0 * SUM(viewed_product) / COUNT(*), 2) AS session_to_view_pct,
    ROUND(100.0 * SUM(added_to_cart) / NULLIF(SUM(viewed_product), 0), 2) AS view_to_cart_pct,
    ROUND(100.0 * SUM(purchased) / NULLIF(SUM(added_to_cart), 0), 2) AS cart_to_purchase_pct
FROM user_funnel
GROUP BY variant;

