import os
import glob
from datetime import datetime
from dotenv import load_dotenv
from app.utils import upload_file_to_s3

# Load environment variables
load_dotenv()
PREDICT_OUT_DIR = os.getenv("PREDICT_OUT_DIR", "./predict_outputs")
BUCKET_NAME = os.getenv("MODEL_BUCKET")
S3_PREFIX = "predict_outputs"

def upload_today_csvs():
    today = datetime.now().strftime("%Y%m%d")
    pattern = os.path.join(PREDICT_OUT_DIR, f"*{today}*.csv")
    files = glob.glob(pattern)

    if not files:
        print(f"[WARN] No CSV files generated today ({today}) found in {PREDICT_OUT_DIR}.")
        return

    for local_path in files:
        basename = os.path.basename(local_path)
        s3_key = f"{S3_PREFIX}/{basename}"   # All files are in predict_outputs/ (no date subdirectory)
        upload_file_to_s3(local_path, BUCKET_NAME, s3_key)

if __name__ == "__main__":
    upload_today_csvs()
