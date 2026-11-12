import re


def clean_job_text(text: str) -> str:
    """Metin ön işleme: fazla boşlukları temizler ve standart Türkçe karakter korunumu sağlar."""
    if not text:
        return ""
    cleaned = re.sub(r"<[^>]+>", " ", text)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()
