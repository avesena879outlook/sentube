# Panduan Revisi Metodologi Skripsi

## 1. Tujuan Dokumen

Dokumen ini menjadi panduan revisi penelitian analisis sentimen publik terhadap Coretax di YouTube menggunakan Support Vector Machine (SVM). Penelitian membandingkan dua skenario:

1. SVM menggunakan seleksi fitur Minimum Redundancy Maximum Relevance (mRMR).
2. SVM tanpa seleksi fitur mRMR.

Tujuan perbandingan adalah mengukur pengaruh mRMR terhadap performa klasifikasi sekaligus efisiensi model, bukan membandingkan algoritma klasifikasi yang berbeda.

## 2. Revisi Paling Penting

### Wajib diperbaiki

- Lakukan pembagian data latih dan data uji sebelum TF-IDF, mRMR, SMOTE, dan pelatihan SVM.
- Jangan menggunakan data uji untuk menentukan kosakata TF-IDF, fitur mRMR, parameter SVM, atau jumlah fitur terbaik.
- Ganti pelabelan InSet Lexicon dengan pelabelan manual berbantuan model IndoBERT.
- Gunakan data uji berlabel manual sebagai ground truth.
- Jalankan TF-IDF, mRMR, penanganan ketidakseimbangan kelas, dan SVM di dalam pipeline cross-validation.
- Pastikan kedua skenario memakai data, preprocessing, pembagian data, dan ruang pencarian parameter yang sama.
- Gunakan Macro-F1 sebagai metrik utama karena penelitian menggunakan tiga kelas yang berpotensi tidak seimbang.

### Sangat disarankan

- Bandingkan Linear SVM dan RBF SVM, atau berikan alasan akademis yang kuat jika hanya menggunakan RBF.
- Uji `class_weight="balanced"` sebagai alternatif SMOTE untuk data teks TF-IDF.
- Laporkan waktu pelatihan, waktu prediksi, jumlah fitur, dan ukuran model sebagai bagian dari pengukuran optimasi.
- Lakukan analisis kesalahan terhadap komentar dengan negasi, sarkasme, singkatan, bahasa campuran, pertanyaan, dan komentar di luar topik.

## 3. Alur Penelitian Revisi

```text
Mulai
  |
  v
Business Understanding
  - Merumuskan kebutuhan analisis sentimen Coretax
  - Menentukan tujuan perbandingan SVM dengan dan tanpa mRMR
  |
  v
Data Understanding
  - Crawling komentar menggunakan YouTube Data API v3
  - Eksplorasi distribusi, duplikasi, missing value, dan kualitas data
  |
  v
Data Preparation Awal
  - Menyaring komentar berbahasa Indonesia
  - Menghapus duplikasi dan komentar tidak relevan
  - Menetapkan label positif, netral, dan negatif
  - Melakukan validasi kualitas label
  |
  v
Stratified Train-Test Split 80:20
  - Data uji dikunci dan tidak digunakan selama pengembangan model
  |
  v
Optimasi pada Data Latih dengan Stratified K-Fold Cross-Validation
  |
  +------------------------------+------------------------------+
  |                                                             |
  v                                                             v
Skenario A                                                   Skenario B
SVM + mRMR                                                  SVM tanpa mRMR
  - Preprocessing                                             - Preprocessing
  - TF-IDF                                                    - TF-IDF
  - mRMR K=100/200/300/500                                    - Tanpa mRMR
  - Penanganan imbalance                                      - Penanganan imbalance
  - Grid Search SVM                                           - Grid Search SVM
  |                                                             |
  +------------------------------+------------------------------+
                                 |
                                 v
Pemilihan Konfigurasi Berdasarkan Macro-F1 Cross-Validation
                                 |
                                 v
Evaluasi Final Satu Kali pada Data Uji
  - Accuracy
  - Precision, Recall, dan F1 per kelas
  - Macro-F1 dan Weighted-F1
  - Confusion Matrix
  - Multiclass ROC-AUC jika diperlukan
  - Waktu pelatihan dan prediksi
  - Jumlah fitur dan ukuran model
                                 |
                                 v
Perbandingan Kedua Skenario dan Analisis Kesalahan
                                 |
                                 v
Deployment Model Terpilih
                                 |
                                 v
Selesai
```

## 4. Rancangan Pelabelan yang Direkomendasikan

### Keputusan utama

IndoBERT tidak langsung dianggap sebagai ground truth. IndoBERT digunakan untuk memberikan label awal, sedangkan keputusan label akhir tetap diperiksa oleh manusia.

Jika SVM dilatih dan diuji hanya menggunakan label otomatis IndoBERT, hasil penelitian akan menunjukkan kemampuan SVM meniru IndoBERT. Hasil tersebut belum cukup membuktikan bahwa prediksi sesuai dengan sentimen yang sebenarnya.

### Definisi kelas

| Kelas | Definisi operasional | Contoh |
|---|---|---|
| Positif | Komentar berisi dukungan, kepuasan, apresiasi, atau pengalaman baik terhadap Coretax | "Sekarang pelaporan pajak jadi lebih praktis." |
| Negatif | Komentar berisi kritik, keluhan, kekecewaan, atau pengalaman buruk terhadap Coretax | "Dari pagi tidak bisa login dan OTP tidak masuk." |
| Netral | Komentar bersifat informatif, bertanya, tidak menunjukkan polaritas yang jelas, atau menyampaikan fakta | "Coretax mulai digunakan tanggal berapa?" |

### Prosedur pelabelan

1. Simpan teks mentah untuk pelabelan. Jangan melakukan stemming sebelum anotator membaca komentar.
2. Gunakan model IndoBERT yang sudah di-fine-tune untuk klasifikasi sentimen tiga kelas sebagai pemberi label awal.
3. Simpan label prediksi dan confidence score dari model.
4. Periksa manual seluruh komentar dengan confidence rendah.
5. Audit sampel komentar dengan confidence tinggi dari setiap kelas.
6. Gunakan minimal dua anotator pada data validasi atau data uji.
7. Hitung Cohen's Kappa untuk mengukur kesepakatan antar-anotator.
8. Selesaikan perbedaan melalui diskusi atau anotator ketiga.
9. Jadikan label hasil verifikasi manusia sebagai label final.
10. Dokumentasikan nama checkpoint IndoBERT, versi model, ambang confidence, jumlah data yang diperiksa, dan jumlah label yang dikoreksi.

### Aturan kasus khusus

- Pertahankan kata negasi seperti "tidak", "bukan", "belum", "kurang", dan "gagal".
- Pertanyaan tidak otomatis netral. Kalimat "Kenapa sistemnya selalu gagal?" dapat mengandung sentimen negatif.
- Komentar di luar topik sebaiknya diberi penanda `irrelevant` dan dikeluarkan sebelum klasifikasi tiga kelas.
- Sarkasme dan ironi diberi label berdasarkan makna keseluruhan, bukan arti literal tiap kata.
- Komentar campuran dinilai berdasarkan sentimen dominan terhadap Coretax.
- Jika sentimen tidak dapat ditentukan, tandai sebagai `uncertain` untuk proses adjudikasi, bukan langsung dipaksa menjadi netral.

## 5. Pembagian Data dan Pencegahan Data Leakage

Urutan yang benar adalah:

1. Selesaikan label final.
2. Pisahkan data menjadi 80% data latih dan 20% data uji menggunakan stratifikasi kelas.
3. Kunci data uji sampai semua konfigurasi model selesai dipilih.
4. Jalankan Grid Search dan Stratified K-Fold hanya pada data latih.
5. Pada setiap fold, fit preprocessing yang mempelajari statistik data hanya pada bagian training fold.
6. Evaluasi konfigurasi terpilih satu kali pada data uji.

Komponen berikut tidak boleh di-fit menggunakan keseluruhan dataset sebelum split:

- kosakata dan nilai IDF dari TF-IDF;
- skor serta subset fitur mRMR;
- proses SMOTE atau resampling lain;
- parameter `C`, `gamma`, dan kernel SVM;
- nilai K terbaik pada mRMR.

Jika banyak komentar berasal dari video yang sama, pertimbangkan `GroupShuffleSplit` atau `StratifiedGroupKFold` berdasarkan `video_id`. Hal ini mengurangi kemungkinan komentar yang sangat mirip dari satu video tersebar pada data latih dan data uji.

## 6. Desain Dua Skenario yang Adil

| Komponen | Skenario A: SVM + mRMR | Skenario B: SVM tanpa mRMR |
|---|---|---|
| Dataset | Sama | Sama |
| Train-test split | Sama | Sama |
| Preprocessing | Sama | Sama |
| Konfigurasi TF-IDF | Sama | Sama |
| Batas fitur awal | Maksimal 10.000 | Maksimal 10.000 |
| Seleksi fitur | mRMR K=100/200/300/500 | Tidak ada |
| Penanganan imbalance | Sama | Sama |
| Algoritma klasifikasi | SVM | SVM |
| Ruang Grid Search | Sama | Sama |
| Fold cross-validation | Sama | Sama |
| Data uji final | Sama | Sama |

Perbedaan performa baru dapat dikaitkan dengan mRMR apabila komponen lain dibuat tetap.

## 7. TF-IDF dan Preprocessing

Parameter TF-IDF yang perlu ditulis secara eksplisit dalam skripsi:

- `max_features=10000`;
- `ngram_range`, misalnya unigram atau unigram-bigram;
- `min_df` untuk membuang istilah yang terlalu jarang;
- `max_df` untuk membuang istilah yang terlalu umum;
- `sublinear_tf` jika digunakan;
- jenis normalisasi;
- penggunaan token kata atau karakter.

Tahapan preprocessing yang direkomendasikan:

1. Case folding.
2. Penghapusan URL dan karakter yang tidak relevan.
3. Normalisasi kata tidak baku jika kamus normalisasi tersedia.
4. Penanganan kata negasi.
5. Tokenisasi.
6. Stopword removal secara hati-hati.
7. Stemming hanya jika hasil eksperimen menunjukkan manfaat.

Stemming dan stopword removal tidak selalu meningkatkan model. Karena itu, konfigurasi preprocessing harus dilaporkan dan diterapkan sama pada kedua skenario.

## 8. Penerapan mRMR

Skripsi perlu menjelaskan hal berikut:

- varian mRMR yang digunakan, misalnya MID atau MIQ;
- cara menghitung mutual information pada nilai TF-IDF yang bersifat kontinu;
- nama dan versi pustaka;
- nilai K yang diuji;
- random seed jika implementasi melibatkan proses acak;
- waktu komputasi seleksi fitur;
- daftar contoh fitur yang terpilih.

Nilai K `100`, `200`, `300`, dan `500` harus diperlakukan sebagai hyperparameter. Nilai terbaik dipilih dari hasil cross-validation pada data latih, bukan dari hasil data uji.

## 9. Penanganan Ketidakseimbangan Kelas

Jangan menerapkan SMOTE secara otomatis hanya karena jumlah kelas berbeda. Laporkan terlebih dahulu:

- jumlah data tiap kelas;
- persentase tiap kelas;
- rasio kelas mayoritas terhadap minoritas;
- performa awal model tanpa balancing.

Konfigurasi yang dapat dibandingkan pada data latih:

1. Tanpa balancing.
2. SVM dengan `class_weight="balanced"`.
3. SMOTE pada training fold saja.

Untuk data TF-IDF, `class_weight="balanced"` dapat menjadi pilihan utama karena SMOTE membuat vektor sintetis yang belum tentu merepresentasikan komentar nyata. Jika SMOTE digunakan, tempatkan SMOTE di dalam `imblearn.pipeline.Pipeline` agar tidak memengaruhi validation fold dan test set.

## 10. Pemodelan SVM

### Pilihan yang disarankan

- Gunakan Linear SVM sebagai konfigurasi utama atau baseline karena TF-IDF menghasilkan matriks sparse berdimensi tinggi.
- Jika menggunakan RBF SVM, jelaskan alasan pemilihannya dan lakukan pencarian parameter `C` serta `gamma`.
- Jangan menetapkan kernel berdasarkan skor data uji.

Contoh ruang pencarian parameter:

```text
Linear SVM:
  C = 0.01, 0.1, 1, 10, 100

RBF SVM:
  C = 0.1, 1, 10, 100
  gamma = scale, 0.001, 0.01, 0.1
```

Jika tujuan utama penelitian hanya mengukur pengaruh mRMR, gunakan kernel dan ruang parameter yang sama untuk kedua skenario.

## 11. Evaluasi

### Metrik utama

- Macro-F1 sebagai dasar utama pemilihan model.
- Precision, recall, dan F1-score untuk setiap kelas.
- Weighted-F1 sebagai informasi tambahan.
- Accuracy sebagai informasi umum, bukan satu-satunya dasar kesimpulan.
- Confusion matrix untuk melihat pola kesalahan antar-kelas.

Jika ROC-AUC digunakan pada tiga kelas, tuliskan pendekatan multiclass yang dipakai, misalnya One-vs-Rest dengan macro average. Jangan memakai rumus TP, TN, FP, dan FN biner tanpa penjelasan perluasan multiclass.

### Metrik efisiensi

- jumlah fitur sebelum dan sesudah mRMR;
- waktu seleksi fitur;
- waktu training;
- waktu prediksi;
- ukuran file model;
- penggunaan memori jika dapat diukur secara konsisten.

### Pelaporan cross-validation

Laporkan rata-rata dan standar deviasi, misalnya:

```text
Macro-F1 = 0,82 +/- 0,03
```

Hasil akhir data uji dilaporkan terpisah dari skor cross-validation.

## 12. Analisis Kesalahan

Periksa contoh kesalahan dari kategori berikut:

- positif diprediksi netral;
- negatif diprediksi netral;
- pertanyaan bernada keluhan;
- kalimat dengan negasi;
- sarkasme atau ironi;
- komentar dengan singkatan dan salah ketik;
- komentar campuran Bahasa Indonesia dan bahasa lain;
- komentar yang sebenarnya tidak membahas Coretax.

Analisis ini penting untuk menjelaskan mengapa model tertentu memperoleh skor lebih tinggi atau lebih rendah dan bagaimana mRMR memengaruhi fitur yang digunakan.

## 13. Koreksi Konsistensi Naskah

- Ubah seluruh penulisan `Coretex` menjadi `Coretax`.
- Ubah `CRIPS-DM` menjadi `CRISP-DM`.
- Ganti tanggal `31 April 2026` karena tanggal tersebut tidak ada.
- Samakan seluruh rentang pengumpulan data. Naskah saat ini menyebut beberapa batas akhir yang berbeda.
- Ganti istilah `SVM murni` menjadi `SVM tanpa seleksi fitur mRMR`.
- Pisahkan kotak pelabelan dari kotak ekstraksi fitur pada diagram.
- Bedakan preprocessing untuk pelabelan IndoBERT dan preprocessing untuk TF-IDF-SVM.
- Konsistenkan teknologi deployment antara naskah dan implementasi aktual.
- Perbaiki istilah `Support Vektor Machine` menjadi `Support Vector Machine`.
- Gunakan istilah `redundansi`, bukan `redudansi`.
- Tuliskan `precision`, `recall`, dan `F1-score` dengan pemisah yang jelas pada diagram.

## 14. Revisi Diagram Penelitian

Kotak `Labeling & Fitur` sebaiknya dipecah menjadi:

1. Pelabelan manual berbantuan IndoBERT.
2. Validasi label dan pengukuran kesepakatan anotator.
3. Stratified train-test split.
4. Pipeline pemodelan dua skenario.

Kotak keputusan `Dengan mRMR?` tidak perlu menggabungkan kembali data sebelum balancing secara global. Setiap cabang harus memiliki pipeline sendiri dan berjalan di dalam cross-validation.

Bagian evaluasi perlu menampilkan dua jenis hasil:

1. Kualitas klasifikasi: Macro-F1, precision, recall, confusion matrix, dan metrik lain.
2. Efisiensi: jumlah fitur, waktu training, waktu inferensi, dan ukuran model.

## 15. Penyesuaian Implementasi Sistem

Kondisi project saat ini yang harus diperbaiki sebelum disebut sebagai implementasi penelitian:

- Endpoint hasil masih menggunakan data simulasi dan belum memanggil pipeline inferensi aktual.
- Artifact model mRMR dummy hanya membatasi `max_features`; hal tersebut belum merupakan algoritma mRMR.
- Halaman hasil belum memperlihatkan perbandingan kedua model secara lengkap.
- Preprocessing aplikasi belum sepenuhnya sama dengan preprocessing yang dijelaskan dalam skripsi.
- Upload CSV belum terhubung sampai tahap prediksi.
- Teknologi frontend pada naskah perlu disamakan dengan aplikasi aktual.

Hasil website minimal perlu menampilkan:

- distribusi prediksi setiap model;
- jumlah dan persentase prediksi yang berbeda;
- label setiap komentar dari kedua model;
- konfigurasi model yang digunakan;
- jumlah fitur model mRMR dan model tanpa mRMR;
- waktu prediksi masing-masing model.

## 16. Urutan Pengerjaan Revisi

### Prioritas 1 - Validitas penelitian

- [ ] Tentukan metode pelabelan final.
- [ ] Susun pedoman anotasi tiga kelas.
- [ ] Tentukan model IndoBERT untuk pre-labeling.
- [ ] Siapkan label manual untuk data uji.
- [ ] Pindahkan train-test split sebelum TF-IDF dan mRMR.
- [ ] Tempatkan seluruh proses training di dalam pipeline cross-validation.

### Prioritas 2 - Eksperimen

- [ ] Tetapkan parameter TF-IDF.
- [ ] Implementasikan mRMR yang sebenarnya.
- [ ] Tetapkan K=100/200/300/500 sebagai hyperparameter.
- [ ] Bandingkan strategi penanganan imbalance.
- [ ] Jalankan Grid Search pada data latih.
- [ ] Evaluasi satu kali pada data uji.
- [ ] Simpan seluruh konfigurasi, random seed, dan hasil eksperimen.

### Prioritas 3 - Penulisan skripsi

- [ ] Revisi batasan masalah mengenai pelabelan.
- [ ] Revisi bagian H.4 tahapan penelitian.
- [ ] Revisi diagram penelitian.
- [ ] Jelaskan pipeline pencegahan data leakage.
- [ ] Jelaskan metrik multiclass dan metrik efisiensi.
- [ ] Perbaiki istilah, tanggal, dan teknologi yang belum konsisten.

### Prioritas 4 - Implementasi website

- [ ] Hubungkan endpoint dengan model aktual.
- [ ] Implementasikan alur input YouTube dan CSV.
- [ ] Tampilkan hasil dua model secara berdampingan.
- [ ] Tampilkan ringkasan perbedaan prediksi.
- [ ] Pastikan preprocessing inferensi identik dengan proses training.
- [ ] Uji aplikasi menggunakan data yang belum pernah dilatih.

## 17. Rumusan Kesimpulan Eksperimen

Kesimpulan tidak cukup menyatakan model dengan akurasi tertinggi. Kesimpulan perlu menjawab:

1. Apakah mRMR meningkatkan Macro-F1 pada data uji?
2. Nilai K berapa yang memberikan keseimbangan performa dan efisiensi terbaik?
3. Berapa banyak fitur yang dapat dikurangi?
4. Apakah pengurangan fitur mempercepat training dan inferensi?
5. Kelas sentimen apa yang paling sering salah diklasifikasikan?
6. Apakah peningkatan yang diperoleh konsisten pada cross-validation dan data uji?

Jika mRMR tidak meningkatkan skor tetapi mengurangi fitur dan waktu komputasi secara signifikan, mRMR tetap dapat dinilai bermanfaat dari sisi efisiensi. Kesimpulan harus mengikuti hasil pengujian, bukan mengharuskan skenario mRMR selalu menang.
