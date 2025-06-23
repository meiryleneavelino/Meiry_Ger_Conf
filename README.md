# Trabalho de Conclusão – Controle de Versão (UFF)

**Professor:** Leonardo Murta  
**Universidade Federal Fluminense**  
[Link para a disciplina](https://leomurta.github.io/courses/2025.1/cv.html)

---

## Análise de Maturidade SAST em Projetos Open Source do GitHub

Este repositório contém um script Python projetado para identificar e avaliar a maturidade da implementação de **Análise Estática de Segurança de Aplicações (SAST)** em pipelines de CI/CD de projetos de código aberto hospedados no GitHub.  
O objetivo é compreender como projetos de alta reputação integram práticas de segurança automatizada.

---

## Etapas do Script

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


## Configuração do GitHub PAT
Gere um Personal Access Token (PAT) Clássico:

Vá em: Settings → Developer settings → Personal access tokens → Tokens (classic)

Clique em Generate new token (classic)

Marque apenas a permissão public_repo

Copie o token gerado

Atualize o script:

python
Copiar
Editar
PAT = "ghp_SEU_TOKEN_REAL_AQUI"


## Saída Esperada
Durante a execução, o script mostra:

A query GraphQL utilizada

O status do Rate Limit da API

Progresso da paginação

Status da verificação de cada repositório

| Campo                                 | Descrição                                 |
|---------------------------------------|--------------------------------------------|
| `nome_completo`                      | owner/nome do repositório                 |
| `url`                                | URL do repositório                        |
| `estrelas`                           | Número de estrelas                        |
| `forks`                              | Número de forks                           |
| `ultimo_push`                        | Data do último push                       |
| `linguagem_principal`                | Linguagem predominante                    |
| `descricao`                          | Descrição do projeto                      |
| `arquivos_workflow_sast`            | Arquivos de workflow com SAST             |
| `nivel_maturidade_sast`             | Baixo, Médio ou Alto                      |
| `sast_ferramentas_detectadas`       | Lista de palavras-chave encontradas      |
| `maturidade_has_cache_config`       | Uso de cache                              |
| `maturidade_has_pr_trigger`         | Trigger em PR                             |
| `maturidade_has_push_trigger`       | Trigger em push                           |
| `maturidade_has_fail_fast_or_gate`  | Fail-fast / Quality Gate                  |
| `maturidade_integrates_dependabot_sca` | Integração com Dependabot/Snyk         |


## Contribuições são bem-vindas!

Você pode ajudar a:

Expandir a lista de SAST_KEYWORDS

Incluir suporte a outras plataformas de CI/CD (ex: GitLab, Jenkins, Azure)

Refinar os critérios de maturidade

Sinta-se à vontade para abrir issues ou enviar pull requests!
