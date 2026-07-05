-- The bottom-of-page table: monthly_by_service minus the internal `ord`
-- series-ordering column (plumbing, not a stat a reader needs).
SELECT month, service, trips, revenue, share_pct,
       avg_fare, avg_miles, avg_minutes, tip_pct
FROM ref('monthly_by_service')
ORDER BY month DESC, ord
