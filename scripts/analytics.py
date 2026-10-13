"""Analytics marts with explicit denominators and independent SQL reconciliation."""
import numpy as np
import pandas as pd
from scripts.common import ROOT, AS_OF, read_csv, write_csv, write_json, ratio
from scripts.data_cleaning import risk_components

def monthly_metrics(s):
    fields=["is_active_start","new_customer","churn_event","is_active_end","opening_customer_churn",
            "new_customer_churn","renewal_due","renewal_success","start_mrr","new_mrr","churned_mrr",
            "end_mrr","recognized_revenue"]
    m=s.groupby("snapshot_month")[fields].sum().reset_index().rename(columns={"snapshot_month":"month"})
    m["retained_opening_customers"]=m.is_active_start-m.opening_customer_churn
    m["churn_rate"]=m.opening_customer_churn.div(m.is_active_start.replace(0,np.nan))
    m["retention_rate"]=m.retained_opening_customers.div(m.is_active_start.replace(0,np.nan))
    m["renewal_rate"]=m.renewal_success.div(m.renewal_due.replace(0,np.nan))
    m["net_customer_growth"]=m.new_customer-m.churn_event
    m["customer_growth_rate"]=m.net_customer_growth.div(m.is_active_start.replace(0,np.nan))
    m["arpu"]=m.end_mrr.div(m.is_active_end.replace(0,np.nan))
    return m

def cohort_metrics(c):
    rows=[]
    for cohort,g in c.groupby("acquisition_cohort"):
        for age in range(24):
            month=cohort+pd.DateOffset(months=age)
            observed=month.to_period("M")<=AS_OF.to_period("M")
            retained=int((g.subscription_end_date.isna() | g.subscription_end_date.gt(month+pd.offsets.MonthEnd(0))).sum()) if observed else None
            rows.append({"cohort_month":cohort,"cohort_age":age,"cohort_size":len(g),
                         "retained_customers":retained,"retention_rate":retained/len(g) if observed else None,"is_observed":int(observed)})
    return pd.DataFrame(rows)

def performance(c,dimension):
    p=c.groupby(dimension,dropna=False).agg(total_customers=("customer_id","size"),
         active_customers=("active_flag","sum"),churned_customers=("churn_flag","sum"),
         active_mrr=("active_mrr","sum"),revenue_at_risk=("revenue_at_risk","sum"),
         observed_revenue=("observed_clv","sum"),average_clv=("observed_clv","mean"),
         average_tenure=("tenure_months","mean")).reset_index()
    p["churn_rate"]=p.churned_customers/p.total_customers
    p["retention_rate"]=p.active_customers/p.total_customers
    p["arpu"]=p.active_mrr.div(p.active_customers.replace(0,np.nan))
    return p

def drivers(c,s):
    p=s.merge(c[["customer_id","subscription_start_date","churn_date"]],on="customer_id",validate="many_to_one")
    p=p[p.is_active_end.eq(1) & p.snapshot_month.lt(AS_OF.to_period("M").start_time)].copy()
    p["label_month"]=p.snapshot_month+pd.offsets.MonthBegin(1)
    p["next_month_churn"]=(p.churn_date.dt.to_period("M")==p.label_month.dt.to_period("M")).astype(int)
    for col,source,bins,labels in [
        ("tenure_band","customer_age_months",[-1,3,6,12,100],["0-2 months","3-5 months","6-11 months","12+ months"]),
        ("support_ticket_band","support_tickets",[-1,1,3,100],["0","1-2","3+"]),
        ("usage_band","monthly_usage",[-1,80,180,10000],["Low","Medium","High"]),
        ("engagement_band","engagement_score",[-1,35,65,101],["Low","Medium","High"]),
        ("fee_band","monthly_fee",[0,40,80,200],["Under 40","40-79","80+"]),
        ("discount_band","discount_percentage",[-1,.001,.101,1],["None","Up to 10%","Over 10%"])]:
        p[col]=pd.cut(p[source],bins,right=False,labels=labels).astype(str)
    output=[]
    for col in ["tenure_band","plan_type","contract_type","fee_band","discount_band","payment_failures",
                "payment_method","login_frequency","feature_usage_score","usage_band","engagement_band",
                "support_ticket_band","complaints","auto_renew","acquisition_channel","region"]:
        group=p.groupby(col,dropna=False).agg(exposures=("customer_id","size"),
                next_month_churns=("next_month_churn","sum"),distinct_customers=("customer_id","nunique")).reset_index()
        group["driver"]=col
        group["category"]=group[col].astype(str)
        group["next_month_churn_rate"]=group.next_month_churns/group.exposures
        output.append(group[["driver","category","exposures","distinct_customers","next_month_churns","next_month_churn_rate"]])
    return pd.concat(output,ignore_index=True)

def analyze():
    c,s=read_csv("customers_clean"),read_csv("monthly_snapshots")
    m=monthly_metrics(s)
    write_csv(m,ROOT/"data/processed/monthly_churn_kpis.csv")
    write_csv(m[["month","is_active_start","retained_opening_customers","opening_customer_churn","retention_rate","renewal_due","renewal_success","renewal_rate"]],
              ROOT/"data/processed/monthly_retention_kpis.csv")
    write_csv(cohort_metrics(c),ROOT/"data/processed/cohort_retention.csv")
    fields=["customer_id","as_of_date","plan_type","contract_type","acquisition_channel","region",
            "monthly_revenue","tenure_months","observed_clv","engagement_score","customer_segment",
            "churn_flag","active_flag","risk_score","risk_band","high_value_flag","high_risk_flag",
            "active_mrr","revenue_at_risk","retention_priority"]
    write_csv(c[fields],ROOT/"data/processed/customer_segments.csv")
    r=c[fields].copy()
    for name,values in risk_components(c).items():
        r[name]=values.where(c.active_flag.eq(1)).astype("Int64")
    write_csv(r,ROOT/"data/processed/customer_risk_scores.csv")
    for dim,name in [("plan_type","plan_performance"),("acquisition_channel","channel_performance"),("region","geography_performance")]:
        write_csv(performance(c,dim),ROOT/"data/processed"/f"{name}.csv")
    write_csv(m[["month","start_mrr","new_mrr","churned_mrr","end_mrr","recognized_revenue","is_active_end","arpu"]],ROOT/"data/processed/revenue_churn_impact.csv")
    write_csv(drivers(c,s),ROOT/"data/processed/churn_driver_associations.csv")
    support=c.groupby(["support_ticket_band","usage_band"]).agg(customers=("customer_id","size"),churned_customers=("churn_flag","sum"),
            active_mrr=("active_mrr","sum"),average_engagement=("engagement_score","mean"),revenue_at_risk=("revenue_at_risk","sum")).reset_index()
    support["churn_rate"]=support.churned_customers/support.customers
    write_csv(support,ROOT/"data/processed/support_usage_analysis.csv")
    eligible=c[c.acquisition_cohort.le(AS_OF.to_period("M").start_time-pd.DateOffset(months=6))].copy()
    endpoint=eligible.acquisition_cohort+pd.DateOffset(months=6)+pd.offsets.MonthEnd(0)
    eligible["retained_at_month_6"]=(eligible.subscription_end_date.isna() | eligible.subscription_end_date.gt(endpoint)).astype(int)
    retention=[]
    for col in ["plan_type","contract_type","acquisition_channel","region"]:
        g=eligible.groupby(col).agg(eligible_customers=("customer_id","size"),retained_customers=("retained_at_month_6","sum")).reset_index()
        g["dimension"]=col
        g["category"]=g[col].astype(str)
        g["retention_rate"]=g.retained_customers/g.eligible_customers
        retention.append(g[["dimension","category","eligible_customers","retained_customers","retention_rate"]])
    write_csv(pd.concat(retention,ignore_index=True),ROOT/"data/processed/retention_by_dimension.csv")
    last=m.iloc[-1]
    k={"as_of_date":AS_OF.date().isoformat(),"currency":"USD","total_customers":len(c),
       "active_customers":int(c.active_flag.sum()),"churned_customers":int(c.churn_flag.sum()),
       "cumulative_churn_rate":float(c.churn_flag.mean()),"active_customer_share":float(c.active_flag.mean()),
       "latest_month_churn_rate":float(last.churn_rate),"latest_month_retention_rate":float(last.retention_rate),
       "average_customer_tenure_months":float(c.tenure_months.mean()),"monthly_recurring_revenue":float(c.active_mrr.sum()),
       "arpu":ratio(c.active_mrr.sum(),c.active_flag.sum()),"latest_month_churned_mrr":float(last.churned_mrr),
       "total_mrr_removed_at_churn_events":float(s.churned_mrr.sum()),"revenue_at_risk":float(c.revenue_at_risk.sum()),
       "latest_month_renewal_rate":float(last.renewal_rate),"average_support_tickets_latest_observation":float(c.support_tickets.mean()),
       "average_monthly_usage_latest_observation":float(c.monthly_usage.mean()),"average_observed_clv":float(c.observed_clv.mean()),
       "total_observed_revenue":float(s.recognized_revenue.sum()),"revenue_generated_before_churn":float(c.loc[c.churn_flag.eq(1),"observed_clv"].sum()),
       "high_risk_customers":int(c.high_risk_flag.sum()),"latest_month_net_customer_growth":int(last.net_customer_growth),
       "customer_month_records":len(s),"cohorts":int(c.acquisition_cohort.nunique())}
    write_json(k,ROOT/"outputs/executive_kpis.json")
    print(f"Analytics: MRR USD {k['monthly_recurring_revenue']:,.2f}; monthly churn {k['latest_month_churn_rate']:.2%}.")
    return k

if __name__=="__main__": analyze()
