import pandas as pd
import os
import re
from unidecode import unidecode

''' Visto que este pipeline de chamados trata de textos grandes, iremos realizar um tratamento mais minucioso.
esta função irá limpar e normalizar as strings: Converte para minúsculas, remove acentos (ex: 'ação' -> 'acao'),
remove caracteres que não são letras, números ou espaços e remove espaços extras.'''

def clean_text(text: str) -> str:
    if not isinstance(text, str): return ""
    text = text.lower()
    text = unidecode(text)
    text = re.sub(r'[^a-z0-9\s]', '', text) 
    text = re.sub(r'\s+', ' ', text).strip()
    return text

'''Corrige erros de digitação ou variações comuns nos nomes de sistemas.
O replace direto tinha um efeito colateral grave: a correção 'moodl' -> 'moodle' também atingia
a palavra correta e transformava "moodle" em "moodlee" em todos os chamados. Troquei por
substituição com fronteira de palavra, que só corrige o termo isolado e não mexe no que já está certo.'''
def correct_common_errors(text: str) -> str:    
    if not isinstance(text, str):
        return ""

    # Dicionário de correções
    corrections = {
        'share point': 'sharepoint',
        'lyceun': 'lyceum',
        'moodl': 'moodle',
        }

    for wrong, right in corrections.items():
        text = re.sub(rf'\b{re.escape(wrong)}\b', right, text)
    
    return text


''' aqui irá os dados brutos da camada Bronze, limpar, normalizar e salvar 
o resultado na camada Silver como um arquivo Parquet.'''
    
def process_to_silver(bronze_file_path: str, silver_path: str, rejected_path: str) -> str:
    
    print("Iniciando Camada Silver (Chamados)...")
    try:
        # Lê o arquivo CSV já padronizado como UTF-8 pela camada Bronze
        df = pd.read_csv(bronze_file_path)
        linhas_entrada = len(df)

        # Aplica a limpeza e correção nas colunas de texto
        for col in ['titulo', 'descricao']:
            # Cria colunas limpas separadas para manter o original se necessário
            df[col + '_clean'] = df[col].apply(clean_text).apply(correct_common_errors)

        # Garante a tipagem correta da data, descartando registros com data inválida
        df['data_abertura'] = pd.to_datetime(df['data_abertura'], errors='coerce')

        # O descarte agora deixa rastro em arquivo, para não perder chamado sem ninguém saber
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

        #  Enriquece os dados criando um campo de texto unificado para análise
        df['texto_completo'] = df['titulo_clean'] + ' ' + df['descricao_clean']

        # Crio a chave de conteúdo aqui para a camada Gold poder sinalizar chamado repetido
        df['chave_conteudo'] = df['texto_completo'] + '|' + df['data_abertura'].dt.strftime('%Y-%m-%d')

        #  Seleciona as colunas que serão úteis para a camada Gold.
        silver_df = df[['id', 'titulo', 'descricao', 'texto_completo', 'chave_conteudo', 'origem', 'prioridade', 'data_abertura']]

        os.makedirs(silver_path, exist_ok=True)
        output_path = os.path.join(silver_path, "chamados_suporte_silver.parquet")
        silver_df.to_parquet(output_path, index=False)

        metricas = {'linhas_silver': len(silver_df), 'linhas_rejeitadas': len(data_invalida)}

        print(f"-> Sucesso! {linhas_entrada} chamado(s) na entrada, {len(silver_df)} limpo(s) em: {output_path}")
        return output_path, metricas
    except Exception as e:
        print(f"-> ERRO na camada Silver (Chamados): {e}")
        return None, {}
