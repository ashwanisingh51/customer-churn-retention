# Amazon S3 setup

Use a private bucket with a globally unique name in the same AWS Region as Athena and the QuickSight account. The included name customer-churn-retention-analytics is an example and is not provisioned.

    s3://YOUR_BUCKET/
      raw/                               # optional future source landing; not uploaded automatically
      processed/                         # optional internal work area
      quicksight/customers_clean/customers_clean.csv
      quicksight/monthly_snapshots/monthly_snapshots.csv
      quicksight/<dataset>/<dataset>.csv
      quicksight/manifests/<dataset>.json
      athena-results/                    # query results, outside all dataset prefixes

Separate folders per dataset prevent Athena from reading incompatible CSVs together. Keep one current CSV in each dataset folder; uploading multiple full copies would duplicate every row. The uploader uses stable keys, so rerunning replaces the current object. S3 versioning can retain history without exposing old versions to Athena.

## Local configuration

The .env.example file documents environment variables. Scripts read the actual process environment; they do not automatically load .env. Use a configured AWS SSO profile or IAM role, never keys committed into a file.

PowerShell example:

    $env:AWS_REGION = "us-east-1"
    $env:S3_BUCKET_NAME = "your-globally-unique-bucket"
    $env:AWS_PROFILE = "your-configured-sso-profile"
    python -m scripts.upload_to_s3 --dry-run
    python -m scripts.export_analytics_data --bucket $env:S3_BUCKET_NAME
    python -m scripts.upload_to_s3

Bash example:

    export AWS_REGION=us-east-1
    export S3_BUCKET_NAME=your-globally-unique-bucket
    export AWS_PROFILE=your-configured-sso-profile
    python -m scripts.upload_to_s3 --dry-run
    python -m scripts.export_analytics_data --bucket "$S3_BUCKET_NAME"
    python -m scripts.upload_to_s3

If using the AWS CLI for SSO, run aws sso login --profile with your actual profile first. Role-based environments do not need a profile. The Python workflow uses the standard [boto3 credential chain](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html).

## Access

Uploader: s3:PutObject on the chosen quicksight prefix and s3:AbortMultipartUpload if multipart cleanup is needed. The script sets AES256 encryption and does not change bucket policy or ACL. A bucket requiring KMS encryption needs an explicitly adapted encryption configuration and matching KMS permissions.

QuickSight's service role needs access independently of the human user: S3 read access to dataset/manifest prefixes, Glue catalog read access, Athena query access and read/write access to the configured Athena result location. If Lake Formation manages the tables, grant the corresponding database/table access there. Scope workgroup, catalog, bucket and key permissions to your account configuration.

Create the bucket with Block Public Access enabled and default encryption. Do not use a public bucket to bypass IAM. For production datasets, additionally apply the organization's classification, access and retention policies.

## Failure and refresh behavior

--dry-run validates local schemas and row counts without creating a boto3 session or making an AWS call. It writes outputs/s3_upload_plan.json.

Missing configuration returns exit code 2. Credential, access and service failures return 3 with an actionable message. Partial upload failure is logged. Rerun to complete stable keys, then refresh SPICE only after all datasets upload successfully. This is not an atomic multi-table refresh; coordinate refresh windows for a live reporting system.

The uploader uploads CSVs and per-dataset manifests. It does not create buckets, execute Athena SQL or publish a dashboard.
