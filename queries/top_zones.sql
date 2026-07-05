-- Busiest pickup zones in the newest month, all services combined.
-- TLC zone names are long ("Penn Station/Madison Sq West") and get clipped
-- as chart labels, so compound names keep only their first part.
SELECT
    replace(replace(replace(replace(replace(replace(replace(replace(
        CASE z.Zone
            WHEN 'LaGuardia Airport'     THEN 'LaGuardia'
            WHEN 'Upper East Side South' THEN 'UES South'
            WHEN 'Upper East Side North' THEN 'UES North'
            WHEN 'Upper West Side South' THEN 'UWS South'
            WHEN 'Upper West Side North' THEN 'UWS North'
            ELSE split_part(z.Zone, '/', 1)
        END,
        'Washington', 'Wash'), 'Heights', 'Hts'), 'Square', 'Sq'), 'Center', 'Ctr'),
        ' North', ' N'), ' South', ' S'), ' East', ' E'), ' West', ' W') AS zone,
    COUNT(*) AS trips
FROM ref('latest_union') u
JOIN read_parquet('data/history/taxi_zones.parquet') z ON u.pu = z.LocationID
WHERE z.Borough NOT IN ('Unknown', 'N/A')
GROUP BY zone
ORDER BY trips DESC
LIMIT 12
