"""Create four explanatory notebooks and execute with a local, isolated kernel."""
import json
import os
import sys
import asyncio
from pathlib import Path
import nbformat as nbf
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager
from scripts.common import ROOT, write_json

def create_notebooks():
    setup="""from pathlib import Path
import sys, json
root = Path.cwd()
if not (root / 'scripts').exists():
    root = root.parent
assert (root / 'scripts').exists(), 'Open this notebook inside the project'
if str(root) not in sys.path:
    sys.path.insert(0, str(root))
import pandas as pd
from scripts.common import ROOT, AS_OF, read_csv
from IPython.display import display, Image
"""
    notebooks={
    "01_data_cleaning":[
    ("markdown","# Data quality and cleaning\n\nThis synthetic subscription dataset contains deliberately injected defects. We repair deterministic fields and quarantine ambiguous financial/date records. Cancellation is the only churn definition."),
    ("code",setup),
    ("code","raw = pd.read_csv(ROOT / 'data/raw/customers.csv')\nraw.shape, raw.customer_id.nunique(), raw.head()"),
    ("markdown","## Audit the cleaning policy\n\nExact duplicates can be removed safely. Conflicting identities or invalid fees/dates require quarantine. We do not invent replacement monthly fees or cancellation dates."),
    ("code","from scripts.data_cleaning import clean_customers\nclean, quarantine, repairs, audit = clean_customers(raw)\ndisplay(pd.Series({k:v for k,v in audit.items() if not isinstance(v,dict)}))\ndisplay(quarantine.quarantine_reason.value_counts())"),
    ("code","display(repairs.groupby(['field','rule']).size().rename('repair_events').reset_index())\nassert len(raw) == audit['exact_duplicate_customer_rows_removed'] + len(quarantine) + len(clean)\nassert clean.customer_id.is_unique"),
    ("markdown","## Review derived customer attributes\n\nTenure ends at cancellation for churned customers. Observed CLV is earned historical revenue. Risk scores apply to active customers only."),
    ("code","customers = read_csv('customers_clean')\ndisplay(customers[['customer_id','tenure_months','engagement_score','observed_clv','risk_band','customer_segment']].head(10))\nassert customers.loc[customers.churn_flag.eq(1),'risk_score'].isna().all()"),
    ("markdown","## Interpretation\n\nThe quarantine population is excluded consistently from customer and monthly facts. See outputs/data_quality_report.json and data/quarantine/repair_log.csv for row accounting and field-level provenance.")],
    "02_eda":[
    ("markdown","# Customer, engagement and revenue exploration\n\nAll findings describe synthetic data. Driver comparisons are observational. Current customer characteristics and historical monthly exposure answer different questions."),
    ("code",setup),
    ("code","c = read_csv('customers_clean')\ns = read_csv('monthly_snapshots')\nk = json.loads((ROOT/'outputs/executive_kpis.json').read_text())\ndisplay(pd.Series(k))"),
    ("code","summary = c.groupby('plan_type').agg(customers=('customer_id','size'),active_mrr=('active_mrr','sum'),average_clv=('observed_clv','mean'))\ndisplay(summary)\nassert abs(summary.active_mrr.sum()-k['monthly_recurring_revenue']) < .01"),
    ("markdown","## Use prior-month signals for driver analysis\n\nA customer active at month end contributes an exposure only if the next calendar month is observed. The target is next-month cancellation. Customers can contribute multiple exposures."),
    ("code","drivers = read_csv('churn_driver_associations')\ndisplay(drivers[drivers.driver.isin(['engagement_band','payment_failures','support_ticket_band'])].sort_values(['driver','next_month_churn_rate'],ascending=[True,False]))"),
    ("code","display(Image(filename=str(ROOT/'outputs/charts/churn_by_engagement.png')))\ndisplay(Image(filename=str(ROOT/'outputs/charts/churn_by_payment_failures.png')))"),
    ("markdown","## Revenue interpretation\n\nMRR is a monthly stock, observed CLV is historical earned revenue, and MRR at risk is an intervention pool. None of these establishes saved revenue. Acquisition spend and costs are absent."),
    ("code","display(c.groupby('customer_segment').agg(customers=('customer_id','size'),mrr=('active_mrr','sum'),mean_clv=('observed_clv','mean')).sort_values('mrr',ascending=False))\ndisplay(Image(filename=str(ROOT/'outputs/charts/revenue_by_risk.png')))")],
    "03_retention_churn_analysis":[
    ("markdown","# Retention, cohort survival and revenue bridges\n\nOpening-population monthly retention and acquisition-cohort survival have different denominators. Future periods stay unavailable."),
    ("code",setup),
    ("code","m = read_csv('monthly_churn_kpis')\nco = read_csv('cohort_retention')\ndisplay(m[['month','is_active_start','new_customer','churn_event','is_active_end','churn_rate','retention_rate']].tail(6))\nassert (m.is_active_start+m.new_customer-m.churn_event).equals(m.is_active_end)"),
    ("code","import numpy as np\nassert np.allclose(m.start_mrr+m.new_mrr-m.churned_mrr,m.end_mrr)\nassert co.loc[co.is_observed.eq(0),'retention_rate'].isna().all()\ndisplay(co.pivot(index='cohort_month',columns='cohort_age',values='retention_rate').tail(8))"),
    ("markdown","## Comparable follow-up\n\nFor each age-specific KPI, keep observed cohorts only and weight by original cohort size. Month 0 is actual acquisition-month-end survival, not a forced 100%."),
    ("code","age_rates=[]\nfor age in [0,1,2,3,6,12,18,23]:\n    g=co[co.cohort_age.eq(age)&co.is_observed.eq(1)]\n    age_rates.append({'age':age,'eligible_customers':int(g.cohort_size.sum()),'retention':g.retained_customers.sum()/g.cohort_size.sum()})\ndisplay(pd.DataFrame(age_rates))"),
    ("code","display(Image(filename=str(ROOT/'outputs/charts/cohort_retention_heatmap.png')))\ndisplay(read_csv('retention_by_dimension'))"),
    ("markdown","## Verify with independently executed SQL\n\nThe SQL cohort query derives survival from customer start/end dates. The Python validation also reconciles survival against monthly snapshot activity."),
    ("code","import sqlite3\nwith sqlite3.connect(ROOT/'outputs/churn_retention.sqlite') as conn:\n    display(pd.read_sql_query('SELECT snapshot_month,SUM(start_mrr) AS opening_mrr,SUM(new_mrr) AS new_mrr,SUM(churned_mrr) AS churned_mrr,SUM(end_mrr) AS closing_mrr FROM monthly_snapshots GROUP BY snapshot_month ORDER BY snapshot_month DESC LIMIT 6',conn))")],
    "04_churn_model":[
    ("markdown","# Supporting churn prediction prototype\n\nPredict cancellation in the next calendar month from active month-end features. This notebook trains models, reports held-out performance, and explains why accuracy alone is misleading."),
    ("code",setup),
    ("code","from scripts.model import modeling_frame, train_model, FEATURES\np=modeling_frame()\ndisplay(p[p.split.ne('unused')].groupby('split').agg(rows=('customer_id','size'),customers=('customer_id','nunique'),churn_events=('next_month_churn','sum')))\nprint('Features:', FEATURES)"),
    ("markdown","## Leakage controls\n\nTrain/validation/test customers are disjoint SHA-256 buckets. Training outcomes finish before validation feature months; validation outcomes finish before test feature months. Imputation, scaling and encoding fit only on training rows. Final churn dates are used to create labels, never as features."),
    ("code","sets={name:set(p.loc[p.split.eq(name),'customer_id']) for name in ['train','validation','test']}\nassert not (sets['train']&sets['validation'] or sets['train']&sets['test'] or sets['validation']&sets['test'])\nsummary=train_model()"),
    ("code","table=pd.DataFrame({name:{k:v for k,v in result['test'].items() if k!='confusion_matrix'} for name,result in summary['models'].items()}).T\ndisplay(table)\nprint('Selected on validation PR-AUC:',summary['selected_model'])"),
    ("markdown","## Class imbalance and operational limits\n\nA majority-class baseline can have high accuracy while finding no cancellations. Inspect precision, recall and average precision alongside ROC-AUC. The F1 threshold is selected on validation data; test outcomes do not tune the model. Repeated monthly observations are correlated and scores are uncalibrated."),
    ("code","selected=summary['models'][summary['selected_model']]['test']\ndisplay(pd.DataFrame(selected['confusion_matrix'],index=['Actual stay','Actual churn'],columns=['Predicted stay','Predicted churn']))\nprint('\\n'.join(summary['limitations']))"),
    ("markdown","## Next work with real data\n\nValidate across later customer cohorts, calibrate probabilities on untouched validation data, evaluate top-k lift at actual outreach capacity, and compare intervention value after contact costs. Use randomized retention experiments to estimate incremental impact.")]}
    for name,cells in notebooks.items():
        nb=nbf.v4.new_notebook()
        nb.cells=[nbf.v4.new_markdown_cell(text) if kind=="markdown" else nbf.v4.new_code_cell(text) for kind,text in cells]
        nb.metadata={"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},"language_info":{"name":"python","version":"3.12"}}
        nbf.write(nb,ROOT/"notebooks"/f"{name}.ipynb")
    print("Created four analytical notebooks.")

def execute_notebooks():
    if sys.platform=="win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    cache=ROOT/".cache"
    kernel_dir=cache/"kernels"/"churn-python"
    kernel_dir.mkdir(parents=True,exist_ok=True)
    os.environ["IPYTHONDIR"]=str(cache/"ipython")
    os.environ["JUPYTER_RUNTIME_DIR"]=str(cache/"jupyter_runtime")
    os.environ["MPLCONFIGDIR"]=str(cache/"matplotlib")
    kernel_dir.joinpath("kernel.json").write_text(json.dumps({
        "argv":[sys.executable,"-m","ipykernel_launcher","-f","{connection_file}"],
        "display_name":"Churn project local kernel","language":"python"}))
    reports=[]
    for path in sorted((ROOT/"notebooks").glob("*.ipynb")):
        nb=nbf.read(path,as_version=4)
        km=KernelManager(kernel_name="churn-python",kernel_spec_manager=KernelSpecManager(kernel_dirs=[str(cache/"kernels")]))
        client=NotebookClient(nb,timeout=600,km=km,resources={"metadata":{"path":str(ROOT)}})
        try:
            client.execute()
        finally:
            if km.has_kernel: km.shutdown_kernel(now=True)
            if client.kc is not None: client.kc.stop_channels()
        nbf.write(nb,path)
        reports.append({"notebook":path.name,"executed_code_cells":sum(c.cell_type=="code" for c in nb.cells),"status":"PASS"})
        print(f"Executed {path.name}",flush=True)
    write_json({"status":"PASS","notebooks":reports},ROOT/"outputs/notebook_execution_report.json")

if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute",action="store_true")
    args=parser.parse_args()
    create_notebooks()
    if args.execute:execute_notebooks()
