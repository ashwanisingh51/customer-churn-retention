# Amazon QuickSight calculated fields

Create each field in its stated dataset. Curly braces reference columns. All rates are fractions formatted as percentages. Use the precomputed monthly and cohort marts for reconciliation.

These expressions follow the [AWS aggregate-field guidance](https://docs.aws.amazon.com/quick/latest/userguide/adding-a-calculated-field-analysis.html), [sumIf reference](https://docs.aws.amazon.com/quick/latest/userguide/sumIf-function.html), and [nullIf reference](https://docs.aws.amazon.com/quick/latest/userguide/nullIf-function.html). Live console compilation remains a deployment QA step.

## customers_clean

| Field name | Expression | Format |
|---|---|---|
| Total Customers | distinct_count({customer_id}) | Integer |
| Active Customers | sum({active_flag}) | Integer |
| Churned Customers | sum({churn_flag}) | Integer |
| Cumulative Churn Rate | sum({churn_flag}) / nullIf(count({customer_id}), 0) | Percent |
| Active Customer Share | sum({active_flag}) / nullIf(count({customer_id}), 0) | Percent |
| Current MRR | sum({active_mrr}) | USD |
| ARPU | sum({active_mrr}) / nullIf(sum({active_flag}), 0) | USD |
| Revenue at Risk | sum({revenue_at_risk}) | USD |
| High-Risk Customers | sum({high_risk_flag}) | Integer |
| Average Tenure | avg({tenure_months}) | Months, 1 decimal |
| Average CLV | avg({observed_clv}) | USD |
| Observed Revenue | sum({observed_clv}) | USD |
| Historical Revenue of Active Customers | sumIf({observed_clv}, {active_flag} = 1) | USD |
| Revenue Earned Before Churn | sumIf({observed_clv}, {churn_flag} = 1) | USD |
| High-Value High-Risk MRR | sumIf({active_mrr}, {high_value_flag} = 1 AND {high_risk_flag} = 1) | USD |

Customer-detail columns use raw fields without aggregate formulas. Observed CLV is historical earned revenue; do not label it predicted lifetime value.

## monthly_snapshots

| Field name | Expression |
|---|---|
| Opening Customers | sum({is_active_start}) |
| Closing Customers | sum({is_active_end}) |
| New Customers | sum({new_customer}) |
| Cancellations | sum({churn_event}) |
| Monthly Churn Rate | sum({opening_customer_churn}) / nullIf(sum({is_active_start}), 0) |
| Monthly Retention Rate | (sum({is_active_start}) - sum({opening_customer_churn})) / nullIf(sum({is_active_start}), 0) |
| Month-End MRR | sum({end_mrr}) |
| Earned Revenue | sum({recognized_revenue}) |
| Churned MRR | sum({churned_mrr}) |
| Renewal Rate | sum({renewal_success}) / nullIf(sum({renewal_due}), 0) |
| Net Customer Growth | sum({new_customer}) - sum({churn_event}) |
| Customer Growth Rate | (sum({new_customer}) - sum({churn_event})) / nullIf(sum({is_active_start}), 0) |
| Monthly ARPU | sum({end_mrr}) / nullIf(sum({is_active_end}), 0) |

Group historical charts by snapshot_month (month granularity). For headline monthly KPIs, filter to August 2026 or a single chosen month. Do not sum closing-customer or MRR stocks across the selected date range. Multi-month churn/renewal ratios are weighted customer-month opportunity rates, not unique-customer event probabilities.

## cohort_retention

Heatmap cell: use retention_rate with MAX at exactly cohort_month × cohort_age. Hide totals. Do not substitute zero for null.

For age-1, age-3 and age-6 cards, filter each visual to its stated age and is_observed=1. Then use:

    sum({retained_customers}) / nullIf(sum({cohort_size}), 0)

Use the same expression for age-12 where requested.

## churn_driver_associations

Each visual filters driver to one field, such as engagement_band. Group by category:

    sum({next_month_churns}) / nullIf(sum({exposures}), 0)

Label "Next-month churn rate". Add exposures and next_month_churns to tooltips. Do not relabel these as causal drivers.

## retention_by_dimension

Filter dimension to exactly one of plan_type, contract_type, acquisition_channel or region:

    sum({retained_customers}) / nullIf(sum({eligible_customers}), 0)

This is cohort-age-6 retention among mature customers. It does not respond to unrestricted snapshot-date filters.

## Precomputed fields

Risk components, customer segments, observed CLV, usage decline, monthly acquisition/churn flags and cohort eligibility are computed in Python and verified in SQL. Do not reconstruct their event logic with dashboard row calculations.

For plan_performance, channel_performance and geography_performance, use summed count/revenue numerators and appropriate denominators. Average CLV across groups is sum(observed_revenue)/sum(total_customers), not avg(average_clv).
