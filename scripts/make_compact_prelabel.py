"""Buat salinan ringkas hasil pre-label untuk anotasi sentimen."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "data/processed/dataset_coretax_youtube_prelabel_indobert.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "data/processed/dataset_coretax_youtube_prelabel_indobert_ringkas.csv"

# Nomor baris menghubungkan hasil anotasi dengan metadata pada file sumber.
COLUMNS = [
    "nomor_baris_sumber",
    "komentar",
    "komentar_clean",
    "komentar_preprocessed",
    "pseudo_label_indobert",
    "confidence_indobert",
    "perlu_review",
    "alasan_review",
    "label_annotator_1",
    "label_annotator_2",
    "label_final",
    "catatan_anotator",
    "status_anotasi",
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    input_path = args.input.resolve()
    output_path = args.output.resolve()
    if input_path == output_path:
        parser.error("Output harus berbeda dari input agar file asli tetap utuh.")

    with input_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        missing = set(COLUMNS[1:]) - set(reader.fieldnames or [])
        if missing:
            parser.error(f"Kolom sumber tidak tersedia: {sorted(missing)}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("x", encoding="utf-8-sig", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=COLUMNS)
            writer.writeheader()
            count = 0
            for count, row in enumerate(reader, start=1):
                writer.writerow({"nomor_baris_sumber": count, **{
                    column: row[column] for column in COLUMNS[1:]
                }})

    print(f"Salinan dibuat: {output_path} ({count} baris, {len(COLUMNS)} kolom)")


if __name__ == "__main__":
    main()
