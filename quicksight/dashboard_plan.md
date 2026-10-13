# Five-sheet dashboard specification

Canvas: tiled 16:9, white background, dark navy headings, blue trends, teal retention, amber medium risk, rose high risk. Use 8–12 px spacing, readable 12–14 pt labels, USD currency, one decimal on display percentages and exact values in tooltips. No decorative charts. A static local preview is available at ../outputs/dashboard_preview.html.

Create an analysis named **Customer Churn & Retention Analytics**. Data and formulas are specified in dataset_mapping.md and calculated_fields.md. Default reporting month: August 2026. Current-state visuals are labeled **As of 31 Aug 2026**. The preview is not an AWS-published dashboard.

## Sheet 1 — Executive Overview

Top row: 8 KPI cards in two rows of four.

| Visual | Dataset and field wells | Scope |
|---|---|---|
| Total Customers | customers_clean; distinct_count(customer_id) | Current population |
| Active Customers | customers_clean; SUM(active_flag) | Current |
| Monthly Churn Rate | monthly_snapshots; opening churn / opening customers | Single reporting month |
| Monthly Retention Rate | monthly_snapshots; retained opening / opening customers | Single reporting month |
| Current MRR | customers_clean; SUM(active_mrr) | Current |
| Revenue at Risk | customers_clean; SUM(revenue_at_risk) | Current |
| Average Tenure | customers_clean; AVG(tenure_months) | Current population |
| High-Risk Customers | customers_clean; SUM(high_risk_flag) | Current |
| Monthly churn trend | Line; snapshot_month X, Monthly Churn Rate Y | Trend date range |
| Monthly retention trend | Line; snapshot_month X, Monthly Retention Rate Y | Trend date range |
| Active vs churned | Horizontal bar; customer_status category, distinct customer count | Current |
| Revenue trend | Line; snapshot_month X, SUM(end_mrr) Y; earned revenue separate series with clear labels if used | Monthly marks |
| Net customer growth | Column; snapshot_month X, Net Customer Growth Y | Monthly flow |

Controls: trend date range; plan, region, acquisition channel, contract type for customer and snapshot visuals. A separate single-month control handles monthly KPI cards. Do not use a date-range sum of MRR.

## Sheet 2 — Churn Drivers

Main comparisons use churn_driver_associations. Each chart has category on the category axis and SUM(next_month_churns)/SUM(exposures) on the value axis, sorted descending, with exposures and churn events in tooltips. Use one driver filter per chart.

| Chart title | driver filter |
|---|---|
| Next-month churn by plan | plan_type |
| Next-month churn by contract | contract_type |
| Next-month churn by payment method | payment_method |
| Next-month churn by payment failures | payment_failures |
| Next-month churn by support tickets | support_ticket_band |
| Next-month churn by usage | usage_band |
| Next-month churn by engagement | engagement_band |
| Next-month churn by acquisition channel | acquisition_channel |
| Next-month churn by geography | region |
| Next-month churn by tenure | tenure_band |

Use horizontal bars in a two-column grid. Keep percentage axes starting at zero and consistent where practical. Label feature window September 2024–July 2026; outcomes October 2024–August 2026. Explain that the same customer can contribute several monthly exposures. These unadjusted associations are not causal effects. Do not apply current customer or date controls to the aggregate driver mart.

## Sheet 3 — Customer Segments & Risk

Use customers_clean, except auditable component detail may use customer_risk_scores separately.

| Visual | Field wells / filter |
|---|---|
| Customers by risk band | Bar; risk_band category, distinct customer count; active_flag=1 |
| MRR by risk band | Bar; risk_band, SUM(active_mrr); active_flag=1 |
| Customer segment distribution | Horizontal bar; customer_segment, distinct customer count |
| CLV by segment | Bar; customer_segment, AVG(observed_clv); show group count |
| High-value at-risk customers | KPI; distinct customer count; active=1, high_value=1, high_risk=1 |
| Engagement vs cumulative churn | Bar; engagement_band, cumulative churn rate; title states latest observation |
| Usage vs cumulative churn | Bar; usage_band, cumulative churn rate; title states latest observation |
| Support tickets vs risk | Bar; support_ticket_band, AVG(risk_score); active=1 |
| Customer detail | Table; customer_id, plan_type, monthly_revenue, tenure_months, risk_score, risk_band, engagement_score, observed_clv, customer_status |

Detail defaults to active=1, sorted monthly_revenue descending then risk_score descending. Enable risk-band and segment filters and a customer search. Color risk status cells; keep text visible without relying only on color. Medium risk is not silently labeled low risk.

## Sheet 4 — Retention & Cohorts

| Visual | Dataset and field wells |
|---|---|
| Cohort survival heatmap | cohort_retention; rows cohort_month, columns cohort_age, MAX(retention_rate) |
| Month 1 retention | cohort_retention; cohort_age=1 and is_observed=1; SUM(retained_customers)/SUM(cohort_size) |
| Month 3 retention | Same, age=3 |
| Month 6 retention | Same, age=6 |
| Month 12 retention | Same, age=12 |
| Age-6 retention by plan | retention_by_dimension; dimension=plan_type; category, SUM(retained_customers)/SUM(eligible_customers) |
| Age-6 retention by channel | Same with acquisition_channel |
| Age-6 retention by contract | Same with contract_type |
| Retention by tenure | churn_driver_associations; driver=tenure_band; 1 − SUM(next_month_churns)/SUM(exposures) |
| Monthly retention | monthly_snapshots; snapshot_month, Monthly Retention Rate |

Heatmap: use a pivot table if explicit numeric cells and conditional formatting are preferred. Row field cohort_month, column field cohort_age, value MAX(retention_rate); percent formatting; low-to-high light-to-dark fill; fixed 0–1 scale; hide row/column totals. Future values remain blank with neutral background. Month 0 is actual month-end survival, not an artificial 100%.

Controls: cohort range and cohort age for heatmap. Do not apply age filter to the separate fixed-age cards. Fixed-horizon dimension charts and historical monthly retention have separate labeled scopes.

## Sheet 5 — Revenue & Retention Opportunity

| Visual | Dataset and fields |
|---|---|
| MRR at risk | customers_clean; SUM(revenue_at_risk) |
| Latest churned MRR | monthly_snapshots; SUM(churned_mrr), reporting month only |
| Revenue earned before churn | customers_clean; SUMIF(observed_clv, churn_flag=1) using the documented QuickSight formula |
| High-value churned customers | Table; customer_id, churn_date, monthly_revenue, observed_clv; churn_flag=1, high_value_flag=1 |
| MRR by segment | Bar; customer_segment, SUM(active_mrr) |
| CLV vs risk | Scatter; X risk_score, Y observed_clv, color risk_band, group customer_id; active=1 |
| Plan revenue vs churn | Combo/bar; plan_performance; plan_type, active_mrr and churned/total customers; axes explicitly labeled |
| Channel revenue vs churn | Same with channel_performance/acquisition_channel |
| Retention priority matrix | Pivot; high_value_flag rows, risk_band columns; customer count and SUM(active_mrr), active=1 |
| Priority summary | Bar/table; retention_priority, SUM(active_mrr), distinct customer count |

Use monthly_revenue, not future CLV, for the value threshold. Show the high-risk column separately from low and medium. The descriptive matrix can summarize low/medium together but must keep that exact label.

## Interactions and acceptance

Select a risk band to filter the customer detail table within the same customer dataset; select a customer segment to filter customer-level visuals. Use explicit reset controls. Do not filter the cohort matrix using a current-state segment because it changes the cohort denominator in a misleading way.

Use full numbers in tooltips, reporting period in titles, and numerator/denominator notes for rates. Validate every published sheet with dashboard_qa_checklist.md and test it as a viewer.
