-- Which month is the "latest month", plus its trip count — for the KPI row
-- and the deep-dive section intro.
SELECT
    strftime(median(pickup), '%B %Y') AS label,
    COUNT(*)                          AS trips
FROM ref('latest_union')
