import os
import pandas as pd
from pipelines.run_pipeline_chamados import run_chamados_pipeline
from pipelines.run_pipeline_moodle import run_moodle_pipeline
from pipelines.run_pipeline_sharepoint import run_sharepoint_pipeline

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def test_integration_pipelines_execucao():
    data_teste = "2026-10-12"
    
    sucesso_moodle = run_moodle_pipeline(data_teste)
    assert sucesso_moodle is True

    sucesso_sharepoint = run_sharepoint_pipeline(data_teste)
    assert sucesso_sharepoint is True

    sucesso_chamados = run_chamados_pipeline(data_teste)
    assert sucesso_chamados is True

    # Valida geracao dos entregaveis Gold
    assert os.path.exists(os.path.join(PROJECT_ROOT, "data", "gold", "acoes_provas.json"))
    assert os.path.exists(os.path.join(PROJECT_ROOT, "data", "gold", "publicacao_documentos.csv"))
    assert os.path.exists(os.path.join(PROJECT_ROOT, "data", "gold", "triagem_chamados.csv"))

    # Valida presenca e integridade do log
    log_path = os.path.join(PROJECT_ROOT, "logs", "log_execucao.csv")
    assert os.path.exists(log_path)
    df_log = pd.read_csv(log_path)
    assert len(df_log) > 0
    assert (df_log['status'] == 'SUCESSO').all()
