# Pre-labeling Sentimen dengan IndoBERT

Skrip `scripts/prelabel_indobert.py` menggunakan IndoBERT yang telah di-*fine-tune* pada IndoNLU SmSA untuk memberi **pseudo-label awal**. Hasil model bukan *ground truth* dan tetap perlu diverifikasi manusia.

## 1. Pastikan GPU aktif

Jalankan dari terminal VS Code di folder proyek:

```powershell
uv run python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else '-')"
```

Hasil yang diharapkan adalah `True` dan `NVIDIA GeForce RTX 3050 Laptop GPU`.

## 2. Uji dengan 100 komentar

Gunakan output khusus agar tidak tertukar dengan hasil penuh:

```powershell
uv run python scripts/prelabel_indobert.py --limit 100 --output data/processed/dataset_coretax_youtube_prelabel_indobert_sample.csv --report data/processed/indobert_prelabel_sample_report.json
```

Model akan diunduh pada eksekusi pertama. Periksa beberapa hasil positif, netral, dan negatif sebelum menjalankan seluruh data.

## 3. Jalankan seluruh data

```powershell
uv run python scripts/prelabel_indobert.py
```

Konfigurasi bawaan:

- Input: `data/processed/dataset_coretax_youtube_preprocessed.csv`
- Teks untuk IndoBERT: `komentar_clean`
- Output: `data/processed/dataset_coretax_youtube_prelabel_indobert.csv`
- Perangkat: CUDA jika tersedia, lalu CPU sebagai cadangan
- Batch: 16, sesuai titik awal aman untuk RTX 3050 Laptop 4 GB
- Batas *review*: confidence di bawah 0,80 atau margin di bawah 0,30
- Checkpoint: setiap 1.000 baris

Jika VRAM tidak cukup, turunkan ukuran batch:

```powershell
uv run python scripts/prelabel_indobert.py --batch-size 8
```

Jika proses terhenti, lanjutkan dari hasil terakhir:

```powershell
uv run python scripts/prelabel_indobert.py --resume
```

## 4. Arti kolom hasil

| Kolom | Kegunaan |
|---|---|
| `pseudo_label_indobert` | Prediksi awal: positif, netral, atau negatif |
| `confidence_indobert` | Probabilitas kelas terpilih |
| `margin_indobert` | Selisih probabilitas kelas pertama dan kedua |
| `entropy_indobert` | Tingkat ketidakpastian, 0 paling yakin dan 1 paling tidak yakin |
| `probabilitas_*` | Probabilitas masing-masing kelas |
| `perlu_review` | Prioritas verifikasi manusia |
| `alasan_review` | Penyebab data masuk antrean review |
| `label_annotator_1/2` | Label dari anotator manusia |
| `label_final` | Label final hasil verifikasi/adjudikasi |
| `status_anotasi` | Status pekerjaan anotasi |

## 5. Prosedur anotasi yang disarankan

1. Verifikasi semua baris dengan `perlu_review = True`.
2. Ambil sampel acak minimal 10% dari baris `perlu_review = False`.
3. Gunakan dua anotator pada subset yang sama untuk menghitung Cohen's Kappa.
4. Selesaikan perbedaan label melalui adjudikasi dan isi `label_final`.
5. Gunakan hanya `label_final` sebagai target `y` untuk eksperimen SVM.
6. Pisahkan data latih dan data uji sebelum TF-IDF, mRMR, dan SMOTE.

Jangan mengisi `label_final` secara otomatis dari `pseudo_label_indobert`. Langkah tersebut akan mengubah penelitian menjadi evaluasi SVM terhadap label buatan model lain, bukan terhadap label sentimen yang tervalidasi.
