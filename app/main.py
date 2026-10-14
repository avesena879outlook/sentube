from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app.ml_pipeline import ml_engine
from app.services import fetch_youtube_comments, parse_csv_dataset


BASE_DIR = Path(__file__).resolve().parent.parent
REPORT_DIR = BASE_DIR / "reports"
DATA_DIR = BASE_DIR / "data" / "processed"

app = FastAPI(title="SenTube Dashboard", version="0.2.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


class PredictionRequest(BaseModel):
    texts: list[str] = Field(min_length=1, max_length=500)


def load_dashboard_context() -> dict:
    split_report = json.loads(
        (DATA_DIR / "train_test_split_report.json").read_text(encoding="utf-8")
    )
    training_report = json.loads(
        (REPORT_DIR / "training_report_fast.json").read_text(encoding="utf-8")
    )
    comparison = [
        {
            "name": item["model"],
            "cv_macro_f1": item["cv_macro_f1"],
            "accuracy": item["test_accuracy"],
            "macro_f1": item["test_macro_f1"],
            "features": "100" if item["model"] == "SVM + mRMR" else "TF-IDF penuh",
        }
        for item in training_report["results"]
    ]
    feature_frame = pd.read_csv(
        REPORT_DIR / "mrmr_selected_features_fast.csv", encoding="utf-8-sig"
    )
    distribution = split_report["class_distribution_all"]
    total = split_report["rows_included"]
    return {
        "dataset": {
            "total": total,
            "train": split_report["train_rows"],
            "test": split_report["test_rows"],
            "excluded": split_report["rows_excluded"],
            "distribution": [
                {
                    "label": label,
                    "count": distribution.get(label, 0),
                    "percentage": round(distribution.get(label, 0) / total * 100, 1),
                }
                for label in ("negatif", "netral", "positif")
            ],
        },
        "models": comparison,
        "best_model": max(comparison, key=lambda item: item["macro_f1"]),
        "features": feature_frame["feature"].head(14).tolist(),
        "model_ready": ml_engine.ready,
        "preliminary": training_report.get("preliminary", True),
    }


def render_prediction(request: Request, results: dict, source: str, query: str) -> HTMLResponse:
    return templates.TemplateResponse(
        "fragments/result.html",
        {"request": request, "results": results, "source": source, "query": query},
    )


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request, **load_dashboard_context()}
    )


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "models_ready": ml_engine.ready}


@app.post("/api/predict")
async def api_predict(payload: PredictionRequest) -> dict:
    results = ml_engine.predict_comparison(payload.texts)
    if "error" in results:
        raise HTTPException(status_code=422, detail=results["error"])
    return results


@app.post("/analyze/text", response_class=HTMLResponse)
async def analyze_text(
    request: Request,
    text: Annotated[str, Form(min_length=2)],
):
    results = ml_engine.predict_comparison([text])
    return render_prediction(request, results, "text", text[:80])


@app.post("/analyze/csv", response_class=HTMLResponse)
async def analyze_csv(
    request: Request,
    file: Annotated[UploadFile, File()],
    text_column: Annotated[str | None, Form()] = None,
):
    try:
        comments = parse_csv_dataset(await file.read(), text_column=text_column)
        results = ml_engine.predict_comparison(comments[:2000])
    except Exception as exc:
        results = {"error": f"CSV tidak dapat diproses: {exc}"}
    return render_prediction(request, results, "csv", file.filename or "dataset.csv")


@app.post("/analyze/youtube", response_class=HTMLResponse)
async def analyze_youtube(
    request: Request,
    keyword: Annotated[str, Form(min_length=2)],
):
    try:
        comments = fetch_youtube_comments(keyword, max_results=100)
        if not comments:
            raise ValueError("Komentar tidak ditemukan untuk kueri tersebut.")
        results = ml_engine.predict_comparison(comments)
    except Exception as exc:
        results = {"error": str(exc)}
    return render_prediction(request, results, "youtube", keyword)
