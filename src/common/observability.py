import os
import pandas as pd
from typing import Dict, Any


def log_pipeline_execution(log_path: str, log_entry: Dict[str, Any]) -> None:
    """Registra uma linha auditavel em log_execucao.csv garantindo presenca de cabecalho e encoding utf-8."""
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    colunas_obrigatorias = [
        'timestamp', 'run_id', 'pipeline', 'ingestion_date',
        'status', 'duration_seconds', 'linhas_entrada',
        'linhas_saida', 'linhas_rejeitadas', 'details'
    ]
    
    # Garante todas as colunas mesmo se omitidas
    dados = {col: log_entry.get(col, '') for col in colunas_obrigatorias}
    df = pd.DataFrame([dados])
    
    header = not os.path.exists(log_path) or os.path.getsize(log_path) == 0
    df.to_csv(log_path, mode='a', index=False, header=header, encoding='utf-8')
