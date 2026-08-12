import pandas as pd
import os
import re

from src.chamados.silver import clean_text

# nesta etapa Aplico regras de negócio para triar chamados e salvo a saída no formato padronizado."""

'''Aqui estava o erro mais silencioso do projeto. A Silver remove a pontuação, então "e-mail" chega
como "email", mas a regra continuava procurando por "e-mail" com hífen: seis chamados de e-mail
institucional caíam no Suporte N1 em vez de ir para Infraestrutura. Agora passo o próprio vocabulário
pelo clean_text, garantindo que regra e dado sejam normalizados pela mesma função.'''

'''O segundo ajuste é a forma de comparar. A busca era por substring, então "ava" casaria dentro de
"avaliação" e "rede" dentro de "credenciais". Passei a usar fronteira de palavra com plural opcional,
que mantém "provas" casando com "prova" sem casar no meio de outra palavra.'''

REGRAS_TRIAGEM = [
    ('Equipe AVA', ['moodle', 'ava', 'prova', 'questionario', 'turma espelho', 'tempo especial']),
    ('Equipe Sistemas Internos', ['sharepoint', 'intranet']),
    ('Equipe Sistemas Acadêmicos', ['lyceum', 'academico', 'boleto', 'matricula']),
    ('Equipe Infraestrutura', ['e-mail', 'login', 'sso', 'rede', 'vpn', 'credencial']),
    ('Equipe Business Intelligence', ['bi', 'relatorio', 'painel', 'dashboard'])
]

EQUIPE_PADRAO = 'Suporte N1 (Geral)'


def triar_chamado(texto):

    for equipe, palavras_chave in REGRAS_TRIAGEM:
        for palavra in palavras_chave:
            termo = clean_text(palavra)
            if re.search(rf'\b{re.escape(termo)}s?\b', texto):
                return equipe, termo

    return EQUIPE_PADRAO, 'nenhuma'


def process_to_gold(silver_file_path, gold_path):

    print("Iniciando Camada Gold (Chamados)...")
    try:
        df = pd.read_parquet(silver_file_path)

        triagem = df['texto_completo'].apply(triar_chamado)
        df['equipe_responsavel'] = triagem.apply(lambda x: x[0])
        df['regra_acionada'] = triagem.apply(lambda x: x[1])

        # Os mesmos chamados chegam por canais diferentes (Teams, Email, Formulário). Não apago
        # nenhum, apenas sinalizo o grupo e aponto o id mais antigo para o atendente consolidar.
        df['id_referencia'] = df.groupby('chave_conteudo')['id'].transform('min')
        df['possivel_duplicata'] = (df['id'] != df['id_referencia']).map({True: 'S', False: 'N'})

        output_df = df[['id', 'titulo', 'descricao', 'origem', 'prioridade', 'data_abertura',
                        'equipe_responsavel', 'regra_acionada', 'possivel_duplicata', 'id_referencia']]

        os.makedirs(gold_path, exist_ok=True)
        output_path = os.path.join(gold_path, "triagem_chamados.csv")

        # Padrão de escrita para CSVs finais
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
        return None, {}
