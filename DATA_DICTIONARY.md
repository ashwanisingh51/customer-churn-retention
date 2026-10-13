# Data dictionary
All data are synthetic. Reporting cutoff: 2026-08-31. Currency: USD. Rates and discounts are fractions 0-1. Dates are ISO YYYY-MM-DD. Null means unavailable, unobserved or inapplicable, never an inferred zero.
Detailed metric and segmentation definitions: [METRIC_DEFINITIONS.md](METRIC_DEFINITIONS.md).

## channel_performance
One acquisition channel; cumulative outcomes and current MRR.

Key: acquisition_channel. Rows in bundled run: 5.
| Column | Athena view type | Nullable in this run | Meaning |
|---|---|---|---|
| acquisition_channel | varchar | No | Acquisition channel |
| total_customers | bigint | No | Total customers |
| active_customers | bigint | No | Active customers |
| churned_customers | bigint | No | Churned customers |
| active_mrr | double | No | Monthly revenue when currently active, otherwise zero. |
| revenue_at_risk | double | No | Current MRR of active customers with risk score above 60; opportunity size, not expected loss. |
| observed_revenue | double | No | Observed revenue |
| average_clv | double | No | Average clv |
| average_tenure | double | No | Average tenure |
| churn_rate | double | No | Monthly: opening-customer cancellations/opening customers. Customer aggregates: cumulative churned/all customers. |
| retention_rate | double | No | Cohort: retained/cohort size; monthly: retained opening/opening customers; dimension summary: active/total. |
| arpu | double | No | Arpu |

## churn_driver_associations
One driver and category; prior-month exposure linked to next-month cancellations. Different drivers reuse exposures.

Key: driver, category. Rows in bundled run: 9,761.
| Column | Athena view type | Nullable in this run | Meaning |
|---|---|---|---|
| driver | varchar | No | Driver |
| category | varchar | Yes | Category |
| exposures | bigint | No | Eligible active-end customer-months with a fully observed next-month label. |
| distinct_customers | bigint | No | Unique customers within a driver/category, not additive across categories. |
| next_month_churns | bigint | No | Next month churns |
| next_month_churn_rate | double | No | Next-month cancellations/customer-month exposures in the selected driver/category. |

## cohort_retention
One subscription-start cohort month and age 0-23; future outcomes are null.

Key: cohort_month, cohort_age. Rows in bundled run: 576.
| Column | Athena view type | Nullable in this run | Meaning |
|---|---|---|---|
| cohort_month | date | No | Cohort month |
| cohort_age | bigint | No | Cohort age |
| cohort_size | bigint | No | Original cohort population, repeated across ages; never sum across ages. |
| retained_customers | double | Yes | Subscriptions still active at target cohort-age month end; null if future. |
| retention_rate | double | Yes | Cohort: retained/cohort size; monthly: retained opening/opening customers; dimension summary: active/total. |
| is_observed | bigint | No | 1 for elapsed cohort periods; 0 for future periods. |

## customer_risk_scores
One customer at cutoff and nine auditable risk components; risk is null for churned customers.

Key: customer_id. Rows in bundled run: 11,880.
| Column | Athena view type | Nullable in this run | Meaning |
|---|---|---|---|
| customer_id | varchar | No | Customer id |
| as_of_date | date | No | Fixed reporting cutoff, 2026-08-31. |
| plan_type | varchar | No | Plan type |
| contract_type | varchar | No | Contract type |
| acquisition_channel | varchar | No | Acquisition channel |
| region | varchar | No | Region |
| monthly_revenue | double | No | Monthly fee after discount, normalized to a full month; not necessarily earned revenue. |
| tenure_months | double | No | Days from subscription start to cancellation or cutoff divided by 30.4375. |
| observed_clv | double | No | Sum of prorated recognized subscription revenue to cancellation or cutoff; not predicted LTV or profit. |
| engagement_score | double | No | 40% capped logins/25, 35% capped usage/250, 25% feature score; scaled 0-100. |
| customer_segment | varchar | No | Customer segment |
| churn_flag | bigint | No | 1 when validated subscription cancellation/termination occurred by cutoff. |
| active_flag | bigint | No | 1 when no subscription end date at cutoff. |
| risk_score | bigint | Yes | Heuristic points 0-100 for active customers only; null for churned customers. |
| risk_band | varchar | No | Risk band |
| high_value_flag | bigint | No | 1 if discounted monthly rate is at least USD 80. |
| high_risk_flag | bigint | No | High risk flag |
| active_mrr | double | No | Monthly revenue when currently active, otherwise zero. |
| revenue_at_risk | double | No | Current MRR of active customers with risk score above 60; opportunity size, not expected loss. |
| retention_priority | varchar | No | High/low value crossed with high vs low/medium heuristic risk; churned separately. |
| risk_inactivity | bigint | Yes | Risk inactivity |
| risk_engagement | bigint | Yes | Risk engagement |
| risk_support | bigint | Yes | Risk support |
| risk_complaints | bigint | Yes | Risk complaints |
| risk_payment | bigint | Yes | Risk payment |
| risk_usage | bigint | Yes | Risk usage |
| risk_new | bigint | Yes | Risk new |
| risk_renewal | bigint | Yes | Risk renewal |
| risk_decline | bigint | Yes | Risk decline |

## customer_segments
One customer at cutoff, with mutually exclusive segment and current-risk attributes.

Key: customer_id. Rows in bundled run: 11,880.
| Column | Athena view type | Nullable in this run | Meaning |
|---|---|---|---|
| customer_id | varchar | No | Customer id |
| as_of_date | date | No | Fixed reporting cutoff, 2026-08-31. |
| plan_type | varchar | No | Plan type |
| contract_type | varchar | No | Contract type |
| acquisition_channel | varchar | No | Acquisition channel |
| region | varchar | No | Region |
| monthly_revenue | double | No | Monthly fee after discount, normalized to a full month; not necessarily earned revenue. |
| tenure_months | double | No | Days from subscription start to cancellation or cutoff divided by 30.4375. |
| observed_clv | double | No | Sum of prorated recognized subscription revenue to cancellation or cutoff; not predicted LTV or profit. |
| engagement_score | double | No | 40% capped logins/25, 35% capped usage/250, 25% feature score; scaled 0-100. |
| customer_segment | varchar | No | Customer segment |
| churn_flag | bigint | No | 1 when validated subscription cancellation/termination occurred by cutoff. |
| active_flag | bigint | No | 1 when no subscription end date at cutoff. |
| risk_score | bigint | Yes | Heuristic points 0-100 for active customers only; null for churned customers. |
| risk_band | varchar | No | Risk band |
| high_value_flag | bigint | No | 1 if discounted monthly rate is at least USD 80. |
| high_risk_flag | bigint | No | High risk flag |
| active_mrr | double | No | Monthly revenue when currently active, otherwise zero. |
| revenue_at_risk | double | No | Current MRR of active customers with risk score above 60; opportunity size, not expected loss. |
| retention_priority | varchar | No | High/low value crossed with high vs low/medium heuristic risk; churned separately. |

## customers_clean
One customer at the reporting cutoff; latest telemetry for active customers or at cancellation.

Key: customer_id. Rows in bundled run: 11,880.
| Column | Athena view type | Nullable in this run | Meaning |
|---|---|---|---|
| customer_id | varchar | No | Customer id |
| subscription_start_date | date | No | Subscription start date |
| signup_date | date | No | Signup date |
| plan_type | varchar | No | Plan type |
| contract_type | varchar | No | Contract type |
| monthly_fee | double | No | Monthly fee |
| payment_method | varchar | No | Payment method |
| auto_renew | bigint | No | Auto renew |
| acquisition_channel | varchar | No | Acquisition channel |
| city | varchar | No | City |
| region | varchar | No | Region |
| age_group | varchar | No | Age group |
| discount_percentage | double | No | Discount fraction, e.g. 0.10 is 10%. |
| subscription_end_date | date | Yes | Subscription end date |
| support_tickets | bigint | No | Support tickets |
| complaints | bigint | No | Complaints |
| login_frequency | bigint | No | Logins observed during that customer-month exposure. |
| monthly_usage | double | No | Usage units observed in the customer-month (synthetic unit). |
| feature_usage_score | double | No | Synthetic feature breadth score 0-100. |
| payment_failures | bigint | No | Payment failures |
| late_payments | bigint | No | Late payments |
| last_activity_date | date | No | Latest simulated activity on or before observation. |
| churn_date | date | Yes | Churn date |
| churn_flag | bigint | No | 1 when validated subscription cancellation/termination occurred by cutoff. |
| customer_status | varchar | No | Customer status |
| tenure_months | double | No | Days from subscription start to cancellation or cutoff divided by 30.4375. |
| engagement_score | double | No | 40% capped logins/25, 35% capped usage/250, 25% feature score; scaled 0-100. |
| recent_usage_decline | double | Yes | max(0,1-current usage/mean of up to 3 prior months), capped at 1; null without nonzero history. |
| as_of_date | date | No | Fixed reporting cutoff, 2026-08-31. |
| observation_date | date | No | Cancellation date for churned customers, otherwise reporting cutoff. |
| customer_tenure | double | No | Alias of tenure_months for dashboard readability. |
| customer_age_months | bigint | No | Calendar-month age since subscription-start month; zero in acquisition month. |
| days_since_last_activity | bigint | No | Days from last activity to latest observation date; churned records use cancellation date. |
| monthly_revenue | double | No | Monthly fee after discount, normalized to a full month; not necessarily earned revenue. |
| observed_clv | double | No | Sum of prorated recognized subscription revenue to cancellation or cutoff; not predicted LTV or profit. |
| support_ticket_band | varchar | No | Support ticket band |
| usage_band | varchar | No | Usage band |
| engagement_band | varchar | No | Engagement band |
| tenure_band | varchar | No | Tenure band |
| acquisition_cohort | date | No | Acquisition cohort |
| churn_month | date | Yes | Churn month |
| risk_score | bigint | Yes | Heuristic points 0-100 for active customers only; null for churned customers. |
| risk_band | varchar | No | Risk band |
| high_value_flag | bigint | No | 1 if discounted monthly rate is at least USD 80. |
| active_flag | bigint | No | 1 when no subscription end date at cutoff. |
| high_risk_flag | bigint | No | High risk flag |
| active_mrr | double | No | Monthly revenue when currently active, otherwise zero. |
| revenue_at_risk | double | No | Current MRR of active customers with risk score above 60; opportunity size, not expected loss. |
| customer_segment | varchar | No | Customer segment |
| retention_priority | varchar | No | High/low value crossed with high vs low/medium heuristic risk; churned separately. |

## geography_performance
One region; cumulative outcomes and current MRR.

Key: region. Rows in bundled run: 4.
| Column | Athena view type | Nullable in this run | Meaning |
|---|---|---|---|
| region | varchar | No | Region |
| total_customers | bigint | No | Total customers |
| active_customers | bigint | No | Active customers |
| churned_customers | bigint | No | Churned customers |
| active_mrr | double | No | Monthly revenue when currently active, otherwise zero. |
| revenue_at_risk | double | No | Current MRR of active customers with risk score above 60; opportunity size, not expected loss. |
| observed_revenue | double | No | Observed revenue |
| average_clv | double | No | Average clv |
| average_tenure | double | No | Average tenure |
| churn_rate | double | No | Monthly: opening-customer cancellations/opening customers. Customer aggregates: cumulative churned/all customers. |
| retention_rate | double | No | Cohort: retained/cohort size; monthly: retained opening/opening customers; dimension summary: active/total. |
| arpu | double | No | Arpu |

## monthly_churn_kpis
One calendar month; opening base, flows and closing stocks.

Key: month. Rows in bundled run: 24.
| Column | Athena view type | Nullable in this run | Meaning |
|---|---|---|---|
| month | date | No | Month |
| is_active_start | bigint | No | Is active start |
| new_customer | bigint | No | New customer |
| churn_event | bigint | No | Churn event |
| is_active_end | bigint | No | Is active end |
| opening_customer_churn | bigint | No | Opening customer churn |
| new_customer_churn | bigint | No | New customer churn |
| renewal_due | bigint | No | Opening customer reaches calendar-month contract anniversary: every month or every 12 months. |
| renewal_success | bigint | No | Eligible customer remains subscribed at end of anniversary month. |
| start_mrr | double | No | Start mrr |
| new_mrr | double | No | New mrr |
| churned_mrr | double | No | Full normalized monthly revenue removed by cancellations in this month; not lost recognized revenue. |
| end_mrr | double | No | End mrr |
| recognized_revenue | double | No | Discounted monthly rate multiplied by inclusive active days/calendar days, rounded to cents per customer-month. |
| retained_opening_customers | bigint | No | Retained opening customers |
| churn_rate | double | Yes | Monthly: opening-customer cancellations/opening customers. Customer aggregates: cumulative churned/all customers. |
| retention_rate | double | Yes | Cohort: retained/cohort size; monthly: retained opening/opening customers; dimension summary: active/total. |
| renewal_rate | double | Yes | Renewal rate |
| net_customer_growth | bigint | No | Net customer growth |
| customer_growth_rate | double | Yes | Customer growth rate |
| arpu | double | No | Arpu |

## monthly_retention_kpis
One calendar month; retention of opening customers and renewal events.

Key: month. Rows in bundled run: 24.
| Column | Athena view type | Nullable in this run | Meaning |
|---|---|---|---|
| month | date | No | Month |
| is_active_start | bigint | No | Is active start |
| retained_opening_customers | bigint | No | Retained opening customers |
| opening_customer_churn | bigint | No | Opening customer churn |
| retention_rate | double | Yes | Cohort: retained/cohort size; monthly: retained opening/opening customers; dimension summary: active/total. |
| renewal_due | bigint | No | Opening customer reaches calendar-month contract anniversary: every month or every 12 months. |
| renewal_success | bigint | No | Eligible customer remains subscribed at end of anniversary month. |
| renewal_rate | double | Yes | Renewal rate |

## monthly_snapshots
One customer and calendar month with subscription exposure, including cancellation month; no rows after cancellation.

Key: customer_id, snapshot_month. Rows in bundled run: 107,858.
| Column | Athena view type | Nullable in this run | Meaning |
|---|---|---|---|
| customer_id | varchar | No | Customer id |
| plan_type | varchar | No | Plan type |
| contract_type | varchar | No | Contract type |
| acquisition_channel | varchar | No | Acquisition channel |
| region | varchar | No | Region |
| payment_method | varchar | No | Payment method |
| auto_renew | bigint | No | Auto renew |
| monthly_fee | double | No | Monthly fee |
| discount_percentage | double | No | Discount fraction, e.g. 0.10 is 10%. |
| snapshot_month | date | No | Snapshot month |
| customer_age_months | bigint | No | Calendar-month age since subscription-start month; zero in acquisition month. |
| is_active_start | bigint | No | Is active start |
| new_customer | bigint | No | New customer |
| churn_event | bigint | No | Churn event |
| is_active_end | bigint | No | Is active end |
| opening_customer_churn | bigint | No | Opening customer churn |
| new_customer_churn | bigint | No | New customer churn |
| renewal_due | bigint | No | Opening customer reaches calendar-month contract anniversary: every month or every 12 months. |
| renewal_success | bigint | No | Eligible customer remains subscribed at end of anniversary month. |
| monthly_revenue | double | No | Monthly fee after discount, normalized to a full month; not necessarily earned revenue. |
| start_mrr | double | No | Start mrr |
| new_mrr | double | No | New mrr |
| churned_mrr | double | No | Full normalized monthly revenue removed by cancellations in this month; not lost recognized revenue. |
| end_mrr | double | No | End mrr |
| recognized_revenue | double | No | Discounted monthly rate multiplied by inclusive active days/calendar days, rounded to cents per customer-month. |
| active_days | bigint | No | Inclusive billed subscription days during the month, including cancellation day. |
| support_tickets | bigint | No | Support tickets |
| complaints | bigint | No | Complaints |
| login_frequency | bigint | No | Logins observed during that customer-month exposure. |
| monthly_usage | double | No | Usage units observed in the customer-month (synthetic unit). |
| feature_usage_score | double | No | Synthetic feature breadth score 0-100. |
| payment_failures | bigint | No | Payment failures |
| late_payments | bigint | No | Late payments |
| last_activity_date | date | No | Latest simulated activity on or before observation. |
| engagement_score | double | No | 40% capped logins/25, 35% capped usage/250, 25% feature score; scaled 0-100. |
| prior_usage_mean | double | Yes | Mean usage from up to 3 strictly previous customer-month records. |
| recent_usage_decline | double | Yes | max(0,1-current usage/mean of up to 3 prior months), capped at 1; null without nonzero history. |

## plan_performance
One plan; cumulative customer outcomes and current MRR.

Key: plan_type. Rows in bundled run: 3.
| Column | Athena view type | Nullable in this run | Meaning |
|---|---|---|---|
| plan_type | varchar | No | Plan type |
| total_customers | bigint | No | Total customers |
| active_customers | bigint | No | Active customers |
| churned_customers | bigint | No | Churned customers |
| active_mrr | double | No | Monthly revenue when currently active, otherwise zero. |
| revenue_at_risk | double | No | Current MRR of active customers with risk score above 60; opportunity size, not expected loss. |
| observed_revenue | double | No | Observed revenue |
| average_clv | double | No | Average clv |
| average_tenure | double | No | Average tenure |
| churn_rate | double | No | Monthly: opening-customer cancellations/opening customers. Customer aggregates: cumulative churned/all customers. |
| retention_rate | double | No | Cohort: retained/cohort size; monthly: retained opening/opening customers; dimension summary: active/total. |
| arpu | double | No | Arpu |

## retention_by_dimension
One dimension and category; fixed age-6 retention for mature acquisition cohorts only.

Key: dimension, category. Rows in bundled run: 14.
| Column | Athena view type | Nullable in this run | Meaning |
|---|---|---|---|
| dimension | varchar | No | Dimension |
| category | varchar | No | Category |
| eligible_customers | bigint | No | Eligible customers |
| retained_customers | bigint | No | Subscriptions still active at target cohort-age month end; null if future. |
| retention_rate | double | No | Cohort: retained/cohort size; monthly: retained opening/opening customers; dimension summary: active/total. |

## revenue_churn_impact
One calendar month; normalized MRR bridge and prorated recognized revenue.

Key: month. Rows in bundled run: 24.
| Column | Athena view type | Nullable in this run | Meaning |
|---|---|---|---|
| month | date | No | Month |
| start_mrr | double | No | Start mrr |
| new_mrr | double | No | New mrr |
| churned_mrr | double | No | Full normalized monthly revenue removed by cancellations in this month; not lost recognized revenue. |
| end_mrr | double | No | End mrr |
| recognized_revenue | double | No | Discounted monthly rate multiplied by inclusive active days/calendar days, rounded to cents per customer-month. |
| is_active_end | bigint | No | Is active end |
| arpu | double | No | Arpu |

## support_usage_analysis
One latest-observation support-ticket band and usage band; descriptive cumulative outcomes.

Key: support_ticket_band, usage_band. Rows in bundled run: 9.
| Column | Athena view type | Nullable in this run | Meaning |
|---|---|---|---|
| support_ticket_band | varchar | No | Support ticket band |
| usage_band | varchar | No | Usage band |
| customers | bigint | No | Customers |
| churned_customers | bigint | No | Churned customers |
| active_mrr | double | No | Monthly revenue when currently active, otherwise zero. |
| average_engagement | double | No | Average engagement |
| revenue_at_risk | double | No | Current MRR of active customers with risk score above 60; opportunity size, not expected loss. |
| churn_rate | double | No | Monthly: opening-customer cancellations/opening customers. Customer aggregates: cumulative churned/all customers. |
