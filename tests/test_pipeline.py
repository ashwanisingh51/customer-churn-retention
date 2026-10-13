"""Regression and edge-case tests; all AWS tests use isolated fakes."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from botocore.exceptions import NoCredentialsError
from scripts.common import ROOT, AS_OF
from scripts.analytics import cohort_metrics, monthly_metrics
from scripts.data_cleaning import clean_customers, risk_components
from scripts.upload_to_s3 import upload, upload_plan, main
from scripts.validation import validate

@pytest.fixture(scope="session")
def report():
    return validate(False)

@pytest.mark.parametrize("index",range(100))
def test_data_validation(report,index):
    assert index<len(report["checks"])
    item=report["checks"][index]
    assert item["passed"],item["check"]

def fixture_customer():
    return pd.DataFrame([{"customer_id":"fixture","signup_date":"2026-01-01",
        "subscription_start_date":"2026-01-02","subscription_end_date":None,"last_activity_date":"2026-08-30",
        "churn_date":None,"plan_type":"Basic","monthly_fee":29.,"discount_percentage":.1,"tenure_months":1.,
        "churn_flag":0,"auto_renew":1,"support_tickets":0,"complaints":0,"login_frequency":20,
        "monthly_usage":150.,"feature_usage_score":70.,"payment_failures":0,"late_payments":0,
        "payment_method":"Credit Card","region":"South","city":"Austin","customer_status":"Active"}])

def test_cleaning_exact_duplicate():
    raw=fixture_customer()
    clean,quarantine,_,report=clean_customers(pd.concat([raw,raw],ignore_index=True))
    assert len(clean)==1 and len(quarantine)==0 and report["exact_duplicate_customer_rows_removed"]==1

def test_conflicting_duplicate_ids_quarantined():
    raw=fixture_customer()
    other=raw.copy();other["monthly_fee"]=59.
    clean,quarantine,_,_=clean_customers(pd.concat([raw,other],ignore_index=True))
    assert clean.empty and len(quarantine)==2

@pytest.mark.parametrize("field,value",[("monthly_fee",-1),("discount_percentage",1.1),
    ("subscription_start_date","2027-01-01"),("churn_date","2025-12-01"),("last_activity_date","2027-01-01")])
def test_invalid_values_quarantined(field,value):
    raw=fixture_customer();raw[field]=value
    clean,quarantine,_,_=clean_customers(raw)
    assert clean.empty and len(quarantine)==1

def test_missing_payment_and_plan_repair():
    raw=fixture_customer();raw["payment_method"]=None;raw["plan_type"]=" basic plan "
    clean,quarantine,repairs,_=clean_customers(raw)
    assert quarantine.empty
    assert clean.iloc[0].payment_method=="Unknown" and clean.iloc[0].plan_type=="Basic"
    assert {"standardize_plan","missing_category_to_unknown"}<=set(repairs.rule)

def test_cancellation_at_month_end_not_retained():
    c=pd.DataFrame({"acquisition_cohort":pd.to_datetime(["2026-07-01","2026-07-01"]),
                    "subscription_end_date":pd.to_datetime(["2026-07-31",None])})
    result=cohort_metrics(c)
    assert result.iloc[0].retention_rate==.5
    assert result.iloc[1].retention_rate==.5
    assert result.loc[result.cohort_age.ge(2),"retention_rate"].isna().all()

def test_risk_score_extremes_and_thresholds():
    f=pd.DataFrame({"days_since_last_activity":[14,13],"engagement_score":[34,35],"support_tickets":[3,2],
                   "complaints":[1,0],"payment_failures":[1,0],"monthly_usage":[79,80],
                   "tenure_months":[2.9,3],"auto_renew":[0,1],"recent_usage_decline":[.30,.29]})
    assert risk_components(f).sum(axis=1).tolist()==[100,0]

def test_zero_opening_base_returns_null():
    cols=["is_active_start","new_customer","churn_event","is_active_end","opening_customer_churn",
          "new_customer_churn","renewal_due","renewal_success","start_mrr","new_mrr","churned_mrr","end_mrr","recognized_revenue"]
    row={col:0 for col in cols};row.update(snapshot_month=pd.Timestamp("2026-08-01"),new_customer=1,is_active_end=1)
    result=monthly_metrics(pd.DataFrame([row])).iloc[0]
    assert pd.isna(result.churn_rate) and pd.isna(result.retention_rate) and pd.isna(result.renewal_rate)

def test_s3_dry_run_never_creates_client(monkeypatch):
    def forbidden(*a,**kw):raise AssertionError("AWS session created during dry run")
    monkeypatch.setattr("scripts.upload_to_s3.boto3.Session",forbidden)
    assert len(upload("portfolio-validation-bucket",dry_run=True))==14

def test_s3_missing_bucket_has_clear_exit_code():
    assert main(["--bucket",""])==2

def test_s3_missing_credentials_has_clear_exit_code(monkeypatch):
    def missing(*a,**kw):raise NoCredentialsError()
    monkeypatch.setattr("scripts.upload_to_s3.upload",missing)
    assert main(["--bucket","portfolio-validation-bucket"])==3

def test_s3_successful_upload_with_fake():
    class Fake:
        def __init__(self):self.csvs=[];self.manifests=[]
        def upload_file(self,path,bucket,key,ExtraArgs):self.csvs.append((bucket,key,ExtraArgs))
        def put_object(self,**kwargs):self.manifests.append(kwargs)
    fake=Fake()
    result_path=ROOT/"outputs/s3_upload_result.json"
    previous=result_path.read_bytes() if result_path.exists() else None
    try:
        upload("portfolio-validation-bucket",client=fake)
        assert len(fake.csvs)==14 and len(fake.manifests)==14
        for (_,key,extra),manifest in zip(fake.csvs,fake.manifests):
            assert extra["ServerSideEncryption"]=="AES256"
            parsed=json.loads(manifest["Body"])
            assert parsed["fileLocations"][0]["URIs"][0].endswith(key)
    finally:
        # A fake upload must never leave a live-success artifact in the deliverable.
        if previous is None:result_path.unlink(missing_ok=True)
        else:result_path.write_bytes(previous)

@pytest.mark.parametrize("prefix",["../bad","folder with spaces","/../"])
def test_invalid_upload_prefix(prefix):
    with pytest.raises(ValueError):upload_plan("portfolio-validation-bucket",prefix)

def test_athena_typed_views_parse():
    import sqlglot
    sql=(ROOT/"quicksight/athena_setup.sql").read_text()
    views=[chunk for chunk in sql.split(";") if "CREATE OR REPLACE VIEW" in chunk]
    assert len(views)==14
    for view in views:
        tree=sqlglot.parse_one(view,read="trino")
        assert tree is not None

def test_manifests_reference_separate_dataset_folders():
    for path in (ROOT/"quicksight/manifests").glob("*.json"):
        manifest=json.loads(path.read_text())
        uri=manifest["fileLocations"][0]["URIs"][0]
        assert uri.endswith(f"/{path.stem}/{path.stem}.csv")
        assert manifest["globalUploadSettings"]["containsHeader"]=="true"

def test_notebooks_have_no_execution_errors():
    import nbformat
    paths=list((ROOT/"notebooks").glob("*.ipynb"))
    assert len(paths)==4
    for path in paths:
        notebook=nbformat.read(path,as_version=4)
        nbformat.validate(notebook)
        for cell in notebook.cells:
            if cell.cell_type=="code":
                assert cell.execution_count is not None
                assert all(o.output_type!="error" for o in cell.outputs)
