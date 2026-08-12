import pandas as pd
import os
from datetime import datetime

# Nesta etapa é realizada a Cópia os dados brutos de chamados e trata o encoding na leitura.

'''O fallback de encoding cobre o arquivo que é latin-1 de verdade, porque nesse caso a leitura em
UTF-8 levanta exceção. O caso do NutriÃ§Ã£o não levanta nada: o arquivo já é UTF-8 válido e o texto
apenas chega quebrado. Então detecto a assinatura do duplo encoding e desfaço.'''

def corrigir_mojibake(texto):

    if not isinstance(texto, str):
        return texto

    if 'Ã' not in texto and 'Â' not in texto:
        return texto

    try:
        return texto.encode('latin-1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        return texto


def ingest_to_bronze(source_path, bronze_path, ingestion_date=None):

    print("Iniciando Camada Bronze (Chamados)...")
    try:
        try:
            df = pd.read_csv(source_path, encoding='utf-8')
        except UnicodeDecodeError:
            print(f"INFO: Leitura com UTF-8 falhou para {os.path.basename(source_path)}. Tentando com latin-1.")
            df = pd.read_csv(source_path, encoding='latin-1')

        for col in df.select_dtypes(include='object').columns:
            df[col] = df[col].apply(corrigir_mojibake)

        # A data de ingestão vira parâmetro para permitir reprocessamento de uma partição antiga
        if not ingestion_date:
            ingestion_date = datetime.now().strftime('%Y-%m-%d')

        output_dir = os.path.join(bronze_path, f"ingestion_date={ingestion_date}")
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, "chamados_suporte.csv")
        # Salva no padrão UTF-8
        df.to_csv(output_path, index=False, encoding='utf-8')

        metricas = {'linhas_entrada': len(df), 'ingestion_date': ingestion_date}

        print(f"-> Sucesso! {len(df)} linhas ingeridas e padronizadas para UTF-8.")
        return output_path, metricas
    except Exception as e:
        print(f"-> ERRO na camada Bronze (Chamados): {e}")
        return None, {}
