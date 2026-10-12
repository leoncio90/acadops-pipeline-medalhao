import tempfile
import os
import pandas as pd
from src.moodle.gold import parse_tempo_especial
from src.moodle.silver import standardize_header, process_to_silver


def test_parse_tempo_especial_valido():
    valor = "ID2372:50%;ID8566:25%"
    alunos, erros = parse_tempo_especial(valor, 1)
    assert len(alunos) == 2
    assert len(erros) == 0
    assert alunos[0] == {"aluno_id": "ID2372", "acrescimo_percentual": 50}
    assert alunos[1] == {"aluno_id": "ID8566", "acrescimo_percentual": 25}


def test_parse_tempo_especial_invalido():
    valor = "ID100:150%;ID200:abc;ID300:0%"
    alunos, erros = parse_tempo_especial(valor, 2)
    assert len(alunos) == 0
    assert len(erros) == 3
    motivos = [e['motivo'] for e in erros]
    assert 'percentual fora da faixa de 1 a 100' in motivos
    assert 'formato esperado aluno:percentual' in motivos


def test_parse_tempo_especial_vazio():
    alunos, erros = parse_tempo_especial(None, 3)
    assert alunos == []
    assert erros == []


def test_standardize_header():
    assert standardize_header("Sem Cabeçalho") == "nenhum"
    assert standardize_header("Cabeçalho com orientações") == "customizado"
    assert standardize_header("Padrão AcadOps 2025") == "padrao"
    assert standardize_header("Qualquer outro texto") == "nao_identificado"


def test_silver_solicitacao_id_invalido_quarentenado():
    with tempfile.TemporaryDirectory() as tmpdir:
        bronze_csv = os.path.join(tmpdir, "bronze.csv")
        silver_dir = os.path.join(tmpdir, "silver")
        rejected_dir = os.path.join(tmpdir, "rejected")

        # Cria dados onde uma linha tem ID invalido (string nao numerica)
        df_fake = pd.DataFrame([
            {
                'solicitacao_id': '10', 'curso': 'Medicina', 'modulo_codigo': 'MED1',
                'tipo_prova': 'QME', 'data_prova': '2025-10-10', 'cabecalho': 'Padrao',
                'professor_email': 'prof@acadops.edu.br', 'alunos_tempo_especial': ''
            },
            {
                'solicitacao_id': 'INVALIDO_ABC', 'curso': 'Direito', 'modulo_codigo': 'DIR1',
                'tipo_prova': 'QME', 'data_prova': '2025-10-10', 'cabecalho': 'Padrao',
                'professor_email': 'prof2@acadops.edu.br', 'alunos_tempo_especial': ''
            }
        ])
        df_fake.to_csv(bronze_csv, index=False)

        out_path, metricas = process_to_silver(bronze_csv, silver_dir, rejected_dir)
        assert metricas['linhas_silver'] == 1
        assert metricas['linhas_rejeitadas'] == 1
        assert os.path.exists(os.path.join(rejected_dir, "pedidos_provas_rejeitados.csv"))
