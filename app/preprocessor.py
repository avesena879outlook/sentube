"""Preprocessing Bahasa Indonesia untuk pelabelan dan TF-IDF-SVM."""

from __future__ import annotations

import html
import re
import unicodedata
from functools import lru_cache

from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory


URL_PATTERN = re.compile(r"(?:https?://|www\.)\S+", flags=re.IGNORECASE)
MENTION_PATTERN = re.compile(r"(?<!\w)@[A-Za-z0-9_.-]+")
WHITESPACE_PATTERN = re.compile(r"\s+")
NON_WORD_PATTERN = re.compile(r"[^\w\s]", flags=re.UNICODE)
DIGIT_PATTERN = re.compile(r"\d+")

# Negasi membawa polaritas dan tidak boleh dibuang sebagai stopword.
NEGATIONS = {"tidak", "tak", "bukan", "belum", "jangan", "kurang", "tanpa", "gagal"}
TOKEN_NORMALIZATION = {
    "g": "tidak",
    "ga": "tidak",
    "gak": "tidak",
    "gk": "tidak",
    "ngga": "tidak",
    "nggak": "tidak",
    "enggak": "tidak",
    "ndak": "tidak",
    "blm": "belum",
    "bkn": "bukan",
    "jgn": "jangan",
}


@lru_cache(maxsize=1)
def _resources():
    stemmer = StemmerFactory().create_stemmer()
    stopwords = set(StopWordRemoverFactory().get_stop_words()) - NEGATIONS
    return stemmer, stopwords


def clean_for_labeling(text: str) -> str:
    """Pembersihan ringan untuk anotator atau model kontekstual seperti IndoBERT."""
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize("NFKC", html.unescape(text))
    text = URL_PATTERN.sub(" ", text)
    return WHITESPACE_PATTERN.sub(" ", text).strip()


def tokenize_for_svm(text: str) -> list[str]:
    """Normalisasi dan stopword removal sebelum stemming."""
    text = clean_for_labeling(text).casefold()
    if not text:
        return []

    text = MENTION_PATTERN.sub(" ", text)
    text = text.replace("#", " ")  # Pertahankan kata pada hashtag.
    text = NON_WORD_PATTERN.sub(" ", text)
    text = DIGIT_PATTERN.sub(" ", text)
    tokens = [
        TOKEN_NORMALIZATION.get(token, token)
        for token in WHITESPACE_PATTERN.sub(" ", text).strip().split()
    ]

    _, stopwords = _resources()
    return [token for token in tokens if (len(token) > 1 or token in NEGATIONS) and token not in stopwords]


def preprocess_for_svm(text: str) -> str:
    """Normalisasi, stopword removal, dan stemming untuk fitur TF-IDF."""
    stemmer, _ = _resources()
    stemmed = [stemmer.stem(token) for token in tokenize_for_svm(text)]
    return " ".join(token for token in stemmed if token)


def clean_text(text: str) -> str:
    """Alias kompatibilitas untuk pipeline inferensi dan training yang sudah ada."""
    return preprocess_for_svm(text)
