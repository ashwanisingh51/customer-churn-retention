"""Upload validated CSV datasets to private S3 using boto3's credential chain."""
import argparse
import hashlib
import json
import logging
import os
import re
from pathlib import Path
import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from boto3.exceptions import S3UploadFailedError
from scripts.common import ROOT, write_json
LOG=logging.getLogger(__name__)

def upload_plan(bucket,prefix="quicksight"):
    if not bucket or not re.fullmatch(r"[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]",bucket):
        raise ValueError("Set S3_BUCKET_NAME or --bucket to your existing S3 bucket name.")
    if not re.fullmatch(r"[A-Za-z0-9_/-]+",prefix) or ".." in prefix:
        raise ValueError("Invalid S3 prefix.")
    prefix=prefix.strip("/")
    contracts=json.loads((ROOT/"quicksight/dataset_contracts.json").read_text())
    plan=[]
    for name,contract in contracts.items():
        path=ROOT/"data/processed"/f"{name}.csv"
        if not path.is_file(): raise FileNotFoundError(f"Missing dataset: {path}")
        import csv
        with path.open(newline="",encoding="utf-8") as f:
            reader=csv.reader(f)
            if next(reader)!=[x["name"] for x in contract["columns"]]:
                raise ValueError(f"Schema changed: {name}. Rerun the pipeline.")
            rows=sum(1 for _ in reader)
        if rows!=contract["rows"]: raise ValueError(f"Row count changed: {name}. Rerun the pipeline.")
        plan.append({"dataset":name,"local_file":f"data/processed/{name}.csv",
                     "key":f"{prefix}/{name}/{name}.csv","rows":rows,
                     "sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"bytes":path.stat().st_size})
    return plan

def upload(bucket,prefix="quicksight",region=None,dry_run=False,client=None):
    plan=upload_plan(bucket,prefix)
    write_json({"bucket":bucket,"region":region,"dry_run":dry_run,"datasets":plan},ROOT/"outputs/s3_upload_plan.json")
    if dry_run:
        for item in plan: LOG.info("PLAN %s -> s3://%s/%s",item["local_file"],bucket,item["key"])
        return plan
    # Uploader IAM: s3:PutObject on the chosen prefix. Multipart transfers may also
    # require s3:AbortMultipartUpload. No public ACL, bucket creation or raw upload.
    # For SSE-KMS, grant the required KMS GenerateDataKey/Decrypt permissions separately.
    client=client or boto3.Session(region_name=region).client("s3",config=Config(
        retries={"max_attempts":3,"mode":"standard"},connect_timeout=10,read_timeout=60))
    completed=[]
    try:
        for item in plan:
            client.upload_file(str(ROOT/item["local_file"]),bucket,item["key"],
                               ExtraArgs={"ContentType":"text/csv","ServerSideEncryption":"AES256"})
            manifest={"fileLocations":[{"URIs":[f"s3://{bucket}/{item['key']}"]}],
                      "globalUploadSettings":{"format":"CSV","delimiter":",","textqualifier":"\"","containsHeader":"true"}}
            client.put_object(Bucket=bucket,Key=f"{prefix.strip('/')}/manifests/{item['dataset']}.json",
                              Body=json.dumps(manifest).encode(),ContentType="application/json",ServerSideEncryption="AES256")
            completed.append(item["dataset"])
            LOG.info("Uploaded %s (%s rows)",item["dataset"],item["rows"])
    except (BotoCoreError,ClientError,S3UploadFailedError):
        LOG.error("Upload stopped after %s of %s datasets. Fix access, then rerun; stable object keys make retries idempotent.",len(completed),len(plan))
        raise
    write_json({"bucket":bucket,"datasets_uploaded":completed,"success":True},ROOT/"outputs/s3_upload_result.json")
    return plan

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bucket",default=os.getenv("S3_BUCKET_NAME"))
    p.add_argument("--region",default=os.getenv("AWS_REGION"))
    p.add_argument("--prefix",default=os.getenv("S3_PREFIX","quicksight"))
    p.add_argument("--dry-run",action="store_true",help="Validate and log the upload plan without credential lookup or AWS requests.")
    a=p.parse_args(argv)
    logging.basicConfig(level=logging.INFO,format="%(levelname)s %(message)s")
    try:
        upload(a.bucket,a.prefix,a.region,a.dry_run)
    except (ValueError,FileNotFoundError) as exc:
        LOG.error("%s",exc); return 2
    except (BotoCoreError,ClientError,S3UploadFailedError) as exc:
        LOG.error("AWS upload failed (%s). Configure an AWS SSO profile or IAM role, confirm region and bucket permissions, then retry. No credentials belong in this repository.",type(exc).__name__)
        return 3
    return 0

if __name__=="__main__": raise SystemExit(main())
