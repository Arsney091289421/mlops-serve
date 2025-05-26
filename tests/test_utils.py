import os
import pandas as pd
import numpy as np
import tempfile
import xgboost as xgb
import pytest
from moto import mock_s3
import boto3

import app.utils as utils  # Assuming your utils.py is in the app/ directory

# 1. Test S3 download
@mock_s3
def test_download_model_from_s3():
    bucket_name = "test-bucket"
    s3_key = "model/latest_model.json"
    model_content = b"mock model file"
    
    # Set up mock S3
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=bucket_name)
    s3.put_object(Bucket=bucket_name, Key=s3_key, Body=model_content)

    with tempfile.TemporaryDirectory() as tmpdir:
        local_path = utils.download_model_from_s3(bucket_name, s3_key, tmpdir)
        assert os.path.exists(local_path)
        with open(local_path, "rb") as f:
            assert f.read() == model_content

# 2. Test feature extraction (using mock issue objects)
class MockLabel:
    def __init__(self, name):
        self.name = name

class MockIssue:
    def __init__(self, number, title, body, labels, created_at, comments, state="open", pull_request=None):
        self.number = number
        self.title = title
        self.body = body
        self.labels = [MockLabel(name) for name in labels]
        self.created_at = created_at
        self.comments = comments
        self.state = state
        self.pull_request = pull_request

def test_extract_features_from_issues():
    from datetime import datetime
    mock_issues = [
        MockIssue(1, "Fix bug", "body", ["bug", "help"], datetime(2024,1,1,10,30), 5),
        MockIssue(2, "Add doc", "", [], datetime(2024,1,2,14,0), 0),
    ]
    df = utils.extract_features_from_issues(mock_issues)
    assert isinstance(df, pd.DataFrame)
    assert "title_len" in df.columns
    assert df.loc[0, "has_bug_label"] == 1
    assert df.loc[1, "has_bug_label"] == 0

# 3. Test model prediction (using a mock xgboost model)
def test_predict_proba(tmp_path):
    # Train and save a dummy model
    X = pd.DataFrame({
        "title_len": [10, 20],
        "body_len": [20, 30],
        "num_labels": [1, 2],
        "has_bug_label": [1, 0],
        "hour_created": [10, 15],
        "comments": [2, 1]
    })
    y = [1, 0]
    model = xgb.XGBClassifier(use_label_encoder=False, eval_metric="auc")
    model.fit(X, y)
    model_path = tmp_path / "test_model.json"
    model.save_model(str(model_path))

    proba = utils.predict_proba(str(model_path), X)
    assert isinstance(proba, np.ndarray)
    assert len(proba) == 2
    assert np.all((proba >= 0) & (proba <= 1))
