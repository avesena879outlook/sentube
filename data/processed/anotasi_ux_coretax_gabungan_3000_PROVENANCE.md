# Asal dan status anotasi UX Coretax (3.000 komentar)

Tanggal pengerjaan: 2026-09-30. Sampel dipilih acak tanpa pengulangan dari 12.230 komentar, memakai seed 42. Rincian pemilihan ada di `anotasi_ux_coretax_sampel_3000.json`.

Kedua lembar dikerjakan **oleh dua agen AI secara terpisah**, bukan dua anotator manusia. Agen pertama memakai Codex CLI dengan model `gpt-6-sol` dalam batch 50 komentar, lalu mengaudit sampel dan mengoreksi 20 keputusan. Agen kedua membaca langsung 200 komentar pertama, memakai Codex CLI secara mandiri untuk 2.800 sisanya, lalu mengaudit dan mengoreksi 18 keputusan. Keduanya hanya membaca komentar asli saat membuat label dan tidak memakai `pseudo_label_indobert` sebagai jawaban. Pengerjaan batch oleh AI tidak setara dengan verifikasi manusia per komentar.

| Ringkasan | Jumlah |
| --- | ---: |
| Baris pada masing-masing lembar | 3.000 |
| Kesepakatan kode persis | 2.506 (83,53%) |
| Kode berbeda | 494 |
| Sama-sama `tidak_pasti` | 81 |
| Sama-sama `di_luar_topik` | 894 |
| Sama-sama memilih satu kelas sentimen yang sama | 1.531 |
| Ditandai `perlu_adjudikasi` pada file gabungan | 575 |

Cohen's kappa lima kategori untuk **dua keluaran AI** adalah 0,756. Nilai ini hanya menggambarkan kesamaan keluaran kedua agen AI; jangan dilaporkan sebagai reliabilitas dua anotator manusia. Kolom `label_final` sengaja dibiarkan kosong. Baris `perlu_adjudikasi` memerlukan keputusan lanjutan, dan semua baris yang akan dipakai sebagai *ground truth* penelitian memerlukan pemeriksaan manusia sesuai pedoman anotasi.

File gabungan dibuat dengan `python3 scripts/merge_numeric_annotations.py`. Kolom `label_annotator_1` dan `label_annotator_2` pada file gabungan berisi kata, sedangkan lembar kerja masing-masing anotator tetap memakai kode angka 1–5.
