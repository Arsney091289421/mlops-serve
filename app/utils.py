import os
import pandas as pd
import numpy as np
import boto3
from github import Github
import xgboost as xgb
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

# Load environment variables 
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("REPO_NAME", "huggingface/transformers")

def fetch_open_issues_by_recent(days=1):
    """Fetch open issues created within the past 'days' days."""
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    since = datetime.now(timezone.utc) - timedelta(days=days)
    issues = repo.get_issues(state="open", since=since)
    results = []
    for issue in issues:
        if issue.pull_request is not None:
            continue
        if issue.created_at < since:  # API may return older issues, so filter again
            continue
        results.append(issue)
    return results

def fetch_open_issues_by_ids(ids):
    """Fetch open issues by given issue numbers (IDs)."""
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    results = []
    for iid in ids:
        try:
            issue = repo.get_issue(number=int(iid))
            if issue.state != "open":
                continue
            if issue.pull_request is not None:
                continue
            results.append(issue)
        except Exception:
            continue
    return results

def extract_features_from_issues(issues):
    """Extract features matching those used during model training."""
    feature_rows = []
    for issue in issues:
        title = issue.title or ""
        body = issue.body or ""
        labels = [l.name for l in issue.labels] if issue.labels else []
        created_at = issue.created_at

        feature_rows.append({
            "title_len": len(title),
            "body_len": len(body),
            "num_labels": len(labels),
            "has_bug_label": int("bug" in labels),
            "hour_created": created_at.hour if created_at else None,
            "comments": issue.comments,
            "number": issue.number,
            "title": title,
            "created_at": created_at.strftime('%Y-%m-%d %H:%M:%S') if created_at else "",
        })
    return pd.DataFrame(feature_rows)

def predict_proba(model_path, feature_df):
    """Load trained XGBoost model and predict probabilities."""
    feature_cols = ["title_len", "body_len", "num_labels", "has_bug_label", "hour_created", "comments"]
    bst = xgb.XGBClassifier()
    bst.load_model(model_path)
    proba = bst.predict_proba(feature_df[feature_cols])[:, 1]  # Probability for label 1 (closed)
    return proba

def predict_issues(issues, model_path):
    """Fetch DataFrame of issues with predicted probability of closing within 7 days."""
    if not issues:
        return pd.DataFrame(columns=["number", "title", "created_at", "prob_closed_within_7_days"])
    df = extract_features_from_issues(issues)
    proba = predict_proba(model_path, df)
    df["prob_closed_within_7_days"] = np.round(proba, 4)
    return df[["number", "title", "created_at", "prob_closed_within_7_days"]]


def download_model_from_s3(bucket_name, s3_key, model_dir, local_model_name="latest_model.json"):
    """
    Download model file from S3 to the specified local directory
    """
    os.makedirs(model_dir, exist_ok=True)
    local_path = os.path.join(model_dir, local_model_name)
    s3 = boto3.client("s3")
    s3.download_file(bucket_name, s3_key, local_path)
    print(f"[DONE] Downloaded s3://{bucket_name}/{s3_key} → {local_path}")
    return local_path

def upload_file_to_s3(local_path, bucket_name, s3_key):
    """
    Upload a local file to S3 with the given bucket and key.
    """
    s3 = boto3.client("s3")
    s3.upload_file(local_path, bucket_name, s3_key)
    print(f"[DONE] Uploaded {local_path} -> s3://{bucket_name}/{s3_key}")
