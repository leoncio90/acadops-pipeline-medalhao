import argparse
from datetime import datetime
import os
import sys
import traceback
import uuid

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from src.sharepoint.bronze import ingest_to_bronze
from src.sharepoint.silver import process_to_silver
from src.sharepoint.gold import process_to_gold
from src.common.observability import log_pipeline_execution


def run_sharepoint_pipeline(ingestion_date=None):
    pipeline_name = 'SharePoint'
    run_id = uuid.uuid4().hex[:8]
    start_time = datetime.now()
    status = 'SUCESSO'
    details = ''
    metricas = {}
    print(f"--- INICIANDO PIPELINE: {pipeline_name} | run_id: {run_id} ---")

    PENDENCIAS_PATH = os.path.join(PROJECT_ROOT, 'source_data', 'pendencias_sharepoint.csv')
    MAPA_PATH = os.path.join(PROJECT_ROOT, 'source_data', 'mapa_sites_sharepoint.csv')
    BRONZE_PATH = os.path.join(PROJECT_ROOT, 'data', 'bronze', 'sharepoint')
    SILVER_PATH = os.path.join(PROJECT_ROOT, 'data', 'silver')
    GOLD_PATH = os.path.join(PROJECT_ROOT, 'data', 'gold')
    REJECTED_PATH = os.path.join(PROJECT_ROOT, 'data', 'rejected', 'sharepoint')

    try:
        bronze_pend_file, bronze_mapa_file, m_bronze = ingest_to_bronze(PENDENCIAS_PATH, MAPA_PATH, BRONZE_PATH, ingestion_date)
        actual_ingestion_date = m_bronze.get('ingestion_date', ingestion_date or datetime.now().strftime('%Y-%m-%d'))
        rejected_dir = os.path.join(REJECTED_PATH, f"ingestion_date={actual_ingestion_date}")

        silver_file, m_silver = process_to_silver(bronze_pend_file, bronze_mapa_file, SILVER_PATH, rejected_dir)
        gold_file, m_gold = process_to_gold(silver_file, GOLD_PATH)

        metricas = {**m_bronze, **m_silver, **m_gold}
        ja_publicados = m_gold.get('ja_publicados', 0)
        details = (f"Pipeline executado com sucesso. Arquivo final: {os.path.relpath(gold_file, PROJECT_ROOT)}"
                   f" (conciliacao: {ja_publicados} registros ja publicados nao exigem nova acao)")
        print(f"--- PIPELINE {pipeline_name} FINALIZADO COM SUCESSO ---")
    except Exception as e:
        status = 'ERRO'
        details = f"Pipeline falhou: {str(e)} | {traceback.format_exc().splitlines()[-1]}"
        print(f"--- PIPELINE {pipeline_name} FINALIZADO COM ERRO: {e} ---")
    finally:
        end_time = datetime.now()
        log_entry = {
            'timestamp': end_time.isoformat(),
            'run_id': run_id,
            'pipeline': pipeline_name,
            'ingestion_date': metricas.get('ingestion_date', ingestion_date or ''),
            'status': status,
            'duration_seconds': (end_time - start_time).total_seconds(),
            'linhas_entrada': metricas.get('linhas_entrada', 0),
            'linhas_saida': metricas.get('linhas_saida', 0),
            'linhas_rejeitadas': metricas.get('linhas_rejeitadas', 0),
            'details': details
        }
        LOG_PATH = os.path.join(PROJECT_ROOT, 'logs', 'log_execucao.csv')
        log_pipeline_execution(LOG_PATH, log_entry)

    return status == 'SUCESSO'


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Pipeline de publicação de documentos no SharePoint.')
    parser.add_argument('--ingestion-date', dest='ingestion_date', default=None,
                        help='Data da partição no formato YYYY-MM-DD. Sem o parâmetro usa a data de hoje.')
    args = parser.parse_args()
    success = run_sharepoint_pipeline(args.ingestion_date)
    sys.exit(0 if success else 1)
