"""Conservative cleaning: repair deterministic fields; quarantine ambiguous records."""
import numpy as np
import pandas as pd
from scripts.common import ROOT, AS_OF, DATE_COLUMNS, ensure_dirs, write_csv, write_json

def clean_customers(raw):
    c = raw.drop_duplicates().copy()
    duplicate_rows = len(raw)-len(c)
    reasons = pd.Series("", index=c.index)
    repairs=[]
    def reject(mask, reason):
        reasons.loc[mask] += reason + ";"
    def repair(col, values, rule):
        values = pd.Series(values, index=c.index)
        mask = ~(c[col].eq(values) | (c[col].isna() & values.isna()))
        for i in c.index[mask]:
            repairs.append({"customer_id":c.at[i,"customer_id"],"field":col,"old_value":str(c.at[i,col]),"new_value":str(values.at[i]),"rule":rule})
        c[col]=values
    reject(c.customer_id.isna() | c.customer_id.duplicated(keep=False), "missing_or_conflicting_customer_id")
    for col in set(c) & DATE_COLUMNS:
        parsed=pd.to_datetime(c[col],errors="coerce")
        reject(c[col].notna() & parsed.isna(), "unparseable_"+col)
        c[col]=parsed
    required=["signup_date","subscription_start_date","last_activity_date"]
    reject(c[required].isna().any(axis=1),"missing_required_date")
    reject(c.subscription_start_date.lt(c.signup_date) | c.subscription_start_date.gt(AS_OF),"invalid_subscription_start")
    reject(c.subscription_end_date.notna() & (c.subscription_end_date.lt(c.subscription_start_date) | c.subscription_end_date.gt(AS_OF)),"invalid_subscription_end")
    reject(c.churn_date.notna() & (c.churn_date.lt(c.subscription_start_date) | c.churn_date.gt(AS_OF)),"invalid_churn_date")
    reject(c.churn_date.isna().ne(c.subscription_end_date.isna()) | (c.churn_date.notna() & c.churn_date.ne(c.subscription_end_date)),"conflicting_end_and_churn_dates")
    reject(c.last_activity_date.lt(c.subscription_start_date) | c.last_activity_date.gt(c.subscription_end_date.fillna(AS_OF)),"invalid_last_activity")
    for col in ["monthly_fee","discount_percentage","tenure_months","churn_flag","auto_renew",
                "support_tickets","complaints","login_frequency","monthly_usage","feature_usage_score","payment_failures","late_payments"]:
        c[col]=pd.to_numeric(c[col],errors="coerce")
    reject(c.monthly_fee.isna() | c.monthly_fee.lt(0),"invalid_monthly_fee")
    reject(c.discount_percentage.isna() | ~c.discount_percentage.between(0,1),"invalid_discount")
    telemetry=["support_tickets","complaints","login_frequency","monthly_usage","feature_usage_score","payment_failures","late_payments"]
    reject(c[telemetry].isna().any(axis=1) | c[telemetry].lt(0).any(axis=1) | c.feature_usage_score.gt(100) | ~c.auto_renew.isin([0,1]),"invalid_telemetry_or_auto_renew")
    repair("plan_type",c.plan_type.astype(str).str.strip().str.lower().str.replace(r"\s+plan$","",regex=True).str.title(),"standardize_plan")
    reject(~c.plan_type.isin(["Basic","Standard","Premium"]),"unknown_plan")
    repair("payment_method",c.payment_method.fillna("Unknown"),"missing_category_to_unknown")
    # Region inferred only from a complete, explicit city mapping supplied by the synthetic scenario.
    city_region={"New York":"Northeast","Boston":"Northeast","Chicago":"Midwest","Detroit":"Midwest","Austin":"South","Atlanta":"South","Seattle":"West","Denver":"West"}
    repair("region",c.region.fillna(c.city.map(city_region)).fillna("Unknown"),"city_reference_mapping")
    repair("churn_flag",c.subscription_end_date.notna().astype(int),"validated_end_date_authoritative")
    repair("customer_status",np.where(c.churn_flag.eq(1),"Cancelled","Active"),"validated_end_date_authoritative")
    repair("tenure_months",((c.subscription_end_date.fillna(AS_OF)-c.subscription_start_date).dt.days/30.4375).round(4),"recompute_tenure_from_dates")
    quarantine=c.loc[reasons.ne("")].copy()
    quarantine["quarantine_reason"]=reasons[reasons.ne("")].str.rstrip(";")
    c=c.loc[reasons.eq("")].copy().reset_index(drop=True)
    report={"raw_customer_rows":len(raw),"exact_duplicate_customer_rows_removed":duplicate_rows,
            "quarantined_customers":len(quarantine),"clean_customers":len(c),
            "repair_events":len(repairs),"repairs_by_rule":pd.Series([r["rule"] for r in repairs]).value_counts().to_dict(),
            "quarantine_reason_counts":quarantine.quarantine_reason.str.split(";").explode().value_counts().to_dict(),
            "policy":"Exact duplicates removed. Conflicting IDs and invalid financial/date records quarantined; no guessed fees or end dates. Repairs are logged before quarantine, so logs can include quarantined IDs."}
    return c,quarantine,pd.DataFrame(repairs),report

def risk_components(c):
    return pd.DataFrame({
        "risk_inactivity":np.where(c.days_since_last_activity.ge(14),20,0),
        "risk_engagement":np.where(c.engagement_score.lt(35),15,0),
        "risk_support":np.where(c.support_tickets.ge(3),10,0),
        "risk_complaints":np.where(c.complaints.ge(1),10,0),
        "risk_payment":np.where(c.payment_failures.ge(1),15,0),
        "risk_usage":np.where(c.monthly_usage.lt(80),10,0),
        "risk_new":np.where(c.tenure_months.lt(3),5,0),
        "risk_renewal":np.where(c.auto_renew.eq(0),5,0),
        "risk_decline":np.where(c.recent_usage_decline.ge(.30),10,0),
    },index=c.index)

def clean():
    ensure_dirs()
    raw=pd.read_csv(ROOT/"data/raw/customers.csv")
    c,q,repairs,report=clean_customers(raw)
    raw_s=pd.read_csv(ROOT/"data/raw/monthly_snapshots.csv")
    s=raw_s.drop_duplicates().copy()
    report["raw_snapshot_rows"]=len(raw_s)
    report["duplicate_snapshot_rows_removed"]=len(raw_s)-len(s)
    excluded=s[~s.customer_id.isin(c.customer_id)].copy()
    excluded["quarantine_reason"]="parent_customer_quarantined"
    write_csv(excluded,ROOT/"data/quarantine/monthly_snapshots.csv")
    s=s[s.customer_id.isin(c.customer_id)].copy()
    s["snapshot_month"]=pd.to_datetime(s.snapshot_month)
    s["last_activity_date"]=pd.to_datetime(s.last_activity_date)
    if s.duplicated(["customer_id","snapshot_month"]).any():
        raise ValueError("Conflicting customer-month snapshots; source review required.")
    s=s.sort_values(["customer_id","snapshot_month"]).reset_index(drop=True)
    s["engagement_score"]=(.4*(s.login_frequency/25).clip(0,1)*100 + .35*(s.monthly_usage/250).clip(0,1)*100 + .25*s.feature_usage_score).round(4)
    s["prior_usage_mean"]=s.groupby("customer_id").monthly_usage.transform(lambda x:x.shift().rolling(3,min_periods=1).mean())
    s["recent_usage_decline"]=(1-s.monthly_usage/s.prior_usage_mean.replace(0,np.nan)).clip(0,1)
    latest=s.groupby("customer_id",sort=False).tail(1).set_index("customer_id")
    c["engagement_score"]=c.customer_id.map(latest.engagement_score)
    c["recent_usage_decline"]=c.customer_id.map(latest.recent_usage_decline)
    c["as_of_date"]=AS_OF
    c["observation_date"]=c.subscription_end_date.fillna(AS_OF)
    c["customer_tenure"]=c.tenure_months
    c["customer_age_months"]=(c.observation_date.dt.year-c.subscription_start_date.dt.year)*12+c.observation_date.dt.month-c.subscription_start_date.dt.month
    c["days_since_last_activity"]=(c.observation_date-c.last_activity_date).dt.days
    c["monthly_revenue"]=(c.monthly_fee*(1-c.discount_percentage)).round(2)
    c["observed_clv"]=c.customer_id.map(s.groupby("customer_id").recognized_revenue.sum()).round(2)
    c["support_ticket_band"]=pd.cut(c.support_tickets,[-1,0,2,float("inf")],labels=["0","1-2","3+"]).astype(str)
    c["usage_band"]=pd.cut(c.monthly_usage,[-1,80,180,float("inf")],right=False,labels=["Low","Medium","High"]).astype(str)
    c["engagement_band"]=pd.cut(c.engagement_score,[-1,35,65,float("inf")],right=False,labels=["Low","Medium","High"]).astype(str)
    c["tenure_band"]=pd.cut(c.tenure_months,[-1,3,6,12,float("inf")],right=False,labels=["0-2 months","3-5 months","6-11 months","12+ months"]).astype(str)
    c["acquisition_cohort"]=c.subscription_start_date.dt.to_period("M").dt.to_timestamp()
    c["churn_month"]=c.churn_date.dt.to_period("M").dt.to_timestamp()
    components=risk_components(c)
    c["risk_score"]=components.sum(axis=1).where(c.churn_flag.eq(0)).astype("Int64")
    c["risk_band"]=pd.cut(c.risk_score.astype(float),[-1,30,60,100],labels=["Low Risk","Medium Risk","High Risk"]).astype(object).fillna("Not Applicable")
    c["high_value_flag"]=(c.monthly_revenue.ge(80)).astype(int)
    active=c.churn_flag.eq(0)
    c["active_flag"]=active.astype(int)
    c["high_risk_flag"]=(active & c.risk_band.eq("High Risk")).astype(int)
    c["active_mrr"]=c.monthly_revenue*c.active_flag
    c["revenue_at_risk"]=c.monthly_revenue*c.high_risk_flag
    conditions=[~active & c.high_value_flag.eq(1),~active,
                active & c.high_value_flag.eq(1) & c.high_risk_flag.eq(1),active & c.high_risk_flag.eq(1),
                active & c.days_since_last_activity.ge(30),active & c.tenure_months.lt(3),
                active & c.tenure_months.ge(12) & c.high_value_flag.eq(1) & c.engagement_score.ge(50),
                active & c.tenure_months.ge(12) & c.engagement_score.ge(50),active & c.engagement_score.ge(65),active & c.engagement_score.lt(35)]
    c["customer_segment"]=np.select(conditions,["Churned High Value","Churned Low Value","High Value At Risk","At Risk","Dormant","New Customers","Loyal High Value","Loyal Standard","Highly Engaged","Low Engagement"],default="Core Customers")
    c["retention_priority"]=np.where(~active,"Churned",np.where(c.high_value_flag.eq(1),"High Value","Low Value")+" + "+np.where(c.high_risk_flag.eq(1),"High Risk","Low/Medium Risk"))
    write_csv(c,ROOT/"data/processed/customers_clean.csv")
    write_csv(s,ROOT/"data/processed/monthly_snapshots.csv")
    write_csv(q,ROOT/"data/quarantine/customers.csv")
    write_csv(repairs,ROOT/"data/quarantine/repair_log.csv")
    report["snapshot_rows_excluded_with_quarantined_parent"]=len(excluded)
    report["clean_snapshot_rows"]=len(s)
    write_json(report,ROOT/"outputs/data_quality_report.json")
    print(f"Cleaned {len(c):,} customers; quarantined {len(q):,}; retained {len(s):,} monthly snapshots.")
    return c,s

if __name__=="__main__": clean()
