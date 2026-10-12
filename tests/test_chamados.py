from src.chamados.silver import correct_common_errors
from src.chamados.gold import triar_chamado, EQUIPE_PADRAO


def test_correct_common_errors():
    assert correct_common_errors("erro no moodl") == "erro no moodle"
    # Garante que 'moodle' nao vira 'moodlee'
    assert correct_common_errors("acesso ao moodle ok") == "acesso ao moodle ok"
    assert correct_common_errors("sistema share point") == "sistema sharepoint"
    assert correct_common_errors("banco lyceun") == "banco lyceum"


def test_triar_chamado_equipes():
    equipe, termo = triar_chamado("aluno precisa de mais tempo especial na prova")
    assert equipe == "Equipe AVA"

    equipe, termo = triar_chamado("falha de login com sso e credencial corporativa")
    assert equipe == "Equipe Infraestrutura"

    equipe, termo = triar_chamado("solicitacao de novo painel no power bi")
    assert equipe == "Equipe Business Intelligence"

    equipe, termo = triar_chamado("duvida generica sobre estacionamento")
    assert equipe == EQUIPE_PADRAO
    assert termo == "nenhuma"


def test_triar_chamado_fronteira_palavra():
    # 'avaliacao' nao deve acionar 'ava'
    equipe, termo = triar_chamado("avaliacao semestral concluida")
    assert equipe != "Equipe AVA"
