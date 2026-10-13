# Retention experiment: personalized support outreach

## Decision and hypothesis

Test whether proactive, personalized outreach reduces 60-day cancellation among active high-value/high-risk subscribers, relative to business-as-usual service. High value means monthly revenue ≥USD 80; high risk means heuristic score >60.

The current synthetic pool contains **46 customers** and **USD 4,796 in monthly recurring revenue**. This identifies an intervention target; it does not measure expected or realized savings.

## Eligibility and assignment

Freeze eligibility before randomization using a dated snapshot. Include active customers meeting the thresholds with a valid permitted contact channel. Exclude customers already in conflicting retention experiments or with a pending effective cancellation. Real deployment requires contact consent and a verified customer ID.

Randomize customers 1:1 to treatment and control, stratifying by plan, contract and risk band where sample size permits. Use a recorded random seed and assignment table. Customer is the unit of assignment and analysis; never count monthly rows as independent customers. Keep assignments fixed and avoid cross-group contamination.

Treatment: a support-led outreach offering troubleshooting, usage guidance and payment assistance. Define contact attempts and messaging before launch. No unbudgeted blanket discount is assumed.

Control: normal service and existing standard notifications. Both groups retain normal support access.

## Metrics and evaluation

- **Primary:** intention-to-treat 60-day cumulative cancellation rate, cancelled assigned customers / all assigned customers. Compare treatment minus control and report a customer-level confidence interval.
- **Secondary:** retained MRR at day 60, net recognized revenue per assigned customer after intervention costs, engagement change and payment recovery where a genuine payment ledger exists.
- **Guardrails:** complaints, contact opt-outs, support workload, excessive concessions, adverse customer feedback and intervention cost per assigned customer.
- **Window:** 60 days of follow-up after assignment plus a predefined data-latency allowance. Do not classify unobserved follow-up as retained or non-churn.
- **Analysis:** fixed-horizon intention-to-treat analysis. Use survival methods if follow-up is administratively censored. Check sample-ratio mismatch and baseline balance. Report all randomized customers, not only contacted or responding customers.

## Sample considerations

Forty-six candidates would produce roughly 23 customers per arm. That is a feasibility pilot, not a credible power basis for a small churn reduction.

Illustrative planning only: with a **hypothetical** 10% control churn rate, a target 7.5% treatment rate, two-sided 5% significance and 80% power, the usual two-proportion normal approximation requires about **2,000 customers per arm**, before attrition or design effects. These rates are assumptions, not estimates from the current synthetic pool.

Estimate a real baseline on a separate historical eligibility cohort, specify a commercially meaningful minimum effect, then calculate sample size with a qualified experiment owner. Options include rolling enrollment until a fixed sample is reached or broadening eligibility under a predeclared rule. Do not repeatedly test significance and stop when a favorable result appears.

## Success criteria

Before launch, define the minimum worthwhile reduction and permissible guardrail thresholds with the business owner. For a powered confirmatory test, require the primary confidence interval to support improvement and evaluate whether incremental net revenue exceeds outreach cost. Report economic uncertainty, not just a p-value.

For the current small pilot, success means valid randomization, deliverable treatment, complete event logging and usable feedback. Do not claim proven retention impact.

## Required real-company inputs

Consent/contact eligibility, actual cancellation reasons, intervention assignments and timestamps, outreach costs, concessions, cash/payment recovery, renewal dates, and reliable follow-up. These are absent from this simulation. No experiment has been run.
