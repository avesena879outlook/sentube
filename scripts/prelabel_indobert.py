"""Create IndoBERT-assisted sentiment pre-labels for manual annotation.

The model output is a pseudo-label, not ground truth. Human annotators should
review low-confidence predictions and a representative sample of the rest.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "processed" / "dataset_coretax_youtube_preprocessed.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "processed" / "dataset_coretax_youtube_prelabel_indobert.csv"
DEFAULT_REPORT = PROJECT_ROOT / "data" / "processed" / "indobert_prelabel_report.json"
DEFAULT_MODEL = "tyqiangz/indobert-lite-large-p2-smsa"

# IndoNLU SmSA class order. This is used only when the downloaded model config
# contains generic names such as LABEL_0, LABEL_1, and LABEL_2.
SMSA_FALLBACK_LABELS = {0: "positif", 1: "netral", 2: "negatif"}
SENTIMENT_ALIASES = {
    "positive": "positif",
    "positif": "positif",
    "neutral": "netral",
    "netral": "netral",
    "negative": "negatif",
    "negatif": "negatif",
}

PREDICTION_COLUMNS = [
    "pseudo_label_indobert",
    "confidence_indobert",
    "margin_indobert",
    "entropy_indobert",
    "probabilitas_positif",
    "probabilitas_netral",
    "probabilitas_negatif",
    "perlu_review",
    "alasan_review",
    "model_prelabel",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Buat pseudo-label sentimen IndoBERT untuk diverifikasi anotator manusia."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--text-column", default="komentar_clean")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--max-length", type=int, default=256)
    parser.add_argument("--confidence-threshold", type=float, default=0.80)
    parser.add_argument("--margin-threshold", type=float, default=0.30)
    parser.add_argument("--checkpoint-every", type=int, default=1000)
    parser.add_argument(
        "--device",
        choices=("auto", "cuda", "cpu"),
        default="auto",
        help="'auto' memilih CUDA jika tersedia.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Lanjutkan baris yang belum diprediksi dari file output yang ada.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Batasi jumlah baris untuk uji coba. Gunakan --output terpisah.",
    )
    return parser.parse_args()


def choose_device(requested: str) -> torch.device:
    if requested == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA diminta tetapi torch.cuda.is_available() bernilai False.")
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(requested)


def normalize_label(value: str) -> str | None:
    return SENTIMENT_ALIASES.get(value.strip().casefold())


def resolve_label_map(model) -> dict[int, str]:
    raw_map = {int(key): str(value) for key, value in model.config.id2label.items()}
    normalized = {key: normalize_label(value) for key, value in raw_map.items()}
    if set(normalized.values()) == {"positif", "netral", "negatif"}:
        return {key: value for key, value in normalized.items() if value is not None}
    if len(raw_map) == 3 and all(value.upper().startswith("LABEL_") for value in raw_map.values()):
        return SMSA_FALLBACK_LABELS.copy()
    raise ValueError(
        "Pemetaan label model tidak dikenali. id2label="
        f"{raw_map}. Gunakan model SmSA tiga kelas atau perbarui pemetaan label."
    )


def atomic_write_csv(data: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    data.to_csv(temporary_path, index=False, encoding="utf-8-sig")
    temporary_path.replace(path)


def load_data(input_path: Path, output_path: Path, text_column: str, resume: bool) -> pd.DataFrame:
    source = pd.read_csv(input_path, encoding="utf-8-sig", low_memory=False)
    if text_column not in source.columns:
        raise ValueError(f"Kolom teks '{text_column}' tidak ditemukan.")

    if resume and output_path.exists():
        result = pd.read_csv(output_path, encoding="utf-8-sig", low_memory=False)
        if len(result) != len(source):
            raise ValueError("Output checkpoint tidak memiliki jumlah baris yang sama dengan input.")
        for column in source.columns:
            if column not in result.columns:
                result[column] = source[column]
        return result

    result = source.copy()
    for column in PREDICTION_COLUMNS:
        result[column] = pd.NA
    result["label_annotator_1"] = pd.NA
    result["label_annotator_2"] = pd.NA
    result["label_final"] = pd.NA
    result["catatan_anotator"] = pd.NA
    result["status_anotasi"] = "belum_diperiksa"
    return result


def pending_indices(data: pd.DataFrame, limit: int | None) -> list[int]:
    if "pseudo_label_indobert" not in data.columns:
        pending = data.index.tolist()
    else:
        pending = data.index[data["pseudo_label_indobert"].isna()].tolist()
    return pending[:limit] if limit is not None else pending


def review_reasons(
    text: str,
    confidence: float,
    margin: float,
    confidence_threshold: float,
    margin_threshold: float,
    duplicate: bool,
) -> list[str]:
    reasons: list[str] = []
    if confidence < confidence_threshold:
        reasons.append("confidence_rendah")
    if margin < margin_threshold:
        reasons.append("margin_kecil")
    if len(text.split()) < 3:
        reasons.append("teks_sangat_pendek")
    if duplicate:
        reasons.append("duplikat_lintas_konteks")
    return reasons


def run_prelabel(args: argparse.Namespace) -> dict:
    if args.batch_size < 1 or args.max_length < 8 or args.checkpoint_every < 1:
        raise ValueError("batch-size, max-length, dan checkpoint-every harus bernilai positif.")
    if not 0 <= args.confidence_threshold <= 1 or not 0 <= args.margin_threshold <= 1:
        raise ValueError("Threshold harus berada pada rentang 0 sampai 1.")
    if args.limit is not None and args.limit < 1:
        raise ValueError("--limit minimal 1.")
    if args.limit is not None and args.output.resolve() == DEFAULT_OUTPUT.resolve():
        raise ValueError("Saat memakai --limit, tentukan --output terpisah agar output utama tidak parsial.")

    device = choose_device(args.device)
    data = load_data(args.input.resolve(), args.output.resolve(), args.text_column, args.resume)
    pending = pending_indices(data, args.limit)
    if not pending:
        print("Tidak ada baris yang perlu diprediksi.")
        return build_report(data, args, device, 0.0)

    print(f"Memuat tokenizer dan model: {args.model}")
    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=False)
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model,
        trust_remote_code=False,
    ).to(device)
    model.eval()
    label_map = resolve_label_map(model)
    if set(label_map.values()) != {"positif", "netral", "negatif"}:
        raise ValueError(f"Model harus memiliki tiga kelas sentimen, ditemukan: {label_map}")

    device_name = torch.cuda.get_device_name(0) if device.type == "cuda" else "CPU"
    print(f"Perangkat: {device_name}; baris diproses: {len(pending)}; batch: {args.batch_size}")
    started = time.perf_counter()
    processed_since_save = 0

    with torch.inference_mode():
        for start in range(0, len(pending), args.batch_size):
            batch_indices = pending[start : start + args.batch_size]
            texts = data.loc[batch_indices, args.text_column].fillna("").astype(str).tolist()
            encoded = tokenizer(
                texts,
                padding=True,
                truncation=True,
                max_length=args.max_length,
                return_tensors="pt",
            )
            encoded = {key: value.to(device, non_blocking=True) for key, value in encoded.items()}
            with torch.autocast(device_type="cuda", dtype=torch.float16, enabled=device.type == "cuda"):
                logits = model(**encoded).logits
            probabilities = torch.softmax(logits.float(), dim=-1).cpu().numpy()

            for row_index, text, row_probabilities in zip(batch_indices, texts, probabilities, strict=True):
                ordered = np.sort(row_probabilities)[::-1]
                prediction_id = int(np.argmax(row_probabilities))
                confidence = float(ordered[0])
                margin = float(ordered[0] - ordered[1])
                entropy = float(
                    -np.sum(row_probabilities * np.log(np.clip(row_probabilities, 1e-12, 1.0)))
                    / math.log(len(row_probabilities))
                )
                duplicate = bool(data.at[row_index, "duplikat_teks_lintas_konteks"]) if (
                    "duplikat_teks_lintas_konteks" in data.columns
                    and pd.notna(data.at[row_index, "duplikat_teks_lintas_konteks"])
                ) else False
                reasons = review_reasons(
                    text,
                    confidence,
                    margin,
                    args.confidence_threshold,
                    args.margin_threshold,
                    duplicate,
                )
                probability_by_label = {
                    label_map[class_id]: float(row_probabilities[class_id])
                    for class_id in range(len(row_probabilities))
                }
                data.at[row_index, "pseudo_label_indobert"] = label_map[prediction_id]
                data.at[row_index, "confidence_indobert"] = round(confidence, 6)
                data.at[row_index, "margin_indobert"] = round(margin, 6)
                data.at[row_index, "entropy_indobert"] = round(entropy, 6)
                for label in ("positif", "netral", "negatif"):
                    data.at[row_index, f"probabilitas_{label}"] = round(probability_by_label[label], 6)
                data.at[row_index, "perlu_review"] = bool(reasons)
                data.at[row_index, "alasan_review"] = ";".join(reasons)
                data.at[row_index, "model_prelabel"] = args.model

            processed_since_save += len(batch_indices)
            completed = start + len(batch_indices)
            if processed_since_save >= args.checkpoint_every or completed == len(pending):
                atomic_write_csv(data, args.output.resolve())
                elapsed = time.perf_counter() - started
                print(f"Checkpoint {completed}/{len(pending)} ({elapsed:.1f} detik)")
                processed_since_save = 0

    elapsed = time.perf_counter() - started
    report = build_report(data, args, device, elapsed)
    args.report.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.report.resolve().write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return report


def build_report(data: pd.DataFrame, args: argparse.Namespace, device: torch.device, elapsed: float) -> dict:
    predicted = data["pseudo_label_indobert"].notna() if "pseudo_label_indobert" in data else pd.Series(False, index=data.index)
    review = (
        data.loc[predicted, "perlu_review"].astype("boolean").fillna(False)
        if "perlu_review" in data
        else pd.Series(dtype=bool)
    )
    return {
        "input": str(args.input.resolve()),
        "output": str(args.output.resolve()),
        "model": args.model,
        "text_column": args.text_column,
        "device": str(device),
        "gpu": torch.cuda.get_device_name(0) if device.type == "cuda" else None,
        "rows_total": int(len(data)),
        "rows_predicted": int(predicted.sum()),
        "label_counts": data.loc[predicted, "pseudo_label_indobert"].value_counts().to_dict(),
        "review_rows": int(review.sum()),
        "review_percentage": round(float(review.mean() * 100), 2) if len(review) else 0.0,
        "confidence_threshold": args.confidence_threshold,
        "margin_threshold": args.margin_threshold,
        "elapsed_seconds": round(elapsed, 2),
    }


def main() -> None:
    args = parse_args()
    report = run_prelabel(args)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
