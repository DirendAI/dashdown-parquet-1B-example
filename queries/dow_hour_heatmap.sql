-- When does New York move? All services combined: weekday × hour, newest month.
SELECT hour(pickup) AS hour, dayname(pickup) AS day, COUNT(*) AS trips
FROM ref('latest_union')
GROUP BY hour, day, isodow(pickup)
ORDER BY isodow(pickup), hour
