# 📂 Struktur Proyek: SenTube

Dokumentasi mengenai arsitektur dan organisasi direktori untuk proyek **SenTube**.

---

## 🌳 Pohon Direktori (Directory Tree)

```text
sentube/
├── 📁 app/                          # Core Application Code
│   ├── 📄 __init__.py               # Python Package Initializer
│   ├── ⚙️ config.py                 # Settings, Konfigurasi & Path Artefak (.env)
│   ├── 🚀 main.py                   # FastAPI Entrypoint & Route Handlers
│   ├── 🤖 ml_pipeline.py            # Inference ML (Load Model & Predict)
│   ├── 🧹 preprocessor.py           # Text Preprocessing (Cleaning, Stemming, Stopwords)
│   └── 🛠️ services.py               # Services (YouTube Crawler & CSV Handling)
│
├── 📁 artifacts/                    # Model ML Output (Colab / Training Result)
│   ├── 📦 model_a_mrmr.joblib       # Model Utama (Feature Selection mRMR)
│   └── 📦 model_b_baseline.joblib   # Model Baseline
│
├── 📁 data/                         # Temporary File Storage
│   └── 📁 uploads/                  # Tempat Penyimpanan Sementara Upload/Crawl
│
├── 📁 notebooks/                    # Jupyter Notebooks (Eksperimen & Training)
│   ├── 📓 01_crawl_and_prep.ipynb   # Exploration & Data Preparation
│   └── 📓 02_training_svm_mrmr.ipynb # Training Model SVM + mRMR
│
├── 📁 templates/                    # Frontend HTML Templates (Jinja2)
│   ├── 📁 fragments/                # HTML Fragments (Alpine AJAX)
│   │   ├── 🧩 loading.html
│   │   └── 🧩 results.html
│   └── 📄 index.html                # Layout Utama (Alpine.js)
│
├── 📁 static/                       # Local Static Assets (CSS, JS, Images)
│
├── 📄 .env                          # Environment Variables (YouTube API Key)
├── 📄 .gitignore                    # Git Ignore Rules
└── 📄 create_dummy_models.py        # Script Generator Dummy Model untuk Local Run
