"""Preprocess the merged YouTube dataset into a modeling-ready CSV."""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import json
import os
import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.preprocessor import clean_for_labeling, tokenize_for_svm  # noqa: E402
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory  # noqa: E402


DEFAULT_INPUT = PROJECT_ROOT / "data" / "raw" / "yt" / "merged" / "dataset_coretax_youtube_raw_merged.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "processed" / "dataset_coretax_youtube_preprocessed.csv"
DEFAULT_REPORT = PROJECT_ROOT / "data" / "processed" / "preprocessing_report.json"


def normalized_text_key(series: pd.Series) -> pd.Series:
    return (
        series.fillna("")
        .astype(str)
        .str.normalize("NFKC")
        .str.casefold()
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )


def stem_chunk(words: list[str]) -> dict[str, str]:
    stemmer = StemmerFactory().create_stemmer()
    return {word: stemmer.stem(word) for word in words}


def build_stem_map(token_rows: list[list[str]]) -> dict[str, str]:
    vocabulary = sorted({token for tokens in token_rows for token in tokens})
    if not vocabulary:
        return {}
    worker_count = min(max((os.cpu_count() or 2) - 1, 1), 8, len(vocabulary))
    chunk_size = (len(vocabulary) + worker_count - 1) // worker_count
    chunks = [vocabulary[index : index + chunk_size] for index in range(0, len(vocabulary), chunk_size)]
    stem_map: dict[str, str] = {}
    with ProcessPoolExecutor(max_workers=worker_count) as executor:
        for partial in executor.map(stem_chunk, chunks):
            stem_map.update(partial)
    return stem_map


def preprocess(input_path: Path, output_path: Path, report_path: Path) -> dict:
    data = pd.read_csv(input_path, encoding="utf-8-sig")
    required = {"video_id", "penulis", "komentar", "tanggal_komentar"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Kolom wajib tidak tersedia: {sorted(missing)}")

    result = data.copy()
    result["komentar_clean"] = result["komentar"].map(clean_for_labeling)
    token_rows = result["komentar"].map(tokenize_for_svm).tolist()
    stem_map = build_stem_map(token_rows)
    result["komentar_preprocessed"] = [
        " ".join(stem_map[token] for token in tokens if stem_map.get(token))
        for tokens in token_rows
    ]
    result["jumlah_kata_raw"] = result["komentar"].fillna("").astype(str).str.split().str.len()
    result["jumlah_token_preprocessed"] = result["komentar_preprocessed"].str.split().str.len()

    text_key = normalized_text_key(result["komentar"])
    result["duplikat_teks_lintas_konteks"] = text_key.duplicated(keep=False)
    result["status_preprocessing"] = "valid"
    result.loc[result["komentar_clean"].eq(""), "status_preprocessing"] = "teks_kosong"
    result.loc[
        result["komentar_clean"].ne("") & result["komentar_preprocessed"].eq(""),
        "status_preprocessing",
    ] = "token_habis_setelah_preprocessing"

    result["tanggal_komentar"] = pd.to_datetime(
        result["tanggal_komentar"], errors="coerce", utc=True
    ).dt.strftime("%Y-%m-%d")
    result["tanggal_upload"] = pd.to_datetime(
        result["tanggal_upload"], errors="coerce", utc=True
    ).dt.strftime("%Y-%m-%d")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(".tmp")
    result.to_csv(temporary_path, index=False, encoding="utf-8-sig")
    temporary_path.replace(output_path)

    report = {
        "input": str(input_path),
        "output": str(output_path),
        "rows_input": int(len(data)),
        "rows_output": int(len(result)),
        "columns_output": int(len(result.columns)),
        "status_counts": result["status_preprocessing"].value_counts().to_dict(),
        "duplicate_text_rows": int(result["duplikat_teks_lintas_konteks"].sum()),
        "unique_tokens_before_stemming": int(len(stem_map)),
        "unique_stems": int(len(set(stem_map.values()))),
        "empty_clean_text": int(result["komentar_clean"].eq("").sum()),
        "empty_preprocessed_text": int(result["komentar_preprocessed"].eq("").sum()),
        "raw_word_count": {
            "min": int(result["jumlah_kata_raw"].min()),
            "median": float(result["jumlah_kata_raw"].median()),
            "max": int(result["jumlah_kata_raw"].max()),
        },
        "preprocessed_token_count": {
            "min": int(result["jumlah_token_preprocessed"].min()),
            "median": float(result["jumlah_token_preprocessed"].median()),
            "max": int(result["jumlah_token_preprocessed"].max()),
        },
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    report = preprocess(args.input.resolve(), args.output.resolve(), args.report.resolve())
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
