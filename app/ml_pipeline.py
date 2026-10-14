import joblib
import pandas as pd
from typing import Dict, Any, List
from app.config import settings

class SentimentInference:
    def __init__(self):
        self.model_a = None
        self.model_b = None
        self.load_models()

    def load_models(self):
        """Memuat artefak model saat startup server."""
        try:
            if settings.MODEL_A_PATH.exists():
                self.model_a = joblib.load(settings.MODEL_A_PATH)
            if settings.MODEL_B_PATH.exists():
                self.model_b = joblib.load(settings.MODEL_B_PATH)
            print("Model SVM mRMR dan baseline berhasil dimuat.")
        except Exception as e:
            print(f"Gagal memuat model: {e}")

    @property
    def ready(self) -> bool:
        return self.model_a is not None and self.model_b is not None

    def predict_comparison(self, texts: List[str]) -> Dict[str, Any]:
        """Melakukan prediksi paralel pada kedua model dan menghitung statistik perbandingan."""
        valid_texts = [str(text).strip() for text in texts if str(text).strip()]

        if not valid_texts:
            return {"error": "Tidak ada teks valid untuk dianalisis."}

        if not self.ready:
            return {"error": "Artefak model belum tersedia atau gagal dimuat."}

        # Pipeline artefak sudah memuat preprocessing dan TF-IDF.
        preds_a = self.model_a.predict(valid_texts)
        preds_b = self.model_b.predict(valid_texts)

        # Buat DataFrame perbandingan
        df_res = pd.DataFrame({
            "text_raw": valid_texts,
            "pred_a_mrmr": preds_a,
            "pred_b_baseline": preds_b,
            "is_different": preds_a != preds_b
        })

        # Hitung Ringkasan Statistik Perbandingan
        summary_a = df_res["pred_a_mrmr"].value_counts().to_dict()
        summary_b = df_res["pred_b_baseline"].value_counts().to_dict()
        total_data = len(df_res)
        difference_count = int(df_res["is_different"].sum())
        difference_pct = round((difference_count / total_data) * 100, 2) if total_data > 0 else 0

        return {
            "total_data": total_data,
            "difference_count": difference_count,
            "difference_pct": difference_pct,
            "summary_a": summary_a,
            "summary_b": summary_b,
            "details": df_res.to_dict(orient="records"),
            "model_status": "preliminary",
        }

ml_engine = SentimentInference()
