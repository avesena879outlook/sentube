# Analisis dan Penggabungan Dataset YouTube v1-v2

## Sumber

- `v1/dataset_coretax_youtube_raw.csv`
- `v2/dataset_coretax_youtube_raw (1).csv`

Workbook labeling tidak digabungkan secara terpisah karena isinya merupakan turunan dari CSV mentah masing-masing versi dan seluruh kolom `label` masih kosong.

## Ringkasan Sumber

| Metrik | v1 | v2 |
|---|---:|---:|
| Baris | 6.974 | 11.749 |
| Video unik | 65 | 148 |
| Channel unik | 42 | 73 |
| Tanggal komentar awal | 31 Desember 2024 | 31 Desember 2024 |
| Tanggal komentar akhir | 16 Mei 2026 | 17 Mei 2026 |
| Duplikasi identitas internal | 0 | 0 |

Kedua versi memiliki 15 kolom yang sama dan tipe data yang konsisten.

## Tumpang Tindih

- 6.493 komentar terdapat pada v1 dan v2.
- 481 komentar hanya terdapat pada v1.
- 5.256 komentar hanya terdapat pada v2.
- v1 bukan subset penuh dari v2, sehingga v1 tidak boleh langsung dibuang.
- Pada komentar yang sama, v2 memiliki banyak perubahan pada `view_count`, `like_count`, dan `keyword_cari`. Nilai v2 diprioritaskan karena merupakan crawling yang lebih baru.

Identitas komentar ditentukan dari gabungan:

```text
video_id + penulis ternormalisasi + komentar ternormalisasi + tanggal_komentar
```

Normalisasi untuk pencocokan hanya mencakup Unicode NFKC, huruf kecil, perapian spasi, dan penghapusan spasi di awal/akhir. Teks asli dalam output tidak diubah.

## Hasil Gabungan

Output: `dataset_coretax_youtube_raw_merged.csv`

| Metrik | Nilai |
|---|---:|
| Total komentar | 12.230 |
| Video unik | 156 |
| Channel unik | 78 |
| Penulis unik | 11.433 |
| Duplikasi identitas | 0 |
| Tanggal tidak valid | 0 |
| Nilai kosong selain label | 0 |
| Baris dari kedua versi | 6.493 |
| Baris hanya dari v1 | 481 |
| Baris hanya dari v2 | 5.256 |

Kolom `source_version` ditambahkan dengan nilai:

- `both`: komentar muncul pada v1 dan v2;
- `v1`: komentar hanya ditemukan pada v1;
- `v2`: komentar hanya ditemukan pada v2.

## Catatan Kualitas Data

- Seluruh 12.230 nilai pada kolom `label` masih kosong.
- Terdapat tiga pengulangan teks ternormalisasi yang berasal dari identitas atau video berbeda. Data ini dipertahankan karena belum tentu merupakan duplikasi crawling.
- Dua pengulangan tampak seperti komentar lintas video oleh penulis yang sama dan layak diperiksa sebagai kemungkinan spam atau salinan.
- Satu pengulangan adalah kalimat umum dari penulis berbeda sehingga tidak aman untuk dihapus otomatis.
- Jumlah kata per komentar: minimum 5, median 12, persentil ke-95 38, dan maksimum 320.
- Distribusi komentar cukup terkonsentrasi pada beberapa channel dan video. Saat membagi train-test, gunakan `video_id` sebagai grup untuk mengurangi kebocoran konteks antarvideo.

## Rekomendasi Tahap Berikutnya

1. Lakukan pemeriksaan relevansi komentar terhadap Coretax.
2. Tandai spam, promosi, dan komentar salinan sebelum pelabelan sentimen.
3. Jangan menganggap komentar pertanyaan otomatis sebagai netral.
4. Simpan data mentah gabungan ini tanpa perubahan dan buat hasil pembersihan di `data/processed`.
5. Lakukan pembagian train-test berdasarkan `video_id` atau minimal audit kemiripan komentar lintas split.
