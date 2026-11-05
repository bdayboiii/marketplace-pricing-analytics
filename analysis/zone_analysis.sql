-- 1. ZONE-LEVEL SUPPLY-DEMAND ANALYSIS

WITH demand AS (
    SELECT
        zone_id,
        SUM(search_sessions) AS total_searches,
        SUM(ride_requests) AS total_requests,
        AVG(ride_requests::NUMERIC) AS avg_hourly_requests
    FROM demand_observations
    GROUP BY zone_id
),

supply AS (
    SELECT
        zone_id,
        AVG(available_drivers::NUMERIC) AS avg_available_drivers,
        SUM(available_drivers) AS total_driver_observations
    FROM supply_observations
    GROUP BY zone_id
)

SELECT
    c.city_name,
    z.zone_name,

    d.total_searches,
    d.total_requests,

    ROUND(d.avg_hourly_requests, 2)
        AS avg_hourly_requests,

    ROUND(s.avg_available_drivers, 2)
        AS avg_available_drivers,

    ROUND(
        d.avg_hourly_requests /
        NULLIF(s.avg_available_drivers, 0),
        3
    ) AS demand_supply_ratio

FROM zones z

JOIN cities c
    ON z.city_id = c.city_id

JOIN demand d
    ON z.zone_id = d.zone_id

JOIN supply s
    ON z.zone_id = s.zone_id

ORDER BY demand_supply_ratio DESC;
