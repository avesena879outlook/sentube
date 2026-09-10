# app/services.py
import io
from typing import List

import pandas as pd
from googleapiclient.discovery import build

from app.config import settings


def fetch_youtube_comments(keyword: str, max_results: int = 50) -> List[str]:
    """Mengambil komentar dari YouTube API berdasarkan keyword."""
    if not settings.YOUTUBE_API_KEY:
        raise ValueError("API Key YouTube tidak ditemukan pada .env")

    youtube = build("youtube", "v3", developerKey=settings.YOUTUBE_API_KEY)

    # Cari Video
    search_res = (
        youtube.search()
        .list(
            part="snippet",
            q=keyword,
            type="video",
            maxResults=5,
            relevanceLanguage="id",
        )
        .execute()
    )

    video_ids = [item["id"]["videoId"] for item in search_res.get("items", [])]
    comments = []

    for vid in video_ids:
        try:
            comm_res = (
                youtube.commentThreads()
                .list(
                    part="snippet",
                    videoId=vid,
                    maxResults=max_results // max(len(video_ids), 1),
                    textFormat="plainText",
                )
                .execute()
            )
            for item in comm_res.get("items", []):
                text = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                comments.append(text)
        except Exception:
            continue

    return comments


def parse_csv_dataset(file_contents: bytes) -> List[str]:
    """Membaca file CSV yang di-upload user dan mengambil kolom teks."""
    df = pd.read_csv(io.BytesIO(file_contents))

    text_col = None
    possible_cols = ["text", "komentar", "comment", "tweet", "review", "content"]

    for col in df.columns:
        if col.lower() in possible_cols:
            text_col = col
            break

    if not text_col:
        text_col = df.select_dtypes(include=["object"]).columns[0]

    return df[text_col].dropna().astype(str).tolist()
