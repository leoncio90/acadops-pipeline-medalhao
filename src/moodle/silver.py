import pandas as pd
import os
import re
from unidecode import unidecode


# Esta etapa limpa, valida e estrutura os dados das provas na camada Silver.

def process_to_silver(bronze_file_path, silver_path, rejected_path):
    print("Iniciando Camada Silver (Moodle)...")
    try:
        df = pd.read_csv(bronze_file_path)
        linhas_entrada = len(df)
        rejeitados = []

        # Em vez de descartar em silêncio, separo o que sai e por qual motivo
        obrigatorias = ['solicitacao_id', 'curso', 'modulo_codigo']
        sem_chave = df[df[obrigatorias].isna().any(axis=1)].copy()
        if not sem_chave.empty:
            sem_chave['motivo_rejeicao'] = 'campo obrigatorio ausente'
            rejeitados.append(sem_chave)
        df = df.dropna(subset=obrigatorias)

        df['solicitacao_id'] = df['solicitacao_id'].astype(int)

        df['data_prova'] = pd.to_datetime(df['data_prova'], errors='coerce')
        data_invalida = df[df['data_prova'].isna()].copy()
        if not data_invalida.empty:
            data_invalida['motivo_rejeicao'] = 'data_prova invalida'
            rejeitados.append(data_invalida)
        df = df.dropna(subset=['data_prova'])

        # A mesma solicitação chegando duas vezes geraria duas provas no Moodle, então mantenho a última
        duplicadas = df[df.duplicated(subset=['solicitacao_id'], keep='last')].copy()
        if not duplicadas.empty:
            duplicadas['motivo_rejeicao'] = 'solicitacao_id duplicado'
            rejeitados.append(duplicadas)
        df = df.drop_duplicates(subset=['solicitacao_id'], keep='last')

        '''Antes eu comparava o texto do cabeçalho com acento. Se o encoding chegasse quebrado,
        nenhuma condição casava e tudo caía no "padrao" sem ninguém perceber. Agora normalizo
        o texto antes de comparar e devolvo "nao_identificado" quando não reconheço o valor,
        para o problema aparecer no lugar de virar configuração errada de prova.'''

        def standardize_header(text):
            texto_normalizado = unidecode(str(text)).lower().strip()
            if 'sem cabecalho' in texto_normalizado:
                return 'nenhum'
            if 'com orientacoes' in texto_normalizado:
                return 'customizado'
            if 'padrao' in texto_normalizado:
                return 'padrao'
            return 'nao_identificado'

        df['cabecalho_padronizado'] = df['cabecalho'].apply(standardize_header)

        df['professor_email'] = df['professor_email'].str.strip().str.lower()

        # Sem e-mail válido não há como notificar o professor, então isso também é rejeição
        email_valido = df['professor_email'].str.match(r'^[^@\s]+@[^@\s]+\.[a-z]{2,}$', na=False)
        email_invalido = df[~email_valido].copy()
        if not email_invalido.empty:
            email_invalido['motivo_rejeicao'] = 'professor_email invalido'
            rejeitados.append(email_invalido)
        df = df[email_valido]

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
        return None, {}
