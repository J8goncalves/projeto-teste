# ADR-005: Fase F — Autonomia Governada, Identidade Honesta, Telemetria e Aprendizado do Core

## Status
Aprovado (V5.2)

## Contexto
Na versão V5.1.1, a organização alcançou rigor criptográfico e fail-closed com anti-replay de aprovações humanas no GitHub e proteção de gates críticos. Contudo, na operação prática (como observado nas runs `RUN-EVENTO-VIAB-002` e `RUN-POMODORO-001`):
1. O avanço formal para `BUILD` e aceitação de artefatos críticos foi bloqueado fail-closed em ambiente local porque os agentes não tinham `GITHUB_TOKEN` configurado para simular revisores externos nem autoridade de identidade `VERIFIED`. Isso forçou o desenvolvimento a ocorrer fora do ledger formal.
2. Não havia distinção formal entre runs em modo de produção/padrão (`STANDARD`) e runs de experimentação rápida em sandbox/feature branch (`TURBO_SANDBOX`).
3. Não havia telemetria padronizada de invocações de subagentes conectada ao CLI (`report`), resultando em métricas difíceis de auditar ou dados não medidos.
4. O AI Memory exigia aprovação humana duplicada (`MEMORY_WRITE`) mesmo para melhorias do core da organização que já haviam sido implementadas, testadas com sucesso na suíte de testes e aprovadas em revisão de código, gerando descompasso onde aprendizados comprovados ficavam retidos apenas em logs.

## Decisão

1. **Política de Execução Imutável (`execution_policy`):**
   - Introduzir o parâmetro imutável `execution_policy: STANDARD | TURBO_SANDBOX` no `init` da run.
   - Default estrito: `STANDARD` (preserva 100% das regras e gates humanos da V5.1.1).
   - `TURBO_SANDBOX`: autorizado exclusivamente em branches que NÃO sejam `main` ou `master`. A run fica vinculada à branch de criação.
   - Em `TURBO_SANDBOX`, o avanço formal para `BUILD` e `RELEASE` (pacote candidato) é liberado com registro de evento de política auditável (`POLICY_AUTO_APPROVED`), DESDE QUE os pré-requisitos e revisões independentes estejam cumpridos.
   - **Deploy externo e merge em `main` permanecem estritamente bloqueados fail-closed** até aprovação humana externa verificada.

2. **Identidade e Revisão Provisória com Garantias Honestas:**
   - Subagentes locais sem autoridade externa de assinatura recebem honestamente a garantia `UNVERIFIED/ROLE_ONLY` ou `SANDBOX_PROVISIONAL`.
   - É terminantemente proibido fingir `VERIFIED` ou auto-assinar tokens dentro do processo do agente.
   - Em `TURBO_SANDBOX`, revisões de artefatos críticos por instâncias distintas (`producer_id != reviewer_id`) são aceitas como `SANDBOX_PROVISIONAL`, permitindo progressão na sandbox sem autorizar produção.
   - Revisor e autor que compartilhem a mesma instância continuam estritamente rejeitados.

3. **Telemetria Real e Relatório Auditável (`org_v5.cli report`):**
   - Instrumentação das fronteiras de invocação em `runs/<RUN_ID>/telemetry/events.jsonl`.
   - Registro de `invocation_id`, `parent_invocation_id`, `instance_id`, `role`, timestamps, durações, evidências e artefatos gerados.
   - Métricas não disponibilizadas pelo runtime (tokens por subagente e custo monetário) são explicitamente categorizadas como `NÃO MEDIDO`, sem estimativas alucinadas.
   - Ausência de eventos de telemetria é explicitada como `NÃO VERIFICÁVEL`.

4. **Aprendizado Automático Comprovado do Core (`memory-promote-core`):**
   - Manter a rota de escrita existente para memórias gerais com aprovação humana.
   - Criar uma rota restrita `promote_core` para melhorias do core da organização (`org_v5/**`, `.agents/**`, testes, arquitetura).
   - Requisitos determinísticos para promoção sem segunda aprovação:
     1. Alteração confirmada no Git por commit SHA válido.
     2. Verificação de que os arquivos alterados pertencem à allowlist do Core (mudanças puramente em `src/**` de aplicações são rejeitadas).
     3. Execução real da suíte completa de testes de governança e regressão via subprocesso com `exit_code == 0` e 0 erros/falhas.
     4. Validação estrutural do candidato de memória (tipo `learning`, `decision`, `error`, 30-400 chars, sem credenciais/PII).
     5. Escrita via `_AuthorizedMemoryWriteContext` no AI Memory on-prem com recibo e leitura de confirmação imediata.
     6. Em caso de backend offline: enfileiramento transacional idempotente com status `PENDENTE_SINCRONIZACAO`.

## Consequências
- **Positivas:**
  - Desenvolvimento autônomo e fluido em feature branches sem atrito artificial de gates humanos em etapas intermediárias.
  - Rastreabilidade total e auditabilidade de execuções de subagentes via CLI.
  - Aprendizado contínuo da organização preservado no AI Memory de forma auditável e automática para o core.
  - Proteção absoluta de produção (`main`) inalterada e inviolável.
- **Negativas / Limitações:**
  - Revisões provisórias em sandbox não substituem auditoria humana para liberação em produção.
  - O runtime Antigravity local ainda não fornece telemetria granular de tokens por subagente, mantendo o status `NÃO MEDIDO` para custos.
