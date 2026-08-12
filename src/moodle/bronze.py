import pandas as pd
import os
from datetime import datetime


'''Criei esta função porque o fallback de encoding sozinho não resolve tudo.
Quando o arquivo é latin-1 de verdade, a leitura em UTF-8 estoura e o fallback entra.
Mas quando o arquivo já é UTF-8 e foi salvo por um editor que leu como latin-1,
não há exceção nenhuma: o texto chega quebrado (Nutrição -> NutriÃ§Ã£o) e passa silencioso.
Aqui eu detecto a assinatura desse duplo encoding e desfaço a conversão.'''

def corrigir_mojibake(texto):

    if not isinstance(texto, str):
        return texto

    if 'Ã' not in texto and 'Â' not in texto:
        return texto

    try:
        return texto.encode('latin-1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        return texto


# Esta função irá copiar os dados brutos de pedidos de prova para a camada Bronze e trata o encoding na leitura.

def ingest_to_bronze(source_path, bronze_path, ingestion_date=None):
    print("Iniciando Camada Bronze (Moodle)...")
    try:
        try:
            df = pd.read_csv(source_path, encoding='utf-8')
        except UnicodeDecodeError:
            print(f"INFO: Leitura com UTF-8 falhou para {os.path.basename(source_path)}. Tentando com latin-1.")
            df = pd.read_csv(source_path, encoding='latin-1')

        # Aplico a correção de mojibake em todas as colunas de texto
        for col in df.select_dtypes(include='object').columns:
            df[col] = df[col].apply(corrigir_mojibake)

        # A data de ingestão vira parâmetro para permitir reprocessamento de uma partição antiga
        if not ingestion_date:
            ingestion_date = datetime.now().strftime('%Y-%m-%d')

        output_dir = os.path.join(bronze_path, f"ingestion_date={ingestion_date}")
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, "pedidos_provas.csv")

        # aqui também salvo no padrão UTF-8 para garantir a consistência
        df.to_csv(output_path, index=False, encoding='utf-8')

        metricas = {'linhas_entrada': len(df), 'ingestion_date': ingestion_date}

        print(f"-> Sucesso! {len(df)} linhas ingeridas e padronizadas para UTF-8.")
        return output_path, metricas
    except Exception as e:
        print(f"-> ERRO na camada Bronze (Moodle): {e}")
        return None, {}
