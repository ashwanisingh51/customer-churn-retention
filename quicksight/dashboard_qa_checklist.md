# Dashboard QA checklist

Local automated results: ../outputs/validation_report.json and ../outputs/test_results.xml. An unchecked AWS item means it has not been verified in the live service.

## Source and import

- [x] Customer and customer-month keys reconcile locally.
- [x] Revenue, customer bridges, risk totals and cohort survival reconcile locally.
- [x] SQL outputs executed and match independent Python/date-based controls.
- [ ] Athena typed-view row counts equal dataset_contracts.json.
- [ ] SPICE imported all expected rows without skipped records or type errors.
- [ ] ISO dates import as dates; blank churn dates and cohort outcomes remain null.
- [ ] No manifest/CSV shares an Athena dataset folder with a different schema.
- [ ] SPICE refreshes refer to the same complete upload batch.

## Metric controls at default filters

- [ ] Total customers = 11,880; active = 8,531; churned = 3,349.
- [ ] Current MRR = USD 458,229.60; ARPU = USD 53.7134685.
- [ ] August opening-customer churn = 2.9755318%; retention = 97.0244682%.
- [ ] Cumulative churn = 28.1902357%, clearly distinct from monthly churn.
- [ ] High-risk active customers = 212; MRR at risk = USD 11,977.55.
- [ ] August MRR removed at cancellation = USD 15,176.45.
- [ ] Observed revenue = USD 5,569,843.56.
- [ ] August net customer growth = 398.
- [ ] Renewals use eligible anniversary opportunities, not the active customer denominator.
- [ ] No sum of monthly MRR stocks or customer stocks is presented as a period total.

## Filters and interaction

- [ ] August selected for monthly KPI cards; current-state cards labeled as of cutoff.
- [ ] Plan/region/channel/contract controls update only datasets that contain the dimensions.
- [ ] Multi-select filters reconcile to a matching SQL/Python subset.
- [ ] Historical date control does not alter current-state risk cards or static driver marts.
- [ ] Each driver visual has exactly one driver filter; exposure counts are not summed across drivers.
- [ ] Optional joins preserve rows and revenue; no current CLV repeated across monthly facts.
- [ ] Customer detail export has one row per customer and excludes churned customers for risk outreach.
- [ ] Click/filter actions stay within the intended dataset and have an obvious reset.

## Cohorts and presentation

- [ ] Heatmap: cohort_month rows, cohort_age columns, retention_rate value, 0–100% scale.
- [ ] Future periods appear blank/unavailable rather than zero or red.
- [ ] Age-1/3/6 cards exclude immature cohorts and weight by original cohort size.
- [ ] Month 0 is actual month-end survival; heatmap totals are hidden.
- [ ] Null risk for churned customers is displayed as not applicable.
- [ ] Currency is USD, rates are percentages, and axes are readable without misleading truncation.
- [ ] Tooltips include denominators, reporting period and observational caveats where relevant.
- [ ] Published viewer account can access only the intended dashboard/data.
- [ ] Screenshots and live dashboard URL are added only after actual publication.

Re-run controls if filters, joins, data types, formulas or source data change.
