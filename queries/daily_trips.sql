-- Every single day of the newest month: total trips per day across all
-- services, shaped for a GitHub-style calendar heatmap (one value per date).
SELECT strftime(pickup, '%Y-%m-%d') AS day, COUNT(*) AS trips
FROM ref('latest_union')
WHERE service != 'Other'
GROUP BY day
ORDER BY day
