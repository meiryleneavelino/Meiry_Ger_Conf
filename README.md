# Trabalho de Conclusão – Controle de Versão (UFF)

**Professor:** Leonardo Murta  
**Universidade Federal Fluminense**  
[Link para a disciplina](https://leomurta.github.io/courses/2025.1/cv.html)

---

## Análise de Maturidade SAST em Projetos Open Source do GitHub

Este repositório contém um script Python projetado para identificar e avaliar a maturidade da implementação de **Análise Estática de Segurança de Aplicações (SAST)** em pipelines de CI/CD de projetos de código aberto hospedados no GitHub.  
O objetivo é compreender como projetos de alta reputação integram práticas de segurança automatizada.

---

## 🔍 Etapas do Script

### 1. Busca de Repositórios Populares (API GraphQL)

- Realiza uma busca inicial na API GraphQL (v4) do GitHub.
- Filtra repositórios públicos com número mínimo de estrelas (`MIN_STARS`).
- Coleta metadados como: nome, descrição, estrelas, forks e branch padrão.

### 2. Detecção de Workflows do GitHub Actions (API REST)

- Verifica se existem arquivos `.yml` ou `.yaml` na pasta `.github/workflows/` de cada repositório.
- Usa a API REST (v3) de Conteúdo do GitHub.

### 3. Análise de Implementação SAST

- Baixa o conteúdo de cada arquivo de workflow.
- Busca por palavras-chave definidas em `SAST_KEYWORDS` como: `CodeQL`, `SonarQube`, `Snyk`, `Semgrep`, entre outros.

### 4. Avaliação da Maturidade SAST

- Avalia boas práticas com base nos seguintes critérios:
  - `has_cache_config`: Configuração de cache
  - `has_pr_trigger`: Triggers em Pull Requests
  - `has_push_trigger`: Triggers em Push
  - `has_fail_fast_or_gate`: Fail-fast / Quality Gates
  - `integrates_dependabot_sca`: Integração com ferramentas como Dependabot

- Classifica o nível de maturidade como:
  - **Baixo**
  - **Médio**
  - **Alto**

### 5. Geração de Relatório CSV

- Exporta um arquivo `sast_maturity_results.csv` contendo todos os resultados coletados.

---

## Como Usar

### Pré-requisitos

- Python 3.x  
- Módulos necessários:
  - `requests`
  - `csv`
  - `json`
  - `os`
  - `time`
  - `base64`

Instale o módulo externo via pip:

```bash
pip install requests
