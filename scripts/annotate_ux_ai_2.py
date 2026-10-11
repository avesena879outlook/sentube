"""AI-assisted, independent UX annotation for annotator 2's remaining rows."""

import concurrent.futures
import csv
import json
import subprocess
import sys
from pathlib import Path


PATH = Path("data/processed/anotasi_ux_coretax_anotator_2_3000.csv")
BATCH_SIZE = 75
MAX_WORKERS = 2


def classify(batch):
    numbered = [
        {"i": i, "komentar": row["komentar"]}
        for i, row in batch
    ]
    prompt = (
        "Anda anotator AI kedua yang mandiri untuk riset UX aplikasi Coretax. "
        "Nilai setiap komentar bahasa Indonesia dari teks aslinya, bukan dari prediksi model lain. "
        "Tentukan dahulu apakah komentar membicarakan pengalaman menggunakan aplikasi/situs Coretax: "
        "login, aktivasi, tampilan, fitur, alur pengisian, kelambatan, galat, OTP, bantuan operasional. "
        "Kode 1=positif terhadap pengalaman aplikasi (berhasil, mudah, terbantu); "
        "2=negatif terhadap pengalaman aplikasi (gagal, sulit, error, lambat, bingung, sindiran); "
        "3=netral tentang cara menggunakan fitur, tanpa pujian/keluhan; "
        "4=di luar topik UX (aturan/tarif pajak, pejabat, anggaran proyek, video/tutorial, "
        "pembuat konten, permintaan topik video, aplikasi lain tanpa hubungan Coretax); "
        "5=tidak pasti bila rujukan atau kaitan UX tak dapat ditentukan dari teks. "
        "Pujian kepada tutorial bukan otomatis pujian UX. Pertanyaan yang menyebut kegagalan/error "
        "adalah negatif. Jangan tebak dari konteks video yang tak tersedia. "
        "Jika ada pajak dan aplikasi sekaligus, nilai sikap terhadap penggunaan aplikasinya. "
        "Balas JSON murni satu objek dengan 'codes' berupa larik angka urut sesuai masukan, "
        "dan 'notes' berupa objek yang memetakan indeks i (sebagai string) ke alasan singkat "
        "untuk SETIAP kode 4/5 atau kasus sulit. Jangan sertakan markdown, narasi, atau teks lain. "
        f"Jumlah komentar: {len(numbered)}. Data:\n"
        + json.dumps(numbered, ensure_ascii=False, separators=(",", ":"))
    )
    for attempt in range(3):
        result = subprocess.run(
            [
                "codex", "exec", "--ephemeral", "--skip-git-repo-check",
                "-C", "/tmp", "-s", "read-only", "-",
            ],
            input=prompt,
            text=True,
            capture_output=True,
            timeout=600,
        )
        if result.returncode != 0:
            print(
                f"Batch {batch[0][0]}–{batch[-1][0]} attempt {attempt+1}: "
                f"Codex exited {result.returncode}: {result.stderr[-350:]}",
                file=sys.stderr,
                flush=True,
            )
            continue
        try:
            data = json.loads(result.stdout.strip())
            codes = data["codes"]
            notes = data["notes"]
            if len(codes) != len(batch) or any(code not in (1, 2, 3, 4, 5) for code in codes):
                raise ValueError("Wrong code count or invalid code")
            if not isinstance(notes, dict):
                raise ValueError("notes is not a mapping")
            output = {}
            for (i, _), code in zip(batch, codes):
                note = str(notes.get(str(i), "")).strip()
                if code == 4 and not note:
                    note = "Tidak membahas pengalaman penggunaan Coretax."
                elif code == 5 and not note:
                    note = "Kaitan atau sikap terhadap UX Coretax tidak cukup jelas."
                output[i] = (str(code), note)
            return output
        except (ValueError, TypeError, KeyError) as exc:
            print(
                f"Batch {batch[0][0]}–{batch[-1][0]} attempt {attempt+1}: "
                f"invalid JSON/result: {exc}; output tail={result.stdout[-300:]}",
                file=sys.stderr,
                flush=True,
            )
    raise RuntimeError(f"Batch {batch[0][0]}–{batch[-1][0]} failed three times")


def write_rows(fieldnames, rows):
    with PATH.open("w", newline="", encoding="utf-8-sig") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    with PATH.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        fieldnames = reader.fieldnames
        rows = list(reader)
    if len(rows) != 3000 or fieldnames is None:
        raise ValueError("Unexpected CSV shape")
    pending = [(i, row) for i, row in enumerate(rows, 1) if not row["label_annotator_2"]]
    batches = [pending[i:i+BATCH_SIZE] for i in range(0, len(pending), BATCH_SIZE)]
    print(f"Pending {len(pending)} comments in {len(batches)} batches", flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(classify, batch): batch for batch in batches}
        for future in concurrent.futures.as_completed(futures):
            annotations = future.result()
            for i, (code, note) in annotations.items():
                rows[i-1]["label_annotator_2"] = code
                rows[i-1]["catatan_anotator"] = note
            write_rows(fieldnames, rows)
            print(
                f"Completed {min(annotations)}–{max(annotations)}; "
                f"remaining {sum(not row['label_annotator_2'] for row in rows)}",
                flush=True,
            )


if __name__ == "__main__":
    main()
