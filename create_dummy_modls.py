import joblib
from pathlib import Path
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC

# Buat folder artifacts
artifacts_dir = Path("artifacts")
artifacts_dir.mkdir(exist_ok=True)

# Dummy Training Data
train_data = [
    "aplikasi coretax sangat bagus dan mempermudah",
    "sistem error terus tidak bisa login sangat mengecewakan",
    "pajak online biasa saja tidak ada yang istimewa",
    "sangat membantu layanan DJP cepat",
    "lambat sekali web ini membingungkan"
]
train_labels = ["positif", "negatif", "netral", "positif", "negatif"]

# 1. Pipeline A (Model mRMR Dummy)
pipeline_a = Pipeline([
    ("tfidf", TfidfVectorizer(max_features=10)),
    ("svm", SVC(kernel="linear"))
])
pipeline_a.fit(train_data, train_labels)

# 2. Pipeline B (Model Baseline Dummy)
pipeline_b = Pipeline([
    ("tfidf", TfidfVectorizer()),
    ("svm", SVC(kernel="linear"))
])
pipeline_b.fit(train_data, train_labels)

# Save Artefak
joblib.dump(pipeline_a, artifacts_dir / "model_a_mrmr.joblib")
joblib.dump(pipeline_b, artifacts_dir / "model_b_baseline.joblib")

print("✅ Artefak dummy berhasil dibuat di folder artifacts/")