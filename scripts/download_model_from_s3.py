import os
import boto3
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# S3 configuration
BUCKET_NAME = os.getenv("MODEL_BUCKET")
MODEL_S3_KEY = "model/latest_model.json"  # Main file on S3

# Local model file directory (for the inference API service on EC2)
MODEL_DIR = os.getenv("MODEL_DIR", "/home/ec2-user/mlops-api/model")
LOCAL_MODEL_PATH = os.path.join(MODEL_DIR, "latest_model.json")

def download_model():
    os.makedirs(MODEL_DIR, exist_ok=True)
    s3 = boto3.client("s3")
    s3.download_file(BUCKET_NAME, MODEL_S3_KEY, LOCAL_MODEL_PATH)
    print(f"[DONE] Downloaded s3://{BUCKET_NAME}/{MODEL_S3_KEY} → {LOCAL_MODEL_PATH}")

if __name__ == "__main__":
    download_model()
