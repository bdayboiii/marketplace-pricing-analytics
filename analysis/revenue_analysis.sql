-- PRICING EXPERIMENT: ACTUAL REVENUE AND RIDE OUTCOMES

WITH experiment_totals AS (
    SELECT
        experiment_group,
        SUM(search_sessions) AS total_searches,
        SUM(ride_requests) AS total_requests
    FROM demand_observations
    GROUP BY experiment_group
),

ride_outcomes AS (
    SELECT
        d.experiment_group,

        COUNT(r.ride_id) AS total_ride_records,

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

    LEFT JOIN rides r
        ON r.pickup_zone_id = d.zone_id
        AND DATE_TRUNC('hour', r.request_time) = d.observation_time

    GROUP BY d.experiment_group
)

SELECT
    e.experiment_group,
    e.total_searches,
    e.total_requests,

    r.completed_rides,
    r.customer_cancellations,
    r.driver_cancellations,
    r.unfulfilled_requests,

    ROUND(
        100.0 * r.completed_rides /
        NULLIF(e.total_requests, 0), 2
    ) AS completion_rate,

    ROUND(
        100.0 * r.customer_cancellations /
        NULLIF(e.total_requests, 0), 2
    ) AS customer_cancellation_rate,

    ROUND(
        100.0 * r.driver_cancellations /
        NULLIF(e.total_requests, 0), 2
    ) AS driver_cancellation_rate,

    ROUND(
        100.0 * r.unfulfilled_requests /
        NULLIF(e.total_requests, 0), 2
    ) AS unfulfilled_rate,

    ROUND(r.actual_revenue::NUMERIC, 2)
        AS actual_revenue,

    ROUND(r.avg_completed_fare::NUMERIC, 2)
        AS avg_completed_fare,

    ROUND(
        r.actual_revenue / NULLIF(e.total_searches, 0),
        2
    ) AS revenue_per_search

FROM experiment_totals e
JOIN ride_outcomes r
    ON e.experiment_group = r.experiment_group

ORDER BY e.experiment_group;
