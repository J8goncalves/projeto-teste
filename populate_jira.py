import os, requests, json
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()
jira_url = 'https://j8goncalves.atlassian.net'
email = os.getenv('JIRA_EMAIL')
token = os.getenv('JIRA_API_TOKEN')
auth = HTTPBasicAuth(email, token)

def create_issue(summary, description, issuetype_id="10008"):
    url = f"{jira_url}/rest/api/3/issue"
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    
    # Formato do description pro API V3 (Atlassian Document Format)
    desc_adf = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": description}]
            }
        ]
    }
    
    payload = json.dumps({
        "fields": {
            "project": {"key": "DS"},
            "summary": summary,
            "description": desc_adf,
            "issuetype": {"id": issuetype_id}
        }
    })
    
    res = requests.post(url, data=payload, headers=headers, auth=auth)
    if res.status_code == 201:
        print(f"✅ Criado: {res.json()['key']} - {summary}")
    else:
        print(f"❌ Erro ao criar '{summary}': {res.status_code} - {res.text}")

backlog = [
    # Epic 1: Arquitetura
    {"s": "[Arq] Configurar Ambiente ERPNext Core", "d": "Subir container Frappe/ERPNext sem modificar o core, garantindo upgrade path seguro."},
    {"s": "[Arq] Criar Frappe Custom App 'ERP Svet'", "d": "Criar a app desacoplada onde todo o código customizado da Svet Engenharia será escrito (DocTypes, Scripts)."},
    {"s": "[Arq] Criar Microserviço Headless de IA (OCR)", "d": "Setup de um container FastAPI isolado rodando o Chandra OCR via Python para receber os PDFs e retornar JSON para o ERPNext."},
    
    # Epic 2: Cadastros
    {"s": "[Cad] Parametrizar Fornecedores e Clientes", "d": "Adaptar módulos padrão do ERPNext para incluir campos específicos do setor público (UASG, CNPJ, Órgão)."},
    {"s": "[Cad] Gestão de Contratos de Obra", "d": "Criar DocType no Custom App para vincular contrato público, anexos e centro de custo financeiro."},
    
    # Epic 3: Compras e OCR
    {"s": "[Compras] Tela de Importação de Proposta (OCR)", "d": "Interface onde o usuário faz upload da planilha/PDF do fornecedor. O Frappe envia para o microserviço Chandra."},
    {"s": "[Compras] Motor de Decisão do Menor Preço", "d": "Rotina que lê os 3 orçamentos (RFQ) inseridos via OCR e exige justificativa caso o usuário não escolha o menor valor."},
    
    # Epic 4: Financeiro
    {"s": "[Fin] Habilitar Contas a Pagar/Receber e Relatórios", "d": "Ativar e traduzir/parametrizar o módulo Accounting do ERPNext para a Svet. Configurar Fluxo de Caixa base."},
    
    # Epic 5: Licitações (Buscador)
    {"s": "[Gov] Integração com API Pública do PNCP", "d": "Criar job agendado no Frappe que consulta as licitações diárias via API do Gov (PNCP) com base nas palavras-chave da Svet."},
    {"s": "[Gov] Dashboard e Alerta de Novas Licitações", "d": "Exibir os dados filtrados do PNCP num dashboard limpo, e disparar notificação interna (Frappe Notification)."}
]

print("Criando backlog no Jira (Projeto DS)...")
for item in backlog:
    create_issue(item["s"], item["d"])

