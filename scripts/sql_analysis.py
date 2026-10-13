"""Build a constrained SQLite database, execute named SQL and save each result."""
import re
import sqlite3
import pandas as pd
from scripts.common import ROOT, read_csv, write_csv

KEYS={"customers_clean":["customer_id"],"monthly_snapshots":["customer_id","snapshot_month"],
      "customer_segments":["customer_id"],"customer_risk_scores":["customer_id"],
      "monthly_churn_kpis":["month"],"monthly_retention_kpis":["month"],
      "cohort_retention":["cohort_month","cohort_age"],"plan_performance":["plan_type"],
      "channel_performance":["acquisition_channel"],"geography_performance":["region"],
      "revenue_churn_impact":["month"],"support_usage_analysis":["support_ticket_band","usage_band"],
      "churn_driver_associations":["driver","category"],"retention_by_dimension":["dimension","category"]}
def build_database():
    frames={p.stem:read_csv(p.stem) for p in sorted((ROOT/"data/processed").glob("*.csv"))}
    statements=["PRAGMA foreign_keys = ON;"]
    for name,frame in frames.items():
        cols=[]
        for col in frame:
            kind="INTEGER" if pd.api.types.is_integer_dtype(frame[col]) else "REAL" if pd.api.types.is_numeric_dtype(frame[col]) else "TEXT"
            cols.append(f'"{col}" {kind}')
        cols.append("PRIMARY KEY ("+", ".join(f'"{x}"' for x in KEYS[name])+")")
        if name in ["monthly_snapshots","customer_segments","customer_risk_scores"]:
            cols.append('FOREIGN KEY ("customer_id") REFERENCES customers_clean(customer_id)')
        if name=="customers_clean":
            cols += ["CHECK (monthly_fee >= 0)","CHECK (discount_percentage BETWEEN 0 AND 1)",
                     "CHECK (active_flag + churn_flag = 1)","CHECK (risk_score IS NULL OR risk_score BETWEEN 0 AND 100)"]
        statements.append(f"CREATE TABLE IF NOT EXISTS {name} (\n  "+",\n  ".join(cols)+"\n);")
    statements.extend(["CREATE INDEX IF NOT EXISTS idx_snapshot_month ON monthly_snapshots(snapshot_month);",
                       "CREATE INDEX IF NOT EXISTS idx_churn_date ON customers_clean(churn_date);"])
    ddl="\n\n".join(statements)+"\n"
    (ROOT/"sql").mkdir(exist_ok=True)
    (ROOT/"sql/schema.sql").write_text(ddl,encoding="utf-8")
    db=ROOT/"outputs/churn_retention.sqlite"
    with sqlite3.connect(db) as conn:
        conn.execute("PRAGMA foreign_keys=OFF")
        for name in frames: conn.execute(f'DROP TABLE IF EXISTS "{name}"')
        conn.commit()
        conn.executescript(ddl)
        for name in ["customers_clean"]+[n for n in frames if n!="customers_clean"]:
            frame=frames[name].copy()
            for col in frame:
                if pd.api.types.is_datetime64_any_dtype(frame[col]):
                    frame[col]=frame[col].dt.strftime("%Y-%m-%d").where(frame[col].notna(),None)
            frame.to_sql(name,conn,if_exists="append",index=False,chunksize=1000)
        if conn.execute("PRAGMA foreign_key_check").fetchall(): raise ValueError("Foreign key failure")
    return db

def query_definitions():
    queries=[
    ("01_total_customers","SELECT COUNT(*) AS total_customers FROM customers_clean"),
    ("02_active_customers","SELECT COUNT(*) AS active_customers FROM customers_clean WHERE subscription_end_date IS NULL"),
    ("03_churned_customers","SELECT COUNT(*) AS churned_customers FROM customers_clean WHERE subscription_end_date IS NOT NULL"),
    ("04_overall_churn_rate","SELECT 1.0 * SUM(CASE WHEN subscription_end_date IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) AS cumulative_churn_rate FROM customers_clean"),
    ("05_monthly_churn_trend","SELECT snapshot_month, SUM(is_active_start) AS opening_customers, SUM(opening_customer_churn) AS opening_churns, 1.0*SUM(opening_customer_churn)/NULLIF(SUM(is_active_start),0) AS churn_rate FROM monthly_snapshots GROUP BY snapshot_month ORDER BY snapshot_month"),
    ("06_monthly_retention_trend","SELECT snapshot_month, SUM(is_active_start)-SUM(opening_customer_churn) AS retained_opening_customers, 1.0*(SUM(is_active_start)-SUM(opening_customer_churn))/NULLIF(SUM(is_active_start),0) AS retention_rate FROM monthly_snapshots GROUP BY snapshot_month ORDER BY snapshot_month")]
    for number,dimension in enumerate(["plan_type","contract_type","acquisition_channel","region","payment_method","tenure_band","support_ticket_band","usage_band","payment_failures","engagement_band"],7):
        queries.append((f"{number:02d}_churn_by_{dimension}",f"SELECT {dimension}, COUNT(*) AS customers, SUM(churn_flag) AS churned_customers, AVG(churn_flag*1.0) AS cumulative_churn_rate FROM customers_clean GROUP BY {dimension} ORDER BY cumulative_churn_rate DESC"))
    queries.extend([
    ("17_average_revenue_per_customer","SELECT SUM(active_mrr)/NULLIF(SUM(active_flag),0) AS active_arpu, AVG(observed_clv) AS average_observed_clv FROM customers_clean"),
    ("18_revenue_lost_to_churn","SELECT snapshot_month, SUM(churned_mrr) AS mrr_removed_at_churn FROM monthly_snapshots GROUP BY snapshot_month ORDER BY snapshot_month"),
    ("19_clv_by_segment","SELECT customer_segment, COUNT(*) AS customers, AVG(observed_clv) AS mean_observed_clv, SUM(observed_clv) AS observed_revenue FROM customers_clean GROUP BY customer_segment ORDER BY observed_revenue DESC"),
    ("20_at_risk_customers","SELECT customer_id, plan_type, monthly_revenue, risk_score, risk_band, observed_clv FROM customers_clean WHERE active_flag=1 AND risk_score>60 ORDER BY monthly_revenue DESC, risk_score DESC, customer_id"),
    ("21_cohort_retention","WITH RECURSIVE ages(age) AS (SELECT 0 UNION ALL SELECT age+1 FROM ages WHERE age<23) SELECT c.acquisition_cohort AS cohort_month, a.age AS cohort_age, COUNT(*) AS cohort_size, CASE WHEN date(c.acquisition_cohort, '+'||a.age||' months') <= date('2026-08-01') THEN SUM(CASE WHEN c.subscription_end_date IS NULL OR c.subscription_end_date > date(c.acquisition_cohort, '+'||(a.age+1)||' months','-1 day') THEN 1 ELSE 0 END) END AS retained_customers FROM customers_clean c CROSS JOIN ages a GROUP BY c.acquisition_cohort,a.age ORDER BY c.acquisition_cohort,a.age"),
    ("22_renewal_behavior","SELECT contract_type, SUM(renewal_due) AS eligible_renewals, SUM(renewal_success) AS successful_renewals, 1.0*SUM(renewal_success)/NULLIF(SUM(renewal_due),0) AS renewal_rate FROM monthly_snapshots GROUP BY contract_type"),
    ("23_high_value_churned","SELECT customer_id, plan_type, churn_date, monthly_revenue, observed_clv FROM customers_clean WHERE churn_flag=1 AND high_value_flag=1 ORDER BY observed_clv DESC,customer_id"),
    ("24_customer_revenue_concentration","WITH ranked AS (SELECT active_mrr, NTILE(10) OVER (ORDER BY active_mrr DESC,customer_id) AS revenue_decile FROM customers_clean WHERE active_flag=1) SELECT revenue_decile,COUNT(*) AS customers,SUM(active_mrr) AS mrr,1.0*SUM(active_mrr)/(SELECT SUM(active_mrr) FROM customers_clean) AS mrr_share FROM ranked GROUP BY revenue_decile ORDER BY revenue_decile"),
    ("25_high_revenue_high_risk","SELECT customer_id, monthly_revenue, risk_score, customer_segment FROM customers_clean WHERE active_flag=1 AND high_value_flag=1 AND high_risk_flag=1 ORDER BY monthly_revenue DESC,risk_score DESC,customer_id"),
    ("26_customer_rollforward","SELECT snapshot_month,SUM(is_active_start) AS opening_customers,SUM(new_customer) AS acquired,SUM(churn_event) AS churned,SUM(is_active_end) AS closing_customers,SUM(is_active_start+new_customer-churn_event-is_active_end) AS reconciliation_difference FROM monthly_snapshots GROUP BY snapshot_month ORDER BY snapshot_month"),
    ("27_mrr_rollforward","SELECT snapshot_month,SUM(start_mrr) AS opening_mrr,SUM(new_mrr) AS new_mrr,SUM(churned_mrr) AS churned_mrr,SUM(end_mrr) AS closing_mrr,ROUND(SUM(start_mrr+new_mrr-churned_mrr-end_mrr),2) AS reconciliation_difference FROM monthly_snapshots GROUP BY snapshot_month ORDER BY snapshot_month"),
    ("28_revenue_at_risk","SELECT risk_band,COUNT(*) AS active_customers,SUM(monthly_revenue) AS active_mrr FROM customers_clean WHERE active_flag=1 GROUP BY risk_band"),
    ("29_early_and_long_tenure_churn","SELECT CASE WHEN tenure_months<3 THEN 'Early: under 3 months' WHEN tenure_months>=12 THEN 'Long: 12+ months' ELSE '3-11 months' END AS churn_tenure,COUNT(*) AS churned_customers,SUM(monthly_revenue) AS removed_mrr FROM customers_clean WHERE churn_flag=1 GROUP BY churn_tenure"),
    ("30_prechurn_revenue","SELECT SUM(s.recognized_revenue) AS revenue_generated_before_churn FROM monthly_snapshots s JOIN customers_clean c ON s.customer_id=c.customer_id WHERE c.churn_flag=1"),
    ("31_lagged_engagement_association","SELECT CASE WHEN s.engagement_score<35 THEN 'Low' WHEN s.engagement_score<65 THEN 'Medium' ELSE 'High' END AS engagement_band, COUNT(*) AS customer_month_exposures,SUM(CASE WHEN strftime('%Y-%m',c.churn_date)=strftime('%Y-%m',date(s.snapshot_month,'+1 month')) THEN 1 ELSE 0 END) AS next_month_churns FROM monthly_snapshots s JOIN customers_clean c ON s.customer_id=c.customer_id WHERE s.is_active_end=1 AND s.snapshot_month<'2026-08-01' GROUP BY engagement_band"),
    ("32_cohort_age_six","SELECT dimension,category,eligible_customers,retained_customers,retention_rate FROM retention_by_dimension ORDER BY dimension,retention_rate DESC")])
    return queries

def run_sql():
    db=build_database()
    queries=query_definitions()
    text="-- Each named query executes independently. Rates are fractions; amounts are USD.\n\n"
    with sqlite3.connect(db) as conn:
        for name,query in queries:
            text+=f"-- name: {name}\n{query};\n\n"
            write_csv(pd.read_sql_query(query,conn),ROOT/"outputs/sql_results"/f"{name}.csv")
    (ROOT/"sql/analysis_queries.sql").write_text(text,encoding="utf-8")
    print(f"SQLite: {len(queries)} queries executed and exported.")

if __name__=="__main__": run_sql()
