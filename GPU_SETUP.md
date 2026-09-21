# Konfigurasi RTX 3050 untuk Notebook

## Ringkasan

Laptop memiliki dua adapter grafis:

- NVIDIA GeForce RTX 3050 Laptop GPU dengan VRAM 4 GB;
- Intel Iris Xe Graphics.

Hasil pemeriksaan `nvidia-smi` menunjukkan RTX 3050 terdeteksi sebagai GPU nomor `0`, menggunakan driver NVIDIA `529.04`, dan melaporkan kompatibilitas CUDA sampai versi `12.0`.

GPU dipakai untuk proses berbasis PyTorch seperti pre-labeling atau fine-tuning IndoBERT. Komponen berikut tetap berjalan di CPU karena implementasinya menggunakan scikit-learn:

- pembersihan teks;
- TF-IDF;
- seleksi fitur mRMR;
- SVM;
- GridSearchCV.

## 1. Perbarui Driver NVIDIA

Driver `529.04` sudah dapat mendeteksi GPU, tetapi tergolong lama untuk rilis PyTorch CUDA terbaru. Perbarui ke NVIDIA Studio Driver atau Game Ready Driver terbaru yang mendukung RTX 3050 sebelum memasang PyTorch CUDA.

CUDA Toolkit terpisah biasanya tidak diperlukan ketika memakai wheel PyTorch resmi. Wheel tersebut membawa CUDA runtime yang diperlukan. Driver NVIDIA tetap harus kompatibel dengan runtime yang dipilih.

## 2. Buat Environment VS Code dengan uv

Jalankan dari root project:

```powershell
uv sync
```

Perintah `uv python list` hanya menampilkan interpreter Python. Perintah tersebut tidak menunjukkan apakah Torch mempunyai dukungan CUDA. Environment project yang digunakan oleh `uv run` dan VS Code berada di `.venv`.

Pada Windows, Torch dari PyPI dapat berupa build CPU. Project ini mengunci Python ke seri 3.12 dan mengatur index `pytorch-cu118` sebagai index eksplisit khusus Torch di `pyproject.toml`. Dependensi lain tetap diambil dari PyPI. Terapkan konfigurasi tersebut dengan:

```powershell
uv lock --refresh-package torch
uv sync --reinstall-package torch
```

Untuk driver NVIDIA `529.04` yang melaporkan CUDA `12.0`, project memilih CUDA 11.8. Jangan menambahkan URL PyTorch sebagai index umum karena uv kemudian dapat mencoba mengambil Jinja2 dan dependensi non-Torch dari index tersebut.

Untuk eksperimen sementara tanpa mengubah konfigurasi project, uv juga dapat membaca driver NVIDIA dan memilih backend secara otomatis:

```powershell
uv pip install torch --torch-backend=auto --reinstall
```

Untuk penggunaan jangka panjang, perbarui driver NVIDIA terlebih dahulu. Setelah driver diperbarui, jalankan kembali instalasi menggunakan `--torch-backend=auto` agar uv memilih runtime CUDA yang sesuai.

Alternatifnya, buka halaman instalasi resmi PyTorch, lalu pilih:

- OS: Windows;
- Package: Pip;
- Language: Python;
- Compute Platform: versi CUDA yang direkomendasikan oleh PyTorch dan didukung driver terbaru.

Jalankan perintah yang dihasilkan menggunakan `uv pip` sebagai pengganti `pip`. Jika sebelumnya terpasang build CPU, hapus terlebih dahulu:

```powershell
uv pip uninstall torch torchvision torchaudio
```

## 3. Verifikasi CUDA

Jalankan di terminal VS Code:

```powershell
uv run python -c "import torch; print('Python/Torch:', torch.__version__); print('CUDA tersedia:', torch.cuda.is_available()); print('CUDA runtime:', torch.version.cuda); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else '-')"
```

Hasil yang diharapkan:

```text
CUDA tersedia: True
GPU: NVIDIA GeForce RTX 3050 Laptop GPU
```

Jika `CUDA tersedia` bernilai `False`, penyebab yang paling umum adalah kernel VS Code menggunakan environment yang berbeda atau PyTorch yang terpasang merupakan build CPU.

Periksa interpreter yang benar dengan:

```powershell
uv run python -c "import sys; print(sys.executable)"
```

Lokasinya seharusnya mengarah ke `.venv\Scripts\python.exe` di dalam project.

## 4. Pilih Kernel yang Benar

Di VS Code:

1. Buka file notebook.
2. Klik **Select Kernel**.
3. Pilih Python dari `.venv` project ini.
4. Jalankan sel pemeriksaan GPU pada notebook `01_crawl_and_prep.ipynb`.

Notebook memilih perangkat secara eksplisit:

```python
TORCH_DEVICE = 0 if torch.cuda.is_available() else -1
```

Nilai `0` berarti NVIDIA RTX 3050. Intel Iris Xe tidak akan dipilih oleh PyTorch CUDA.

## 5. Pengaturan untuk VRAM 4 GB

Notebook menggunakan:

- `device=0` untuk RTX 3050;
- `float16` untuk mengurangi penggunaan VRAM;
- `batch_size=8` sebagai nilai awal yang aman.

Jika muncul `CUDA out of memory`, turunkan batch menjadi `4`, lalu `2`. Tutup aplikasi lain yang menggunakan GPU dan mulai ulang kernel notebook untuk melepaskan memori CUDA.

Pantau penggunaan GPU dari terminal lain:

```powershell
nvidia-smi -l 2
```

## 6. Mengoptimalkan Pipeline SVM

SVM scikit-learn tidak otomatis berpindah ke RTX 3050. Notebook training sudah memakai:

```python
GridSearchCV(..., n_jobs=-1)
```

Artinya, kombinasi parameter dan fold diproses menggunakan seluruh core CPU. Untuk laptop, perhatikan suhu dan gunakan mode daya performa tinggi ketika menjalankan eksperimen final.

Mengganti SVM ke library GPU seperti RAPIDS cuML akan mengubah environment, implementasi, dan aspek reproduksibilitas penelitian. Untuk skripsi ini, mempertahankan scikit-learn pada CPU lebih sederhana dan membuat perbandingan mRMR tetap konsisten.
