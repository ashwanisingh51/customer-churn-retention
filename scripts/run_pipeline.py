"""Single entry point. No AWS calls are made by the local analytics pipeline."""
import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import time
from scripts.common import ROOT, ensure_dirs, write_json

def run(test=False,execute_notebooks=False,skip_generate=False):
    ensure_dirs()
    os.environ["MPLCONFIGDIR"]=str(ROOT/".cache/matplotlib")
    os.environ["IPYTHONDIR"]=str(ROOT/".cache/ipython")
    from scripts.generate_dataset import generate
    from scripts.data_cleaning import clean
    from scripts.analytics import analyze
    from scripts.sql_analysis import run_sql
    from scripts.export_analytics_data import export
    from scripts.model import train_model
    from scripts.reporting import charts,insights
    from scripts.notebooks import create_notebooks,execute_notebooks as execute
    from scripts.validation import validate
    steps=([("generate_dataset",generate)] if not skip_generate else [])+[
        ("clean",clean),("analytics",analyze),("sql",run_sql),("quicksight_export",export),
        ("model",train_model),("charts",charts),("insights",insights),("notebook_creation",create_notebooks)]
    if execute_notebooks or test: steps.append(("notebook_execution",execute))
    steps.append(("validation",validate))
    timings=[]
    for name,fn in steps:
        print(f"Running {name}...",flush=True);start=time.perf_counter();fn()
        timings.append({"step":name,"seconds":round(time.perf_counter()-start,3),"status":"PASS"})
    if test:
        result=subprocess.run([sys.executable,"-m","pytest","-q","--junitxml=outputs/test_results.xml"],cwd=ROOT,text=True,capture_output=True)
        (ROOT/"outputs/test_run.log").write_text(result.stdout+result.stderr,encoding="utf-8")
        print(result.stdout,flush=True)
        if result.returncode: raise RuntimeError("Tests failed; see outputs/test_run.log")
        timings.append({"step":"pytest","status":"PASS"})
    packages={name:importlib.metadata.version(name) for name in ["pandas","numpy","matplotlib","scikit-learn","boto3","nbformat","nbclient","ipykernel","pytest","sqlglot"]}
    hashes={str(p.relative_to(ROOT)).replace("\\","/"):hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in ["data/raw","data/processed"] for p in sorted((ROOT/folder).glob("*")) if p.is_file()}
    write_json({"status":"PASS","python":platform.python_version(),"platform":platform.system(),
        "packages":packages,"steps":timings,"source_and_mart_sha256":hashes,
        "aws_status":"Not deployed; local artifacts prepared. No AWS calls performed by pipeline."},
        ROOT/"outputs/run_manifest.json")
    print("Local pipeline completed successfully.",flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--test",action="store_true",help="Execute notebooks and the complete test suite.")
    p.add_argument("--execute-notebooks",action="store_true")
    p.add_argument("--skip-generate",action="store_true",help="Reuse existing synthetic raw inputs.")
    a=p.parse_args();run(a.test,a.execute_notebooks,a.skip_generate)
