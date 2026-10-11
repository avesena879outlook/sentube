"""Apply independently reviewed UX codes to annotator 2's CSV.

Only entries in REVIEWED receive a code. The CSV is kept in its original order.
"""

import csv
from pathlib import Path


PATH = Path("data/processed/anotasi_ux_coretax_anotator_2_3000.csv")

# Positional codes for the first 100 comments, reviewed against the original text.
FIRST_100 = """
1 3 2 2 2 4 4 4 4 5
2 4 3 2 3 2 2 2 2 5
4 4 5 2 4 2 2 5 4 2
3 4 4 2 4 4 4 1 4 2
4 4 4 3 2 4 3 4 2 3
5 3 4 4 4 3 2 1 4 2
2 3 2 4 2 2 4 4 4 4
4 4 4 4 2 3 3 2 4 2
5 2 2 3 2 4 2 3 4 4
4 4 4 3 2 4 4 2 1 4
"""

# Positions 101–200, read directly from the original comments.
NEXT_100 = """
2 2 4 4 5 5 4 4 2 2
3 3 2 3 2 2 3 5 4 2
1 2 2 2 4 4 4 3 2 2
4 4 4 4 3 4 4 4 1 4
4 4 4 2 4 3 2 4 4 2
2 2 2 2 3 2 2 2 2 2
4 5 2 2 3 3 4 2 4 2
2 2 3 4 2 2 2 4 3 2
4 5 4 5 1 2 5 3 4 3
4 2 4 2 4 2 2 2 2 4
"""

NOTES = {
    5: "Keluhan langsung tentang membuka dan mengisi aplikasi Coretax.",
    6: "Membahas komposisi tim pemerintah, bukan pengalaman memakai aplikasi.",
    7: "Membahas tim IT, bukan pengalaman memakai aplikasi.",
    8: "Keinginan tidak membayar pajak, tanpa kaitan dengan UX.",
    9: "Ucapan terima kasih kepada orang, tanpa pengalaman aplikasi.",
    10: "Keluhan 'ribet' tanpa objek jelas; konteks UX tidak pasti.",
    12: "Memuji penjelasan video, bukan pengalaman aplikasi.",
    15: "Pertanyaan isi SPT; tidak ada evaluasi UX yang jelas.",
    20: "Rujukan 'itu' tidak jelas; sikap terhadap UX tidak dapat dipastikan.",
    21: "Membahas korupsi, bukan pengalaman aplikasi.",
    22: "Membahas kewajiban pelaporan pajak, bukan penggunaan aplikasi.",
    23: "Keluhan lapor pajak; aplikasi tidak disebut, kaitan UX tak pasti.",
    25: "Memuji pembuat video, bukan pengalaman aplikasi.",
    28: "Tanpa konteks jelas.",
    29: "Komentar mengenai kondisi kesehatan seseorang.",
    32: "Membahas pengadaan dan pertanggungjawaban proyek aplikasi.",
    33: "Memuji tutorial, bukan pengalaman aplikasi.",
    35: "Mengkritik tutorial, bukan pengalaman aplikasi.",
    36: "Meminta video lanjutan, bukan menilai aplikasi.",
    37: "Komentar umum tentang Indonesia.",
    39: "Pertanyaan kewajiban aktivasi, bukan proses menggunakan aplikasi.",
    41: "Informasi tentang tim IT, bukan UX.",
    42: "Memuji pembicara video.",
    43: "Mengkritik anggaran proyek aplikasi, tanpa pengalaman UX spesifik.",
    46: "Tuduhan penggunaan anggaran proyek, bukan UX.",
    48: "Membahas perhatian publik terhadap pelaporan pajak.",
    51: "Frustrasi pelaporan, tetapi aplikasi tidak jelas.",
    53: "Ancaman pemeriksaan pajak kepada pembuat video.",
    54: "Pertanyaan jumlah pajak lebih bayar, tanpa proses aplikasi.",
    55: "Mengeluhkan tenggat dan antrean kantor, bukan UX aplikasi.",
    56: "Rujukan L4 tidak jelas sebagai fitur aplikasi.",
    59: "Komentar umum tentang kesiapan SDM.",
    64: "Memuji video.",
    67: "Memuji penjelasan pembuat video.",
    68: "Komentar anggaran, bukan UX.",
    69: "Komentar anggaran, bukan UX.",
    70: "Membahas transparansi dana pajak, bukan UX.",
    71: "Komentar anggaran, bukan UX.",
    72: "Komentar praktik pejabat, bukan UX.",
    73: "Membahas pajak kendaraan dan administrasi fisik.",
    74: "Komentar pihak penerima keuntungan, tanpa UX.",
    79: "Memuji tutorial.",
    81: "Rujukan 'this' tanpa konteks; kaitan UX tidak pasti.",
    86: "Memuji penjelasan pembuat video.",
    88: "Membahas status keluarga dan bukti potong; tanpa UX jelas.",
    89: "Memuji penjelasan pembuat video.",
    90: "Permintaan topik video lain, bukan Coretax.",
    91: "Pengalaman penipuan lewat telepon, bukan aplikasi.",
    92: "Memuji tutorial.",
    93: "Komentar politik umum.",
    96: "Komentar sindiran kepada pembuat video, tanpa UX langsung.",
    97: "Menyapa pembuat video, tanpa pengalaman aplikasi.",
    100: "Membahas web OSS, bukan Coretax.",
    103: "Pertanyaan status lebih bayar pajak, bukan penggunaan aplikasi.",
    104: "Membahas proses pengadaan dan personel IT.",
    105: "Sasaran kritik tidak jelas.",
    106: "Keluhan jumlah aplikasi umum, tidak jelas merujuk UX Coretax.",
    107: "Sindiran pembagian anggaran.",
    108: "Membahas petugas keuangan dan masalah IT secara umum.",
    118: "Lapor terasa sulit, tanpa hubungan aplikasi yang jelas.",
    119: "Mengkritik konten video, bukan aplikasi.",
    125: "Mengkritik biaya dan pengadaan website.",
    126: "Ajakan tidak membayar pajak karena korupsi.",
    127: "Sindiran proyek dan korupsi.",
    131: "Memuji tutorial.",
    132: "Memuji informasi video, bukan pengalaman Coretax langsung.",
    133: "Menanyakan nilai pajak lebih bayar.",
    134: "Memuji pembuat video.",
    136: "Memuji gaya pembicara.",
    137: "Ajakan tidak membayar pajak.",
    138: "Keberatan kewajiban lapor pajak, tanpa UX.",
    139: "Menyebut telah selesai setelah tutorial; pengalaman aplikasi tidak dijelaskan.",
    140: "Sindiran korupsi anggaran.",
    141: "Tuduhan korupsi anggaran.",
    142: "Lelucon tentang laptop.",
    143: "Pujian kepada pembicara.",
    145: "Membahas pengadaan barang dan jasa.",
    148: "Memuji tutorial.",
    149: "Membahas besaran anggaran.",
    161: "Menanyakan perhitungan kurang bayar SPT.",
    162: "Keterangan warna orange tidak cukup jelas sebagai hambatan UX.",
    165: "Pertanyaan status perkawinan dan perubahan data, tidak jelas tindakan di aplikasi.",
    167: "Komentar politik umum.",
    169: "Membahas pembagian anggaran proyek.",
    174: "Membahas pejabat dan anggaran proyek.",
    178: "Membandingkan anggaran dengan hasil proyek; UX tidak jelas.",
    179: "Menanyakan identitas NPWP pemotong dan isi contoh video.",
    181: "Memuji tutorial.",
    182: "Rujukan tanpa konteks yang cukup.",
    183: "Mengkritik durasi pembukaan video.",
    184: "Rujukan 'ini' tidak jelas.",
    187: "Sindiran kebijakan pemerintah secara umum; kaitan UX tidak pasti.",
    189: "Pertanyaan jumlah pajak lebih bayar.",
    191: "Memuji tutorial, tanpa keberhasilan UX yang eksplisit.",
    193: "Memuji tutorial.",
    195: "Komentar tentang pembicara.",
    200: "Membahas pengadaan proyek IT pemerintah.",
}

# Corrections from later independent review of AI-assisted batches.
CORRECTIONS = {
    230: ("3", ""),  # Pertanyaan prosedur unggah SPT.
    435: ("2", ""),  # Surat penerbitan tidak diterima.
    652: ("3", ""),  # Menanyakan apakah data sekuritas sudah tertarik.
    655: ("2", ""),  # Refresh berulang tetap gagal.
    1230: ("2", ""),  # Surat penerbitan tidak diterima setelah proses lain berhasil.
    1234: ("2", ""),  # Tombol simpan berulang kali gagal.
    1237: ("2", ""),  # Faktur keluaran gagal dibuat karena error.
    1598: ("1", ""),  # Melaporkan keberhasilan.
    1606: ("2", ""),  # Unduh menghasilkan dokumen yang salah.
    1691: ("2", ""),  # Verifikasi identitas menampilkan permission denied.
    1934: ("3", ""),  # Pertanyaan prosedur aktivasi Coretax PT perorangan.
    2102: ("4", "Menanyakan nilai pajak terutang, bukan pengalaman aplikasi."),
    2110: ("4", "Menanyakan bagian yang dilewati di video, bukan pengalaman aplikasi."),
    2365: ("3", ""),  # Menanyakan cara mengisi SPT di Coretax.
    2454: ("3", ""),  # Menanyakan cara saat lupa kredensial.
    2458: ("4", "Keluhan utama tentang AHU Online, aplikasi lain."),
    2459: ("3", ""),  # Pertanyaan pemulihan nomor dan email.
    2464: ("4", "Komentar umum tentang pengembangan aplikasi, tanpa pengalaman pengguna."),
}


def main() -> None:
    codes = FIRST_100.split() + NEXT_100.split()
    assert len(codes) == 200, len(codes)
    with PATH.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        fieldnames = reader.fieldnames
        rows = list(reader)
    assert fieldnames is not None and len(rows) == 3000
    for number, code in enumerate(codes, 1):
        assert code in {"1", "2", "3", "4", "5"}
        row = rows[number - 1]
        if row["label_annotator_2"] not in ("", code):
            raise ValueError(f"Existing label differs at sample position {number}")
        row["label_annotator_2"] = code
        row["catatan_anotator"] = NOTES.get(
            number,
            "Tidak membahas pengalaman penggunaan Coretax."
            if code == "4"
            else "Kaitan atau sikap terhadap UX Coretax tidak cukup jelas."
            if code == "5"
            else "",
        )
    for number, (code, note) in CORRECTIONS.items():
        row = rows[number - 1]
        if row["label_annotator_2"]:
            row["label_annotator_2"] = code
            row["catatan_anotator"] = note
    with PATH.open("w", newline="", encoding="utf-8-sig") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
