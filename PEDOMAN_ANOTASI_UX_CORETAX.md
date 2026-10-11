# Pedoman Anotasi Sentimen Pengalaman Pengguna Aplikasi Coretax

## 1. Tujuan dan batas tugas

Unit anotasi adalah **satu komentar YouTube**. Anotator menilai sentimen penulis terhadap **pengalaman menggunakan aplikasi Coretax**, seperti login, navigasi, fitur, alur kerja, kecepatan, pesan kesalahan, atau bantuan penggunaan. Tugas ini tidak menilai benar-salah aturan perpajakan. Latar belakang IT/S.Kom memadai jika anotator memahami bahasa komentar dan mengikuti pedoman ini; keahlian pajak tidak disyaratkan untuk penilaian UX.

Gunakan teks asli pada kolom `komentar` sebagai rujukan utama. `komentar_clean` dan `komentar_preprocessed` hanya membantu pencarian; keduanya dapat menghilangkan konteks, tanda baca, atau nuansa. Jangan menebak maksud komentar dari `pseudo_label_indobert` atau nilai `confidence_indobert`.

## 2. Putuskan relevansi sebelum sentimen

Komentar **relevan** jika menyebut pengalaman, kesulitan, kemudahan, harapan, atau informasi praktis tentang penggunaan aplikasi/situs Coretax. Tidak perlu menyebut kata “UX”. Pengalaman orang lain yang diceritakan penulis tetap relevan.

Komentar **di luar topik UX** jika hanya membahas aturan, tarif, kewajiban pajak, kebijakan, orang, atau isi video tanpa hubungan yang jelas dengan penggunaan aplikasi. Jangan memberi label `netral` hanya karena komentar di luar topik tidak mengandung emosi. Tulis `di_luar_topik` pada kolom anotator; biarkan `label_final` kosong, lalu tetapkan `status_anotasi = di_luar_topik` setelah pemeriksaan akhir.

Jika komentar menyebut pajak dan aplikasi sekaligus, nilai hanya sikap terhadap penggunaan aplikasinya. Misalnya, “Aturan pajaknya rumit, tapi pengisian di Coretax mudah” adalah `positif` untuk UX. Bila kaitannya dengan aplikasi tidak dapat dipastikan dari teks, gunakan `tidak_pasti` dan catat alasannya.

## 3. Definisi label

| Kode | Gunakan ketika komentar relevan dan... | Contoh buatan |
| --- | --- | --- |
| `positif` | Menyatakan puas, terbantu, mudah, cepat, atau memuji pengalaman memakai Coretax. | “Sekarang lapor lewat Coretax lebih gampang, menunya jelas.” |
| `negatif` | Menyatakan keluhan, kesulitan, kegagalan, lambat, membingungkan, atau ketidakpuasan terhadap pemakaian Coretax. | “OTP tidak masuk terus, saya tidak bisa login.” |
| `netral` | Bertanya atau menyampaikan fakta/instruksi penggunaan tanpa penilaian positif atau negatif yang jelas. | “Di mana menu untuk melihat bukti lapor?” |

`netral` bukan tempat untuk komentar yang tidak jelas, di luar topik, atau memiliki dua sentimen yang sama kuat.

## 4. Aturan untuk kasus yang sering membingungkan

| Kasus | Keputusan |
| --- | --- |
| “Bagaimana cara masuk ke Coretax?” | `netral`: pertanyaan penggunaan tanpa keluhan. |
| “Kenapa Coretax selalu gagal saat login?” | `negatif`: pertanyaan yang memuat pengalaman gagal. |
| “Mantap, loading-nya lama sekali.” | `negatif` jika konteks jelas menyindir; catat “sarkasme”. |
| “Fiturnya bagus, tetapi tiap klik sering error.” | Nilai sentimen UX yang dominan. Jika kekuatan keduanya seimbang, `tidak_pasti` untuk dibahas. |
| “NSFP untuk tahun pajak berikutnya bisa diminta kapan?” | `di_luar_topik` jika tidak membicarakan penggunaan fitur Coretax. |
| “Di Coretax tombol permintaan NSFP ada di mana?” | `netral`: bertanya tentang letak fitur aplikasi. |
| “Terima kasih, akhirnya bisa login!” | `positif` bila jelas mengapresiasi keberhasilan penggunaan. |
| “Ini mah aplikasi paling stabil, tiap menit logout.” | `negatif`: sindiran terhadap stabilitas aplikasi. |
| “Iya”, “sama”, emoji saja, atau balasan tanpa konteks | `tidak_pasti` jika sikap terhadap UX tidak bisa diketahui dari teks. |

Pertahankan makna negasi (`tidak`, `belum`, `bukan`, `gagal`) dan bahasa tidak baku. Jangan menyimpulkan sentimen dari jumlah like, nama penulis, atau judul video. Jika komentar hanya melaporkan masalah teknis (“Muncul error 500 saat simpan”), beri `negatif` karena pengalaman penggunaan terhambat, meski tanpa kata marah.

## 5. Cara mengisi CSV ringkas

Sampel kerja acak sudah tersedia pada `data/processed/anotasi_ux_coretax_anotator_1_3000.csv` dan `data/processed/anotasi_ux_coretax_anotator_2_3000.csv`. Keduanya memuat 3.000 komentar yang sama. Baris bertanda `tahap = uji_coba` adalah 100 komentar untuk menyamakan penerapan pedoman; sisanya bertanda `utama`. Pilihan baris, seed, dan ringkasan sampel tercatat pada `data/processed/anotasi_ux_coretax_sampel_3000.json`. Masing-masing anotator mengerjakan file sendiri dan tidak melihat hasil rekannya. Pertahankan `nomor_baris_sumber` sebagai kunci penggabungan; jangan mengubah nilainya. Anotator 1 hanya mengisi `label_annotator_1`, anotator 2 hanya mengisi `label_annotator_2`.

Untuk mempercepat pengisian, isi **satu angka** pada kolom label anotator: `1` = `positif`, `2` = `negatif`, `3` = `netral`, `4` = `di_luar_topik`, `5` = `tidak_pasti`. Kolom kosong berarti belum dikerjakan. Kode ini bersifat kategori, bukan skala nilai; jangan menghitung rata-rata angkanya. Jika memakai Excel atau Google Sheets, pasang validasi input yang hanya menerima angka 1–5 untuk mencegah salah ketik. Untuk `4`, `5`, sarkasme, atau keputusan sulit, beri alasan singkat di `catatan_anotator` pada salinan masing-masing. File kerja ini sengaja tidak memuat prediksi IndoBERT atau label rekan anotator agar penilaian pertama mandiri.

Setelah kedua file **selesai seluruhnya**, jalankan `python3 scripts/merge_numeric_annotations.py` dari akar proyek. Skrip memeriksa ID dan komentar kedua file, menerjemahkan kode menjadi kata, dan membuat `data/processed/anotasi_ux_coretax_gabungan_3000.csv` sebagai file baru. Skrip tidak menimpa file anotator dan membiarkan `label_final` kosong untuk keputusan setelah perbandingan. Jika ada kode kosong atau tidak dikenal, proses dihentikan dan nomor baris sumber yang perlu diperbaiki ditampilkan.

Setelah kedua hasil digabung berdasarkan `nomor_baris_sumber`, penanggung jawab memeriksa perbedaan. `label_final` hanya berisi `positif`, `netral`, atau `negatif` setelah diputuskan. `status_anotasi` memakai:

- `belum_diperiksa`: belum selesai dinilai;
- `perlu_adjudikasi`: dua anotator berbeda atau ada kode `tidak_pasti`;
- `di_luar_topik`: diputuskan tidak terkait UX; `label_final` tetap kosong;
- `selesai`: label sentimen final sudah diputuskan.

Jika kedua anotator sama-sama memberi satu dari tiga label, label itu dapat menjadi `label_final` setelah pemeriksaan konsistensi. Jika berbeda, diskusikan berdasarkan teks dan pedoman; gunakan anotator ketiga bila kesepakatan tidak tercapai. Jangan mengisi `label_final` otomatis dari `pseudo_label_indobert`.

## 6. Pemeriksaan mutu dan penggunaan untuk training

Sebelum anotasi penuh, kedua anotator mengerjakan sampel kecil yang sama, membahas perbedaan, lalu memperjelas contoh pada pedoman. Untuk data evaluasi, gunakan label manusia yang telah diperiksa. Hitung dan laporkan jumlah data yang dianotasi ganda, persentase kesepakatan, dan Cohen's kappa pada sampel yang sama; kappa mengukur konsistensi, bukan jaminan bahwa setiap label benar. Catat jumlah komentar di luar topik dan kasus yang diselesaikan lewat adjudikasi.

Tidak wajib menganotasi seluruh 12.230 komentar. Jika memakai subset, pilih baris secara acak dari keseluruhan data, simpan aturan pemilihan dan *random seed*, lalu beri label manusia pada **setiap baris yang akan dipakai** untuk training maupun pengujian. `perlu_review = True` adalah prioritas urutan kerja di dalam subset, bukan alasan menganggap baris lain sudah berlabel benar. Jika memakai semua baris, 1.505 baris yang ditandai `perlu_review` dapat dikerjakan lebih dahulu. Tambahan data yang sengaja dipilih karena model ragu boleh masuk training setelah dianotasi, tetapi jangan ditambahkan ke data uji acak yang sudah dikunci.

Baris dengan `status_anotasi = di_luar_topik`, `perlu_adjudikasi`, atau `label_final` kosong **tidak masuk** dataset training tiga kelas. Jangan menggunakan `pseudo_label_indobert` sebagai target pengganti. Setelah label final selesai, pisahkan data latih dan data uji, lalu kunci data uji sebelum pemilihan fitur, tuning, atau pelatihan. Bila ingin membagi train/test berdasarkan video, ambil kembali `video_id` dari file sumber memakai `nomor_baris_sumber`; kolom itu tidak menjadi fitur sentimen.
