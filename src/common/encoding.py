import os
import pandas as pd


def corrigir_mojibake(texto):
    """Detecta assinatura de duplo encoding UTF-8 (lido incorretamente como latin-1) e desfaz."""
    if not isinstance(texto, str):
        return texto

    if 'Ã' not in texto and 'Â' not in texto:
        return texto

    try:
        return texto.encode('latin-1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        return texto


def read_csv_with_fallback(path: str) -> pd.DataFrame:
    """Tenta ler CSV com UTF-8; se falhar por erro de decodificação, tenta latin-1."""
    try:
        return pd.read_csv(path, encoding='utf-8')
    except UnicodeDecodeError:
        print(f"INFO: Leitura com UTF-8 falhou para {os.path.basename(path)}. Tentando com latin-1.")
        return pd.read_csv(path, encoding='latin-1')
