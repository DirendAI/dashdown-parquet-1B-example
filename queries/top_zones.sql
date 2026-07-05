-- Busiest pickup zones in the newest month, all services combined.
SELECT z.Zone AS zone, COUNT(*) AS trips
FROM ref('latest_union') u
JOIN zones z ON u.pu = z.LocationID
WHERE z.Borough NOT IN ('Unknown', 'N/A')
GROUP BY z.Zone
ORDER BY trips DESC
LIMIT 12
