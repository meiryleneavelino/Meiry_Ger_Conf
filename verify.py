import requests
import os
import json
import time 
import csv 

# --- Configuração do Personal Access Token (PAT) ---
#API de Busca e tem limite de 5000/h.
PAT = "ghp_"  #<--- Sua PAT aqui

# Validação do PAT: essencial para garantir que o script não execute sem um token.
if not PAT:
    print("ERRO: Personal Access Access Token (PAT) não configurado.")

# --- Cabeçalhos das Requisições ---
headers = {
    "Authorization": f"Bearer {PAT}",
    "Accept": "application/vnd.github.com",
    "Content-Type": "application/json"        
}

# --- DEFINIÇÕES DE BUSCA ---
graphql_url = "https://api.github.com/graphql"
MIN_STARS = 1000
REPOS_PER_PAGE = 100 
search_term_graphql = f"stars:>={MIN_STARS}"

# --- QUERY GRAPHQL (mesma de antes) ---
graphql_query_template = """
query ($queryString: String!, $numRepos: Int!, $cursor: String) {
  search(query: $queryString, type: REPOSITORY, first: $numRepos, after: $cursor) {
    repositoryCount
    pageInfo {
      endCursor
      hasNextPage
    }
    edges {
      node {
        ... on Repository {
          name
          nameWithOwner
          url
          description
          forkCount
          stargazerCount
          pushedAt
          primaryLanguage {
            name
          }
          defaultBranchRef {
            name
          }
        }
      }
    }
  }
}
"""

# --- Palavras-Chave para Detecção de SAST ---
SAST_KEYWORDS = [
    # CodeQL
    "github/codeql-action", "codeql-action/analyze", "codeql-action/init", 
    "codeql database", "codeql query", "codeql pack",

    # SonarQube
    "sonarsource/sonarqube-scan-action", "sonar-scanner",
    "sonar.host.url", "sonar.projectKey", "sonar.login",

    # Semgrep
    "returntocorp/semgrep-action", "semgrep --config", "semgrep.yml",

    # Snyk
    "snyk/actions", "snyk test", "snyk monitor", "snyk code test",

    # Checkmarx
    "checkmarx", "checkmarx-sast", "cxflow", "checkmarx.yml",

    # Veracode
    "veracode", "veracode scan", "veracode/api-wrapper", "veracode-uploadandscan-action",

    # AppScan
    "appscan", "ibm/appscan", "appscan-config", "appscan.yaml",

    # Fortify
    "fortify", "fortify-sca", "microfocus/fortify", "sourceanalyzer",

    # DevSkim
    "microsoft/devskim", "devskim",

    # ShiftLeft
    "shiftleft", "shiftleft/scan-action", "shiftleft-sast",

    # Trivy
    "aquasecurity/trivy-action", "trivy scan", "trivy fs", "trivy repo", "trivy config",

    # Grype
    "anchore/grype-action", "grype",

    # OWASP Dependency-Check
    "owasp/dependency-check-action", "dependency-check", "org.owasp.dependencycheck",

    # Whitesource / Renovate
    "whitesource", "whitesource/renovate-action", "renovate-config",

    # Dependency-Track
    "dependency-track", "dependency-track-analysis", "dependency-track.yaml",

    # Termos genéricos de SAST/SCA
    "sast", "static-analysis", "security-scan", "vulnerability-scan"
]

# --- NOVAS PALAVRAS-CHAVE E INDICADORES DE MATURIDADE ---
MATURITY_INDICATORS = {
    "has_cache_config": ["cache-action", "actions/cache", "uses: actions/cache"],
    "has_pr_trigger": ["on: pull_request"],
    "has_push_trigger": ["on: push"],
    "has_fail_fast_or_gate": ["fail-fast: true", "continue-on-error: false", "security-gate"],
    "integrates_dependabot_sca": ["dependabot.yml", "snyk/broker", "snyk/cli", "dependency-review-action"],
}

# --- Funções Auxiliares ---

def run_graphql_query(query_template, variables, custom_headers=None):
    if custom_headers is None: custom_headers = headers 
    try:
        response = requests.post(graphql_url, json={'query': query_template, 'variables': variables}, headers=custom_headers)
        response.raise_for_status() 
        json_data = response.json()
        if 'errors' in json_data: raise Exception(f"Erro GraphQL: {json_data['errors']}")
        return json_data
    except requests.exceptions.RequestException as e:
        error_details = f"Erro de requisição: {e}"
        if response is not None and response.status_code:
            error_details = f"Erro HTTP {response.status_code}: {e}"
            if response.status_code == 401: error_details += " - PAT inválido ou expirado."
            elif response.status_code == 403: error_details += " - Acesso proibido. Verifique permissões do PAT ou rate limit."
            elif response.status_code == 422: error_details += f" - Entidade não processável. Detalhes: {response.text[:200]}"
        raise Exception(error_details)

def get_file_content_from_github(repo_full_name, branch, file_path, custom_headers=None):
    if custom_headers is None: custom_headers = headers
    contents_api_url = f"https://api.github.com/repos/{repo_full_name}/contents/{file_path}?ref={branch}"
    try:
        response = requests.get(contents_api_url, headers=custom_headers)
        response.raise_for_status() 
        file_data = response.json()
        if file_data and 'content' in file_data and file_data.get('encoding') == 'base64':
            import base64 
            decoded_content = base64.b64decode(file_data['content']).decode('utf-8')
            return decoded_content
        elif file_data and file_data.get('type') == 'dir': return None
        return None 
    except requests.exceptions.RequestException as e:
        pass 
    return None

def detect_sast_in_workflow(workflow_content):
    if not workflow_content: return False
    content_lower = workflow_content.lower()
    return any(kw.lower() in content_lower for kw in SAST_KEYWORDS)

def get_workflow_files_list(repo_full_name, custom_headers=None):
    if custom_headers is None: custom_headers = headers
    owner, repo_name = repo_full_name.split('/')
    workflow_dir_path = ".github/workflows"
    contents_url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/{workflow_dir_path}"
    try:
        response = requests.get(contents_url, headers=custom_headers)
        response.raise_for_status() 
        workflow_contents = response.json()
        if isinstance(workflow_contents, list):
            yml_files = [f['name'] for f in workflow_contents if f['type'] == 'file' and f['name'].lower().endswith(('.yml', '.yaml'))]
            return yml_files
    except requests.exceptions.RequestException as e:
        pass 
    return []

def assess_sast_maturity(workflow_content_list):
    """
    Avalia a maturidade de SAST de um repositório com base nos conteúdos de seus workflows.
    Retorna um dicionário com indicadores de maturidade e nível de maturidade.
    """
    maturity_assessment = {
        "has_cache_config": False,
        "has_pr_trigger": False,
        "has_push_trigger": False,
        "has_fail_fast_or_gate": False,
        "integrates_dependabot_sca": False,
        "sast_tool_detected": [] 
    }

    combined_content_lower = ""
    for content in workflow_content_list:
        if content:
            combined_content_lower += content.lower() + "\n"

    # 1. Detecção de Ferramentas SAST (quais foram detectadas)
    for kw in SAST_KEYWORDS:
        if kw.lower() in combined_content_lower:
            # Evita duplicatas se um termo SAST for substring de outro
            if kw not in maturity_assessment["sast_tool_detected"]:
                maturity_assessment["sast_tool_detected"].append(kw)

    # 2. Avaliação dos Indicadores de Maturidade
    for indicator, keywords in MATURITY_INDICATORS.items():
        for kw in keywords:
            if kw.lower() in combined_content_lower:
                maturity_assessment[indicator] = True
                break # Encontrou um keyword para este indicador, pode parar e ir para o próximo indicador
            
    # Classificação final de maturidade (lógica baseada nos critérios definidos)
    score = 0
    if maturity_assessment["sast_tool_detected"]: score += 1 # Pelo menos uma ferramenta detectada
    if maturity_assessment["has_cache_config"]: score += 1
    if maturity_assessment["has_pr_trigger"] and maturity_assessment["has_push_trigger"]: score += 1 
    elif maturity_assessment["has_pr_trigger"] or maturity_assessment["has_push_trigger"]: score += 0.5 
    if maturity_assessment["has_fail_fast_or_gate"]: score += 1
    if maturity_assessment["integrates_dependabot_sca"]: score += 1
    
    if score >= 4:
        maturity_assessment["maturity_level"] = "Alto"
    elif score >= 2:
        maturity_assessment["maturity_level"] = "Médio"
    else:
        maturity_assessment["maturity_level"] = "Baixo"
        
    return maturity_assessment

# --- Execução da Busca Principal ---
all_candidate_repos = [] 
cursor = None 
has_next_page = True
repos_graphql_fetched_count = 0 
page = 1 
MAX_GRAPHQL_RESULTS = 1000 

print(f"\nIniciando busca por repositórios com >= {MIN_STARS} estrelas (etapa inicial - GraphQL):")
print(f"Query GraphQL String para busca: '{search_term_graphql}'")

# --- Verificação do Rate Limit (GraphQL) ---
rate_limit_query_graphql = """
query { rateLimit { limit cost remaining resetAt } }
"""
try:
    rate_limit_info = run_graphql_query(rate_limit_query_graphql, {}).get('data', {}).get('rateLimit', {})
    
    print(f"\n--- Verificação do Rate Limit do PAT (GraphQL) ---")
    print(f"Limite de Requisições: {rate_limit_info.get('limit', 'N/A')}")
    print(f"Requisições Restantes: {rate_limit_info.get('remaining', 'N/A')}")
    print(f"Reset em: {rate_limit_info.get('resetAt', 'N/A')}")
    print(f"-----------------------------------------\n")

    if rate_limit_info.get('remaining', 0) == 0:
        print("ATENÇÃO: Seu rate limit GraphQL está zerado. Aguarde até o reset.")
        exit("Saindo devido ao rate limit esgotado.")
    elif rate_limit_info.get('limit', 0) != 5000: 
        print("!!! ALERTA CRÍTICO !!! O LIMITE DE REQUISIÇÕES NÃO É 5000/H.")
        print("Isso indica que o PAT pode não ser CLÁSSICO ou não ter a permissão 'public_repo'.")

except Exception as e:
    print(f"Erro ao verificar rate limit GraphQL: {e}")
    print("Isso pode indicar um problema de conexão ou PAT. A busca principal pode ser afetada.")


# --- Busca GraphQL e Paginação ---
while has_next_page and repos_graphql_fetched_count < MAX_GRAPHQL_RESULTS: 
    variables = {
        "queryString": search_term_graphql,
        "numRepos": REPOS_PER_PAGE, 
        "cursor": cursor
    }
    
    try:
        data = run_graphql_query(graphql_query_template, variables)

    except Exception as e:
        print(f"Erro durante a busca GraphQL na página {page}: {e}")
        break 

    search_data = data['data']['search']
    edges = search_data['edges']
    
    repos_graphql_fetched_count += len(edges)
    
    for edge in edges:
        all_candidate_repos.append(edge['node'])

    print(f"Página {page}: Encontrados {len(edges)} repositórios. Total acumulado: {len(all_candidate_repos)} (Total API reportado: {search_data.get('repositoryCount', 'N/A')})")

    has_next_page = search_data['pageInfo']['hasNextPage']
    cursor = search_data['pageInfo']['endCursor']
    page += 1

    if repos_graphql_fetched_count >= MAX_GRAPHQL_RESULTS:
        print("AVISO: A busca em GraphQL também geralmente limita a 1000 resultados. Parando a paginação.")
        break
    
    time.sleep(0.5) 

print(f"\nBusca de repositórios por estrelas concluída. Total de candidatos: {len(all_candidate_repos)}")


# --- ETAPA 2: FILTRAR E ANALISAR REPOSITÓRIOS PARA WORKFLOWS E MATURIDADE SAST (VIA API REST) ---
print("\n--- INICIANDO ANÁLISE DE WORKFLOWS E DETECÇÃO DE MATURIDADE SAST ---")
sast_implemented_repos = [] 
repos_with_workflows = 0

MAX_REPOS_FOR_CONTENT_ANALYSIS = 100 
repos_to_analyze_content = all_candidate_repos[:min(len(all_candidate_repos), MAX_REPOS_FOR_CONTENT_ANALYSIS)] 

print(f"Analisando workflows e maturidade SAST para os primeiros {len(repos_to_analyze_content)} repositórios coletados...")


for i, repo in enumerate(repos_to_analyze_content):
    repo_full_name = repo['nameWithOwner']
    default_branch = repo.get('defaultBranchRef', {}).get('name') or "main" 

    print(f"[{i+1}/{len(repos_to_analyze_content)}] Verificando: {repo_full_name}")
    
    workflow_files = get_workflow_files_list(repo_full_name, headers)
    time.sleep(0.1) 

    if workflow_files:
        repos_with_workflows += 1
        sast_found_in_this_repo = False
        sast_files_in_this_repo = []

        # 1. Baixar e Analisar cada arquivo de workflow para detecção inicial de SAST
        all_workflow_contents_for_repo = [] # Acumula conteúdo para avaliação de maturidade
        for yml_file in workflow_files:
            file_path_in_repo = f".github/workflows/{yml_file}"
            content = get_file_content_from_github(repo_full_name, default_branch, file_path_in_repo, headers)
            time.sleep(0.1) 
            
            if content:
                all_workflow_contents_for_repo.append(content) 
                if detect_sast_in_workflow(content): # Detecção de SAST em qualquer workflow
                    sast_found_in_this_repo = True
                    sast_files_in_this_repo.append(yml_file)
        
        if sast_found_in_this_repo:
            print(f"  [SAST DETECTADO ✅]: {repo_full_name} em arquivos: {', '.join(sast_files_in_this_repo)}")
            
            # 2. Se SAST foi detectado, avaliar a maturidade (usando o conteúdo de TODOS os workflows)
            maturity_data = assess_sast_maturity(all_workflow_contents_for_repo)
            
            repo['has_sast_workflow'] = True 
            repo['sast_workflow_files'] = sast_files_in_this_repo 
            repo['sast_maturity_assessment'] = maturity_data 
            sast_implemented_repos.append(repo)
            
            print(f"    Maturidade SAST: {maturity_data['maturity_level']} (Ferramentas: {', '.join(maturity_data['sast_tool_detected']) or 'N/A'})")
        else:
            print(f"  [SAST NÃO ENCONTRADO ]: {repo_full_name} (Workflows presentes, mas sem palavras-chave SAST).")
    else:
        print(f"  [SEM WORKFLOWS ]: {repo_full_name} (Não possui arquivos .yml em .github/workflows).")

print(f"\nAnálise de Workflows e Maturidade SAST concluída.")
print(f"Total de repositórios analisados para conteúdo: {len(repos_to_analyze_content)}")
print(f"Total de repositórios com GitHub Actions workflows: {repos_with_workflows}")
print(f"Total de repositórios com SAST implementado e avaliado: {len(sast_implemented_repos)}")


# --- Exibição dos Resultados Finais (Repositórios com SAST Implementado e Avaliado) ---
if sast_implemented_repos:
    print("\n Detalhes dos Repositórios COM SAST Implementado (primeiros 10):")
    for i, repo in enumerate(sast_implemented_repos[:10]):
        print(f"--- Repositório SAST (Maturidade: {repo['sast_maturity_assessment']['maturity_level']}) {i+1} ---")
        print(f"Nome Completo: {repo['nameWithOwner']}")
        print(f"URL: {repo['url']}")
        print(f"Estrelas: {repo['stargazerCount']}")
        print(f"Forks: {repo['forkCount']}")
        print(f"Último Push: {repo['pushedAt']}")
        print(f"Linguagem Principal: {repo['primaryLanguage']['name'] if repo['primaryLanguage'] else 'N/A'}")
        print(f"Descrição: {repo['description'][:100]}..." if repo['description'] else "N/A")
        print(f"Arquivos de Workflow com SAST: {', '.join(repo['sast_workflow_files'])}")
        print(f"Detalhes da Maturidade:")
        for key, value in repo['sast_maturity_assessment'].items():
            if key != 'maturity_level': # Já exibido no título
                print(f"  - {key}: {value}")
        print("-" * 60)
else:
    print("\nNenhum repositório com SAST implementado detectado nos critérios especificados e nos resultados analisados.")
    print("Possíveis causas:")
    print("  - Os termos SAST não estão explícitos nos workflows analisados (tente expandir SAST_KEYWORDS).")
    print("  - Os repositórios com SAST podem estar em páginas posteriores da busca inicial (aumente 'MAX_GRAPHQL_RESULTS').")
    print("  - Os filtros iniciais (MIN_STARS) são muito rigorosos (tente flexibilizar, ex: MIN_STARS = 50).")
    print("  - Pode haver problemas de permissão do PAT para acessar o conteúdo dos arquivos (verifique 'public_repo').")

# --- Exportar Resultados para CSV ---
output_filename = "sast_maturity_results.csv"

if sast_implemented_repos:
    
    fieldnames = [
        "nome_completo", "url", "estrelas", "forks", "ultimo_push",
        "linguagem_principal", "descricao", "arquivos_workflow_sast",
        "nivel_maturidade_sast",
        "sast_ferramentas_detectadas",
        "maturidade_has_cache_config",
        "maturidade_has_pr_trigger",
        "maturidade_has_push_trigger",
        "maturidade_has_fail_fast_or_gate",
        "maturidade_integrates_dependabot_sca"
    ]

    with open(output_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader() 

        for repo in sast_implemented_repos:
            # Preparar CSV
            row = {
                "nome_completo": repo.get('nameWithOwner', 'N/A'),
                "url": repo.get('url', 'N/A'),
                "estrelas": repo.get('stargazerCount', 0),
                "forks": repo.get('forkCount', 0),
                "ultimo_push": repo.get('pushedAt', 'N/A'),
                "linguagem_principal": repo.get('primaryLanguage', {}).get('name', 'N/A'),
                "descricao": repo.get('description', 'N/A')[:200], # Limita descrição no CSV
                "arquivos_workflow_sast": ', '.join(repo.get('sast_workflow_files', [])),
                "nivel_maturidade_sast": repo['sast_maturity_assessment'].get('maturity_level', 'N/A'),
                "sast_ferramentas_detectadas": ', '.join(repo['sast_maturity_assessment'].get('sast_tool_detected', [])),
                "maturidade_has_cache_config": repo['sast_maturity_assessment'].get('has_cache_config', False),
                "maturidade_has_pr_trigger": repo['sast_maturity_assessment'].get('has_pr_trigger', False),
                "maturidade_has_push_trigger": repo['sast_maturity_assessment'].get('has_push_trigger', False),
                "maturidade_has_fail_fast_or_gate": repo['sast_maturity_assessment'].get('has_fail_fast_or_gate', False),
                "maturidade_integrates_dependabot_sca": repo['sast_maturity_assessment'].get('integrates_dependabot_sca', False)
            }
            writer.writerow(row) # Escreve a linha no arquivo CSV
    
    print(f"\nResultados exportados para '{output_filename}'")
else:
    print(f"\nNão há resultados para exportar para CSV.")
