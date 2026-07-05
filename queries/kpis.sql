-- Headline numbers, straight off the raw files in data/trips/.
-- COUNT(*) and the byte totals come from Parquet footers, so this is fast
-- even though it "covers" every row.
WITH files AS (
    SELECT COUNT(DISTINCT file_name)                                        AS files,
           ROUND(SUM(total_compressed_size) / 1e9, 1)                       AS gb,
           COUNT(DISTINCT regexp_extract(file_name, '[0-9]{4}-[0-9]{2}'))   AS months
    FROM parquet_metadata('data/trips/*.parquet')
),
counts AS (
    SELECT COUNT(*) AS trips
    FROM read_parquet('data/trips/*.parquet', union_by_name = true)
)
SELECT counts.trips, files.files, files.gb, files.months
FROM counts, files
