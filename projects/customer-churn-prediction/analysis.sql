-- SQLite: import sales_clean.csv into a table named sales, or run build_sales.py.
-- Revenue is net of discounts/returns. Cancelled orders contribute zero.
SELECT substr(order_date,1,7) AS month, SUM(net_revenue_ngn) AS net_revenue_ngn,
       SUM(gross_profit_ngn) AS gross_profit_ngn,
       ROUND(100.0*SUM(gross_profit_ngn)/NULLIF(SUM(net_revenue_ngn),0),2) AS gross_margin_pct
FROM sales GROUP BY month ORDER BY month;

SELECT category,SUM(net_revenue_ngn) AS net_revenue_ngn,
       SUM(gross_profit_ngn) AS gross_profit_ngn
FROM sales GROUP BY category ORDER BY net_revenue_ngn DESC;

SELECT channel, COUNT(DISTINCT CASE WHEN status='Completed' THEN order_id END) AS completed_orders,
       SUM(net_revenue_ngn) AS net_revenue_ngn
FROM sales GROUP BY channel ORDER BY net_revenue_ngn DESC;
