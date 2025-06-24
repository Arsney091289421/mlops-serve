import subprocess
import requests
from datetime import datetime

def run_cmd(cmd):
    print(f"[{datetime.now()}] Running: {cmd}")
    ret = subprocess.run(cmd, shell=True)
    if ret.returncode != 0:
        print(f"[ERROR] Command failed: {cmd}")
        raise RuntimeError(f"Command failed: {cmd}")

def push_workflow_status(job_name, status, gateway_url="http://localhost:9091"):
    # status: 1=succees, 0=fail
    metric = f'workflow_status{{job="{job_name}"}} {status}\n'
    metric += f'workflow_last_run{{job="{job_name}"}} {int(datetime.now().timestamp())}\n'
    try:
        resp = requests.post(f"{gateway_url}/metrics/job/{job_name}", data=metric)
        print(f"[PROMETHEUS] Status pushed: {status}, resp: {resp.status_code}")
    except Exception as e:
        print(f"[PROMETHEUS] Push failed: {e}")

if __name__ == "__main__":
    print(f"=== [{datetime.now()}] Start daily MLOps workflow ===")
    try:
        run_cmd("python scripts/download_model_from_s3.py")
        run_cmd("python scripts/predict_open_issues.py --mode recent")
        run_cmd("python scripts/upload_predict_outputs_to_s3.py")
        print(f"=== [{datetime.now()}] Finished daily MLOps workflow ===")
        push_workflow_status("predict_upload", 1)   # success
    except Exception as e:
        print(f"[FATAL ERROR] {e}")
        push_workflow_status("predict_upload", 0)   # fail
        exit(1)           

