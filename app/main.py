import os
from fastapi import FastAPI, Query, Body
from fastapi.responses import JSONResponse, FileResponse
from typing import List
from dotenv import load_dotenv
from datetime import datetime
from prometheus_fastapi_instrumentator import Instrumentator

from app.predict_utils import (
    fetch_open_issues_by_recent,
    fetch_open_issues_by_ids,
    predict_issues
)

# ===== Load config =====
load_dotenv()
MODEL_DIR = os.getenv("MODEL_DIR", "./model")
MODEL_PATH = os.path.join(MODEL_DIR, "latest_model.json")
CSV_OUTPUT_DIR = os.getenv("CSV_OUTPUT_DIR", "./predict_outputs")
os.makedirs(CSV_OUTPUT_DIR, exist_ok=True)

app = FastAPI()

@app.get("/predict_recent_open_issues")
def predict_recent_open_issues(days: int = Query(1, description="How many recent days")):
    issues = fetch_open_issues_by_recent(days)
    df = predict_issues(issues, MODEL_PATH)
    return JSONResponse(df.to_dict(orient="records"))

@app.post("/predict_by_ids")
def predict_by_ids(ids: List[int] = Body(..., embed=True)):
    issues = fetch_open_issues_by_ids(ids)
    df = predict_issues(issues, MODEL_PATH)
    return JSONResponse(df.to_dict(orient="records"))

@app.get("/export_predictions")
def export_predictions(days: int = Query(1, description="Export CSV for open issues created in recent days")):
    issues = fetch_open_issues_by_recent(days)
    df = predict_issues(issues, MODEL_PATH)
    if df.empty:
        return JSONResponse({"msg": "No open issues found."})
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(CSV_OUTPUT_DIR, f"open_issues_pred_recent_{timestamp}.csv")
    df.to_csv(out_path, index=False)
    return FileResponse(out_path, media_type="text/csv", filename=os.path.basename(out_path))

@app.post("/export_predictions_by_ids")
def export_predictions_by_ids(ids: List[int] = Body(..., embed=True)):
    issues = fetch_open_issues_by_ids(ids)
    df = predict_issues(issues, MODEL_PATH)
    if df.empty:
        return JSONResponse({"msg": "No open issues found."})
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(CSV_OUTPUT_DIR, f"open_issues_pred_by_ids_{timestamp}.csv")
    df.to_csv(out_path, index=False)
    return FileResponse(out_path, media_type="text/csv", filename=os.path.basename(out_path))

# ==== Prometheus metrics ====
Instrumentator().instrument(app).expose(app)