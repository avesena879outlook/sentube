"""Create reproducible visual comparisons of raw and preprocessed comments."""

from __future__ import annotations

import re
import os
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT_ROOT / ".cache" / "matplotlib"))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


RAW_PATH = PROJECT_ROOT / "data" / "raw" / "yt" / "merged" / "dataset_coretax_youtube_raw_merged.csv"
PROCESSED_PATH = PROJECT_ROOT / "data" / "processed" / "dataset_coretax_youtube_preprocessed.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

RAW_COLOR = "#64748B"
PROCESSED_COLOR = "#0F766E"
ACCENT_COLOR = "#C2413B"
TEXT_COLOR = "#17202A"
GRID_COLOR = "#D9E0E6"


def tokenize_raw(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", str(text).casefold(), flags=re.UNICODE)


def style_axis(axis) -> None:
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.spines["left"].set_color(GRID_COLOR)
    axis.spines["bottom"].set_color(GRID_COLOR)
    axis.tick_params(colors="#52606D")
    axis.grid(axis="y", color=GRID_COLOR, linewidth=0.7, alpha=0.7)
    axis.set_axisbelow(True)


def add_bar_labels(axis, decimals: int = 0) -> None:
    for container in axis.containers:
        axis.bar_label(
            container,
            fmt=f"%.{decimals}f",
            padding=3,
            fontsize=9,
            color=TEXT_COLOR,
        )


def load_and_validate() -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = pd.read_csv(RAW_PATH, encoding="utf-8-sig")
    processed = pd.read_csv(PROCESSED_PATH, encoding="utf-8-sig")
    if len(raw) != len(processed):
        raise ValueError(f"Jumlah baris berbeda: raw={len(raw)}, processed={len(processed)}")
    required = {"komentar", "komentar_preprocessed", "status_preprocessing"}
    missing = required - set(processed.columns)
    if missing:
        raise ValueError(f"Kolom processed tidak tersedia: {sorted(missing)}")
    if not processed["status_preprocessing"].eq("valid").all():
        raise ValueError("Masih terdapat baris preprocessing yang tidak valid.")
    return raw, processed


def build_statistics(raw: pd.DataFrame, processed: pd.DataFrame):
    raw_tokens = raw["komentar"].fillna("").map(tokenize_raw)
    processed_tokens = processed["komentar_preprocessed"].fillna("").map(str.split)
    raw_lengths = raw_tokens.map(len)
    processed_lengths = processed_tokens.map(len)
    reduction_pct = (raw_lengths - processed_lengths).div(raw_lengths.replace(0, np.nan)).mul(100)
    raw_counter = Counter(token for tokens in raw_tokens for token in tokens)
    processed_counter = Counter(token for tokens in processed_tokens for token in tokens)

    rows = []

    def add_metric(metric: str, raw_value: float, processed_value: float) -> None:
        difference = processed_value - raw_value
        percentage = difference / raw_value * 100 if raw_value else np.nan
        rows.append(
            {
                "metrik": metric,
                "raw": raw_value,
                "preprocessed": processed_value,
                "perubahan": difference,
                "perubahan_persen": percentage,
            }
        )

    add_metric("Jumlah komentar", len(raw), len(processed))
    add_metric("Total token", int(raw_lengths.sum()), int(processed_lengths.sum()))
    add_metric("Kosakata unik", len(raw_counter), len(processed_counter))
    add_metric("Rata-rata token per komentar", raw_lengths.mean(), processed_lengths.mean())
    add_metric("Median token per komentar", raw_lengths.median(), processed_lengths.median())
    add_metric("Persentil 95 token", raw_lengths.quantile(0.95), processed_lengths.quantile(0.95))
    add_metric("Maksimum token", raw_lengths.max(), processed_lengths.max())

    statistics = pd.DataFrame(rows)
    return statistics, raw_lengths, processed_lengths, reduction_pct, raw_counter, processed_counter


def plot_overview(
    statistics: pd.DataFrame,
    raw_lengths: pd.Series,
    processed_lengths: pd.Series,
    reduction_pct: pd.Series,
) -> Path:
    fig, axes = plt.subplots(2, 2, figsize=(14, 9), constrained_layout=True)
    fig.suptitle("Perbandingan Data Mentah dan Hasil Preprocessing", fontsize=17, fontweight="bold", color=TEXT_COLOR)

    total = statistics.set_index("metrik").loc[["Total token", "Kosakata unik"], ["raw", "preprocessed"]]
    total.plot.bar(ax=axes[0, 0], color=[RAW_COLOR, PROCESSED_COLOR], width=0.72)
    axes[0, 0].set_title("Total token dan kosakata unik", fontweight="bold")
    axes[0, 0].set_xlabel("")
    axes[0, 0].set_ylabel("Jumlah")
    axes[0, 0].tick_params(axis="x", rotation=0)
    axes[0, 0].legend(["Mentah", "Preprocessed"], frameon=False, loc="upper right")
    add_bar_labels(axes[0, 0])
    style_axis(axes[0, 0])

    upper = int(max(raw_lengths.quantile(0.99), processed_lengths.quantile(0.99)))
    bins = np.arange(0, upper + 3, 2)
    axes[0, 1].hist(raw_lengths.clip(upper=upper), bins=bins, alpha=0.60, color=RAW_COLOR, label="Mentah")
    axes[0, 1].hist(
        processed_lengths.clip(upper=upper), bins=bins, alpha=0.65, color=PROCESSED_COLOR, label="Preprocessed"
    )
    axes[0, 1].set_title("Distribusi panjang komentar", fontweight="bold")
    axes[0, 1].set_xlabel("Jumlah token per komentar (dibatasi P99)")
    axes[0, 1].set_ylabel("Jumlah komentar")
    axes[0, 1].legend(frameon=False)
    style_axis(axes[0, 1])

    summary = statistics.set_index("metrik").loc[
        ["Rata-rata token per komentar", "Median token per komentar", "Persentil 95 token"],
        ["raw", "preprocessed"],
    ]
    summary.plot.bar(ax=axes[1, 0], color=[RAW_COLOR, PROCESSED_COLOR], width=0.72)
    axes[1, 0].set_title("Statistik panjang komentar", fontweight="bold")
    axes[1, 0].set_xlabel("")
    axes[1, 0].set_ylabel("Token")
    axes[1, 0].tick_params(axis="x", rotation=12)
    axes[1, 0].legend(["Mentah", "Preprocessed"], frameon=False)
    add_bar_labels(axes[1, 0], decimals=1)
    style_axis(axes[1, 0])

    axes[1, 1].hist(reduction_pct.dropna(), bins=np.arange(-5, 85, 5), color=ACCENT_COLOR, alpha=0.82)
    median_reduction = reduction_pct.median()
    axes[1, 1].axvline(median_reduction, color=TEXT_COLOR, linestyle="--", linewidth=1.5)
    axes[1, 1].text(
        median_reduction + 1,
        axes[1, 1].get_ylim()[1] * 0.88,
        f"Median {median_reduction:.1f}%",
        color=TEXT_COLOR,
        fontsize=10,
    )
    axes[1, 1].set_title("Persentase pengurangan token", fontweight="bold")
    axes[1, 1].set_xlabel("Token berkurang (%)")
    axes[1, 1].set_ylabel("Jumlah komentar")
    style_axis(axes[1, 1])

    path = OUTPUT_DIR / "visualisasi_perbandingan_raw_preprocessed.png"
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def plot_top_terms(raw_counter: Counter, processed_counter: Counter) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(15, 8), constrained_layout=True)
    fig.suptitle("Kata Dominan Sebelum dan Sesudah Preprocessing", fontsize=17, fontweight="bold", color=TEXT_COLOR)

    for axis, counter, title, color in [
        (axes[0], raw_counter, "Data mentah", RAW_COLOR),
        (axes[1], processed_counter, "Data preprocessed", PROCESSED_COLOR),
    ]:
        terms = pd.DataFrame(counter.most_common(20), columns=["kata", "frekuensi"]).sort_values("frekuensi")
        axis.barh(terms["kata"], terms["frekuensi"], color=color)
        axis.set_title(title, fontweight="bold")
        axis.set_xlabel("Frekuensi")
        axis.set_ylabel("")
        style_axis(axis)

    path = OUTPUT_DIR / "visualisasi_kata_dominan_raw_preprocessed.png"
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def plot_length_relationship(raw_lengths: pd.Series, processed_lengths: pd.Series) -> Path:
    sample_size = min(4_000, len(raw_lengths))
    sample_indices = raw_lengths.sample(sample_size, random_state=42).index
    x = raw_lengths.loc[sample_indices]
    y = processed_lengths.loc[sample_indices]
    limit = int(max(x.quantile(0.99), y.quantile(0.99)))

    fig, axis = plt.subplots(figsize=(9, 8), constrained_layout=True)
    axis.scatter(x.clip(upper=limit), y.clip(upper=limit), s=14, alpha=0.26, color=PROCESSED_COLOR, edgecolors="none")
    axis.plot([0, limit], [0, limit], color=ACCENT_COLOR, linestyle="--", linewidth=1.5, label="Tidak ada pengurangan")
    axis.set_xlim(0, limit)
    axis.set_ylim(0, limit)
    axis.set_title("Panjang Komentar Sebelum dan Sesudah Preprocessing", fontsize=15, fontweight="bold")
    axis.set_xlabel("Token data mentah (dibatasi P99)")
    axis.set_ylabel("Token data preprocessed (dibatasi P99)")
    axis.legend(frameon=False, loc="upper left")
    style_axis(axis)

    path = OUTPUT_DIR / "visualisasi_perubahan_panjang_komentar.png"
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", font="DejaVu Sans")
    raw, processed = load_and_validate()
    statistics, raw_lengths, processed_lengths, reduction_pct, raw_counter, processed_counter = build_statistics(
        raw, processed
    )
    summary_path = OUTPUT_DIR / "statistik_perbandingan_raw_preprocessed.csv"
    statistics.to_csv(summary_path, index=False, encoding="utf-8-sig", float_format="%.2f")
    paths = [
        plot_overview(statistics, raw_lengths, processed_lengths, reduction_pct),
        plot_top_terms(raw_counter, processed_counter),
        plot_length_relationship(raw_lengths, processed_lengths),
    ]
    print(statistics.to_string(index=False))
    print("\nOutput:")
    print(summary_path)
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
