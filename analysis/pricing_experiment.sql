
-- ============================================================
-- PRICING EXPERIMENT ANALYSIS
-- Control: 1.00 pricing multiplier
-- Treatment: 1.10 pricing multiplier
-- ============================================================


-- 1. OVERALL EXPERIMENT RESULTS
-- Compare conversion and average quoted fare between groups.

SELECT
    experiment_group,
    COUNT(*) AS observations,
    SUM(search_sessions) AS total_searches,
    SUM(ride_requests) AS total_requests,
    ROUND(
        100.0 * SUM(ride_requests) /
        NULLIF(SUM(search_sessions), 0),
        2
    ) AS conversion_rate,
    ROUND(AVG(average_quoted_fare)::NUMERIC, 2)
        AS avg_quoted_fare,
    ROUND(AVG(pricing_multiplier)::NUMERIC, 2)
        AS avg_pricing_multiplier
FROM demand_observations
GROUP BY experiment_group
ORDER BY experiment_group;


-- 2. ZONE-LEVEL EXPERIMENT RESULTS
-- Compare treatment and control conversion in each zone.

SELECT
    c.city_name,
    z.zone_name,
    d.experiment_group,
    COUNT(*) AS observations,
    SUM(d.search_sessions) AS total_searches,
    SUM(d.ride_requests) AS total_requests,
    ROUND(
        100.0 * SUM(d.ride_requests) /
        NULLIF(SUM(d.search_sessions), 0),
        2
    ) AS conversion_rate,
    ROUND(AVG(d.average_quoted_fare)::NUMERIC, 2)
        AS avg_quoted_fare
FROM demand_observations d
JOIN zones z
    ON d.zone_id = z.zone_id
JOIN cities c
    ON z.city_id = c.city_id
GROUP BY
    c.city_name,
    z.zone_name,
    d.experiment_group
ORDER BY
    c.city_name,
    z.zone_name,
    d.experiment_group;


-- 3. CITY-LEVEL WEIGHTED EXPERIMENT RESULTS
-- Aggregate searches and requests before calculating conversion.
-- This avoids taking a simple average of zone conversion rates.

SELECT
    c.city_name,
    d.experiment_group,
    COUNT(*) AS observations,
    SUM(d.search_sessions) AS total_searches,
    SUM(d.ride_requests) AS total_requests,
    ROUND(
        100.0 * SUM(d.ride_requests) /
        NULLIF(SUM(d.search_sessions), 0),
        2
    ) AS conversion_rate,
    ROUND(AVG(d.average_quoted_fare)::NUMERIC, 2)
        AS avg_quoted_fare,
    ROUND(AVG(d.pricing_multiplier)::NUMERIC, 2)
        AS avg_pricing_multiplier
FROM demand_observations d
JOIN zones z
    ON d.zone_id = z.zone_id
JOIN cities c
    ON z.city_id = c.city_id
GROUP BY
    c.city_name,
    d.experiment_group
ORDER BY
    c.city_name,
    d.experiment_group;
