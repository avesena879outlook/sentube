"""Apply documented spot-audit corrections to AI annotator 1's worksheet."""

from __future__ import annotations

import csv
from pathlib import Path
import tempfile
import os


ROOT = Path(__file__).resolve().parents[1]
WORKSHEET = ROOT / "data/processed/anotasi_ux_coretax_anotator_1_3000.csv"

# Source-row ID: (previous code, reviewed code, note).
CORRECTIONS = {
    "107": ("3", "4", "Meminta video perpajakan tanpa pengalaman aplikasi yang jelas."),
    "3583": ("2", "5", "Kritik perbaikan tidak menjelaskan bagian aplikasi yang dimaksud."),
    "5636": ("3", "5", "Pertanyaan NIK atau nomor pajak tanpa konteks fitur."),
    "7386": ("3", "1", ""),
    "11881": ("2", "5", "Objek yang tampil hitam putih tidak jelas dari komentar."),
    "2536": ("2", "4", "Membahas kemampuan pengembang, bukan pengalaman penggunaan."),
    "9133": ("3", "2", "Penulis tidak dapat melanjutkan karena halaman hilang."),
    "11957": ("3", "4", "Meminta tutorial tanpa pengalaman aplikasi yang jelas."),
    "9503": ("3", "4", "Bertanya prosedur NPWP suami istri tanpa UX yang jelas."),
    "4773": ("1", "4", "Menilai proyek sistem secara umum, bukan pengalaman penggunaan."),
    "1193": ("1", "4", "Menilai konten dan Coretax secara umum tanpa pengalaman penggunaan."),
    "6072": ("3", "1", ""),
    "8099": ("3", "1", ""),
    "7989": ("3", "1", ""),
    "9799": ("3", "1", ""),
    "7741": ("3", "1", ""),
    "10616": ("3", "1", ""),
    "8215": ("3", "2", "Pilihan antarmuka yang dibutuhkan hilang."),
    "6757": ("3", "2", "Penulis menyatakan aplikasi tidak bisa dibuka di HP."),
    "10665": ("3", "1", ""),
}


def main() -> None:
    with WORKSHEET.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        fields = reader.fieldnames or []
        rows = list(reader)
    if len(rows) != 3000:
        raise ValueError(f"Jumlah baris tidak sesuai: {len(rows)}")
    by_id = {row["nomor_baris_sumber"]: row for row in rows}
    if len(by_id) != len(rows) or not set(CORRECTIONS) <= set(by_id):
        raise ValueError("nomor_baris_sumber tidak unik atau koreksi tidak ditemukan")
    for row_id, (previous, reviewed, note) in CORRECTIONS.items():
        row = by_id[row_id]
        if row["label_annotator_1"] != previous:
            raise ValueError(f"Baris sumber {row_id}: kode awal berubah")
        row["label_annotator_1"] = reviewed
        row["catatan_anotator"] = note

    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8-sig", newline="", dir=WORKSHEET.parent,
        prefix=WORKSHEET.name + ".", suffix=".tmp", delete=False,
    ) as target:
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
        temporary_path = Path(target.name)
    os.replace(temporary_path, WORKSHEET)
    print(f"Koreksi audit diterapkan: {len(CORRECTIONS)} baris")


if __name__ == "__main__":
    main()
