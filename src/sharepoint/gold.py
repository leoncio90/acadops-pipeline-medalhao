import os
from urllib.parse import quote, urlsplit, urlunsplit
import pandas as pd


def montar_destino_url(site_sharepoint, pasta_documentos, arquivo):
    """Monto o caminho de destino aplicando percent-encoding correto nas partes do caminho."""
    partes = urlsplit(str(site_sharepoint).strip().rstrip('/'))
    caminho = '/'.join([
        partes.path.strip('/'),
        str(pasta_documentos).strip('/'),
        str(arquivo).strip()
    ])

    return urlunsplit((partes.scheme, partes.netloc, '/' + quote(caminho, safe='/'), '', ''))


REGRAS_STATUS = {
    'A publicar': {'acao': 'publicar', 'novo_status': 'Publicado'},
    'Revisar': {'acao': 'enviar_para_revisao', 'novo_status': 'Em revisão'}
}

COLUNAS_SAIDA = ['id', 'curso', 'arquivo', 'destino_url', 'status_origem', 'acao', 'novo_status']


def process_to_gold(silver_file_path: str, gold_path: str):
    """Gera entregavel final de publicacao de documentos conciliando status operacionais."""
    print("Iniciando Camada Gold (SharePoint)...")
    try:
        df = pd.read_parquet(silver_file_path)

        df_para_publicar = df[df['status'].isin(REGRAS_STATUS.keys())].copy()
        ja_publicados = int((df['status'] == 'Publicado').sum())

        os.makedirs(gold_path, exist_ok=True)
        output_path = os.path.join(gold_path, "publicacao_documentos.csv")

        if df_para_publicar.empty:
            print("-> INFO: Nenhum documento para publicar ou revisar.")
            pd.DataFrame(columns=COLUNAS_SAIDA).to_csv(
                output_path,
                index=False,
                encoding='utf-8-sig'
            )
            return output_path, {'linhas_saida': 0, 'a_publicar': 0, 'para_revisao': 0, 'ja_publicados': ja_publicados}

        df_para_publicar['destino_url'] = df_para_publicar.apply(
            lambda row: montar_destino_url(row['site_sharepoint'], row['pasta_documentos'], row['arquivo']),
            axis=1
        )

        df_para_publicar['status_origem'] = df_para_publicar['status']
        df_para_publicar['acao'] = df_para_publicar['status'].map(lambda s: REGRAS_STATUS[s]['acao'])
        df_para_publicar['novo_status'] = df_para_publicar['status'].map(lambda s: REGRAS_STATUS[s]['novo_status'])

        output_df = df_para_publicar[COLUNAS_SAIDA]
        output_df.to_csv(output_path, index=False, encoding='utf-8-sig')

        metricas = {
            'linhas_saida': len(output_df),
            'a_publicar': int((output_df['acao'] == 'publicar').sum()),
            'para_revisao': int((output_df['acao'] == 'enviar_para_revisao').sum()),
            'ja_publicados': ja_publicados
        }

        print(f"-> Sucesso! {metricas['a_publicar']} para publicar, {metricas['para_revisao']} para revisao e {ja_publicados} ja publicado(s) em: {output_path}")
        return output_path, metricas
    except Exception as e:
        print(f"-> ERRO na camada Gold (SharePoint): {e}")
        raise
