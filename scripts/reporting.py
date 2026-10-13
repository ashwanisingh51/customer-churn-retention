"""Evidence-based charts, insights, resume bullets and a local dashboard preview."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import os
from scripts.common import ROOT
os.environ.setdefault("MPLCONFIGDIR", str(ROOT/".cache/matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter, FuncFormatter
from scripts.common import ROOT, read_csv

BLUE="#2563eb"; TEAL="#0f766e"; RED="#dc4c64"; NAVY="#15263e"
def finish(fig,name):
    fig.savefig(ROOT/"outputs/charts"/f"{name}.png",dpi=160,bbox_inches="tight",facecolor=fig.get_facecolor())
    plt.close(fig)

def charts():
    plt.rcParams.update({"font.family":"DejaVu Sans","axes.spines.top":False,"axes.spines.right":False,
                         "axes.titleweight":"bold","axes.titlesize":14,"axes.labelcolor":NAVY,
                         "text.color":NAVY,"axes.edgecolor":"#cbd5e1","figure.facecolor":"#ffffff"})
    c=read_csv("customers_clean"); m=read_csv("monthly_churn_kpis"); co=read_csv("cohort_retention")
    d=read_csv("churn_driver_associations")
    for field,name,title,color in [("churn_rate","monthly_churn_rate","Monthly churn of opening customers",RED),
        ("retention_rate","monthly_retention_rate","Monthly retention of opening customers",TEAL),
        ("end_mrr","monthly_mrr","Month-end recurring revenue",BLUE),
        ("net_customer_growth","net_customer_growth","New customers minus cancellations",BLUE)]:
        fig,ax=plt.subplots(figsize=(10,4))
        ax.plot(m.month,m[field],marker="o",markersize=3,color=color,linewidth=2)
        ax.set_title(title,loc="left",pad=15)
        ax.grid(axis="y",alpha=.18)
        if "rate" in field: ax.yaxis.set_major_formatter(PercentFormatter(1))
        elif field=="end_mrr": ax.yaxis.set_major_formatter(FuncFormatter(lambda x,pos:f"USD {x/1000:.0f}K"))
        ax.set_xlabel("Calendar month")
        fig.autofmt_xdate()
        finish(fig,name)
    for driver,name,title in [("plan_type","churn_by_plan","Plan"),
        ("contract_type","churn_by_contract","Contract"),
        ("acquisition_channel","churn_by_channel","Acquisition channel"),
        ("tenure_band","churn_by_tenure","Tenure at observation"),
        ("payment_failures","churn_by_payment_failures","Payment failures"),
        ("engagement_band","churn_by_engagement","Engagement"),
        ("support_ticket_band","churn_by_support_tickets","Support tickets"),
        ("usage_band","churn_by_usage","Usage"),
        ("payment_method","churn_by_payment_method","Payment method"),
        ("region","churn_by_geography","Region")]:
        g=d[d.driver.eq(driver)].sort_values("next_month_churn_rate")
        fig,ax=plt.subplots(figsize=(9,4.6))
        ax.barh(g.category,g.next_month_churn_rate,color=BLUE,height=.6)
        ax.set_title(f"Next-month churn by {title.lower()}",loc="left",pad=18)
        ax.set_xlabel("Cancellations / eligible customer-month exposures")
        ax.xaxis.set_major_formatter(PercentFormatter(1))
        ax.set_xlim(0,g.next_month_churn_rate.max()*1.4)
        for y,(_,row) in enumerate(g.iterrows()):
            ax.text(row.next_month_churn_rate+.001,y,f"{row.next_month_churn_rate:.1%}  (n={row.exposures:,.0f})",va="center",fontsize=9)
        fig.subplots_adjust(bottom=.23)
        fig.text(.12,.035,"Synthetic observational associations; exposure counts include repeat observations.",fontsize=8,color="#64748b")
        finish(fig,name)
    g=c.customer_segment.value_counts().sort_values()
    fig,ax=plt.subplots(figsize=(10,6)); ax.barh(g.index,g.values,color=TEAL)
    ax.set_title("Customer segments at 31 Aug 2026",loc="left"); ax.set_xlabel("Customers")
    finish(fig,"customer_segments")
    g=c[c.active_flag.eq(1)].groupby("risk_band").active_mrr.sum().reindex(["Low Risk","Medium Risk","High Risk"])
    fig,ax=plt.subplots(figsize=(8,4.5)); ax.bar(g.index,g.values,color=[TEAL,"#d99b25",RED])
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x,pos:f"USD {x/1000:.0f}K"))
    ax.set_title("Current MRR by heuristic risk band",loc="left"); ax.set_ylabel("Monthly recurring revenue")
    finish(fig,"revenue_by_risk")
    pivot=co.pivot(index="cohort_month",columns="cohort_age",values="retention_rate")
    fig,ax=plt.subplots(figsize=(14,9))
    cmap=plt.get_cmap("YlGnBu").copy(); cmap.set_bad("#f1f5f9")
    im=ax.imshow(np.ma.masked_invalid(pivot.to_numpy()),aspect="auto",vmin=0,vmax=1,cmap=cmap)
    ax.set_yticks(range(len(pivot)),pivot.index.strftime("%b %Y"))
    ax.set_xticks(range(24),range(24)); ax.set_xlabel("Cohort age in calendar months")
    ax.set_title("Subscription survival by acquisition cohort",loc="left",pad=18)
    for y in range(len(pivot)):
        for x in range(24):
            v=pivot.iloc[y,x]
            if pd.notna(v): ax.text(x,y,f"{v:.0%}",ha="center",va="center",fontsize=6.5,color="white" if v>.6 else NAVY)
    fig.colorbar(im,ax=ax,format=PercentFormatter(1),shrink=.7)
    fig.text(.12,.035,"Month 0 is actual acquisition-month-end survival. Gray cells are future, unobserved periods.",fontsize=10)
    finish(fig,"cohort_retention_heatmap")
    fig,ax=plt.subplots(figsize=(9,4.5))
    for status,color,label in [(0,TEAL,"Active"),(1,RED,"Churned")]:
        ax.hist(c.loc[c.churn_flag.eq(status),"observed_clv"],bins=35,alpha=.55,color=color,label=label)
    ax.set_title("Observed subscription revenue per customer",loc="left"); ax.set_xlabel("Observed CLV (USD, revenue only)"); ax.set_ylabel("Customers"); ax.legend(frameon=False)
    finish(fig,"clv_distribution")
    g=c[c.churn_flag.eq(1) & c.high_value_flag.eq(1)].nlargest(10,"observed_clv").sort_values("observed_clv")
    fig,ax=plt.subplots(figsize=(9,5));ax.barh(g.customer_id,g.observed_clv,color=RED)
    ax.set_title("High-value churned customers: top observed CLV",loc="left");ax.set_xlabel("Revenue recognized before cancellation (USD)")
    finish(fig,"high_value_churned_customers")
    metrics=json.loads((ROOT/"outputs/model/model_metrics.json").read_text())
    matrix=np.array(metrics["models"][metrics["selected_model"]]["test"]["confusion_matrix"])
    fig,ax=plt.subplots(figsize=(5.5,4.5));ax.imshow(matrix,cmap="Blues")
    for i in range(2):
        for j in range(2):ax.text(j,i,f"{matrix[i,j]:,}",ha="center",va="center",fontsize=18,color="white" if matrix[i,j]>matrix.max()/2 else NAVY)
    ax.set_xticks([0,1],["Stay","Churn"]);ax.set_yticks([0,1],["Stay","Churn"])
    ax.set_xlabel("Predicted");ax.set_ylabel("Observed");ax.set_title("Prototype: held-out test confusion matrix",fontsize=12)
    finish(fig,"model_confusion_matrix")
    k=json.loads((ROOT/"outputs/executive_kpis.json").read_text())
    fig=plt.figure(figsize=(14,8),facecolor="#f6f8fc")
    fig.text(.055,.925,"Customer retention | Executive snapshot",fontsize=25,weight="bold")
    fig.text(.055,.88,"Synthetic subscription business  /  31 August 2026  /  USD",fontsize=11,color="#64748b")
    cards=[("ACTIVE CUSTOMERS",f"{k['active_customers']:,}"),("MONTHLY CHURN",f"{k['latest_month_churn_rate']:.2%}"),
           ("CURRENT MRR",f"USD {k['monthly_recurring_revenue']/1000:.1f}K"),("MRR AT HIGH RISK",f"USD {k['revenue_at_risk']/1000:.1f}K")]
    for i,(label,value) in enumerate(cards):
        x=.055+i*.237
        fig.text(x,.79,label,fontsize=10,color="#64748b");fig.text(x,.73,value,fontsize=24,weight="bold")
    ax=fig.add_axes([.07,.19,.52,.41]);ax.plot(m.month,m.end_mrr,color=BLUE,linewidth=2.5)
    ax.set_title("Month-end recurring revenue",loc="left")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x,pos:f"{x/1000:.0f}K"));ax.tick_params(axis="x",rotation=25);ax.grid(axis="y",alpha=.15)
    ax2=fig.add_axes([.70,.19,.25,.41])
    risk=c[c.active_flag.eq(1)].groupby("risk_band").active_mrr.sum().reindex(["Low Risk","Medium Risk","High Risk"])
    ax2.bar(["Low","Medium","High"],risk,color=[TEAL,"#d99b25",RED])
    ax2.set_title("MRR by risk band",loc="left");ax2.yaxis.set_major_formatter(FuncFormatter(lambda x,pos:f"{x/1000:.0f}K"))
    fig.text(.055,.06,"Monthly churn uses the opening customer base. Risk is an interpretable heuristic; no realized savings are claimed.",fontsize=10,color="#64748b")
    finish(fig,"executive_overview")
    print("Charts generated.")

def insights():
    c=read_csv("customers_clean"); d=read_csv("churn_driver_associations"); m=read_csv("monthly_churn_kpis")
    r=read_csv("retention_by_dimension");co=read_csv("cohort_retention")
    k=json.loads((ROOT/"outputs/executive_kpis.json").read_text())
    bullets=[]
    for driver,label in [("engagement_band","Engagement"),("usage_band","Usage"),("payment_failures","Payment failures"),
                         ("support_ticket_band","Support interactions"),("contract_type","Contract"),
                         ("acquisition_channel","Acquisition channel"),("tenure_band","Tenure"),("plan_type","Plan")]:
        g=d[d.driver.eq(driver) & d.exposures.ge(100)].sort_values("next_month_churn_rate")
        lo=g.iloc[0];hi=g.iloc[-1]
        bullets.append(f"**{label}:** {hi.category} recorded {hi.next_month_churn_rate:.2%} next-month churn ({int(hi.next_month_churns):,}/{int(hi.exposures):,} customer-month exposures), versus {lo.category} at {lo.next_month_churn_rate:.2%} ({int(lo.next_month_churns):,}/{int(lo.exposures):,}). Difference: {(hi.next_month_churn_rate-lo.next_month_churn_rate)*100:.2f} percentage points. Source: churn_driver_associations.csv; Churn Drivers sheet.")
    for dim,label in [("acquisition_channel","Acquisition"),("contract_type","Contract"),("plan_type","Plan")]:
        g=r[r.dimension.eq(dim)].sort_values("retention_rate");lo=g.iloc[0];hi=g.iloc[-1]
        bullets.append(f"**Six-month {label.lower()} retention:** {hi.category} retained {hi.retention_rate:.1%} ({int(hi.retained_customers):,}/{int(hi.eligible_customers):,}) versus {lo.category} at {lo.retention_rate:.1%}. Both denominators include only cohorts old enough to observe age 6. Source: retention_by_dimension.csv; Retention & Cohorts sheet.")
    bullets.append(f"**Current risk exposure:** {k['high_risk_customers']:,} active customers hold USD {k['revenue_at_risk']:,.2f} in high-risk MRR, {k['revenue_at_risk']/k['monthly_recurring_revenue']:.1%} of current MRR. This is the size of a prioritization group, not expected or realized loss. Source: executive_kpis.json; Customer Segments & Risk sheet.")
    hv=c[c.high_risk_flag.eq(1) & c.high_value_flag.eq(1)]
    bullets.append(f"**High-value intervention pool:** {len(hv):,} customers combine high risk with at least USD 80 monthly revenue, representing USD {hv.active_mrr.sum():,.2f} MRR. Source: customers_clean.csv; Revenue & Retention Opportunity sheet.")
    early=c[c.churn_flag.eq(1) & c.tenure_months.lt(3)]
    bullets.append(f"**Early cancellations:** {len(early):,} of {k['churned_customers']:,} observed cancellations ({len(early)/k['churned_customers']:.1%}) occurred before three months of tenure. This is a distribution of churn events, not a tenure-specific churn probability. Source: customers_clean.csv; Churn Drivers sheet.")
    bullets.append(f"**Latest customer bridge:** {int(m.iloc[-1].new_customer):,} acquisitions minus {int(m.iloc[-1].churn_event):,} cancellations produced {k['latest_month_net_customer_growth']:,} net additions in August 2026. Source: monthly_churn_kpis.csv; Executive Overview sheet.")
    mature=co[(co.cohort_age.eq(6)) & co.is_observed.eq(1)]
    bullets.append(f"**Age-6 survival:** {mature.retained_customers.sum()/mature.cohort_size.sum():.1%} across {int(mature.cohort_size.sum()):,} customers in mature cohorts, weighted by original cohort size. Source: cohort_retention.csv; Retention & Cohorts sheet.")
    text="# Business insights and retention actions\n\nAll findings below are computed from the bundled synthetic data. They describe the simulation, not a real company. Associations are unadjusted; customer-month observations repeat customers and do not establish causation.\n\n"
    text+="\n\n".join(f"{i}. {b}" for i,b in enumerate(bullets,1))
    text+="\n\n## Recommended tests\n\n- Randomize personalized outreach within the high-value/high-risk active pool; evaluate 60-day cancellation rate and net revenue after intervention costs.\n- Test payment recovery messages after failed payments; track recovery, involuntary cancellation and complaints.\n- Test guided onboarding for new low-engagement subscribers; evaluate comparable follow-up windows.\n- Pilot support follow-up after repeated complaints, with service workload and opt-out guardrails.\n- Compare channels on fixed-horizon retention and value before reallocating spend; acquisition costs are absent, so CAC and ROI cannot be calculated.\n- Test re-engagement for low-usage customers; randomize treatment and avoid interpreting contact response as proof of saved customers.\n\nSee [retention_experiment_plan.md](retention_experiment_plan.md) for the evaluation design.\n"
    (ROOT/"outputs/business_insights.md").write_text(text,encoding="utf-8")
    resume=f"""# Resume bullets

Use these only after you can explain and reproduce the work. The AWS layer is locally prepared, not deployed.

- Analyzed {len(c):,} validated synthetic subscription customers and {k['customer_month_records']:,} customer-month records using Python, Pandas and 32 SQL analyses to evaluate churn, retention, engagement and recurring revenue.
- Built reproducible cohort and customer segmentation pipelines with an interpretable risk framework identifying {k['high_risk_customers']:,} active high-risk customers representing USD {k['revenue_at_risk']:,.0f} in monthly recurring revenue at risk.
- Developed and evaluated leakage-aware logistic regression and decision-tree prototypes using customer-disjoint temporal splits, with validation-based model selection and held-out classification metrics.
- Prepared 14 Amazon QuickSight-ready analytics datasets, a five-sheet dashboard specification, boto3 S3 upload workflow and typed Athena views with metric reconciliation and deployment documentation.

After actual AWS deployment, the last bullet can truthfully describe the dashboard you published. Do not claim realized retention improvement or revenue savings from this simulation.
"""
    (ROOT/"RESUME_BULLETS.md").write_text(resume,encoding="utf-8")
    preview="""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Customer Retention Analytics</title>
<style>body{margin:0;background:#f4f7fb;color:#15263e;font:16px system-ui}header,main{max-width:1180px;margin:auto;padding:28px}h1{margin:0;font-size:32px}.muted{color:#64748b}nav{display:flex;gap:8px;flex-wrap:wrap;margin:20px 0}button{border:1px solid #cbd5e1;border-radius:7px;background:white;padding:12px;color:#15263e;cursor:pointer}button[aria-selected=true]{background:#15263e;color:white}.panel{display:none}.panel.active{display:block}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:18px}img{width:100%;background:white;border-radius:10px}.note{background:#e7eef9;padding:16px;border-radius:8px}a{color:#2563eb}</style>
<header><h1>Customer Churn & Retention</h1><p class="muted">Synthetic subscription analytics · 31 August 2026 · USD</p><p class="note">Local dashboard preview. These are validated static analysis outputs; this file is not a live Amazon QuickSight dashboard. The AWS build guide specifies filters and interactions.</p>
<nav role="tablist">"""
    sheets=[("Executive Overview",["executive_overview","monthly_churn_rate","monthly_retention_rate","net_customer_growth"]),
            ("Churn Drivers",["churn_by_plan","churn_by_contract","churn_by_channel","churn_by_payment_failures","churn_by_engagement","churn_by_support_tickets","churn_by_tenure","churn_by_usage"]),
            ("Segments & Risk",["customer_segments","revenue_by_risk","clv_distribution"]),
            ("Retention & Cohorts",["cohort_retention_heatmap","monthly_retention_rate"]),
            ("Revenue Opportunity",["monthly_mrr","revenue_by_risk","high_value_churned_customers"])]
    for i,(title,names) in enumerate(sheets):preview+=f'<button role="tab" aria-selected="{str(i==0).lower()}" onclick="show({i})">{title}</button>'
    preview+="</nav></header><main>"
    for i,(title,names) in enumerate(sheets):
        preview+=f'<section class="panel {"active" if i==0 else ""}" id="p{i}" role="tabpanel"><h2>{title}</h2><div class="grid">'
        for name in names:preview+=f'<img loading="lazy" src="charts/{name}.png" alt="{name.replace("_"," ")}">'
        preview+="</div></section>"
    preview+='<p class="muted">Definitions and denominator checks are documented in the repository. Risk scores are heuristics, observed CLV is historical revenue, and no causal or realized impact is claimed.</p></main><script>function show(n){document.querySelectorAll(".panel").forEach((e,i)=>e.classList.toggle("active",i===n));document.querySelectorAll("button").forEach((e,i)=>e.setAttribute("aria-selected",i===n))}</script></html>'
    (ROOT/"outputs/dashboard_preview.html").write_text(preview,encoding="utf-8")
    print(f"Generated {len(bullets)} evidence-based insights and resume bullets.")

if __name__=="__main__": charts(); insights()
