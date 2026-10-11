"""Gabungkan dua lembar anotasi; ubah kode angka menjadi label teks."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data/processed"
CODE_TO_LABEL = {
    "1": "positif",
    "2": "negatif",
    "3": "netral",
    "4": "di_luar_topik",
    "5": "tidak_pasti",
}
VALID_LABELS = set(CODE_TO_LABEL.values())


def load_annotations(path: Path, annotator: int) -> tuple[list[str], dict[str, dict[str, str]]]:
    label_column = f"label_annotator_{annotator}"
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        required = {"nomor_baris_sumber", "tahap", "komentar", label_column, "catatan_anotator"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path}: kolom tidak tersedia: {sorted(missing)}")
        rows: dict[str, dict[str, str]] = {}
        order: list[str] = []
        for row in reader:
            row_id = row["nomor_baris_sumber"].strip()
            if not row_id or row_id in rows:
                raise ValueError(f"{path}: nomor_baris_sumber kosong atau ganda: {row_id!r}")
            raw_label = row[label_column].strip().casefold()
            label = CODE_TO_LABEL.get(raw_label, raw_label)
            if label not in VALID_LABELS:
                raise ValueError(
                    f"{path}: baris sumber {row_id}: kode {raw_label!r} tidak valid atau belum diisi"
                )
            row[label_column] = label
            rows[row_id] = row
            order.append(row_id)
    return order, rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotator-1", type=Path, default=DATA_DIR / "anotasi_ux_coretax_anotator_1_3000.csv")
    parser.add_argument("--annotator-2", type=Path, default=DATA_DIR / "anotasi_ux_coretax_anotator_2_3000.csv")
    parser.add_argument("--output", type=Path, default=DATA_DIR / "anotasi_ux_coretax_gabungan_3000.csv")
    args = parser.parse_args()

    first_path = args.annotator_1.resolve()
    second_path = args.annotator_2.resolve()
    output_path = args.output.resolve()
    if len({first_path, second_path, output_path}) != 3:
        parser.error("Kedua input dan output harus memakai tiga file yang berbeda.")
    first_order, first = load_annotations(first_path, 1)
    _, second = load_annotations(second_path, 2)
    if set(first) != set(second):
        raise ValueError("Kedua file anotator tidak memuat nomor_baris_sumber yang sama.")

    fields = [
        "nomor_baris_sumber", "tahap", "komentar", "label_annotator_1",
        "label_annotator_2", "catatan_anotator_1", "catatan_anotator_2",
        "hasil_perbandingan", "label_final", "status_anotasi",
    ]
    output_rows = []
    for row_id in first_order:
        left, right = first[row_id], second[row_id]
        if (left["tahap"], left["komentar"]) != (right["tahap"], right["komentar"]):
            raise ValueError(f"Baris sumber {row_id}: tahap atau komentar berbeda antar file.")
        label_1 = left["label_annotator_1"]
        label_2 = right["label_annotator_2"]
        comparison = "sepakat" if label_1 == label_2 else "berbeda"
        if "tidak_pasti" in (label_1, label_2):
            comparison = "perlu_adjudikasi"
        output_rows.append({
            "nomor_baris_sumber": row_id,
            "tahap": left["tahap"],
            "komentar": left["komentar"],
            "label_annotator_1": label_1,
            "label_annotator_2": label_2,
            "catatan_anotator_1": left["catatan_anotator"],
            "catatan_anotator_2": right["catatan_anotator"],
            "hasil_perbandingan": comparison,
            "label_final": "",
            "status_anotasi": "perlu_adjudikasi" if comparison != "sepakat" else "belum_diperiksa",
        })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("x", encoding="utf-8-sig", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output_rows)
    print(f"Gabungan dibuat: {output_path} ({len(output_rows)} baris)")


if __name__ == "__main__":
    main()
