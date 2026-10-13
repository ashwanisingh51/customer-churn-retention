# Reproduce the Amazon QuickSight dashboard

This repository contains locally executed analysis and deployment assets. It does not include an authenticated AWS deployment. Console navigation may appear under Quick or Quick Suite branding; select the QuickSight BI authoring experience in your account. The supplied dataset and formula names are stable implementation references.

## 1. Run and validate the local project

From the repository root:

    python -m scripts.run_pipeline --test

Review outputs/validation_report.json, outputs/test_results.xml and outputs/executive_kpis.json. Open outputs/dashboard_preview.html to see static charts. A passing local run is not a substitute for checking Athena/SPICE imports.

## 2. Create a private S3 bucket

Sign in to the intended AWS account. Select your chosen Region and open S3 → Create bucket. Choose a globally unique name, leave Object Ownership as bucket-owner-enforced, keep Block Public Access enabled, and enable default server-side encryption. Create the bucket.

Use a single Region for this portfolio's S3, Athena and QuickSight setup to simplify permissions and operations. Do not assume the example bucket in this repository exists.

## 3. Configure authentication and upload

Follow s3_setup.md to set AWS_REGION, S3_BUCKET_NAME and optionally AWS_PROFILE in your shell. Authenticate your AWS SSO profile or use the environment's IAM role.

    python -m scripts.upload_to_s3 --dry-run
    python -m scripts.export_analytics_data --bucket YOUR_ACTUAL_BUCKET
    python -m scripts.upload_to_s3

The dry run contacts no AWS services. Inspect the plan for 14 datasets and isolated dataset folders. After actual upload, inspect S3 and confirm a CSV exists in each quicksight/<dataset>/ folder and JSON manifests exist under quicksight/manifests/.

If overriding S3_PREFIX, pass the same --prefix to export_analytics_data. Never upload a manifest into the CSV dataset folder.

## 4. Configure Athena

Open Athena → Query editor. Select the same Region and AwsDataCatalog. Create or select a workgroup using Athena engine version 3. Set its query-result location to s3://YOUR_ACTUAL_BUCKET/athena-results/. Keep results outside quicksight dataset folders. Apply an appropriate per-query scan limit for your account and retain the default encryption or your organization's required setting.

Run the statements from quicksight/athena_setup.sql **one statement at a time**, starting with CREATE DATABASE. For every dataset there is a string staging table ending _csv followed by a typed view without that suffix.

The [AWS Open CSV SerDe documentation](https://docs.aws.amazon.com/athena/latest/ug/csv-serde.html) explains its ISO-date and blank numeric limitations. This project keeps CSV staging fields as strings and converts nonempty values in views. Invalid nonblank values fail conversion rather than being silently replaced with zero.

Run:

    SELECT COUNT(*) FROM churn_retention.customers_clean;
    SELECT SUM(active_mrr), SUM(revenue_at_risk) FROM churn_retention.customers_clean;
    SELECT month, churn_rate, retention_rate FROM churn_retention.monthly_churn_kpis ORDER BY month;
    SELECT * FROM churn_retention.cohort_retention WHERE is_observed = 0 LIMIT 10;

Expected default customer count: 11,880. Compare revenue to executive_kpis.json and confirm future outcomes are null. Check all table/view row counts against dataset_contracts.json. Querying views validates their casts against actual AWS data.

## 5. Grant QuickSight access

Open QuickSight administration, typically profile/menu → Manage QuickSight → Security & permissions or AWS resources access. Grant access to Athena and select the dataset S3 bucket. Include read/write access to the Athena result prefix as needed for queries.

The QuickSight service role requires its own permissions; your console user permissions alone are insufficient. Grant Glue catalog read access and Athena access for the selected workgroup. If Lake Formation controls the catalog, grant the role database and table access there too. Consult the [AWS QuickSight Athena access policy reference](https://docs.aws.amazon.com/aws-managed-policy/latest/reference/AWSQuicksightAthenaAccess.html) and your account's IAM administrator for scoped resources.

No AWS credentials are stored in the repository.

## 6. Create the Athena data source

In the BI authoring area choose Datasets → New dataset → Athena. Name the source Churn Retention Athena. Select the configured workgroup and create the connection. Choose catalog AwsDataCatalog, database churn_retention, and **typed views**, such as customers_clean, instead of raw _csv tables.

For each view choose Edit/Preview data. Compare column types to DATA_DICTIONARY.md. Customer identifiers and category labels are strings; dates are dates; amounts numeric; rates decimal fractions; flags integer. Save the dataset with the same name as its view.

## 7. Import into SPICE

Choose Import to SPICE for interactive analysis. Review estimated capacity and complete the import. Check ingestion status, ingested row count and skipped-row count for every dataset. Investigate every skipped row.

Import at least customers_clean, monthly_snapshots, cohort_retention, churn_driver_associations, retention_by_dimension, plan_performance and channel_performance for the designed sheets. The other marts provide reusable supporting summaries and QA controls; all 14 can be imported.

After future successful uploads, request a full SPICE refresh. Schedule refreshes only once the upstream pipeline and upload have completed, and use a common batch window. No scheduler is configured by this repository.

### Small-dataset alternative: S3 directly

Choose New dataset → S3, then upload the corresponding local manifest from quicksight/manifests or provide its S3 URL. The manifest must have been regenerated with your bucket. This imports the listed CSV into SPICE. Set ISO date types during preparation and check blank values.

One manifest selects one compatible schema. See [AWS manifest specification](https://docs.aws.amazon.com/quick/latest/userguide/supported-manifest-file-format.html). This route does not need Athena for that dataset.

## 8. Configure joins only if needed

The default design uses separate datasets and requires no joins. customers_clean already includes segments and risk. monthly_snapshots already includes stable analysis dimensions.

If adding a join, follow dataset_mapping.md. Select matching customer_id keys, verify the dimension side is unique and compare row counts/revenue before saving. Never join an aggregate mart onto customer-level or monthly facts and then sum its repeated totals.

## 9. Start the analysis and calculated fields

From customers_clean choose Visualize, create a new analysis and name it Customer Churn & Retention Analytics. Add the other imported datasets through the analysis dataset menu.

In each selected dataset's field list choose Add calculated field. Create formulas from calculated_fields.md in the listed dataset. Paste only the expression; set an explicit readable name. Validate each formula in the service before saving. Format rates as percentages and amounts as USD.

## 10. Create and name all five sheets

Add sheets named Executive Overview; Churn Drivers; Customer Segments & Risk; Retention & Cohorts; Revenue & Retention Opportunity. Use tiled layout with consistent gutters. Follow dashboard_plan.md for every visual's dataset, field wells, aggregation and scope.

For each KPI, add a visual, select KPI, choose its dataset, then drag the documented calculated measure into Value. Use a descriptive title and add the period to the title/subtitle. Do not drag a raw fractional rate into an automatically summed value well.

For line charts, choose Line, put snapshot_month on the X axis with month granularity and the documented measure in Value. Sort dates ascending. For bars, put the dimension in Group/Color or category axis and the numeric measure in Value; sort meaningfully.

## 11. Set filter controls and scopes

For customers_clean add plan_type, region, acquisition_channel and contract_type filters with controls. Apply them to relevant visuals using that dataset. Configure equivalent mapped filters on monthly_snapshots if the console supports cross-dataset mapping; otherwise use clearly labeled dataset-specific controls.

Add snapshot_month range filtering to historical trends. Add a separate single-month filter to the monthly churn, retention, renewal and churned-MRR KPI visuals, default August 2026. Exclude current-state cards from historical date filtering.

Each driver chart needs a visual-level filter on driver. Do not apply current customer filters or date controls to the full-window driver mart. Cohort visuals use cohort controls; dimension-age-6 visuals use their own dimension filter. Confirm scope with dataset_mapping.md rather than selecting all visuals indiscriminately.

## 12. Build the cohort heatmap

Select cohort_retention. Add a pivot table: cohort_month in Rows; cohort_age in Columns; retention_rate in Values with MAX aggregation. Sort cohorts and ages ascending. Format values as percent with zero or one decimal.

Open conditional formatting for the value field, choose a sequential light-to-dark scale, set bounds 0 and 1, and leave nulls uncolored. Hide row totals and column totals because cohort-age percentages cannot be added.

Do not replace nulls with zero. Add a subtitle: "Month 0: actual acquisition-month-end survival. Blank cells: future periods."

For Month 1/3/6/12 retention cards, filter each visual to its named age and is_observed=1, then use the weighted formula in calculated_fields.md.

## 13. Add interactions and details

For the risk-band bar, add a filter action targeting only customer detail and customer-level charts. For segment bars, add an analogous action within the customer dataset. Test selection and reset. Do not send current-segment actions into cohort or historical risk calculations.

The detail table contains one row per customer. Add plan, revenue, tenure, risk, engagement, observed CLV and status. Use active_flag=1 for an outreach view and sort high-value high-risk accounts first. Configure tooltips with counts, denominators and dates.

## 14. Validate and publish

Complete dashboard_qa_checklist.md. Compare default totals to executive_kpis.json and filtered totals to equivalent queries. Check results as a viewer, not just an author.

Choose Publish dashboard, give it a clear title and share only with intended users/groups. Apply row-level security if later using real restricted data; the bundled data contain no real customer identities. Verify viewer permissions and SPICE refresh access.

Only after publication should you add a live dashboard URL and AWS screenshots to the README or claim that you built a deployed QuickSight dashboard.

## 15. Troubleshooting

| Symptom | Check |
|---|---|
| HIVE_BAD_DATA | Query the string staging table; verify typed casts, date format and CSV header order |
| Duplicate totals | Extra CSVs under dataset prefix; aggregate joins; MRR summed across months |
| Access denied | QuickSight service role, bucket access, Athena workgroup, query results and Lake Formation |
| Missing dates | ISO format and correct view/type; use typed view rather than _csv table |
| Blank KPI | Zero denominator, empty filters, no SPICE rows; do not replace every blank with zero |
| Wrong cohort colors | Future nulls replaced by zero or totals enabled |
| Filter appears ineffective | Dataset lacks dimension or visual is intentionally excluded by scope |
| Notebook/pipeline dependency issue | Use Python 3.12 and a fresh environment with the pinned requirements |

Local tests cover CSV contracts, SQL views' parsable syntax and upload control flow using fakes. They do not prove AWS authorization, live query execution, SPICE ingestion, formula compilation or dashboard publication.
