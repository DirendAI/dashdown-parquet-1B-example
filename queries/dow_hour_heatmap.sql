-- When does New York move? All services combined: weekday × hour, newest month.
-- Descending isodow because ECharts draws the first y category at the BOTTOM —
-- this puts Monday at the top, calendar-style.
SELECT hour(pickup) AS hour, dayname(pickup) AS day, COUNT(*) AS trips
FROM ref('latest_union')
GROUP BY hour, day, isodow(pickup)
ORDER BY isodow(pickup) DESC, hour
