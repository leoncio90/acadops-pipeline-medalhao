import argparse
from datetime import datetime
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from pipelines.run_pipeline_chamados import run_chamados_pipeline
from pipelines.run_pipeline_moodle import run_moodle_pipeline
from pipelines.run_pipeline_sharepoint import run_sharepoint_pipeline


def run_all(ingestion_date=None):
    print("=" * 60)
    print(f"ACADOPS — EXECUCAO CONSOLIDADA DE TODOS OS PIPELINES")
    print(f"Data Base: {ingestion_date or datetime.now().strftime('%Y-%m-%d')}")
    print("=" * 60)

    resultados = {}

    resultados['Moodle'] = run_moodle_pipeline(ingestion_date)
    resultados['SharePoint'] = run_sharepoint_pipeline(ingestion_date)
    resultados['Chamados'] = run_chamados_pipeline(ingestion_date)

    print("\n" + "=" * 60)
    print("RESUMO CONSOLIDADO:")
    todos_sucesso = True
    for pipeline, sucesso in resultados.items():
        status_txt = "SUCESSO" if sucesso else "FALHA"
        if not sucesso:
            todos_sucesso = False
        print(f"  - {pipeline:12}: {status_txt}")
    print("=" * 60)

    return todos_sucesso


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Dispara todos os pipelines do AcadOps em lote.')
    parser.add_argument('--ingestion-date', dest='ingestion_date', default=None,
                        help='Data da particao no formato YYYY-MM-DD. Opcional.')
    args = parser.parse_args()
    ok = run_all(args.ingestion_date)
    sys.exit(0 if ok else 1)
