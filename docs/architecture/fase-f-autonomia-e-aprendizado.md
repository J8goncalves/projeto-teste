# Fase F — Autonomia Operacional, Identidade, Telemetria e Aprendizado Contínuo (V5.2)

## 1. Visão Geral e Objetivos
A Fase F consolida a evolução da Organização V5.1.1 para a versão V5.2, introduzindo:
1. **Autonomia Governada em Sandbox (`TURBO_SANDBOX`):** Capacidade de executar o ciclo completo de engenharia (Discovery -> Planning -> Design -> Build -> Verify -> Candidate Release) em branch isolada de feature sem atrito de aprovação humana intermediária, preservando a barreira intransponível de deploy em produção e merge na `main`.
2. **Identidade e Revisão Provisória com Honestidade Epistêmica:** Reconhecimento transparente de identidades não atestadas criptograficamente (`UNVERIFIED/ROLE_ONLY`), permitindo verificação cruzada em sandbox entre instâncias distintas de subagentes, sem falsificar status `VERIFIED`.
3. **Telemetria de Execução e Auditoria Integrada (`org_v5.cli report`):** Registro padronizado de eventos de invocações de subagentes com identificação real de instâncias, duração medida, rastreabilidade de artefatos e identificação honesta de métricas não disponíveis (`NÃO MEDIDO` / `NÃO VERIFICÁVEL`).
4. **Aprendizado Automático Comprovado do Core (`memory-promote-core`):** Gravação automática e idempotente no AI Memory on-prem de decisões e aprendizados decorrentes de melhorias efetivamente aplicadas e comprovadas na suíte de testes do core da organização, eliminando a dependência de um segundo gate humano redundante para memória.

---

## 2. Modelo de Ameaças e Invariantes de Segurança

| Invariante | Defesa e Implementação |
| :--- | :--- |
| **Proteção da Branch Principal (`main` / `master`)** | `TURBO_SANDBOX` é rejeitado deterministiamente se inicializado ou executado em `main` ou `master`. Merge ou deploy externo continuam exigindo autorização humana explícita. |
| **Imutabilidade da Política** | `execution_policy` é gravada no evento de `init` e validada em todas as transições. Tentativas de alterar a política no arquivo de estado resultam em bloqueio imediato por adulteração. |
| **Prevenção de Autoaprovação e Spoofing** | O produtor do artefato e seu revisor nunca podem ter a mesma instância (`agent_id`). Tentativas de autoaprovação são rejeitadas. Tokens de autoridade forjados em `os.environ` são detectados e tratados como `UNVERIFIED`. |
| **Confinamento de Escopo do Core** | A promoção automática de memória exige que os arquivos modificados pertençam à allowlist do Core da organização (`org_v5/**`, `.agents/**`, testes, arquitetura). Alterações restritas a aplicações de produto (`src/**`) são rejeitadas. |
| **Validação Empírica de Testes** | A promoção de memória do core exige a execução real da suíte completa de testes via subprocesso controlado, verificando `exit_code == 0`, 0 falhas e 0 erros. Logs em texto fornecidos pelo próprio agente não são aceitos como prova. |
| **Resiliência a Falhas do AI Memory** | Em caso de indisponibilidade do servidor local, a operação falha de forma segura sem inventar sucesso, enfileirando o candidato como `PENDENTE_SINCRONIZACAO` para processamento posterior. |

---

## 3. Especificação dos Novos Fluxos

### 3.1. Máquina de Estados e Políticas
- `execution_policy: STANDARD` (Padrão): Mantém 100% dos requisitos da V5.1.1. Gates `BUILD`, `RELEASE`, `CLOSED` e `MEMORY_WRITE` exigem comentário assinado verificado no GitHub com anti-replay atômico.
- `execution_policy: TURBO_SANDBOX`:
  - Válido apenas em branch de trabalho (ex: `feature/*`).
  - Transições `advance --to BUILD` e `advance --to RELEASE` são autorizadas automaticamente pela política (`POLICY_AUTO_APPROVED`) se os artefatos predecessores estiverem aceitos por revisão independente.
  - Artefatos críticos (`build`, `qa-report`, `security-report`) podem ser aceitos com garantia `SANDBOX_PROVISIONAL` se revisados por uma instância distinta do produtor.
  - O gate de produção e merge em `main` permanece inalterado: **proibido**.

### 3.2. Telemetria e Relatório CLI
O comando `python -m org_v5.cli report --run <RUN_ID>` consolida:
- Modo de workflow, política de execução e branch associada.
- Agentes efetivamente acionados com IDs de instância e duração medida.
- Agentes declarados vs. não acionados.
- Tabela de artefatos com seus respectivos SHAs e status.
- Linha do tempo de handoffs, revisões e contagem de correções.
- Estado dos portões de governança.
- Métricas de tokens/custo: quando não fornecidas pela plataforma, exibidas estritamente como `NÃO MEDIDO`.

### 3.3. Promoção de Memória do Core (`memory-promote-core`)
O comando `python -m org_v5.cli memory-promote-core --run <RUN_ID> --candidate <ID> --commit <SHA>` executa:
1. Validação do candidato em `memory-candidates/<ID>.json`.
2. Inspeção do commit no Git comprovando alteração em arquivos do core.
3. Execução imediata da suíte de testes de governança e regressão.
4. Escrita atômica no AI Memory via `ai-memory write-page` no projeto `projeto-teste`.
5. Confirmação imediata por busca/leitura (FTS5).
6. Caso offline: gravação na fila de sincronização em `memory-sync-queue/` com status `PENDENTE_SINCRONIZACAO`.
