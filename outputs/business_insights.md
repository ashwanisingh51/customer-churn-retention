# Business insights and retention actions

All findings below are computed from the bundled synthetic data. They describe the simulation, not a real company. Associations are unadjusted; customer-month observations repeat customers and do not establish causation.

1. **Engagement:** Low recorded 6.00% next-month churn (834/13,893 customer-month exposures), versus High at 1.60% (583/36,485). Difference: 4.41 percentage points. Source: churn_driver_associations.csv; Churn Drivers sheet.

2. **Usage:** Low recorded 5.66% next-month churn (732/12,926 customer-month exposures), versus High at 1.64% (499/30,406). Difference: 4.02 percentage points. Source: churn_driver_associations.csv; Churn Drivers sheet.

3. **Payment failures:** 2 recorded 4.91% next-month churn (85/1,731 customer-month exposures), versus 0 at 2.87% (2,184/75,994). Difference: 2.04 percentage points. Source: churn_driver_associations.csv; Churn Drivers sheet.

4. **Support interactions:** 3+ recorded 4.34% next-month churn (514/11,842 customer-month exposures), versus 0 at 2.56% (918/35,863). Difference: 1.78 percentage points. Source: churn_driver_associations.csv; Churn Drivers sheet.

5. **Contract:** Monthly recorded 3.43% next-month churn (2,314/67,379 customer-month exposures), versus Annual at 2.01% (574/28,599). Difference: 1.43 percentage points. Source: churn_driver_associations.csv; Churn Drivers sheet.

6. **Acquisition channel:** Social recorded 3.42% next-month churn (529/15,476 customer-month exposures), versus Referral at 2.72% (492/18,069). Difference: 0.70 percentage points. Source: churn_driver_associations.csv; Churn Drivers sheet.

7. **Tenure:** 0-2 months recorded 3.38% next-month churn (996/29,442 customer-month exposures), versus 3-5 months at 2.72% (607/22,302). Difference: 0.66 percentage points. Source: churn_driver_associations.csv; Churn Drivers sheet.

8. **Plan:** Standard recorded 3.08% next-month churn (1,118/36,350 customer-month exposures), versus Basic at 2.96% (1,165/39,356). Difference: 0.12 percentage points. Source: churn_driver_associations.csv; Churn Drivers sheet.

9. **Six-month acquisition retention:** Referral retained 83.6% (1,246/1,491) versus Social at 76.8%. Both denominators include only cohorts old enough to observe age 6. Source: retention_by_dimension.csv; Retention & Cohorts sheet.

10. **Six-month contract retention:** Annual retained 86.2% (1,957/2,271) versus Monthly at 77.6%. Both denominators include only cohorts old enough to observe age 6. Source: retention_by_dimension.csv; Retention & Cohorts sheet.

11. **Six-month plan retention:** Premium retained 80.4% (1,399/1,740) versus Standard at 79.3%. Both denominators include only cohorts old enough to observe age 6. Source: retention_by_dimension.csv; Retention & Cohorts sheet.

12. **Current risk exposure:** 212 active customers hold USD 11,977.55 in high-risk MRR, 2.6% of current MRR. This is the size of a prioritization group, not expected or realized loss. Source: executive_kpis.json; Customer Segments & Risk sheet.

13. **High-value intervention pool:** 46 customers combine high risk with at least USD 80 monthly revenue, representing USD 4,796.00 MRR. Source: customers_clean.csv; Revenue & Retention Opportunity sheet.

14. **Early cancellations:** 1,303 of 3,349 observed cancellations (38.9%) occurred before three months of tenure. This is a distribution of churn events, not a tenure-specific churn probability. Source: customers_clean.csv; Churn Drivers sheet.

15. **Latest customer bridge:** 665 acquisitions minus 267 cancellations produced 398 net additions in August 2026. Source: monthly_churn_kpis.csv; Executive Overview sheet.

16. **Age-6 survival:** 80.0% across 8,231 customers in mature cohorts, weighted by original cohort size. Source: cohort_retention.csv; Retention & Cohorts sheet.

## Recommended tests

- Randomize personalized outreach within the high-value/high-risk active pool; evaluate 60-day cancellation rate and net revenue after intervention costs.
- Test payment recovery messages after failed payments; track recovery, involuntary cancellation and complaints.
- Test guided onboarding for new low-engagement subscribers; evaluate comparable follow-up windows.
- Pilot support follow-up after repeated complaints, with service workload and opt-out guardrails.
- Compare channels on fixed-horizon retention and value before reallocating spend; acquisition costs are absent, so CAC and ROI cannot be calculated.
- Test re-engagement for low-usage customers; randomize treatment and avoid interpreting contact response as proof of saved customers.

See [retention_experiment_plan.md](retention_experiment_plan.md) for the evaluation design.
