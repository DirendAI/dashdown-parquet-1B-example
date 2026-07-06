-- The tipping gap, one bar per service. Cabs record tips only on card
-- payments; Uber/Lyft tips are always in-app — a card/in-app comparison,
-- not like-for-like. Averaged over every month in the history via ref(),
-- so it reads the monthly aggregates instead of re-scanning the Parquet.
SELECT service, ROUND(AVG(tip_pct), 1) AS tip_pct
FROM ref('monthly_by_service')
GROUP BY service
ORDER BY tip_pct DESC
