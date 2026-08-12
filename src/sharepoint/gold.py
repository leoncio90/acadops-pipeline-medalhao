import pandas as pd
import os
from urllib.parse import quote, urlsplit, urlunsplit


# nesta etapa eu filtro e gero a lista final de documentos para publicação e garanto a codificação correta na saída

# A URL era montada por concatenação simples, então "Documentos Acadêmicos" entrava com espaço e
# acento e o endereço final não era válido. Aqui eu monto o caminho e aplico o percent-encoding.
def montar_destino_url(site_sharepoint, pasta_documentos, arquivo):

    partes = urlsplit(str(site_sharepoint).strip().rstrip('/'))
    caminho = '/'.join([
        partes.path.strip('/'),
        str(pasta_documentos).strip('/'),
        str(arquivo).strip()
    ])

    return urlunsplit((partes.scheme, partes.netloc, '/' + quote(caminho, safe='/'), '', ''))


# Antes "A publicar" e "Revisar" recebiam o mesmo novo_status Publicado, ou seja, documento
# pendente de revisão era publicado junto. Agora cada status de origem tem sua própria ação.
REGRAS_STATUS = {
    'A publicar': {'acao': 'publicar', 'novo_status': 'Publicado'},
    'Revisar': {'acao': 'enviar_para_revisao', 'novo_status': 'Em revisão'}
}

COLUNAS_SAIDA = ['id', 'curso', 'arquivo', 'destino_url', 'status_origem', 'acao', 'novo_status']


def process_to_gold(silver_file_path, gold_path):
    print("Iniciando Camada Gold (SharePoint)...")
    try:
        df = pd.read_parquet(silver_file_path)

        df_para_publicar = df[df['status'].isin(REGRAS_STATUS.keys())].copy()

        os.makedirs(gold_path, exist_ok=True)
        output_path = os.path.join(gold_path, "publicacao_documentos.csv")

        # Verifica se há dados para processar
        if df_para_publicar.empty:
            print("-> INFO: Nenhum documento para publicar ou revisar.")
            # Cria um arquivo vazio para indicar que o pipeline rodou com sucesso
            pd.DataFrame(columns=COLUNAS_SAIDA).to_csv(
                output_path,
                index=False,
                encoding='utf-8-sig' #deixo a codificação explicita aqui para forçar o salvamento nesta configuração
            )
            return output_path, {'linhas_saida': 0, 'a_publicar': 0, 'para_revisao': 0}

        df_para_publicar['destino_url'] = df_para_publicar.apply(
            lambda row: montar_destino_url(row['site_sharepoint'], row['pasta_documentos'], row['arquivo']),
            axis=1
        )

        df_para_publicar['status_origem'] = df_para_publicar['status']
        df_para_publicar['acao'] = df_para_publicar['status'].map(lambda s: REGRAS_STATUS[s]['acao'])
        df_para_publicar['novo_status'] = df_para_publicar['status'].map(lambda s: REGRAS_STATUS[s]['novo_status'])

        output_df = df_para_publicar[COLUNAS_SAIDA]

        # Salvo CSV final com a codificação 'utf-8-sig'. Isso ajuda o Excel a entender que o arquivo é UTF-8.
        output_df.to_csv(output_path, index=False, encoding='utf-8-sig')

        metricas = {
            'linhas_saida': len(output_df),
            'a_publicar': int((output_df['acao'] == 'publicar').sum()),
            'para_revisao': int((output_df['acao'] == 'enviar_para_revisao').sum())
        }

        print(f"-> Sucesso! {metricas['a_publicar']} para publicar e {metricas['para_revisao']} para revisao em: {output_path}")
        return output_path, metricas
    except Exception as e:
        print(f"-> ERRO na camada Gold (SharePoint): {e}")
        return None, {}
