-- The daily pulse: trips by hour of day, per service, newest month.
SELECT hour(pickup) AS hour, service, COUNT(*) AS trips
FROM ref('latest_union')
WHERE service != 'Other'
GROUP BY hour, service, ord
ORDER BY hour, ord
