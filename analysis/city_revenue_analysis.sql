-- CITY-LEVEL PRICING EXPERIMENT

-- Aggregate demand independently
WITH city_demand AS (
    SELECT
        c.city_name,
        d.experiment_group,
        SUM(d.search_sessions) AS total_searches,
        SUM(d.ride_requests) AS total_requests
    FROM demand_observations d
    JOIN zones z
        ON d.zone_id = z.zone_id
    JOIN cities c
        ON z.city_id = c.city_id
    GROUP BY
        c.city_name,
        d.experiment_group
),

-- Aggregate ride outcomes independently
city_rides AS (
    SELECT
        c.city_name,
        d.experiment_group,

        COUNT(r.ride_id) FILTER (
            WHERE r.ride_status = 'Completed'
        ) AS completed_rides,

        COUNT(r.ride_id) FILTER (
            WHERE r.ride_status = 'Customer_Cancelled'
        ) AS customer_cancellations,

        COUNT(r.ride_id) FILTER (
            WHERE r.ride_status = 'Driver_Cancelled'
        ) AS driver_cancellations,

        COUNT(r.ride_id) FILTER (
            WHERE r.ride_status = 'Unfulfilled'
        ) AS unfulfilled_requests,

        SUM(r.final_fare) FILTER (
            WHERE r.ride_status = 'Completed'
        ) AS actual_revenue,

        AVG(r.final_fare) FILTER (
            WHERE r.ride_status = 'Completed'
        ) AS avg_completed_fare

    FROM demand_observations d
    JOIN zones z
        ON d.zone_id = z.zone_id
    JOIN cities c
        ON z.city_id = c.city_id
    LEFT JOIN rides r
        ON r.pickup_zone_id = d.zone_id
        AND DATE_TRUNC('hour', r.request_time) = d.observation_time

    GROUP BY
        c.city_name,
        d.experiment_group
)

-- Combine the two independently aggregated datasets
SELECT
    d.city_name,
    d.experiment_group,
    d.total_searches,
    d.total_requests,

    COALESCE(r.completed_rides, 0) AS completed_rides,

    ROUND(
        100.0 * r.completed_rides /
        NULLIF(d.total_requests, 0),
        2
    ) AS completion_rate,

    ROUND(
        100.0 * r.customer_cancellations /
        NULLIF(d.total_requests, 0),
        2
    ) AS customer_cancellation_rate,

    ROUND(
        100.0 * r.driver_cancellations /
        NULLIF(d.total_requests, 0),
        2
    ) AS driver_cancellation_rate,

    ROUND(
        100.0 * r.unfulfilled_requests /
        NULLIF(d.total_requests, 0),
        2
    ) AS unfulfilled_rate,

    ROUND(r.avg_completed_fare::NUMERIC, 2)
        AS avg_completed_fare,

    ROUND(r.actual_revenue::NUMERIC, 2)
        AS actual_revenue,

    ROUND(
        r.actual_revenue /
        NULLIF(d.total_searches, 0),
        2
    ) AS revenue_per_search

FROM city_demand d
LEFT JOIN city_rides r
    ON d.city_name = r.city_name
    AND d.experiment_group = r.experiment_group

ORDER BY
    d.city_name,
    d.experiment_group;
