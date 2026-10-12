import os
import pandas as pd
from src.common.text import clean_text


def process_to_silver(pendencias_path, mapa_path, silver_path, rejected_path):
    """Limpa e relaciona as pendencias do SharePoint com os sites mapeados."""
    print("Iniciando Camada Silver (SharePoint)...")
    try:
        df_pendencias = pd.read_csv(pendencias_path)
        df_mapa = pd.read_csv(mapa_path)
        linhas_entrada = len(df_pendencias)

        for df in (df_pendencias, df_mapa):
            df['curso_chave'] = df['curso'].astype(str).apply(clean_text)

        df_mapa_dedup = df_mapa.drop_duplicates(subset=['curso_chave'], keep='first')

        df_merged = pd.merge(
            df_pendencias,
            df_mapa_dedup.drop(columns=['curso']),
            on='curso_chave',
            how='left'
        )

        sem_site = df_merged[df_merged['site_sharepoint'].isna()].copy()
        if not sem_site.empty:
            sem_site['motivo_rejeicao'] = 'curso sem site mapeado'
            os.makedirs(rejected_path, exist_ok=True)
            sem_site.to_csv(
                os.path.join(rejected_path, "sharepoint_sem_mapeamento.csv"),
                index=False,
                encoding='utf-8-sig'
            )
            print(f"-> ATENCAO: {len(sem_site)} documento(s) sem site mapeado. Ver {rejected_path}")

        df_merged = df_merged.dropna(subset=['site_sharepoint']).copy()
        df_merged = df_merged.drop(columns=['curso_chave'])

        os.makedirs(silver_path, exist_ok=True)
        output_path = os.path.join(silver_path, "sharepoint_consolidado_silver.parquet")
        df_merged.to_parquet(output_path, index=False)

        metricas = {'linhas_silver': len(df_merged), 'linhas_rejeitadas': len(sem_site)}
        print(f"-> Sucesso! {linhas_entrada} linha(s) na entrada, {len(df_merged)} consolidada(s) em: {output_path}")
        return output_path, metricas
    except Exception as e:
        print(f"-> ERRO na camada Silver (SharePoint): {e}")
        raise
