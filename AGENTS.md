# Contexto e Regras do Projeto — AcadOps

## Visão Geral
Pipeline de dados em Python aplicando Arquitetura Medalhão (Bronze, Silver, Gold) para automação de três processos acadêmicos (Moodle, SharePoint e Chamados de Suporte).

## Estrutura do Pipeline
- source_data/: Dados brutos de entrada.
- data/bronze/: Ingestão particionada por data, padronização em UTF-8 e correção de mojibake.
- data/silver/: Tipagem, limpeza textual, deduplicação e quarentena de inválidos em data/rejected/.
- data/gold/: Entregáveis finais de negócio (coes_provas.json, publicacao_documentos.csv, 	riagem_chamados.csv).
- pipelines/: Scripts executáveis de cada fluxo.
- src/: Lógica central e funções utilitárias.

## Invariantes e Boas Práticas
- Proibido descarte silencioso: qualquer registro rejeitado deve ir para data/rejected/ com motivo explícito.
- Tratamento estrito de encoding em duas frentes (correção de duplo encoding UTF-8).
- Observabilidade obrigatória: manter registro auditável em logs/log_execucao.csv.