-- Day-by-day trips in the newest month, per service.
SELECT strftime(pickup, '%Y-%m-%d') AS day, service, COUNT(*) AS trips
FROM ref('latest_union')
WHERE service != 'Other'
GROUP BY day, service, ord
ORDER BY day, ord
