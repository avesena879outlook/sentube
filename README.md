sentube/
├── app/
│   ├── __init__.py
│   ├── config.py             # Settings & path artefak (.env)
│   ├── main.py               # FastAPI entrypoint & Route handlers
│   ├── ml_pipeline.py        # Class & fungsi Inference ML (Load & Predict)
│   ├── preprocessor.py       # Fungsi pembersihan teks (Cleaning, Stemming/Stopwords)
│   └── services.py           # Services: Handling Youtube Crawl & CSV Upload
├── data/                     # Storage sementara file upload/crawl
│   └── uploads/
├── artifacts/                # Artefak Model ML dari Google Colab/Notebook
│   ├── model_a_mrmr.joblib
│   └── model_b_baseline.joblib
├── notebooks/                # Tempat Eksperimen & Training Model
│   ├── 01_crawl_and_prep.ipynb
│   └── 02_training_svm_mrmr.ipynb
├── templates/
│   ├── fragments/            # HTML Fragment untuk Alpine AJAX
│   │   ├── loading.html
│   │   └── results.html
│   └── index.html            # Layout Utama (Alpine.js)
├── static/                   # File CSS/JS lokal (Opsional)
├── .env                      # API Keys (YOUTUBE_API_KEY)
├── .gitignore
├── create_dummy_models.py    # Script pembuat dummy model agar app bisa di-run langsung
└── requirements.txt