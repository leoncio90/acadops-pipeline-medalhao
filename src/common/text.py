import re
from unidecode import unidecode


def clean_text(text: str) -> str:
    """Limpa e normaliza texto: minusculas, sem acento, sem pontuacao e sem espacos extras."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = unidecode(text)
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text
