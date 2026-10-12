import os
import pandas as pd
from src.common.text import clean_text


def standardize_header(text) -> str:
    """Padroniza a opcao de cabecalho da prova a partir de texto normalizado."""
    texto_normalizado = clean_text(str(text))
    if 'sem cabecalho' in texto_normalizado:
        return 'nenhum'
    if 'com orientacoes' in texto_normalizado:
        return 'customizado'
    if 'padrao' in texto_normalizado:
        return 'padrao'
    return 'nao_identificado'


def process_to_silver(bronze_file_path: str, silver_path: str, rejected_path: str):
    """Limpa, valida e estrutura os dados das provas na camada Silver, quarentenando dados invalidos."""
    print("Iniciando Camada Silver (Moodle)...")
    try:
        df = pd.read_csv(bronze_file_path)
        linhas_entrada = len(df)
        rejeitados = []

        # 1. Campos obrigatorios ausentes
        obrigatorias = ['solicitacao_id', 'curso', 'modulo_codigo']
        sem_chave = df[df[obrigatorias].isna().any(axis=1)].copy()
        if not sem_chave.empty:
            sem_chave['motivo_rejeicao'] = 'campo obrigatorio ausente'
            rejeitados.append(sem_chave)
        df = df.dropna(subset=obrigatorias).copy()

        # 2. Validacao de solicitacao_id numerico seguro (sem quebrar no astype)
        df['solicitacao_id_num'] = pd.to_numeric(df['solicitacao_id'], errors='coerce')
        id_invalido = df[df['solicitacao_id_num'].isna() | (df['solicitacao_id_num'] <= 0)].copy()
        if not id_invalido.empty:
            id_invalido['motivo_rejeicao'] = 'solicitacao_id invalido'
            rejeitados.append(id_invalido)
        df = df[df['solicitacao_id_num'].notna() & (df['solicitacao_id_num'] > 0)].copy()
        df['solicitacao_id'] = df['solicitacao_id_num'].astype(int)
        df.drop(columns=['solicitacao_id_num'], inplace=True)

        # 3. Data da prova valida
        df['data_prova'] = pd.to_datetime(df['data_prova'], errors='coerce')
        data_invalida = df[df['data_prova'].isna()].copy()
        if not data_invalida.empty:
            data_invalida['motivo_rejeicao'] = 'data_prova invalida'
            rejeitados.append(data_invalida)
        df = df.dropna(subset=['data_prova']).copy()

        # 4. Deduplicacao por solicitacao_id mantendo o ultimo
        duplicadas = df[df.duplicated(subset=['solicitacao_id'], keep='last')].copy()
        if not duplicadas.empty:
            duplicadas['motivo_rejeicao'] = 'solicitacao_id duplicado'
            rejeitados.append(duplicadas)
        df = df.drop_duplicates(subset=['solicitacao_id'], keep='last').copy()

        # 5. Cabecalho padronizado
        df['cabecalho_padronizado'] = df['cabecalho'].apply(standardize_header)

        # 6. E-mail do professor
        df['professor_email'] = df['professor_email'].astype(str).str.strip().str.lower()
        email_valido = df['professor_email'].str.match(r'^[^@\s]+@[^@\s]+\.[a-z]{2,}$', na=False)
        email_invalido = df[~email_valido].copy()
        if not email_invalido.empty:
            email_invalido['motivo_rejeicao'] = 'professor_email invalido'
            rejeitados.append(email_invalido)
        df = df[email_valido].copy()

        os.makedirs(silver_path, exist_ok=True)
        output_path = os.path.join(silver_path, "pedidos_provas_silver.parquet")
        df.to_parquet(output_path, index=False)

        linhas_rejeitadas = 0
        if rejeitados:
            df_rejeitados = pd.concat(rejeitados, ignore_index=True)
            linhas_rejeitadas = len(df_rejeitados)
            os.makedirs(rejected_path, exist_ok=True)
            df_rejeitados.to_csv(
                os.path.join(rejected_path, "pedidos_provas_rejeitados.csv"),
                index=False,
                encoding='utf-8-sig'
            )
            print(f"-> ATENCAO: {linhas_rejeitadas} linha(s) em quarentena. Ver {rejected_path}")

        metricas = {'linhas_silver': len(df), 'linhas_rejeitadas': linhas_rejeitadas}
        print(f"-> Sucesso! {linhas_entrada} linha(s) na entrada, {len(df)} aprovada(s) em: {output_path}")
        return output_path, metricas
    except Exception as e:
        print(f"-> ERRO na camada Silver (Moodle): {e}")
        raise
