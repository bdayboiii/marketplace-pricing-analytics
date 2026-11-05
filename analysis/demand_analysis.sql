-- 1. DEMAND ANALYSIS BY CITY

SELECT
    c.city_name,

    SUM(d.search_sessions) AS total_searches,

    SUM(d.ride_requests) AS total_requests,

    ROUND(
        100.0 * SUM(d.ride_requests) /
        NULLIF(SUM(d.search_sessions), 0),
        2
    ) AS request_conversion_rate

FROM demand_observations d

JOIN zones z
    ON d.zone_id = z.zone_id

JOIN cities c
    ON z.city_id = c.city_id

GROUP BY c.city_name

ORDER BY total_requests DESC;


-- 2. DEMAND BY HOUR OF DAY

SELECT
    EXTRACT(HOUR FROM observation_time) AS hour,

    SUM(search_sessions) AS total_searches,

    SUM(ride_requests) AS total_requests,

    ROUND(
        100.0 * SUM(ride_requests) /
        NULLIF(SUM(search_sessions), 0),
        2
    ) AS conversion_rate

FROM demand_observations

GROUP BY hour

ORDER BY total_requests DESC;

-- 3. WEEKDAY VS WEEKEND DEMAND

SELECT
    CASE
        WHEN EXTRACT(ISODOW FROM observation_time) IN (6, 7)
        THEN 'Weekend'
        ELSE 'Weekday'
    END AS day_type,

    SUM(search_sessions) AS total_searches,

    SUM(ride_requests) AS total_requests,

    ROUND(
        AVG(ride_requests::NUMERIC),
        2
    ) AS avg_hourly_requests

FROM demand_observations

GROUP BY day_type;

-- HOURLY SUPPLY-DEMAND IMBALANCE

SELECT
    EXTRACT(HOUR FROM d.observation_time)::INT AS hour,

    SUM(d.ride_requests) AS total_demand,

    SUM(s.available_drivers) AS available_drivers,

    ROUND(
        SUM(d.ride_requests)::NUMERIC /
        NULLIF(SUM(s.available_drivers), 0),
        2
    ) AS demand_supply_ratio

FROM demand_observations d

JOIN supply_observations s
    ON d.observation_time = s.observation_time
    AND d.zone_id = s.zone_id

GROUP BY hour
ORDER BY hour;