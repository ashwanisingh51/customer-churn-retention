# Project delivery and verification

The Customer Churn & Retention Analytics project was created from scratch and executed locally. The AWS layer is prepared for deployment; it has not been published.

## Deliverables

- 12,000 generated synthetic customers; 11,880 valid customers after quarantine.
- 107,858 valid customer-month records across 24 months.
- 14 CSV analytics datasets, raw inputs and quarantine/repair audit.
- Constrained SQLite database and 32 executed SQL query outputs.
- Four executed analytical notebooks.
- 21 Matplotlib charts and a five-tab static dashboard preview.
- Logistic regression, decision-tree and baseline evaluation, split audit, coefficients and held-out predictions.
- S3 upload script, 14 manifests, Athena staging tables/typed views and full QuickSight implementation documentation.
- 16 data-derived business insights, experiment plan, four resume bullets and 15 interview Q&As.
- Pinned requirements, resolved dependency snapshot and a GitHub Actions workflow. The workflow is configured but has not run on GitHub.

Every delivered repository file is listed in [FILE_MANIFEST.md](FILE_MANIFEST.md). All repository files are new; no existing project source was supplied or replaced.

## Main KPIs

| Metric | Verified value |
|---|---:|
| Total valid customers | 11,880 |
| Active customers | 8,531 |
| Churned customers | 3,349 |
| August monthly churn | 2.9755% |
| August monthly retention | 97.0245% |
| Current MRR | USD 458,229.60 |
| ARPU | USD 53.71 |
| Revenue at risk | USD 11,977.55 |
| High-risk active customers | 212 |
| Average observed CLV | USD 468.84 |
| August net customer growth | 398 |

Cutoff: 31 August 2026. All data and currency amounts are synthetic.

## Execution evidence

- **121/121 pytest tests passed**, including **100/100 reconciliation checks**.
- **4/4 notebooks executed**, with no cell errors.
- Fresh Python 3.12 virtual environment, no inherited system packages.
- Full installation from requirements.txt and end-to-end command completed successfully.
- All 17 raw/processed source files were byte-identical across regeneration.
- Dependency check: no broken requirements.
- SQLite integrity/foreign keys, customer-date counts, prorated billing, cohort survival and SQL/Python totals checked.
- S3 dry run validated 14 dataset plans without AWS requests.
- Model held-out ROC-AUC 0.650; average precision 0.062. Precision/recall are modest and reported explicitly.

Reports: [validation](outputs/validation_report.json), [pytest XML](outputs/test_results.xml), [test log](outputs/test_run.log), [notebooks](outputs/notebook_execution_report.json), [run manifest](outputs/run_manifest.json), [fresh-environment verification](outputs/verification_summary.json).

The successful run establishes local behavior for the tested environment. AWS permissions, live Athena execution, SPICE ingestion, formula compilation and dashboard publication remain unverified until deployment.

## Strongest business findings

Low prior-month engagement corresponded to 6.00% next-month churn versus 1.60% for high engagement. Support-ticket volume and payment failures also showed elevated next-month churn in selected groups.

At cohort age 6, referral retention was 83.6% versus 76.8% for social acquisitions; annual contracts retained 86.2% versus 77.6% for monthly contracts. These are synthetic unadjusted associations, not causal effects.

The current high-value/high-risk pool has 46 customers and USD 4,796 MRR. It is small enough that outreach should initially be treated as a feasibility pilot, not a powered proof of revenue savings.

Full numerators, denominators and recommended tests: [business_insights.md](outputs/business_insights.md).

## Final architecture

Synthetic subscription data → Python/Pandas cleaning and quarantine → churn/retention analytics → SQLite validation and 32 SQL queries → processed marts → S3 → Athena → QuickSight/SPICE → insights and retention experiment design.

Local stages are executed. Cloud stages are ready to configure.

## Final resume bullets

- Analyzed 11,880 validated synthetic subscription customers and 107,858 customer-month records using Python, Pandas and 32 SQL analyses to evaluate churn, retention, engagement and recurring revenue.
- Built reproducible cohort and customer segmentation pipelines with an interpretable risk framework identifying 212 active high-risk customers representing USD 11,978 in monthly recurring revenue at risk.
- Developed and evaluated leakage-aware logistic regression and decision-tree prototypes using customer-disjoint temporal splits, with validation-based model selection and held-out classification metrics.
- Prepared 14 Amazon QuickSight-ready analytics datasets, a five-sheet dashboard specification, boto3 S3 upload workflow and typed Athena views with metric reconciliation and deployment documentation.

## Remaining AWS Console actions

1. Authenticate to your AWS account and create/select a private S3 bucket and Region.
2. Set configuration, regenerate Athena SQL/manifests with the real bucket and run the uploader.
3. Configure the Athena workgroup/result location and execute staging-table and typed-view statements.
4. Grant QuickSight service-role, S3, catalog/workgroup and any Lake Formation permissions.
5. Import the typed datasets into SPICE and validate row counts/types.
6. Build the five sheets using the supplied field wells, formulas, filter scopes and interactions.
7. Complete dashboard QA and publish to intended viewers.

Follow [quicksight_build_guide.md](quicksight/quicksight_build_guide.md). There are no stored AWS credentials and no claim of a live dashboard.

## Start here

- [README](README.md): setup and full project overview.
- [Dashboard preview](outputs/dashboard_preview.html): static local charts in five tabs.
- [File inventory](FILE_MANIFEST.md): every packaged file.
