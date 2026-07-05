-- The newest month's raw trips, all three files normalized to one shape.
-- data/latest/ holds a stable-named copy of each service's newest month, so the
-- deep-dive charts read one month cheaply instead of scanning the full history.
-- Rows are clipped to their own median month (TLC files carry a few stray
-- out-of-month timestamps). dol = drop-off location ("do" is reserved).
WITH u AS (
    SELECT 'Yellow cab' AS service, 1 AS ord,
           tpep_pickup_datetime AS pickup, PULocationID AS pu, DOLocationID AS dol
    FROM read_parquet('data/latest/yellow.parquet')
    UNION ALL
    SELECT 'Green cab', 4, lpep_pickup_datetime, PULocationID, DOLocationID
    FROM read_parquet('data/latest/green.parquet')
    UNION ALL
    SELECT CASE hvfhs_license_num WHEN 'HV0003' THEN 'Uber'
                                  WHEN 'HV0005' THEN 'Lyft'
                                  ELSE 'Other' END,
           CASE hvfhs_license_num WHEN 'HV0003' THEN 2
                                  WHEN 'HV0005' THEN 3
                                  ELSE 5 END,
           pickup_datetime, PULocationID, DOLocationID
    FROM read_parquet('data/latest/fhvhv.parquet')
),
tm AS (SELECT date_trunc('month', median(pickup)) AS m FROM u)
SELECT u.*
FROM u, tm
WHERE date_trunc('month', u.pickup) = tm.m
