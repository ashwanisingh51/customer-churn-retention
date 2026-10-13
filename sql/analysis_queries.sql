-- Each named query executes independently. Rates are fractions; amounts are USD.

-- name: 01_total_customers
SELECT COUNT(*) AS total_customers FROM customers_clean;

-- name: 02_active_customers
SELECT COUNT(*) AS active_customers FROM customers_clean WHERE subscription_end_date IS NULL;

-- name: 03_churned_customers
SELECT COUNT(*) AS churned_customers FROM customers_clean WHERE subscription_end_date IS NOT NULL;

-- name: 04_overall_churn_rate
SELECT 1.0 * SUM(CASE WHEN subscription_end_date IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) AS cumulative_churn_rate FROM customers_clean;

-- name: 05_monthly_churn_trend
SELECT snapshot_month, SUM(is_active_start) AS opening_customers, SUM(opening_customer_churn) AS opening_churns, 1.0*SUM(opening_customer_churn)/NULLIF(SUM(is_active_start),0) AS churn_rate FROM monthly_snapshots GROUP BY snapshot_month ORDER BY snapshot_month;

-- name: 06_monthly_retention_trend
SELECT snapshot_month, SUM(is_active_start)-SUM(opening_customer_churn) AS retained_opening_customers, 1.0*(SUM(is_active_start)-SUM(opening_customer_churn))/NULLIF(SUM(is_active_start),0) AS retention_rate FROM monthly_snapshots GROUP BY snapshot_month ORDER BY snapshot_month;

-- name: 07_churn_by_plan_type
SELECT plan_type, COUNT(*) AS customers, SUM(churn_flag) AS churned_customers, AVG(churn_flag*1.0) AS cumulative_churn_rate FROM customers_clean GROUP BY plan_type ORDER BY cumulative_churn_rate DESC;

-- name: 08_churn_by_contract_type
SELECT contract_type, COUNT(*) AS customers, SUM(churn_flag) AS churned_customers, AVG(churn_flag*1.0) AS cumulative_churn_rate FROM customers_clean GROUP BY contract_type ORDER BY cumulative_churn_rate DESC;

-- name: 09_churn_by_acquisition_channel
SELECT acquisition_channel, COUNT(*) AS customers, SUM(churn_flag) AS churned_customers, AVG(churn_flag*1.0) AS cumulative_churn_rate FROM customers_clean GROUP BY acquisition_channel ORDER BY cumulative_churn_rate DESC;

-- name: 10_churn_by_region
SELECT region, COUNT(*) AS customers, SUM(churn_flag) AS churned_customers, AVG(churn_flag*1.0) AS cumulative_churn_rate FROM customers_clean GROUP BY region ORDER BY cumulative_churn_rate DESC;

-- name: 11_churn_by_payment_method
SELECT payment_method, COUNT(*) AS customers, SUM(churn_flag) AS churned_customers, AVG(churn_flag*1.0) AS cumulative_churn_rate FROM customers_clean GROUP BY payment_method ORDER BY cumulative_churn_rate DESC;

-- name: 12_churn_by_tenure_band
SELECT tenure_band, COUNT(*) AS customers, SUM(churn_flag) AS churned_customers, AVG(churn_flag*1.0) AS cumulative_churn_rate FROM customers_clean GROUP BY tenure_band ORDER BY cumulative_churn_rate DESC;

-- name: 13_churn_by_support_ticket_band
SELECT support_ticket_band, COUNT(*) AS customers, SUM(churn_flag) AS churned_customers, AVG(churn_flag*1.0) AS cumulative_churn_rate FROM customers_clean GROUP BY support_ticket_band ORDER BY cumulative_churn_rate DESC;

-- name: 14_churn_by_usage_band
SELECT usage_band, COUNT(*) AS customers, SUM(churn_flag) AS churned_customers, AVG(churn_flag*1.0) AS cumulative_churn_rate FROM customers_clean GROUP BY usage_band ORDER BY cumulative_churn_rate DESC;

-- name: 15_churn_by_payment_failures
SELECT payment_failures, COUNT(*) AS customers, SUM(churn_flag) AS churned_customers, AVG(churn_flag*1.0) AS cumulative_churn_rate FROM customers_clean GROUP BY payment_failures ORDER BY cumulative_churn_rate DESC;

-- name: 16_churn_by_engagement_band
SELECT engagement_band, COUNT(*) AS customers, SUM(churn_flag) AS churned_customers, AVG(churn_flag*1.0) AS cumulative_churn_rate FROM customers_clean GROUP BY engagement_band ORDER BY cumulative_churn_rate DESC;

-- name: 17_average_revenue_per_customer
SELECT SUM(active_mrr)/NULLIF(SUM(active_flag),0) AS active_arpu, AVG(observed_clv) AS average_observed_clv FROM customers_clean;

-- name: 18_revenue_lost_to_churn
SELECT snapshot_month, SUM(churned_mrr) AS mrr_removed_at_churn FROM monthly_snapshots GROUP BY snapshot_month ORDER BY snapshot_month;

-- name: 19_clv_by_segment
SELECT customer_segment, COUNT(*) AS customers, AVG(observed_clv) AS mean_observed_clv, SUM(observed_clv) AS observed_revenue FROM customers_clean GROUP BY customer_segment ORDER BY observed_revenue DESC;

-- name: 20_at_risk_customers
SELECT customer_id, plan_type, monthly_revenue, risk_score, risk_band, observed_clv FROM customers_clean WHERE active_flag=1 AND risk_score>60 ORDER BY monthly_revenue DESC, risk_score DESC, customer_id;

-- name: 21_cohort_retention
WITH RECURSIVE ages(age) AS (SELECT 0 UNION ALL SELECT age+1 FROM ages WHERE age<23) SELECT c.acquisition_cohort AS cohort_month, a.age AS cohort_age, COUNT(*) AS cohort_size, CASE WHEN date(c.acquisition_cohort, '+'||a.age||' months') <= date('2026-08-01') THEN SUM(CASE WHEN c.subscription_end_date IS NULL OR c.subscription_end_date > date(c.acquisition_cohort, '+'||(a.age+1)||' months','-1 day') THEN 1 ELSE 0 END) END AS retained_customers FROM customers_clean c CROSS JOIN ages a GROUP BY c.acquisition_cohort,a.age ORDER BY c.acquisition_cohort,a.age;

-- name: 22_renewal_behavior
SELECT contract_type, SUM(renewal_due) AS eligible_renewals, SUM(renewal_success) AS successful_renewals, 1.0*SUM(renewal_success)/NULLIF(SUM(renewal_due),0) AS renewal_rate FROM monthly_snapshots GROUP BY contract_type;

-- name: 23_high_value_churned
SELECT customer_id, plan_type, churn_date, monthly_revenue, observed_clv FROM customers_clean WHERE churn_flag=1 AND high_value_flag=1 ORDER BY observed_clv DESC,customer_id;

-- name: 24_customer_revenue_concentration
WITH ranked AS (SELECT active_mrr, NTILE(10) OVER (ORDER BY active_mrr DESC,customer_id) AS revenue_decile FROM customers_clean WHERE active_flag=1) SELECT revenue_decile,COUNT(*) AS customers,SUM(active_mrr) AS mrr,1.0*SUM(active_mrr)/(SELECT SUM(active_mrr) FROM customers_clean) AS mrr_share FROM ranked GROUP BY revenue_decile ORDER BY revenue_decile;

-- name: 25_high_revenue_high_risk
SELECT customer_id, monthly_revenue, risk_score, customer_segment FROM customers_clean WHERE active_flag=1 AND high_value_flag=1 AND high_risk_flag=1 ORDER BY monthly_revenue DESC,risk_score DESC,customer_id;

-- name: 26_customer_rollforward
SELECT snapshot_month,SUM(is_active_start) AS opening_customers,SUM(new_customer) AS acquired,SUM(churn_event) AS churned,SUM(is_active_end) AS closing_customers,SUM(is_active_start+new_customer-churn_event-is_active_end) AS reconciliation_difference FROM monthly_snapshots GROUP BY snapshot_month ORDER BY snapshot_month;

-- name: 27_mrr_rollforward
SELECT snapshot_month,SUM(start_mrr) AS opening_mrr,SUM(new_mrr) AS new_mrr,SUM(churned_mrr) AS churned_mrr,SUM(end_mrr) AS closing_mrr,ROUND(SUM(start_mrr+new_mrr-churned_mrr-end_mrr),2) AS reconciliation_difference FROM monthly_snapshots GROUP BY snapshot_month ORDER BY snapshot_month;

-- name: 28_revenue_at_risk
SELECT risk_band,COUNT(*) AS active_customers,SUM(monthly_revenue) AS active_mrr FROM customers_clean WHERE active_flag=1 GROUP BY risk_band;

-- name: 29_early_and_long_tenure_churn
SELECT CASE WHEN tenure_months<3 THEN 'Early: under 3 months' WHEN tenure_months>=12 THEN 'Long: 12+ months' ELSE '3-11 months' END AS churn_tenure,COUNT(*) AS churned_customers,SUM(monthly_revenue) AS removed_mrr FROM customers_clean WHERE churn_flag=1 GROUP BY churn_tenure;

-- name: 30_prechurn_revenue
SELECT SUM(s.recognized_revenue) AS revenue_generated_before_churn FROM monthly_snapshots s JOIN customers_clean c ON s.customer_id=c.customer_id WHERE c.churn_flag=1;

-- name: 31_lagged_engagement_association
SELECT CASE WHEN s.engagement_score<35 THEN 'Low' WHEN s.engagement_score<65 THEN 'Medium' ELSE 'High' END AS engagement_band, COUNT(*) AS customer_month_exposures,SUM(CASE WHEN strftime('%Y-%m',c.churn_date)=strftime('%Y-%m',date(s.snapshot_month,'+1 month')) THEN 1 ELSE 0 END) AS next_month_churns FROM monthly_snapshots s JOIN customers_clean c ON s.customer_id=c.customer_id WHERE s.is_active_end=1 AND s.snapshot_month<'2026-08-01' GROUP BY engagement_band;

-- name: 32_cohort_age_six
SELECT dimension,category,eligible_customers,retained_customers,retention_rate FROM retention_by_dimension ORDER BY dimension,retention_rate DESC;

