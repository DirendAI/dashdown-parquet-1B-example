-- Market share in the newest month.
SELECT service, COUNT(*) AS trips
FROM ref('latest_union')
WHERE service != 'Other'
GROUP BY service, ord
ORDER BY ord
