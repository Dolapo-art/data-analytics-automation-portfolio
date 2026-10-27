-- SQLite: import customers_clean.csv as customers (including its header).
-- Cohort description uses observed ChurnFlag; it is not model evaluation.
SELECT Contract, COUNT(*) AS customers, SUM(ChurnFlag) AS churned,
       ROUND(100.0*SUM(ChurnFlag)/COUNT(*),2) AS churn_rate_pct
FROM customers GROUP BY Contract;

SELECT TenureBand, COUNT(*) AS customers, SUM(ChurnFlag) AS churned,
       ROUND(100.0*SUM(ChurnFlag)/COUNT(*),2) AS churn_rate_pct
FROM customers GROUP BY TenureBand;
