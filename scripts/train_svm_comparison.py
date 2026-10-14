"""Train and compare SVM with and without mRMR on the locked data split."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache" / "matplotlib"))

import joblib
import matplotlib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
from sklearn.feature_extraction.text import TfidfVectorizer


matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


sys.path.insert(0, str(ROOT))

from app.feature_selection import MRMRSelector  # noqa: E402
from app.preprocessor import clean_text  # noqa: E402


DEFAULT_INPUT = ROOT / "data/processed/comments_labeled.csv"
LABEL_ORDER = ["negatif", "netral", "positif"]
RANDOM_STATE = 42


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--fast", action="store_true", help="Uji alur dengan satu konfigurasi per skenario.")
    parser.add_argument("--cv-folds", type=int, default=10)
    parser.add_argument("--n-jobs", type=int, default=-1)
    return parser.parse_args()


def build_tfidf() -> TfidfVectorizer:
    return TfidfVectorizer(
        preprocessor=clean_text,
        tokenizer=str.split,
        token_pattern=None,
        lowercase=False,
        max_features=10_000,
        min_df=2,
        max_df=0.95,
        ngram_range=(1, 2),
        sublinear_tf=True,
    )


def train_search(
    name: str,
    pipeline: Pipeline,
    parameters: list[dict],
    cv: StratifiedKFold,
    x_train: pd.Series,
    y_train: pd.Series,
    n_jobs: int,
) -> tuple[GridSearchCV, float]:
    search = GridSearchCV(
        estimator=pipeline,
        param_grid=parameters,
        scoring="f1_macro",
        cv=cv,
        n_jobs=n_jobs,
        verbose=2,
        refit=True,
        return_train_score=False,
        error_score="raise",
    )
    started = time.perf_counter()
    search.fit(x_train, y_train)
    elapsed = time.perf_counter() - started
    print(f"{name}: {elapsed:.2f} detik; CV Macro-F1={search.best_score_:.4f}")
    return search, elapsed


def evaluate(
    name: str,
    search: GridSearchCV,
    train_seconds: float,
    x_test: pd.Series,
    y_test: pd.Series,
) -> dict:
    started = time.perf_counter()
    prediction = search.predict(x_test)
    predict_seconds = time.perf_counter() - started
    return {
        "model": name,
        "cv_macro_f1": float(search.best_score_),
        "test_accuracy": float(accuracy_score(y_test, prediction)),
        "test_macro_f1": float(f1_score(y_test, prediction, average="macro")),
        "test_weighted_f1": float(f1_score(y_test, prediction, average="weighted")),
        "train_seconds": float(train_seconds),
        "predict_seconds": float(predict_seconds),
        "best_params": search.best_params_,
        "classification_report": classification_report(
            y_test,
            prediction,
            labels=LABEL_ORDER,
            output_dict=True,
            zero_division=0,
        ),
        "confusion_matrix": confusion_matrix(y_test, prediction, labels=LABEL_ORDER).tolist(),
        "prediction": prediction,
    }


def main() -> None:
    args = parse_args()
    if args.cv_folds < 2:
        raise ValueError("--cv-folds minimal 2.")

    data = pd.read_csv(args.input.resolve(), encoding="utf-8-sig", low_memory=False)
    required = {"text", "label_final", "split", "nomor_baris_sumber", "status_anotasi"}
    if missing := required - set(data.columns):
        raise ValueError(f"Kolom wajib tidak tersedia: {sorted(missing)}")
    data["label_final"] = data["label_final"].astype(str).str.casefold().str.strip()
    data["split"] = data["split"].astype(str).str.casefold().str.strip()
    if set(data["label_final"]) != set(LABEL_ORDER):
        raise ValueError(f"Label harus tepat tiga kelas: {LABEL_ORDER}")
    if set(data["split"]) != {"train", "test"}:
        raise ValueError("Kolom split harus hanya berisi train dan test.")

    train = data.loc[data["split"].eq("train")].copy()
    test = data.loc[data["split"].eq("test")].copy()
    if set(train["nomor_baris_sumber"]) & set(test["nomor_baris_sumber"]):
        raise ValueError("ID sumber train dan test beririsan.")
    x_train, y_train = train["text"], train["label_final"]
    x_test, y_test = test["text"], test["label_final"]

    effective_folds = min(args.cv_folds, int(y_train.value_counts().min()))
    cv = StratifiedKFold(n_splits=effective_folds, shuffle=True, random_state=RANDOM_STATE)
    svm_grid = (
        [{"svm__kernel": ["linear"], "svm__C": [1]}]
        if args.fast
        else [
            {"svm__kernel": ["linear"], "svm__C": [0.1, 1, 10]},
            {
                "svm__kernel": ["rbf"],
                "svm__C": [0.1, 1, 10],
                "svm__gamma": ["scale", 0.01, 0.1],
            },
        ]
    )
    mrmr_k = [100] if args.fast else [100, 200, 300, 500]

    baseline_pipeline = Pipeline([
        ("tfidf", build_tfidf()),
        ("svm", SVC(class_weight="balanced", decision_function_shape="ovr")),
    ])
    mrmr_pipeline = Pipeline([
        ("tfidf", build_tfidf()),
        ("mrmr", MRMRSelector(random_state=RANDOM_STATE)),
        ("svm", SVC(class_weight="balanced", decision_function_shape="ovr")),
    ])
    mrmr_grid = [{**parameters, "mrmr__k": mrmr_k} for parameters in svm_grid]

    baseline_search, baseline_seconds = train_search(
        "SVM tanpa mRMR", baseline_pipeline, svm_grid, cv, x_train, y_train, args.n_jobs
    )
    mrmr_search, mrmr_seconds = train_search(
        "SVM + mRMR", mrmr_pipeline, mrmr_grid, cv, x_train, y_train, args.n_jobs
    )
    results = [
        evaluate("SVM tanpa mRMR", baseline_search, baseline_seconds, x_test, y_test),
        evaluate("SVM + mRMR", mrmr_search, mrmr_seconds, x_test, y_test),
    ]

    suffix = "_fast" if args.fast else ""
    artifact_dir = ROOT / "artifacts"
    report_dir = ROOT / "reports"
    artifact_dir.mkdir(exist_ok=True)
    report_dir.mkdir(exist_ok=True)
    joblib.dump(baseline_search.best_estimator_, artifact_dir / f"svm_baseline{suffix}.joblib")
    joblib.dump(mrmr_search.best_estimator_, artifact_dir / f"svm_mrmr{suffix}.joblib")

    comparison = pd.DataFrame([{key: result[key] for key in [
        "model", "cv_macro_f1", "test_accuracy", "test_macro_f1",
        "test_weighted_f1", "train_seconds", "predict_seconds",
    ]} for result in results])
    comparison.to_csv(report_dir / f"model_comparison{suffix}.csv", index=False, encoding="utf-8-sig")

    selected_indices = mrmr_search.best_estimator_.named_steps["mrmr"].get_support(indices=True)
    feature_names = mrmr_search.best_estimator_.named_steps["tfidf"].get_feature_names_out()
    selected_features = pd.DataFrame({
        "rank": np.arange(1, len(selected_indices) + 1),
        "feature_index": selected_indices,
        "feature": feature_names[selected_indices],
    })
    selected_features.to_csv(
        report_dir / f"mrmr_selected_features{suffix}.csv", index=False, encoding="utf-8-sig"
    )

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    for axis, result in zip(axes, results, strict=True):
        ConfusionMatrixDisplay(
            np.asarray(result["confusion_matrix"]), display_labels=LABEL_ORDER
        ).plot(ax=axis, cmap="Blues", colorbar=False)
        axis.set_title(result["model"])
    fig.tight_layout()
    fig.savefig(report_dir / f"confusion_matrix_comparison{suffix}.png", dpi=180)
    plt.close(fig)

    unresolved_status = int(data["status_anotasi"].eq("perlu_adjudikasi").sum())
    report = {
        "mode": "fast" if args.fast else "full",
        "preliminary": bool(args.fast or unresolved_status),
        "methodology_warning": (
            f"{unresolved_status} baris masih berstatus perlu_adjudikasi. "
            "Hasil tidak boleh dilaporkan sebagai eksperimen final sebelum status dikonfirmasi."
            if unresolved_status else None
        ),
        "random_state": RANDOM_STATE,
        "cv_folds": effective_folds,
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "train_distribution": y_train.value_counts().to_dict(),
        "test_distribution": y_test.value_counts().to_dict(),
        "results": [{key: value for key, value in result.items() if key != "prediction"} for result in results],
    }
    (report_dir / f"training_report{suffix}.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(comparison.to_string(index=False))
    print(f"Laporan: {report_dir / f'training_report{suffix}.json'}")


if __name__ == "__main__":
    main()
