import os
import pandas as pd
import numpy as np
from github import Github
import xgboost as xgb
import argparse
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

# ========== Environment Variables & Config ==========
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("REPO_NAME", "huggingface/transformers")
MODEL_DIR = os.getenv("MODEL_DIR", "./model")
MODEL_PATH = os.path.join(MODEL_DIR, "latest_model.json")
PREDICT_OUT_DIR = os.getenv("PREDICT_OUT_DIR", "./predict_outputs")   
os.makedirs(PREDICT_OUT_DIR, exist_ok=True)

# ========= Utility Functions =========
def fetch_open_issues_by_recent(days=1):
    """Fetch open issues created within the past 'days' days"""
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    since = datetime.now(timezone.utc) - timedelta(days=days)
    issues = repo.get_issues(state="open", since=since)
    results = []
    for issue in issues:
        if issue.pull_request is not None:
            continue
        if issue.created_at < since:  # The API may return older issues as well
            continue
        results.append(issue)
    return results

def fetch_open_issues_by_ids(ids):
    """Fetch open issues by given IDs"""
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    results = []
    for iid in ids:
        issue = repo.get_issue(number=int(iid))
        if issue.state != "open":
            continue
        if issue.pull_request is not None:
            continue
        results.append(issue)
    return results

def extract_features_from_issues(issues):
    """Extract features; must match features used during training"""
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
            # No closed_within_7_days since we are making predictions for this
            "number": issue.number,
            "title": title,
            "created_at": created_at.strftime('%Y-%m-%d %H:%M:%S') if created_at else "",
        })
    return pd.DataFrame(feature_rows)

def predict_proba(model_path, feature_df):
    # XGBoost uses only the features used during training
    feature_cols = ["title_len", "body_len", "num_labels", "has_bug_label", "hour_created", "comments"]
    bst = xgb.XGBClassifier()
    bst.load_model(model_path)
    proba = bst.predict_proba(feature_df[feature_cols])[:, 1]  # Probability for label 1 (closed)
    return proba

# ========== Main Process ==========
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["recent", "ids"], required=True, help="Prediction mode")
    parser.add_argument("--days", type=int, default=1, help="How many recent days (mode=recent)")
    parser.add_argument("--ids", nargs="+", type=int, help="Issue numbers (mode=ids)")
    parser.add_argument("--out", type=str, help="Export to CSV (optional)")
    args = parser.parse_args()

    # 1. Fetch issues
    if args.mode == "recent":
        issues = fetch_open_issues_by_recent(args.days)
        print(f"[INFO] Fetched {len(issues)} open issues from last {args.days} days.")
    else:
        issues = fetch_open_issues_by_ids(args.ids)
        print(f"[INFO] Fetched {len(issues)} open issues by IDs.")

    if not issues:
        print("[WARN] No open issues found. Exit.")
        exit(0)

    # 2. Feature extraction
    df = extract_features_from_issues(issues)
    # 3. Model prediction
    proba = predict_proba(MODEL_PATH, df)
    df["prob_closed_within_7_days"] = np.round(proba, 4)

    # 4. Output
    output_cols = ["number", "title", "created_at", "prob_closed_within_7_days"]
    print(df[output_cols].to_string(index=False))

    if args.out:
        out_path = args.out
    else:
        # Generate files with timestamps
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = os.path.join(PREDICT_OUT_DIR, f"open_issues_pred_{args.mode}_{timestamp}.csv")

    df[output_cols].to_csv(out_path, index=False)
    print(f"[DONE] Saved prediction to: {out_path}")
