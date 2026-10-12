import os
import tempfile
import pandas as pd
import pytest
from src.common.encoding import corrigir_mojibake, read_csv_with_fallback


def test_corrigir_mojibake_duplo_encoding():
    # Simula o duplo encoding de Nutrição
    quebrado = "NutriÃ§Ã£o"
    assert corrigir_mojibake(quebrado) == "Nutrição"


def test_corrigir_mojibake_texto_limpo():
    assert corrigir_mojibake("Nutrição") == "Nutrição"
    assert corrigir_mojibake("Texto normal sem acentos") == "Texto normal sem acentos"


def test_corrigir_mojibake_tipos_nao_string():
    assert corrigir_mojibake(123) == 123
    assert corrigir_mojibake(None) is None
    assert corrigir_mojibake(45.67) == 45.67


def test_read_csv_with_fallback_utf8():
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', suffix='.csv', delete=False) as f:
        f.write("col1,col2\nvalor1,Educação\n")
        temp_path = f.name
    try:
        df = read_csv_with_fallback(temp_path)
        assert len(df) == 1
        assert df.iloc[0]['col2'] == "Educação"
    finally:
        os.remove(temp_path)


def test_read_csv_with_fallback_latin1():
    with tempfile.NamedTemporaryFile('w', encoding='latin-1', suffix='.csv', delete=False) as f:
        f.write("col1,col2\nvalor1,Informação\n")
        temp_path = f.name
    try:
        df = read_csv_with_fallback(temp_path)
        assert len(df) == 1
        assert df.iloc[0]['col2'] == "Informação"
    finally:
        os.remove(temp_path)
