-- THE big query: every raw trip since 2020 — yellow cab, green cab, Uber,
-- Lyft — normalized in a CTE and grouped to one row per (month, service).
-- No pre-processing: DuckDB reads the TLC Parquet files exactly as published
-- (union_by_name absorbs columns TLC added over the years).
--
-- "tippable" fares: taxi tips are only recorded on card payments; Uber/Lyft
-- tips are always in-app, so there every trip counts.
-- ord pins series order (and colors): Yellow=amber, Uber=blue, Lyft=pink, Green=green.
WITH all_trips AS (
    SELECT strftime(tpep_pickup_datetime, '%Y-%m') AS month,
           'Yellow cab' AS service, 1 AS ord,
           total_amount AS paid, fare_amount AS fare, tip_amount AS tip,
           trip_distance AS miles,
           epoch(tpep_dropoff_datetime - tpep_pickup_datetime) / 60.0 AS minutes,
           payment_type = 1 AS tippable
    FROM read_parquet('data/trips/yellow_tripdata_*.parquet', union_by_name = true)
    WHERE tpep_pickup_datetime >= DATE '2020-01-01'
      AND tpep_pickup_datetime < date_trunc('month', current_date)

    UNION ALL

    SELECT strftime(lpep_pickup_datetime, '%Y-%m'),
           'Green cab', 4,
           total_amount, fare_amount, tip_amount, trip_distance,
           epoch(lpep_dropoff_datetime - lpep_pickup_datetime) / 60.0,
           payment_type = 1
    FROM read_parquet('data/trips/green_tripdata_*.parquet', union_by_name = true)
    WHERE lpep_pickup_datetime >= DATE '2020-01-01'
      AND lpep_pickup_datetime < date_trunc('month', current_date)

    UNION ALL

    SELECT strftime(pickup_datetime, '%Y-%m'),
           CASE hvfhs_license_num WHEN 'HV0003' THEN 'Uber' ELSE 'Lyft' END,
           CASE hvfhs_license_num WHEN 'HV0003' THEN 2 ELSE 3 END,
           COALESCE(base_passenger_fare, 0) + COALESCE(tolls, 0) + COALESCE(bcf, 0)
             + COALESCE(sales_tax, 0) + COALESCE(congestion_surcharge, 0)
             + COALESCE(airport_fee, 0) + COALESCE(tips, 0),
           base_passenger_fare, tips, trip_miles, trip_time / 60.0,
           true
    FROM read_parquet('data/trips/fhvhv_tripdata_*.parquet', union_by_name = true)
    WHERE pickup_datetime >= DATE '2020-01-01'
      AND pickup_datetime < date_trunc('month', current_date)
      AND hvfhs_license_num IN ('HV0003', 'HV0005')
)
SELECT
    month, service, ord,
    COUNT(*)                                                              AS trips,
    ROUND(SUM(paid), 0)                                                   AS revenue,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY month), 2)  AS share_pct,
    ROUND(AVG(fare)    FILTER (fare BETWEEN 0.01 AND 500), 2)             AS avg_fare,
    ROUND(AVG(miles)   FILTER (miles BETWEEN 0.01 AND 100), 2)            AS avg_miles,
    ROUND(AVG(minutes) FILTER (minutes BETWEEN 1 AND 180), 1)             AS avg_minutes,
    ROUND(100.0 * SUM(tip)  FILTER (tippable AND fare > 0)
                / SUM(fare) FILTER (tippable AND fare > 0), 1)            AS tip_pct
FROM all_trips
GROUP BY month, service, ord
-- raw TLC files carry a handful of mis-dated rows (even future years);
-- a real month/service never has fewer than ~10k trips, junk months have ~1
HAVING COUNT(*) >= 1000
ORDER BY month, ord
