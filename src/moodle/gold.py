import json
import os
import re
import pandas as pd


def parse_tempo_especial(valor, id_solicitacao):
    """Extrai configuracoes de alunos com tempo especial e valida formato e faixa percentual."""
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


def process_to_gold(silver_file_path: str, gold_path: str, rejected_path: str):
    """Gera o arquivo JSON final (acoes_provas.json) e isola tempo especial inconsistente."""
    print("Iniciando Camada Gold (Moodle)...")
    try:
        df = pd.read_parquet(silver_file_path)
        acoes_provas = []
        inconsistencias = []

        # Itera via dicionarios em vez do custoso df.iterrows()
        for row in df.to_dict('records'):
            alunos_especiais, erros = parse_tempo_especial(row.get('alunos_tempo_especial'), row['solicitacao_id'])
            inconsistencias.extend(erros)

            data_str = row['data_prova'].strftime('%Y-%m-%d') if hasattr(row['data_prova'], 'strftime') else str(row['data_prova'])[:10]

            acao = {
                "id_solicitacao": int(row['solicitacao_id']),
                "curso": row['curso'],
                "modulo": row['modulo_codigo'],
                "tipo_prova": row['tipo_prova'],
                "data_prova": data_str,
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

        metricas = {
            'linhas_saida': len(acoes_provas),
            'inconsistencias': len(inconsistencias)
        }

        print(f"-> Sucesso! {len(acoes_provas)} acao(oes) geradas em: {output_path}")
        return output_path, metricas
    except Exception as e:
        print(f"-> ERRO na camada Gold (Moodle): {e}")
        raise
