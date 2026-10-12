import os
import tempfile
import pandas as pd
from src.sharepoint.gold import montar_destino_url, process_to_gold


def test_montar_destino_url_espacos_e_acentos():
    site = "https://share.acadops.edu.br/nutricao"
    pasta = "Documentos Acadêmicos"
    arquivo = "Plano de Ensino.pdf"
    url = montar_destino_url(site, pasta, arquivo)

    assert "Documentos%20Acad%C3%AAmicos" in url
    assert "Plano%20de%20Ensino.pdf" in url
    assert url.startswith("https://share.acadops.edu.br/nutricao/")


def test_process_to_gold_conciliacao_status():
    with tempfile.TemporaryDirectory() as tmpdir:
        silver_file = os.path.join(tmpdir, "sharepoint_silver.parquet")
        gold_dir = os.path.join(tmpdir, "gold")

        df = pd.DataFrame([
            {'id': 1, 'curso': 'Nutrição', 'arquivo': 'a.pdf', 'site_sharepoint': 'https://s.br/nut', 'pasta_documentos': 'docs', 'status': 'A publicar'},
            {'id': 2, 'curso': 'Nutrição', 'arquivo': 'b.pdf', 'site_sharepoint': 'https://s.br/nut', 'pasta_documentos': 'docs', 'status': 'Revisar'},
            {'id': 3, 'curso': 'Nutrição', 'arquivo': 'c.pdf', 'site_sharepoint': 'https://s.br/nut', 'pasta_documentos': 'docs', 'status': 'Publicado'}
        ])
        df.to_parquet(silver_file, index=False)

        out_path, metricas = process_to_gold(silver_file, gold_dir)
        assert metricas['linhas_saida'] == 2
        assert metricas['a_publicar'] == 1
        assert metricas['para_revisao'] == 1
        assert metricas['ja_publicados'] == 1
