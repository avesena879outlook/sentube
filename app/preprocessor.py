import re

def clean_text(text: str) -> str:
    """Fungsi pembersihan teks standar untuk input baru."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"http\S+|www\S+|https\S+", "", text, flags=re.MULTILINE) # Hapus URL
    text = re.sub(r"@\w+|#\w+", "", text)                                  # Hapus Mention & Hashtag
    text = re.sub(r"[^\w\s]", "", text)                                    # Hapus Punctuasi
    text = re.sub(r"\d+", "", text)                                        # Hapus Angka
    text = re.sub(r"\s+", " ", text).strip()                                # Hapus Spasi Berlebih
    return text