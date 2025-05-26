import os
import argparse
from datetime import datetime
from dotenv import load_dotenv

from app.utils import (
    fetch_open_issues_by_recent,
    fetch_open_issues_by_ids,
    predict_issues
)

# Environment & Config 
load_dotenv()
MODEL_DIR = os.getenv("MODEL_DIR", "./model")
MODEL_PATH = os.path.join(MODEL_DIR, "latest_model.json")
PREDICT_OUT_DIR = os.getenv("PREDICT_OUT_DIR", "./predict_outputs")
os.makedirs(PREDICT_OUT_DIR, exist_ok=True)

# Main Process 
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["recent", "ids"], required=True, help="Prediction mode")
    parser.add_argument("--days", type=int, default=1, help="How many recent days (mode=recent)")
    parser.add_argument("--ids", nargs="+", type=int, help="Issue numbers (mode=ids)")
    parser.add_argument("--out", type=str, help="Export to CSV (optional)")
    args = parser.parse_args()

    # 1. Fetch issues according to mode
    if args.mode == "recent":
        issues = fetch_open_issues_by_recent(args.days)
        print(f"[INFO] Fetched {len(issues)} open issues from last {args.days} days.")
    else:
        issues = fetch_open_issues_by_ids(args.ids)
        print(f"[INFO] Fetched {len(issues)} open issues by IDs.")

    if not issues:
        print("[WARN] No open issues found. Exit.")
        exit(0)

    # 2. Predict issues
    df = predict_issues(issues, MODEL_PATH)
    output_cols = ["number", "title", "created_at", "prob_closed_within_7_days"]
    print(df[output_cols].to_string(index=False))

    # 3. Output CSV
    if args.out:
        out_path = args.out
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = os.path.join(PREDICT_OUT_DIR, f"open_issues_pred_{args.mode}_{timestamp}.csv")
    df[output_cols].to_csv(out_path, index=False)
    print(f"[DONE] Saved prediction to: {out_path}")

if __name__ == "__main__":
    main()
