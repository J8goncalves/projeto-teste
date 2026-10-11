# Relatório da Sonda B1: Confirmação do PostToolUse

**Data:** 2026-10-11  
**Ambiente:** Windows 11, Antigravity 2.0  
**Conversa / Sessão:** `be6b56bb-23e9-43a9-9ab6-29410e222f3e`  
**Modelo:** `gemini-3.1-pro-low`  

---

## 1. Tabela de Verificação do Payload e Integração

| Item | Esperado pela Documentação | Observado no Runtime Real | Status |
| :--- | :--- | :--- | :--- |
| **Invocação pela plataforma** | Dispara ao completar a ferramenta | Confirmado em execuções de ferramentas reais | **CONFERE** |
| **`toolCall.name`** | Nome da ferramenta (`view_file`, `manage_task`, etc.) | `view_file` | **CONFERE** |
| **`toolCall.args`** | Objeto com argumentos da ferramenta | `{ "AbsolutePath": "...", "toolAction": "...", "toolSummary": "..." }` | **CONFERE** |
| **`stepIdx`** | Inteiro 0-based indicando o passo do agente | Inteiro observável (ex.: `1306`) | **CONFERE** |
| **`error`** | String; vazia em caso de sucesso | `""` (string vazia quando sucesso) | **CONFERE** |
| **Campos Comuns Presentes** | `conversationId`, `workspacePaths`, `transcriptPath`, `artifactDirectoryPath`, `modelName` | Todos os 5 campos presentes no nível raiz do JSON | **CONFERE** |
| **`cwd` do processo do hook** | *Não documentado* | `d:\Antigravity Projects\projeto-teste\.agents` (diretório que contém `hooks.json`) | **DOCUMENTADO** |
| **Formato de caminhos em `workspacePaths`** | Windows (`D:\...`) ou barra normal (`d:/...`) | `["d:/Antigravity Projects/projeto-teste"]` (caminho normalizado com barras) | **DOCUMENTADO** |
| **Código de saída e retorno** | Processo deve retornar JSON `{}` | Retorno `{}` aceito com exit code 0 | **CONFERE** |

---

## 2. Descobertas Críticas do Runtime

1. **Working Directory (`cwd`) dos Hooks:**
   - O processo filho do hook é disparado tendo como diretório de trabalho a pasta onde `hooks.json` reside: `.agents`.
   - Consequentemente, comandos configurados em `.agents/hooks.json` devem referenciar o executável do venv como `..\.venv\Scripts\python.exe` e os scripts como `scripts/hooks/<nome>.py`.
   - Scripts Python que acessam caminhos relativos à raiz do projeto (como `evidence/` ou `telemetry/`) devem redefinir `os.chdir()` para a raiz do repositório calculada a partir de `__file__`.

2. **Formato de Entrada dos Hooks:**
   - O payload chega via `stdin` com chaves em camelCase (`toolCall`, `stepIdx`, `conversationId`, `workspacePaths`, `transcriptPath`, `artifactDirectoryPath`, `modelName`).
   - A ferramenta `toolCall.name` reflete o nome exato da ferramenta cortex (`view_file`, `run_command`, etc.).
