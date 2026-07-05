-- Where rides start and end: borough -> borough flows, newest month.
-- The trailing space on the target label keeps origin and destination as
-- distinct sankey nodes (same-name nodes would form cycles).
SELECT pz.Borough AS source, dz.Borough || ' ' AS target, COUNT(*) AS trips
FROM ref('latest_union') u
JOIN zones pz ON u.pu  = pz.LocationID
JOIN zones dz ON u.dol = dz.LocationID
WHERE pz.Borough NOT IN ('Unknown', 'N/A')
  AND dz.Borough NOT IN ('Unknown', 'N/A')
GROUP BY pz.Borough, dz.Borough
ORDER BY trips DESC
