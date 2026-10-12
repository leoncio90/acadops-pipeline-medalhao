import os
from datetime import datetime
from src.common.encoding import read_csv_with_fallback, corrigir_mojibake


def ingest_to_bronze(pendencias_path, mapa_path, bronze_path, ingestion_date=None):
    """Copia dados brutos de SharePoint para a camada Bronze tratando encoding."""
    print("Iniciando Camada Bronze (SharePoint)...")
    try:
        df_pendencias = read_csv_with_fallback(pendencias_path)
        df_mapa = read_csv_with_fallback(mapa_path)

        for df in (df_pendencias, df_mapa):
            for col in df.select_dtypes(include='object').columns:
                df[col] = df[col].apply(corrigir_mojibake)

        if not ingestion_date:
            ingestion_date = datetime.now().strftime('%Y-%m-%d')

        output_dir_pend = os.path.join(bronze_path, f"pendencias/ingestion_date={ingestion_date}")
        os.makedirs(output_dir_pend, exist_ok=True)
        pendencias_out = os.path.join(output_dir_pend, "pendencias_sharepoint.csv")

        output_dir_mapa = os.path.join(bronze_path, f"mapa/ingestion_date={ingestion_date}")
        os.makedirs(output_dir_mapa, exist_ok=True)
        mapa_out = os.path.join(output_dir_mapa, "mapa_sites_sharepoint.csv")

        df_pendencias.to_csv(pendencias_out, index=False, encoding='utf-8')
        df_mapa.to_csv(mapa_out, index=False, encoding='utf-8')

        metricas = {'linhas_entrada': len(df_pendencias), 'ingestion_date': ingestion_date}
        print(f"-> Sucesso! {len(df_pendencias)} pendencia(s) e {len(df_mapa)} site(s) ingeridos em UTF-8.")
        return pendencias_out, mapa_out, metricas
    except Exception as e:
        print(f"-> ERRO na camada Bronze (SharePoint): {e}")
        raise
