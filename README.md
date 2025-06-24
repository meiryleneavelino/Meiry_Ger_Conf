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

- Verifica a existência de arquivos `.yml` ou `.yaml` na pasta `.github/workflows/`.
- Utiliza a API REST (v3) de Conteúdo do GitHub.

### 3. Análise de Implementação SAST

- Baixa o conteúdo de cada workflow.
- Busca por palavras-chave em `SAST_KEYWORDS` (ex: `CodeQL`, `SonarQube`, `Snyk`, `Semgrep`).

### 4. Avaliação da Maturidade SAST

Avalia boas práticas com base nos seguintes critérios:

- `has_cache_config`: Configuração de cache  
- `has_pr_trigger`: Trigger em Pull Request  
- `has_push_trigger`: Trigger em Push  
- `has_fail_fast_or_gate`: Fail-fast / Quality Gates  
- `integrates_dependabot_sca`: Integração com Dependabot ou similares  

Classificação final:

- **Baixo**
- **Médio**
- **Alto**

### 5. Geração de Relatório CSV

- Os resultados são exportados no arquivo `sast_maturity_results.csv`.

### 6. Saída esperada

Durante a execução, o script exibirá:

- A query GraphQL utilizada
- Status do Rate Limit da API
- Progresso da paginação
- Verificação de workflows e presença de SAST

#### Conteúdo do arquivo sast_maturity_results.csv:

Campo	                                    Descrição
nome_completo	                            owner/nome do repositório
url	                                      URL do repositório
estrelas	                                Número de estrelas
forks	                                    Número de forks
ultimo_push	                              Data do último push
linguagem_principal	                      Linguagem predominante
descricao	                                Descrição do projeto
arquivos_workflow_sast	                  Arquivos de workflow com SAST
nivel_maturidade_sast	                    Baixo, Médio ou Alto
sast_ferramentas_detectadas	              Lista de palavras-chave encontradas
maturidade_has_cache_config	              Uso de cache
maturidade_has_pr_trigger	                Trigger em Pull Request
maturidade_has_push_trigger	              Trigger em Push
maturidade_has_fail_fast_or_gate	        Fail-fast / Quality Gate
maturidade_integrates_dependabot_sca	    Integração com Dependabot/Snyk

---

# Contribuições são bem-vindas!
Você pode:
- Expandir a lista de SAST_KEYWORDS
- Adicionar suporte a outras plataformas de CI/CD (ex: GitLab, Jenkins, Azure)
- Refinar os critérios de avaliação de maturidade

Sinta-se à vontade para abrir issues ou enviar pull requests!

## Como Usar

### Pré-requisitos

- Python 3.x  
- Módulos Python:
  - `requests`
  - `csv`
  - `json`
  - `os`
  - `time`
  - `base64`




