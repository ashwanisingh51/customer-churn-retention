# Metric definitions and analytical policy

## Scope and churn definition

Reporting cutoff: **31 August 2026**, end of day. Observation window: September 2024–August 2026. Synthetic USD subscription business. One subscription per customer, no reactivation, no upgrades/downgrades, no currency conversion.

**Churn is a validated subscription cancellation or termination effective on or before the cutoff.** Subscription end date and churn date must agree. Cancelled customers are inactive at end of their cancellation day. Inactivity does not constitute churn; it is a separately documented risk signal.

The last observed record for a churned customer is at cancellation. For an active customer it is at cutoff. Therefore, latest customer-level usage/support comparisons mix observation dates and are descriptive. The primary driver charts instead relate an active month-end observation to cancellation in the next fully observed month.

## Core KPIs

| Metric | Exact definition | Period and interpretation |
|---|---|---|
| Total customers | Count of valid unique customer IDs | All acquired by cutoff, including churned |
| Active customers | No effective subscription end date by cutoff | Point-in-time stock |
| Churned customers | Effective cancellation by cutoff | Cumulative count |
| Cumulative churn rate | Churned customers / all customers | Unequal observation durations; not monthly churn |
| Active customer share | Active / all customers | Complement of cumulative churn; not longitudinal retention |
| Monthly churn rate | Cancellations among customers active at month start / customers active at month start | Excludes same-month acquisition churn from numerator and denominator |
| Monthly retention rate | Opening customers still subscribed at month end / opening customers | Complement of monthly churn; acquisitions excluded |
| New-customer churn | Acquisition and cancellation in same calendar month | Separately counted; included in closing customer bridge |
| Average customer tenure | Mean of (cancellation or cutoff − subscription start) days / 30.4375 | Churned tenure ends at cancellation |
| MRR | Sum discounted monthly rate of active customers | Point-in-time normalized recurring revenue |
| Monthly revenue | monthly_fee × (1 − discount_percentage), rounded to cents | Full-month contracted rate, not actual earned revenue |
| ARPU | Current MRR / active customers | Per active customer per month |
| Recognized revenue | Monthly rate × inclusive active days / calendar days in month; rounded per customer-month | Synthetic accrual convention; annual contracts normalized monthly |
| Observed CLV | Sum recognized revenue per customer through observation date | Historical revenue, not forecast lifetime value, profit or gross margin |
| Revenue from active customers | Sum observed CLV of customers active at cutoff | Historical contribution of today's active population |
| Revenue generated before churn | Sum recognized revenue across all records of churned customers | Earned through cancellation day; not future forgone revenue |
| Churned MRR | Full monthly rate of subscriptions cancelled in a month | MRR removed at cancellation, not a realized accounting loss |
| Total MRR removed at churn events | Sum churned MRR over historical cancellation events | Descriptive run-rate amounts at different event times; not cumulative lost revenue |
| Revenue at risk | Sum MRR for active customers with heuristic score >60 | Prioritization pool; not probability-weighted loss |
| High-risk customers | Active customers scoring 61–100 | Churned customer scores are null |
| Renewal eligibility | Opening customers in each monthly anniversary month, or each 12th anniversary month for annual contracts | Calendar-month operational proxy |
| Renewal rate | Eligible customers remaining subscribed at anniversary month end / eligible renewal opportunities | Genuine at-risk opportunity denominator; not auto-renew enrollment |
| Net customer growth | Acquisitions − all cancellations in month | Closing − opening customer count |
| Customer growth rate | Net customer growth / opening customers | Null when opening population is zero |
| Average support tickets / usage | Mean latest-observation monthly telemetry across customer rows | Use active-only filter for current operating workload |

Annual subscribers may terminate early in this simulation. There are no penalties, prepayment balances, refunds, taxes, service costs, marketing spend or dunning payment ledgers. Renewal dates are approximated by calendar-month anniversary, not exact-day contract events. Recognized revenue is not a cash collection metric, even when payment failures occur.

## Reconciliation rules

- Closing customers = opening customers + acquisitions − all cancellations.
- Closing MRR = opening MRR + new MRR − cancelled MRR. No expansion or contraction exists in this scenario.
- Next month's opening stock equals prior month's closing stock.
- First month has no opening customers. Monthly churn, retention and renewal rates are null where denominators are zero.
- All percentages are stored as fractions. Format 0.10 as 10%; do not multiply by 100 again.
- Rates must be recomputed from summed numerators and denominators. Never sum rates or average unequal-sized group rates.
- MRR and active customer counts are stocks: do not sum them across months.

## Cohort retention

Cohort = subscription-start calendar month. Age = target calendar month minus cohort month. Denominator = original valid customers in cohort. Numerator = customers active at target month end. **Month 0 measures actual acquisition-month-end survival and is not forced to 100%.**

Cohort ages 0–23 form a rectangular export. Future cells have is_observed=0 and null outcomes. A future null is never a zero. Retention can only stay level or decline because there is no reactivation.

For age-1/3/6/12 KPI cards, filter to exactly that age and is_observed=1, then divide total retained by total cohort size. This weights cohorts by customer count. Fixed age-6 plan/channel/region comparisons include only cohorts through February 2026 and therefore give each customer a comparable six-month endpoint. Calendar conditions and selection differences still limit causal comparisons.

## Engagement, risk and customer value

Engagement score = 40 × min(logins/25,1) + 35 × min(usage/250,1) + 0.25 × feature_usage_score.

Usage bands: Low <80, Medium 80–<180, High ≥180. Engagement: Low <35, Medium 35–<65, High ≥65. Support-ticket bands: 0, 1–2, 3+. Recent usage decline = max(0,1 − current usage / mean usage from up to 3 strictly prior months), capped at 1. It is null with no usable prior history.

High value means discounted monthly recurring rate ≥USD 80. This transparent business threshold does not use future CLV.

| Risk component | Trigger | Points |
|---|---|---:|
| Inactivity | At least 14 days since last activity | 20 |
| Engagement | Score <35 | 15 |
| Support | At least 3 tickets | 10 |
| Complaints | At least 1 | 10 |
| Payment | At least 1 failure | 15 |
| Usage | Fewer than 80 units | 10 |
| Tenure | Under 3 months | 5 |
| Renewal | Auto-renew disabled | 5 |
| Decline | Usage down at least 30% vs prior history | 10 |

Total maximum: 100. Low Risk 0–30; Medium Risk 31–60; High Risk 61–100. Missing prior usage contributes no decline points, so new customers have less evidence, not proof of low risk. All components and scores are null for churned customers. Thresholds are assumptions, not learned probabilities; tune with real outcomes and intervention capacity.

The priority matrix uses High Value versus Low Value, crossed with High Risk versus Low/Medium Risk. Medium risk remains explicitly visible rather than being silently relabeled low risk.

## Mutually exclusive segmentation, in priority order

1. Churned High Value: churned and monthly rate ≥80.
2. Churned Low Value: all other churned customers.
3. High Value At Risk: active, high value, high risk.
4. At Risk: remaining active high risk.
5. Dormant: remaining active customers inactive for at least 30 days.
6. New Customers: remaining active customers with tenure <3 months.
7. Loyal High Value: remaining active, tenure ≥12 months, engagement ≥50, high value.
8. Loyal Standard: remaining active, tenure ≥12 months, engagement ≥50.
9. Highly Engaged: remaining active customers with engagement ≥65.
10. Low Engagement: remaining active customers with engagement <35.
11. Core Customers: all remaining active customers.

Zero members in a rule-defined segment is valid. Do not alter rules to manufacture a visually balanced segmentation.

## Prediction prototype

Target: cancellation in the next calendar month among customers active at the feature month end. August 2026 features are not labeled because September outcomes are unobserved.

A deterministic SHA-256 customer bucket separates train (0–5), validation (6–7), and test (8–9). Training feature months end December 2025; labels end January 2026. Validation features February–March 2026, labels March–April. Test features May–July, labels June–August. Customers never overlap across splits.

Median imputation, scaling and category encoding fit on training data only. Compare balanced logistic regression and a shallow balanced decision tree with a prior-only baseline. Choose the model on validation average precision (reported as PR-AUC); choose its threshold using validation F1. Report accuracy, precision, recall, F1, ROC-AUC, average precision and confusion matrix on held-out test data. Average precision is the non-interpolated precision-recall summary, not trapezoidal integration.

The data are synthetic; repeated customer-months are correlated. Balanced model scores are uncalibrated. Low precision and recall must be reported, not hidden behind high majority-class accuracy. No production or causal claim is made.
