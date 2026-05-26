-- ============================================================
-- Neobank Customer Churn Analysis — SQL Portfolio Queries
-- Portfolio Project | Author: Ebinum
-- Dataset: neobank_churn (1,500 customers)
-- ============================================================


-- ── QUERY 1: Overall churn summary ───────────────────────────────────────────
-- Baseline KPIs: total base, churned, retained, overall churn rate

SELECT
    COUNT(*)                                        AS total_customers,
    SUM(churned)                                    AS total_churned,
    COUNT(*) - SUM(churned)                         AS total_retained,
    ROUND(AVG(churned) * 100, 1)                    AS churn_rate_pct,
    ROUND(AVG(avg_monthly_balance_cad), 0)          AS avg_balance_cad,
    ROUND(AVG(tenure_months), 1)                    AS avg_tenure_months
FROM neobank_churn;


-- ── QUERY 2: Churn rate by plan tier ─────────────────────────────────────────
-- Identify which plan segment drives the most churn volume and rate

SELECT
    plan_tier,
    COUNT(*)                                        AS customers,
    SUM(churned)                                    AS churned,
    ROUND(AVG(churned) * 100, 1)                    AS churn_rate_pct,
    ROUND(AVG(avg_monthly_balance_cad), 0)          AS avg_balance_cad,
    ROUND(AVG(num_products), 2)                     AS avg_products_held,
    SUM(churned * monthly_fee_cad)                  AS mrr_lost_cad
FROM neobank_churn
GROUP BY plan_tier
ORDER BY churn_rate_pct DESC;


-- ── QUERY 3: Churn by engagement recency (login buckets) ─────────────────────
-- Segment customers by days since last login to find disengagement threshold

SELECT
    CASE
        WHEN days_since_last_login <= 7  THEN '1. Active (<=7d)'
        WHEN days_since_last_login <= 21 THEN '2. Moderate (8-21d)'
        WHEN days_since_last_login <= 45 THEN '3. Lapsing (22-45d)'
        ELSE                                  '4. Dormant (45d+)'
    END                                             AS login_recency_segment,
    COUNT(*)                                        AS customers,
    SUM(churned)                                    AS churned,
    ROUND(AVG(churned) * 100, 1)                    AS churn_rate_pct,
    ROUND(AVG(monthly_txn_count), 1)                AS avg_monthly_txns
FROM neobank_churn
GROUP BY login_recency_segment
ORDER BY login_recency_segment;


-- ── QUERY 4: Churn by balance trend & plan cross-tab ─────────────────────────
-- Two-dimensional view: balance behaviour × plan tier

SELECT
    plan_tier,
    balance_trend,
    COUNT(*)                                        AS customers,
    SUM(churned)                                    AS churned,
    ROUND(AVG(churned) * 100, 1)                    AS churn_rate_pct
FROM neobank_churn
GROUP BY plan_tier, balance_trend
ORDER BY plan_tier, churn_rate_pct DESC;


-- ── QUERY 5: Tenure cohort churn analysis ────────────────────────────────────
-- Do newer customers churn more? Map churn rate across account age buckets

SELECT
    CASE
        WHEN tenure_months < 6  THEN '1. <6 months'
        WHEN tenure_months < 18 THEN '2. 6-18 months'
        WHEN tenure_months < 36 THEN '3. 18-36 months'
        ELSE                         '4. 36+ months'
    END                                             AS tenure_bucket,
    COUNT(*)                                        AS customers,
    SUM(churned)                                    AS churned,
    ROUND(AVG(churned) * 100, 1)                    AS churn_rate_pct,
    ROUND(AVG(num_products), 2)                     AS avg_products,
    ROUND(AVG(avg_monthly_balance_cad), 0)          AS avg_balance_cad
FROM neobank_churn
GROUP BY tenure_bucket
ORDER BY tenure_bucket;


-- ── QUERY 6: High-risk customer segment ──────────────────────────────────────
-- Identify customers matching multiple churn risk factors simultaneously

SELECT
    customer_id,
    plan_tier,
    tenure_months,
    avg_monthly_balance_cad,
    balance_trend,
    days_since_last_login,
    monthly_txn_count,
    num_products,
    support_contacts_6mo,
    churned
FROM neobank_churn
WHERE
    plan_tier = 'Free'
    AND balance_trend = 'declining'
    AND days_since_last_login > 21
    AND monthly_txn_count < 10
    AND num_products = 1
ORDER BY days_since_last_login DESC, support_contacts_6mo DESC;


-- ── QUERY 7: Referral source churn analysis ───────────────────────────────────
-- Which acquisition channels bring the highest-quality (lowest-churn) customers?

SELECT
    referral_source,
    COUNT(*)                                        AS customers,
    SUM(churned)                                    AS churned,
    ROUND(AVG(churned) * 100, 1)                    AS churn_rate_pct,
    ROUND(AVG(tenure_months), 1)                    AS avg_tenure_months,
    ROUND(AVG(num_products), 2)                     AS avg_products,
    ROUND(AVG(avg_monthly_balance_cad), 0)          AS avg_balance_cad
FROM neobank_churn
GROUP BY referral_source
ORDER BY churn_rate_pct ASC;


-- ── QUERY 8: Product cross-sell vs churn ─────────────────────────────────────
-- Does holding more products materially reduce churn? Quantify the stickiness effect

SELECT
    num_products,
    COUNT(*)                                        AS customers,
    SUM(churned)                                    AS churned,
    ROUND(AVG(churned) * 100, 1)                    AS churn_rate_pct,
    ROUND(AVG(avg_monthly_balance_cad), 0)          AS avg_balance_cad,
    ROUND(AVG(monthly_txn_count), 1)                AS avg_monthly_txns
FROM neobank_churn
GROUP BY num_products
ORDER BY num_products;


-- ── QUERY 9: Support friction analysis ───────────────────────────────────────
-- Does support contact volume predict churn? Find the friction tipping point

SELECT
    CASE
        WHEN support_contacts_6mo = 0 THEN '0 contacts'
        WHEN support_contacts_6mo = 1 THEN '1 contact'
        WHEN support_contacts_6mo = 2 THEN '2 contacts'
        WHEN support_contacts_6mo >= 3 THEN '3+ contacts'
    END                                             AS support_tier,
    COUNT(*)                                        AS customers,
    SUM(churned)                                    AS churned,
    ROUND(AVG(churned) * 100, 1)                    AS churn_rate_pct,
    ROUND(AVG(avg_monthly_balance_cad), 0)          AS avg_balance_cad
FROM neobank_churn
GROUP BY support_tier
ORDER BY support_tier;


-- ── QUERY 10: Regional churn breakdown ───────────────────────────────────────
-- Identify if churn is geographically concentrated

SELECT
    region,
    COUNT(*)                                        AS customers,
    SUM(churned)                                    AS churned,
    ROUND(AVG(churned) * 100, 1)                    AS churn_rate_pct,
    ROUND(AVG(avg_monthly_balance_cad), 0)          AS avg_balance_cad,
    ROUND(AVG(tenure_months), 1)                    AS avg_tenure_months
FROM neobank_churn
GROUP BY region
ORDER BY churn_rate_pct DESC;


-- ── QUERY 11: MRR at risk — rolling retention opportunity ────────────────────
-- Estimate monthly revenue recoverable by reducing churn in paid tiers

SELECT
    plan_tier,
    SUM(churned * monthly_fee_cad)                  AS mrr_lost_cad,
    SUM((1 - churned) * monthly_fee_cad)            AS mrr_retained_cad,
    ROUND(
        SUM(churned * monthly_fee_cad) /
        NULLIF(SUM(monthly_fee_cad), 0) * 100, 1
    )                                               AS pct_mrr_lost
FROM neobank_churn
WHERE plan_tier != 'Free'
GROUP BY plan_tier
ORDER BY mrr_lost_cad DESC;
