"""Independent reconciliation checks; writes a machine-readable validation report."""
import json
import sqlite3
import numpy as np
import pandas as pd
from scripts.common import ROOT, AS_OF, read_csv, write_json
from scripts.sql_analysis import KEYS
from scripts.model import FEATURES

def validate(raise_on_failure=True):
    c=read_csv("customers_clean");s=read_csv("monthly_snapshots")
    m=read_csv("monthly_churn_kpis");co=read_csv("cohort_retention")
    k=json.loads((ROOT/"outputs/executive_kpis.json").read_text())
    q=json.loads((ROOT/"outputs/data_quality_report.json").read_text())
    checks=[]
    def check(name,condition,detail=""):
        checks.append({"check":name,"passed":bool(condition),"detail":str(detail)})
    def close(a,b,tol=.011):return np.allclose(a,b,atol=tol,rtol=0,equal_nan=True)
    check("minimum_customer_population",len(c)>=10000,len(c))
    check("unique_customer_ids",c.customer_id.is_unique)
    check("unique_customer_months",~s.duplicated(["customer_id","snapshot_month"]).any())
    check("active_plus_churned",int(c.active_flag.sum()+c.churn_flag.sum())==len(c))
    check("date_based_status",c.churn_flag.eq(c.subscription_end_date.notna().astype(int)).all())
    check("status_labels",c.customer_status.eq(np.where(c.churn_flag.eq(1),"Cancelled","Active")).all())
    check("customer_count_kpi",len(c)==k["total_customers"])
    check("active_count_kpi",int(c.active_flag.sum())==k["active_customers"])
    check("churn_count_kpi",int(c.churn_flag.sum())==k["churned_customers"])
    check("cumulative_churn_kpi",close(c.churn_flag.mean(),k["cumulative_churn_rate"],1e-8))
    check("active_share_kpi",close(c.active_flag.mean(),k["active_customer_share"],1e-8))
    check("monthly_churn_kpi",close(m.iloc[-1].churn_rate,k["latest_month_churn_rate"],1e-8))
    check("monthly_retention_complement",close(m.churn_rate+m.retention_rate,pd.Series(np.where(m.is_active_start.eq(0),np.nan,1)),1e-8))
    check("fees_nonnegative",c.monthly_fee.ge(0).all())
    check("discount_fraction_range",c.discount_percentage.between(0,1).all())
    check("signup_before_start",c.signup_date.le(c.subscription_start_date).all())
    check("start_before_cutoff",c.subscription_start_date.le(AS_OF).all())
    check("churn_not_future",(c.churn_date.dropna()<=AS_OF).all())
    check("churn_after_start",(c.churn_date.isna()|c.churn_date.ge(c.subscription_start_date)).all())
    check("end_equals_churn",(c.churn_date.eq(c.subscription_end_date)|(c.churn_date.isna()&c.subscription_end_date.isna())).all())
    check("last_activity_valid",(c.last_activity_date.ge(c.subscription_start_date)&c.last_activity_date.le(c.observation_date)).all())
    check("tenure_recomputed",close(c.tenure_months,((c.observation_date-c.subscription_start_date).dt.days/30.4375).round(4),1e-8))
    check("snapshot_foreign_keys",s.customer_id.isin(c.customer_id).all())
    check("raw_customer_accounting",q["raw_customer_rows"]==q["exact_duplicate_customer_rows_removed"]+q["quarantined_customers"]+len(c))
    check("raw_snapshot_accounting",q["raw_snapshot_rows"]==q["duplicate_snapshot_rows_removed"]+q["snapshot_rows_excluded_with_quarantined_parent"]+len(s))
    check("monthly_rate_normalization",close(c.monthly_revenue,(c.monthly_fee*(1-c.discount_percentage)).round(2)))
    check("mrr_current",close(c.loc[c.churn_flag.eq(0),"monthly_revenue"].sum(),k["monthly_recurring_revenue"]))
    check("arpu",close(k["monthly_recurring_revenue"]/k["active_customers"],k["arpu"],1e-8))
    check("risk_points_range",c.loc[c.active_flag.eq(1),"risk_score"].between(0,100).all())
    check("churned_risk_not_applicable",c.loc[c.churn_flag.eq(1),"risk_score"].isna().all())
    check("risk_bands",c.loc[c.risk_score.gt(60),"risk_band"].eq("High Risk").all() and c.loc[c.risk_score.le(30),"risk_band"].eq("Low Risk").all() and c.loc[c.risk_score.between(31,60),"risk_band"].eq("Medium Risk").all())
    check("at_risk_mrr_independent",close(c.loc[c.active_flag.eq(1)&c.risk_score.gt(60),"monthly_revenue"].sum(),k["revenue_at_risk"]))
    check("high_risk_count",int((c.active_flag.eq(1)&c.risk_score.gt(60)).sum())==k["high_risk_customers"])
    check("risk_below_total_mrr",0<=k["revenue_at_risk"]<=k["monthly_recurring_revenue"])
    check("clv_from_monthly_revenue",close(c.set_index("customer_id").observed_clv.sort_index(),s.groupby("customer_id").recognized_revenue.sum().sort_index()))
    check("observed_revenue_total",close(c.observed_clv.sum(),k["total_observed_revenue"]))
    check("prechurn_revenue",close(c.loc[c.churn_flag.eq(1),"observed_clv"].sum(),k["revenue_generated_before_churn"]))
    check("one_cancellation_per_customer",s.groupby("customer_id").churn_event.sum().max()<=1)
    check("cancellation_events_reconcile",s.churn_event.sum()==c.churn_flag.sum())
    check("new_customer_events_reconcile",s.new_customer.sum()==len(c))
    check("monthly_customer_bridge",m.is_active_start.add(m.new_customer).sub(m.churn_event).eq(m.is_active_end).all())
    check("monthly_mrr_bridge",close(m.start_mrr+m.new_mrr-m.churned_mrr,m.end_mrr))
    check("consecutive_customer_stocks",np.array_equal(m.is_active_end.iloc[:-1],m.is_active_start.iloc[1:]))
    check("consecutive_mrr_stocks",close(m.end_mrr.iloc[:-1],m.start_mrr.iloc[1:]))
    check("closing_customers_current",m.iloc[-1].is_active_end==k["active_customers"])
    check("closing_mrr_current",close(m.iloc[-1].end_mrr,k["monthly_recurring_revenue"]))
    check("renewals_subset",s.renewal_success.le(s.renewal_due).all())
    check("renewal_schedule",s.renewal_due.eq((s.customer_age_months.gt(0)&(s.contract_type.eq("Monthly")|s.customer_age_months.mod(12).eq(0))).astype(int)).all())
    check("renewal_outcomes",s.renewal_success.eq(s.renewal_due*s.is_active_end).all())
    check("renewal_kpi",close(k["latest_month_renewal_rate"],m.iloc[-1].renewal_success/m.iloc[-1].renewal_due,1e-8))
    check("first_month_denominator_null",pd.isna(m.iloc[0].churn_rate) and pd.isna(m.iloc[0].retention_rate))
    independent=[]
    for row in m.itertuples():
        month=row.month; end=month+pd.offsets.MonthEnd(0)
        opening=c.subscription_start_date.lt(month)&(c.churn_date.isna()|c.churn_date.ge(month))
        cancellations=c.churn_date.between(month,end)
        closing=c.subscription_start_date.le(end)&(c.churn_date.isna()|c.churn_date.gt(end))
        independent.append(opening.sum()==row.is_active_start and (opening&cancellations).sum()==row.opening_customer_churn and cancellations.sum()==row.churn_event and closing.sum()==row.is_active_end)
    check("all_monthly_counts_from_customer_dates",all(independent))
    joined=s.merge(c[["customer_id","subscription_start_date","subscription_end_date"]],on="customer_id",validate="many_to_one")
    month_end=joined.snapshot_month+pd.offsets.MonthEnd(0)
    starts=joined.subscription_start_date.where(joined.subscription_start_date.ge(joined.snapshot_month),joined.snapshot_month)
    ends=joined.subscription_end_date.where(joined.subscription_end_date.notna()&joined.subscription_end_date.lt(month_end),month_end)
    expected_revenue=(joined.monthly_revenue*((ends-starts).dt.days+1)/month_end.dt.day).round(2)
    check("billing_proration_independent",close(joined.recognized_revenue,expected_revenue))
    check("no_post_cancellation_snapshots",(joined.subscription_end_date.isna()|joined.snapshot_month.le(joined.subscription_end_date)).all())
    check("future_cohort_values_null",co.loc[co.is_observed.eq(0),["retained_customers","retention_rate"]].isna().all().all())
    check("observed_cohort_values_present",co.loc[co.is_observed.eq(1),["retained_customers","retention_rate"]].notna().all().all())
    check("cohort_bounds",co.retention_rate.dropna().between(0,1).all())
    check("cohort_denominators",co.cohort_size.eq(co.cohort_month.map(c.groupby("acquisition_cohort").size())).all())
    check("cohort_survival_monotone",all(g.retention_rate.dropna().diff().dropna().le(1e-8).all() for _,g in co.groupby("cohort_month")))
    co_obs=co[co.is_observed.eq(1)]
    snap_counts=s[s.is_active_end.eq(1)].groupby(["snapshot_month","customer_age_months"]).size()
    cohort_ok=[]
    for row in co_obs.itertuples():
        month=row.cohort_month+pd.DateOffset(months=row.cohort_age)
        cohort_ok.append(row.retained_customers==snap_counts.get((month,row.cohort_age),0))
    check("cohort_retention_from_snapshot_survival",all(cohort_ok))
    check("cohort_month_zero_not_forced",co.loc[co.cohort_age.eq(0),"retention_rate"].lt(1).any())
    check("cohort_rate_arithmetic",close(co.retention_rate,co.retained_customers/co.cohort_size,1e-8))
    for name in ["customer_segments","customer_risk_scores"]:
        table=read_csv(name)
        check(name+"_count_and_keys",set(table.customer_id)==set(c.customer_id) and table.customer_id.is_unique)
        check(name+"_revenue",close(table.active_mrr.sum(),c.active_mrr.sum()))
    for name in ["plan_performance","channel_performance","geography_performance"]:
        table=read_csv(name)
        check(name+"_customer_count",table.total_customers.sum()==len(c))
        check(name+"_mrr",close(table.active_mrr.sum(),c.active_mrr.sum()))
    risks=read_csv("customer_risk_scores")
    component_columns=[x for x in risks if x.startswith("risk_") and x not in ["risk_score","risk_band"]]
    check("risk_component_sum",close(risks.loc[risks.active_flag.eq(1),component_columns].sum(axis=1),risks.loc[risks.active_flag.eq(1),"risk_score"],1e-8))
    check("segmentation_coverage",c.customer_segment.notna().all() and c.groupby("customer_segment").size().sum()==len(c))
    db=ROOT/"outputs/churn_retention.sqlite"
    with sqlite3.connect(db) as conn:
        check("sqlite_integrity",conn.execute("PRAGMA integrity_check").fetchone()[0]=="ok")
        check("sqlite_foreign_keys",not conn.execute("PRAGMA foreign_key_check").fetchall())
        sql=conn.execute("SELECT COUNT(*),SUM(churn_flag),SUM(active_mrr),SUM(revenue_at_risk),SUM(observed_clv) FROM customers_clean").fetchone()
        check("sql_python_executive",close(sql,[len(c),c.churn_flag.sum(),c.active_mrr.sum(),c.revenue_at_risk.sum(),c.observed_clv.sum()]))
    sql_co=pd.read_csv(ROOT/"outputs/sql_results/21_cohort_retention.csv")
    check("sql_python_cohort",close(sql_co.retained_customers,co.sort_values(["cohort_month","cohort_age"]).retained_customers))
    sql_m=pd.read_csv(ROOT/"outputs/sql_results/05_monthly_churn_trend.csv")
    check("sql_python_monthly_churn",close(sql_m.churn_rate,m.churn_rate,1e-8))
    check("all_sql_outputs",len(list((ROOT/"outputs/sql_results").glob("*.csv")))==32)
    split=pd.read_csv(ROOT/"outputs/model/split_audit.csv",parse_dates=["snapshot_month","label_month"])
    sets={n:set(split.loc[split.split.eq(n),"customer_id"]) for n in ["train","validation","test"]}
    check("model_customer_disjoint",not(sets["train"]&sets["validation"] or sets["train"]&sets["test"] or sets["validation"]&sets["test"]))
    train=split[split.split.eq("train")]; val=split[split.split.eq("validation")];test=split[split.split.eq("test")]
    check("model_temporal_separation",train.label_month.max()<val.snapshot_month.min() and val.label_month.max()<test.snapshot_month.min())
    check("model_labels_fully_observed",split.label_month.max()<=AS_OF)
    check("model_no_leakage_features",not(set(FEATURES)&{"churn_date","churn_flag","customer_status","subscription_end_date","observed_clv","customer_id","risk_band"}))
    metrics=json.loads((ROOT/"outputs/model/model_metrics.json").read_text())
    matrix=np.array(metrics["models"][metrics["selected_model"]]["test"]["confusion_matrix"])
    check("model_test_matrix_total",matrix.sum()==len(test))
    check("model_test_matrix_positives",matrix[1,:].sum()==test.next_month_churn.sum())
    contracts=json.loads((ROOT/"quicksight/dataset_contracts.json").read_text())
    for name,contract in contracts.items():
        frame=pd.read_csv(ROOT/"data/processed"/f"{name}.csv")
        check("dataset_contract_"+name,len(frame)==contract["rows"] and list(frame)==[x["name"] for x in contract["columns"]] and not frame.duplicated(KEYS[name]).any())
    report={"passed":sum(x["passed"] for x in checks),"failed":sum(not x["passed"] for x in checks),"total":len(checks),
            "status":"PASS" if all(x["passed"] for x in checks) else "FAIL","checks":checks,
            "scope":"Executed locally: CSV, customer-date/snapshot/billing reconciliation, SQLite, cohorts, risk and ML split validation. Live AWS validation is pending."}
    write_json(report,ROOT/"outputs/validation_report.json")
    print(f"Validation: {report['passed']}/{report['total']} passed.")
    if raise_on_failure and report["failed"]:
        raise AssertionError("Failed checks: "+", ".join(x["check"] for x in checks if not x["passed"]))
    return report

if __name__=="__main__":validate()
