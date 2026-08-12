import pandas as pd
import json
import os
import re

'''Esta etapa irá gerar o arquivo JSON final (acoes_provas.json) para consumo. Visto que o entregável
SharePoint exigiu ajuste de codificação utf-8, como boa prática também ajustei em todos os pipelines.'''

'''O campo alunos_tempo_especial vem como texto livre (ID2372:50%;ID8566:25%). Antes um valor
malformado derrubava o pipeline inteiro no int() e um trecho sem ":" era descartado calado.
Agora cada aluno é validado isoladamente: o que estiver fora do padrão vai para o relatório de
inconsistências e as demais provas continuam sendo geradas.'''

def parse_tempo_especial(valor, id_solicitacao):

    alunos = []
    inconsistencias = []

    if pd.isna(valor) or str(valor).strip() == '':
        return alunos, inconsistencias

    for parte in str(valor).split(';'):
        parte = parte.strip()
        if not parte:
            continue

        match = re.fullmatch(r'(?P<aluno>[A-Za-z0-9_.-]+)\s*:\s*(?P<percentual>\d{1,3})\s*%?', parte)
        if not match:
            inconsistencias.append({
                'id_solicitacao': id_solicitacao,
                'valor_original': parte,
                'motivo': 'formato esperado aluno:percentual'
            })
            continue

        percentual = int(match.group('percentual'))
        if percentual < 1 or percentual > 100:
            inconsistencias.append({
                'id_solicitacao': id_solicitacao,
                'valor_original': parte,
                'motivo': 'percentual fora da faixa de 1 a 100'
            })
            continue

        alunos.append({
            "aluno_id": match.group('aluno').strip(),
            "acrescimo_percentual": percentual
        })

    return alunos, inconsistencias


def process_to_gold(silver_file_path, gold_path, rejected_path):

    print("Iniciando Camada Gold (Moodle)...")
    try:
        df = pd.read_parquet(silver_file_path)
        acoes_provas = []
        inconsistencias = []

        for _, row in df.iterrows():
            alunos_especiais, erros = parse_tempo_especial(row['alunos_tempo_especial'], row['solicitacao_id'])
            inconsistencias.extend(erros)

            acao = {
                "id_solicitacao": int(row['solicitacao_id']), "curso": row['curso'],
                "modulo": row['modulo_codigo'], "tipo_prova": row['tipo_prova'],
                "data_prova": row['data_prova'].strftime('%Y-%m-%d'),
                "configuracao": {
                    "cabecalho": row['cabecalho_padronizado'],
                    "tempo_especial_alunos": alunos_especiais
                },
                "notificar_professor": row['professor_email']
            }
            acoes_provas.append(acao)

        os.makedirs(gold_path, exist_ok=True)
        output_path = os.path.join(gold_path, "acoes_provas.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(acoes_provas, f, indent=4, ensure_ascii=False)

        if inconsistencias:
            os.makedirs(rejected_path, exist_ok=True)
            pd.DataFrame(inconsistencias).to_csv(
                os.path.join(rejected_path, "tempo_especial_inconsistente.csv"),
                index=False,
                encoding='utf-8-sig'
            )
            print(f"-> ATENCAO: {len(inconsistencias)} configuracao(oes) de tempo especial ignorada(s).")

        metricas = {'linhas_saida': len(acoes_provas), 'inconsistencias': len(inconsistencias)}

        print(f"-> Sucesso! {len(acoes_provas)} acao(oes) geradas em: {output_path}")
        return output_path, metricas
    except Exception as e:
        print(f"-> ERRO na camada Gold (Moodle): {e}")
        return None, {}
