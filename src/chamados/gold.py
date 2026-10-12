import os
import re
import pandas as pd
from src.common.text import clean_text

REGRAS_TRIAGEM = [
    ('Equipe AVA', ['moodle', 'ava', 'prova', 'questionario', 'turma espelho', 'tempo especial']),
    ('Equipe Sistemas Internos', ['sharepoint', 'intranet']),
    ('Equipe Sistemas Acadêmicos', ['lyceum', 'academico', 'boleto', 'matricula']),
    ('Equipe Infraestrutura', ['e-mail', 'login', 'sso', 'rede', 'vpn', 'credencial']),
    ('Equipe Business Intelligence', ['bi', 'relatorio', 'painel', 'dashboard'])
]

EQUIPE_PADRAO = 'Suporte N1 (Geral)'


def triar_chamado(texto: str):
    """Classifica chamado por vocabulario controlado normalizado com fronteira de palavra."""
    for equipe, palavras_chave in REGRAS_TRIAGEM:
        for palavra in palavras_chave:
            termo = clean_text(palavra)
            if re.search(rf'\b{re.escape(termo)}s?\b', texto):
                return equipe, termo

    return EQUIPE_PADRAO, 'nenhuma'


def process_to_gold(silver_file_path: str, gold_path: str):
    """Aplica triagem de equipe, detecta duplicatas e gera o entregavel final de chamados."""
    print("Iniciando Camada Gold (Chamados)...")
    try:
        df = pd.read_parquet(silver_file_path)

        triagem = df['texto_completo'].apply(triar_chamado)
        df['equipe_responsavel'] = triagem.apply(lambda x: x[0])
        df['regra_acionada'] = triagem.apply(lambda x: x[1])

        df['id_referencia'] = df.groupby('chave_conteudo')['id'].transform('min')
        df['possivel_duplicata'] = (df['id'] != df['id_referencia']).map({True: 'S', False: 'N'})

        output_df = df[['id', 'titulo', 'descricao', 'origem', 'prioridade', 'data_abertura',
                        'equipe_responsavel', 'regra_acionada', 'possivel_duplicata', 'id_referencia']]

        os.makedirs(gold_path, exist_ok=True)
        output_path = os.path.join(gold_path, "triagem_chamados.csv")
        output_df.to_csv(output_path, index=False, encoding='utf-8-sig')

        metricas = {
            'linhas_saida': len(output_df),
            'sem_equipe_definida': int((output_df['equipe_responsavel'] == EQUIPE_PADRAO).sum()),
            'possiveis_duplicatas': int((output_df['possivel_duplicata'] == 'S').sum())
        }

        print(f"-> Sucesso! Arquivo de triagem gerado em: {output_path} com encoding UTF-8-SIG.")
        print(f"-> {metricas['sem_equipe_definida']} chamado(s) sem equipe definida e {metricas['possiveis_duplicatas']} possivel(is) duplicata(s).")
        return output_path, metricas
    except Exception as e:
        print(f"-> ERRO na camada Gold (Chamados): {e}")
        raise
