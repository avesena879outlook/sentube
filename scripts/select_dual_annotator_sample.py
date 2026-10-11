"""Pilih komentar acak yang sama untuk dua anotator secara reproducible."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import random


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data/processed/dataset_coretax_youtube_prelabel_indobert_ringkas.csv"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/processed")
    parser.add_argument("--count", type=int, default=3000)
    parser.add_argument("--pilot", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if args.count < 1 or not 0 <= args.pilot <= args.count:
        parser.error("--count harus positif dan --pilot antara 0 dan --count.")

    input_path = args.input.resolve()
    output_dir = args.output_dir.resolve()
    with input_path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        required = {"nomor_baris_sumber", "komentar", "pseudo_label_indobert", "perlu_review"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            parser.error(f"Kolom sumber tidak tersedia: {sorted(missing)}")
        rows = list(reader)

    ids = [row["nomor_baris_sumber"] for row in rows]
    if len(ids) != len(set(ids)):
        parser.error("nomor_baris_sumber tidak unik.")
    if args.count > len(rows):
        parser.error(f"--count ({args.count}) melebihi jumlah baris ({len(rows)}).")

    selected = random.Random(args.seed).sample(rows, args.count)
    outputs = {
        1: output_dir / f"anotasi_ux_coretax_anotator_1_{args.count}.csv",
        2: output_dir / f"anotasi_ux_coretax_anotator_2_{args.count}.csv",
    }
    manifest_path = output_dir / f"anotasi_ux_coretax_sampel_{args.count}.json"
    existing = [str(path) for path in [*outputs.values(), manifest_path] if path.exists()]
    if existing:
        parser.error(f"Output sudah ada; tidak ditimpa: {existing}")

    output_dir.mkdir(parents=True, exist_ok=True)
    for annotator, path in outputs.items():
        label_column = f"label_annotator_{annotator}"
        fields = ["nomor_baris_sumber", "tahap", "komentar", label_column, "catatan_anotator"]
        with path.open("x", encoding="utf-8-sig", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=fields)
            writer.writeheader()
            for position, row in enumerate(selected, start=1):
                writer.writerow({
                    "nomor_baris_sumber": row["nomor_baris_sumber"],
                    "tahap": "uji_coba" if position <= args.pilot else "utama",
                    "komentar": row["komentar"],
                    label_column: "",
                    "catatan_anotator": "",
                })

    manifest = {
        "source": str(input_path),
        "source_sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(),
        "sampling_method": "simple_random_without_replacement",
        "seed": args.seed,
        "source_rows": len(rows),
        "selected_rows": len(selected),
        "pilot_rows": args.pilot,
        "main_rows": len(selected) - args.pilot,
        "pseudo_label_counts_for_sampling_audit": dict(Counter(
            row["pseudo_label_indobert"] for row in selected
        )),
        "review_rows_for_sampling_audit": sum(
            row["perlu_review"].strip().casefold() == "true" for row in selected
        ),
        "output_files": {str(key): str(path) for key, path in outputs.items()},
    }
    with manifest_path.open("x", encoding="utf-8") as target:
        json.dump(manifest, target, ensure_ascii=False, indent=2)
        target.write("\n")

    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
