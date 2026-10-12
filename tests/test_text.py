from src.common.text import clean_text


def test_clean_text_basic():
    assert clean_text("Olá Mundo!") == "ola mundo"


def test_clean_text_acentos_e_pontuacao():
    assert clean_text("Avaliação e Nutrição, São Paulo - SP") == "avaliacao e nutricao sao paulo sp"


def test_clean_text_espacos_multiplos():
    assert clean_text("  Texto   com   muitos     espacos  ") == "texto com muitos espacos"


def test_clean_text_non_string():
    assert clean_text(None) == ""
    assert clean_text(12345) == ""
