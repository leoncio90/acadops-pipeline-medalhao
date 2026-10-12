import os
import re
import pandas as pd
from src.common.text import clean_text


def correct_common_errors(text: str) -> str:
    """Corrige erros comuns de digitacao de sistemas usando fronteira de palavra."""
    if not isinstance(text, str):
        return ""

    corrections = {
        'share point': 'sharepoint',
        'lyceun': 'lyceum',
        'moodl': 'moodle',
    }

    for wrong, right in corrections.items():
        text = re.sub(rf'\b{re.escape(wrong)}\b', right, text)

    return text


def process_to_silver(bronze_file_path: str, silver_path: str, rejected_path: str):
    """Limpa, normaliza e enriquece os chamados, salvando em Silver Parquet e quarentena."""
    print("Iniciando Camada Silver (Chamados)...")
    try:
        df = pd.read_csv(bronze_file_path)
        linhas_entrada = len(df)

        for col in ['titulo', 'descricao']:
            df[col + '_clean'] = df[col].apply(clean_text).apply(correct_common_errors)

        df['data_abertura'] = pd.to_datetime(df['data_abertura'], errors='coerce')

        data_invalida = df[df['data_abertura'].isna()].copy()
        if not data_invalida.empty:
            data_invalida['motivo_rejeicao'] = 'data_abertura invalida'
            os.makedirs(rejected_path, exist_ok=True)
            data_invalida.to_csv(
                os.path.join(rejected_path, "chamados_rejeitados.csv"),
                index=False,
                encoding='utf-8-sig'
            )
            print(f"-> ATENCAO: {len(data_invalida)} chamado(s) em quarentena. Ver {rejected_path}")

        df.dropna(subset=['data_abertura'], inplace=True)

        df['texto_completo'] = df['titulo_clean'] + ' ' + df['descricao_clean']
        df['chave_conteudo'] = df['texto_completo'] + '|' + df['data_abertura'].dt.strftime('%Y-%m-%d')

        silver_df = df[['id', 'titulo', 'descricao', 'texto_completo', 'chave_conteudo', 'origem', 'prioridade', 'data_abertura']]

        os.makedirs(silver_path, exist_ok=True)
        output_path = os.path.join(silver_path, "chamados_suporte_silver.parquet")
        silver_df.to_parquet(output_path, index=False)

        metricas = {'linhas_silver': len(silver_df), 'linhas_rejeitadas': len(data_invalida)}
        print(f"-> Sucesso! {linhas_entrada} chamado(s) na entrada, {len(silver_df)} limpo(s) em: {output_path}")
        return output_path, metricas
    except Exception as e:
        print(f"-> ERRO na camada Silver (Chamados): {e}")
        raise
