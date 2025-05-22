FROM python:3.11-slim-bullseye

WORKDIR /app

COPY requirements.txt ./

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

EXPOSE 8000

# ==== Download model from S3 on container start & run API ====
CMD ["sh", "-c", "python scripts/download_model_from_s3.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
