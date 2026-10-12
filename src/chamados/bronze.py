import os
from datetime import datetime
from src.common.encoding import read_csv_with_fallback, corrigir_mojibake


def ingest_to_bronze(source_path, bronze_path, ingestion_date=None):
    """Copia os dados brutos de chamados, desfaz mojibake e salva particionado em UTF-8."""
    print("Iniciando Camada Bronze (Chamados)...")
    try:
        df = read_csv_with_fallback(source_path)

        for col in df.select_dtypes(include='object').columns:
            df[col] = df[col].apply(corrigir_mojibake)

        if not ingestion_date:
            ingestion_date = datetime.now().strftime('%Y-%m-%d')

        output_dir = os.path.join(bronze_path, f"ingestion_date={ingestion_date}")
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, "chamados_suporte.csv")
        df.to_csv(output_path, index=False, encoding='utf-8')

        metricas = {'linhas_entrada': len(df), 'ingestion_date': ingestion_date}
        print(f"-> Sucesso! {len(df)} linhas ingeridas e padronizadas para UTF-8.")
        return output_path, metricas
    except Exception as e:
        print(f"-> ERRO na camada Bronze (Chamados): {e}")
        raise
