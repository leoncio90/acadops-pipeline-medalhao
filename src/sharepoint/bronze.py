import pandas as pd
import os
from datetime import datetime

'''#Criei esta função para Ler os dados CSV tentando ler com a codificação
utf-8 e depois com latin-1. Pois os dados brutos estavam apresentando erro
no encoding de caracteres. Ex: Nutrição estava sendo apresentado como: NutriÃ§Ã£o.'''

def read_csv_with_fallback_encoding(path):

    try:
        return pd.read_csv(path, encoding='utf-8')
    except UnicodeDecodeError:
        print(f"INFO: Leitura com UTF-8 falhou para {os.path.basename(path)}. Tentando com latin-1.")
        return pd.read_csv(path, encoding='latin-1')


'''Só o fallback acima não fecha o problema. Ele resolve o arquivo que realmente é latin-1,
porque aí a leitura em UTF-8 levanta exceção. O caso do NutriÃ§Ã£o é diferente: o arquivo já é
UTF-8 válido e não gera erro nenhum, o texto simplesmente chega quebrado. Aqui eu detecto a
assinatura desse duplo encoding e desfaço.'''

def corrigir_mojibake(texto):

    if not isinstance(texto, str):
        return texto

    if 'Ã' not in texto and 'Â' not in texto:
        return texto

    try:
        return texto.encode('latin-1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        return texto


#esta função copia os dados brutos de SharePoint para a camada Bronze e corrige o encoding na leitura.
def ingest_to_bronze(pendencias_path, mapa_path, bronze_path, ingestion_date=None):

    print("Iniciando Camada Bronze (SharePoint)...")
    try:
        df_pendencias = read_csv_with_fallback_encoding(pendencias_path)
        df_mapa = read_csv_with_fallback_encoding(mapa_path)

        for df in (df_pendencias, df_mapa):
            for col in df.select_dtypes(include='object').columns:
                df[col] = df[col].apply(corrigir_mojibake)

        # A data de ingestão vira parâmetro para permitir reprocessamento de uma partição antiga
        if not ingestion_date:
            ingestion_date = datetime.now().strftime('%Y-%m-%d')

        # preparação diretórios de saída
        output_dir_pend = os.path.join(bronze_path, f"pendencias/ingestion_date={ingestion_date}")
        os.makedirs(output_dir_pend, exist_ok=True)
        pendencias_out = os.path.join(output_dir_pend, "pendencias_sharepoint.csv")

        output_dir_mapa = os.path.join(bronze_path, f"mapa/ingestion_date={ingestion_date}")
        os.makedirs(output_dir_mapa, exist_ok=True)
        mapa_out = os.path.join(output_dir_mapa, "mapa_sites_sharepoint.csv")

        # Salva no padrão UTF-8 para garantir a consistência dali para frente
        df_pendencias.to_csv(pendencias_out, index=False, encoding='utf-8')
        df_mapa.to_csv(mapa_out, index=False, encoding='utf-8')

        metricas = {'linhas_entrada': len(df_pendencias), 'ingestion_date': ingestion_date}

        print(f"-> Sucesso! {len(df_pendencias)} pendencia(s) e {len(df_mapa)} site(s) ingeridos em UTF-8.")
        return pendencias_out, mapa_out, metricas
    except Exception as e:
        print(f"-> ERRO na camada Bronze (SharePoint): {e}")
        return None, None, {}
