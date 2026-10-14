"""Create the locked 80:20 SVM split from adjudicated annotation labels."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import unicodedata

import pandas as pd
from sklearn.model_selection import train_test_split


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "processed"
DEFAULT_ANNOTATIONS = DATA_DIR / "anotasi_ux_coretax_gabungan_3000.csv"
DEFAULT_SOURCE = DATA_DIR / "dataset_coretax_youtube_prelabel_indobert_ringkas.csv"
VALID_SENTIMENTS = ("negatif", "netral", "positif")
RANDOM_STATE = 42
TEST_SIZE = 0.20


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotations", type=Path, default=DEFAULT_ANNOTATIONS)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--random-state", type=int, default=RANDOM_STATE)
    parser.add_argument("--test-size", type=float, default=TEST_SIZE)
    return parser.parse_args()


def normalize_label(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.casefold().str.strip()


def normalize_text(value: object) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(value))).strip()


def atomic_csv(data: pd.DataFrame, path: Path) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    data.to_csv(temporary, index=False, encoding="utf-8-sig")
    temporary.replace(path)


def sha256_values(values: pd.Series) -> str:
    payload = "\n".join(values.astype(str).tolist()).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def main() -> None:
    args = parse_args()
    if not 0 < args.test_size < 1:
        raise ValueError("--test-size harus berada di antara 0 dan 1.")

    annotation_path = args.annotations.resolve()
    source_path = args.source.resolve()
    output_dir = args.output_dir.resolve()
    annotations = pd.read_csv(annotation_path, encoding="utf-8-sig", low_memory=False)
    source = pd.read_csv(source_path, encoding="utf-8-sig", low_memory=False)

    annotation_required = {"nomor_baris_sumber", "komentar", "label_final"}
    source_required = {
        "nomor_baris_sumber", "komentar", "komentar_clean", "komentar_preprocessed"
    }
    if missing := annotation_required - set(annotations.columns):
        raise ValueError(f"Kolom anotasi tidak tersedia: {sorted(missing)}")
    if missing := source_required - set(source.columns):
        raise ValueError(f"Kolom sumber tidak tersedia: {sorted(missing)}")
    if not annotations["nomor_baris_sumber"].is_unique:
        raise ValueError("nomor_baris_sumber pada anotasi harus unik.")
    if not source["nomor_baris_sumber"].is_unique:
        raise ValueError("nomor_baris_sumber pada sumber harus unik.")

    annotations = annotations.copy()
    annotations["label_final"] = normalize_label(annotations["label_final"])
    annotations["nomor_baris_sumber"] = annotations["nomor_baris_sumber"].astype(int)
    source = source.copy()
    source["nomor_baris_sumber"] = source["nomor_baris_sumber"].astype(int)

    source_text = source.set_index("nomor_baris_sumber")["komentar"]
    missing_ids = sorted(set(annotations["nomor_baris_sumber"]) - set(source_text.index))
    if missing_ids:
        raise ValueError(f"ID anotasi tidak ditemukan pada sumber: {missing_ids[:10]}")
    expected_text = annotations["nomor_baris_sumber"].map(source_text)
    annotation_text_key = annotations["komentar"].fillna("").map(normalize_text)
    source_text_key = expected_text.fillna("").map(normalize_text)
    if not annotation_text_key.equals(source_text_key):
        raise ValueError("Komentar anotasi tidak cocok dengan komentar pada sumber.")

    merged = annotations.merge(
        source[["nomor_baris_sumber", "komentar_clean", "komentar_preprocessed"]],
        on="nomor_baris_sumber",
        how="left",
        validate="one_to_one",
    )
    valid_mask = merged["label_final"].isin(VALID_SENTIMENTS)
    labeled = merged.loc[valid_mask].copy()
    excluded = merged.loc[~valid_mask].copy()
    excluded["alasan_eksklusi"] = excluded["label_final"].replace(
        {"": "label_final_kosong"}
    )

    if labeled.empty or labeled["label_final"].nunique() != len(VALID_SENTIMENTS):
        raise ValueError("Dataset harus memiliki label negatif, netral, dan positif.")
    if labeled["label_final"].value_counts().min() < 2:
        raise ValueError("Setiap kelas membutuhkan sedikitnya dua data.")

    train_indices, test_indices = train_test_split(
        labeled.index,
        test_size=args.test_size,
        stratify=labeled["label_final"],
        random_state=args.random_state,
    )
    labeled["split"] = ""
    labeled.loc[train_indices, "split"] = "train"
    labeled.loc[test_indices, "split"] = "test"
    if (labeled["split"] == "").any():
        raise RuntimeError("Sebagian baris belum memperoleh split.")

    # Notebook memakai teks asli lalu menjalankan preprocessing di dalam pipeline.
    labeled["text"] = labeled["komentar"].fillna("").astype(str)
    output_columns = [
        "nomor_baris_sumber", "split", "text", "komentar_clean",
        "komentar_preprocessed", "label_final", "label_annotator_1",
        "label_annotator_2", "hasil_perbandingan", "status_anotasi",
    ]
    output_columns = [column for column in output_columns if column in labeled.columns]
    master = labeled[output_columns].sort_values("nomor_baris_sumber").reset_index(drop=True)
    train = master.loc[master["split"].eq("train")].reset_index(drop=True)
    test = master.loc[master["split"].eq("test")].reset_index(drop=True)

    excluded_columns = [
        "nomor_baris_sumber", "komentar", "label_final", "label_annotator_1",
        "label_annotator_2", "hasil_perbandingan", "status_anotasi", "alasan_eksklusi",
    ]
    excluded_columns = [column for column in excluded_columns if column in excluded.columns]
    excluded = excluded[excluded_columns].sort_values("nomor_baris_sumber").reset_index(drop=True)

    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "master": output_dir / "comments_labeled.csv",
        "train": output_dir / "comments_labeled_train.csv",
        "test": output_dir / "comments_labeled_test.csv",
        "excluded": output_dir / "comments_excluded.csv",
        "report": output_dir / "train_test_split_report.json",
    }
    atomic_csv(master, paths["master"])
    atomic_csv(train, paths["train"])
    atomic_csv(test, paths["test"])
    atomic_csv(excluded, paths["excluded"])

    report = {
        "annotations": str(annotation_path.relative_to(ROOT)),
        "source": str(source_path.relative_to(ROOT)),
        "random_state": args.random_state,
        "test_size_requested": args.test_size,
        "rows_annotation": int(len(annotations)),
        "rows_included": int(len(master)),
        "rows_excluded": int(len(excluded)),
        "excluded_label_counts": excluded["label_final"].value_counts().to_dict(),
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "actual_test_ratio": round(len(test) / len(master), 6),
        "class_distribution_all": master["label_final"].value_counts().to_dict(),
        "class_distribution_train": train["label_final"].value_counts().to_dict(),
        "class_distribution_test": test["label_final"].value_counts().to_dict(),
        "included_status_counts": master["status_anotasi"].value_counts().to_dict(),
        "included_rows_marked_perlu_adjudikasi": int(
            master["status_anotasi"].eq("perlu_adjudikasi").sum()
        ),
        "methodology_warning": (
            "Label final dipakai untuk split, tetapi status_anotasi pada sebagian baris "
            "masih perlu_adjudikasi. Konfirmasi keputusan final manusia dan ubah status "
            "menjadi selesai sebelum eksperimen final dilaporkan."
        ),
        "train_source_ids_sha256": sha256_values(train["nomor_baris_sumber"]),
        "test_source_ids_sha256": sha256_values(test["nomor_baris_sumber"]),
        "outputs": {key: str(path.relative_to(ROOT)) for key, path in paths.items()},
    }
    paths["report"].write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
