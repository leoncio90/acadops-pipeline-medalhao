# Contexto e Regras do Projeto — AcadOps

## Visão Geral
Pipeline de dados em Python aplicando Arquitetura Medalhão (Bronze, Silver, Gold) para automação de três processos acadêmicos (Moodle, SharePoint e Chamados de Suporte), com esteira de CI no GitHub Actions e suíte de testes automatizados com pytest.

## Estrutura do Pipeline
- `source_data/`: Dados brutos de entrada.
- `data/bronze/`: Ingestão particionada por data (`ingestion_date=YYYY-MM-DD`), padronização em UTF-8 e correção de mojibake.
- `data/silver/`: Tipagem, limpeza textual, deduplicação e quarentena de inválidos em `data/rejected/`.
- `data/gold/`: Entregáveis finais de negócio (`acoes_provas.json`, `publicacao_documentos.csv`, `triagem_chamados.csv`).
- `data/rejected/`: Quarentena particionada com motivo explícito da inconsistência.
- `pipelines/`: Scripts executáveis individuais de cada fluxo e runner unificado (`run_all.py`).
- `src/`: Lógica por domínio (`chamados/`, `moodle/`, `sharepoint/`) e utilitários transversais (`src/common/`).
- `tests/`: Suíte automatizada de testes unitários e de integração (`pytest`).
- `.github/workflows/`: Esteira de CI automatizada com matriz multi-versão de Python.
- `logs/`: Histórico auditável de execuções consolidadas em `log_execucao.csv`.

## Invariantes e Boas Práticas
- Proibido descarte silencioso: qualquer registro rejeitado deve ir para `data/rejected/` com motivo explícito; registros não acionáveis (ex: já publicados) devem ser justificados no log de execução para conciliação ponta a ponta (`linhas_entrada = linhas_saida + linhas_rejeitadas + justificadas`).
- Tratamento estrito de encoding em duas frentes: fallback de leitura para latin-1 e reversão da assinatura de duplo encoding UTF-8 (mojibake).
- Observabilidade obrigatória: manter registro auditável com `run_id`, volumetria e status em `logs/log_execucao.csv`.
- Qualidade contínua: toda alteração em regras de negócio ou utilitários deve manter 100% dos testes aprovados no CI.