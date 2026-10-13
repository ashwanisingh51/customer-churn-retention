# Amazon QuickSight dataset mapping

The authoritative machine-readable schema and row counts are in [dataset_contracts.json](dataset_contracts.json); every column is documented in [../DATA_DICTIONARY.md](../DATA_DICTIONARY.md).

| Dataset | Key / grain | Use and aggregation |
|---|---|---|
| customers_clean | customer_id | Current KPIs, segments, risk, detail table; one customer |
| monthly_snapshots | customer_id + snapshot_month | Filterable historical trends; one exposed customer-month |
| customer_segments | customer_id | Standalone subset of current customer attributes |
| customer_risk_scores | customer_id | Standalone customer view with risk components |
| monthly_churn_kpis | month | Overall monthly QA reference; no plan/region/channel dimensions |
| monthly_retention_kpis | month | Overall retention/renewal QA reference |
| cohort_retention | cohort_month + cohort_age | Survival heatmap; future outcomes null |
| plan_performance | plan_type | Current aggregate QA and plan comparison |
| channel_performance | acquisition_channel | Current aggregate QA and channel comparison |
| geography_performance | region | Current aggregate QA and region comparison |
| revenue_churn_impact | month | Overall MRR bridge and recognized revenue |
| support_usage_analysis | support_ticket_band + usage_band | Latest-observation descriptive grouping |
| churn_driver_associations | driver + category | Prior-month signals and next-month outcomes |
| retention_by_dimension | dimension + category | Age-6 survival among eligible cohorts |

## Safe joins and deliberate separation

The main analysis can use customers_clean and monthly_snapshots independently; both already contain needed customer dimensions. No joins are required for the default dashboard.

customers_clean ↔ customer_segments or customer_risk_scores is one-to-one on customer_id, but the extra tables duplicate many columns. Prefer the complete customers_clean dataset and use the supporting exports for auditing.

If genuinely needed, monthly_snapshots → a dimension containing only customer_id and stable attributes is many-to-one. Validate key uniqueness and unchanged snapshot row count. Never bring current risk, final churn flags, final tenure or final CLV into historical sums or historical predictive features. Current master attributes may reflect later repairs; use snapshot attributes for historical analysis.

Aggregate marts remain separate. Joining a plan total to every customer in the plan repeats the total. Joining cohort retention to customers multiplies each customer by cohort ages. Joining customer-months to another customer-month table on customer_id alone produces many-to-many duplication. Unique-customer counts cannot repair duplicated revenue.

For any optional join, compare rows, distinct customer IDs, recognized revenue and MRR by month before/after the join. Use SQL/Python validated totals as controls.

## Filter scope contract

- Plan, region, acquisition channel and contract controls may target visuals on customers_clean and monthly_snapshots, where those fields exist.
- Date controls on historical charts use snapshot_month. Current customer cards remain explicitly labeled "As of 31 Aug 2026"; a trend date filter must not pretend to recompute historical current-risk scores.
- For monthly churn/retention KPI cards, use one reporting month only. A multi-month selection produces an exposure-weighted rate, not a distinct-customer period churn rate.
- Overall monthly aggregate marts cannot respond to plan/region/channel controls. Use monthly_snapshots for filterable trends and keep the marts as reconciliation references.
- Cohort heatmap controls are cohort_month and cohort_age only. Plan/channel age-6 comparisons use retention_by_dimension with a single dimension filter. There are no cross-dimensional age-6 filters in that mart.
- Each driver visual uses a single driver value in churn_driver_associations. Do not sum exposures across different drivers; the same records appear repeatedly.
- A date filter is not available on pre-aggregated driver comparisons. Clearly label their full September 2024–July 2026 feature window.

## Revenue and count safety

Current MRR: SUM(active_mrr) in customers_clean. Historical MRR: SUM(end_mrr) in monthly_snapshots with exactly one snapshot month per mark. Earned revenue: SUM(recognized_revenue), additive across customer-months. Customer count in a current one-row-per-customer table: distinct_count(customer_id).

Cohort cell values: max(retention_rate) at one cohort/age, with totals hidden. Age-specific KPI: sum(retained_customers)/sum(cohort_size), filtered to one age and observed cells. Never sum cohort_size across ages.

Prioritized customer details use active_flag=1. Churned records have no current risk score.
