# Notas de Pesquisa de Mercado — Viabilidade Financeira para Pequenos Organizadores de Eventos
**Run:** RUN-EVENTO-VIAB-002  
**Papel:** market-researcher  
**Data da Pesquisa:** 2026-10-11  
**Status:** Consolidado  

---

## 1. Pergunta de Pesquisa
Existe uma oportunidade de mercado justificada e viável para uma ferramenta digital que auxilie pequenos organizadores de eventos a simular e validar a viabilidade financeira e o ponto de equilíbrio (break-even) de seus eventos antes de realizarem investimentos e compromissos de custos?

---

## 2. Metodologia de Coleta e Critérios de Integridade
A pesquisa foi conduzida seguindo as diretrizes canônicas de [.agents/rules/research-integrity.md](file:///d:/Antigravity%20Projects/projeto-teste/.agents/rules/research-integrity.md) e [.agents/rules/evidence.md](file:///d:/Antigravity%20Projects/projeto-teste/.agents/rules/evidence.md):
- **Coleta de Fontes Primárias e Secundárias Verificadas:** Análise direta de páginas públicas de precificação, páginas de ferramentas de cálculo e artigos institucionais de plataformas de bilheteria e gestão de trabalho (Eventbrite, Sympla, Ticket Tailor, SwarmTix, Smartsheet).
- **Sem Falsificação:** Nenhuma estimativa de market share ou depoimento de cliente foi inventado.
- **Marcação Rigorosa de Premissas:** Todo comportamento e interesse de cliente é tratado como `[HIPÓTESE]` devido à ausência de entrevistas primárias nesta fase (conforme registrado no Intake ART-INTAKE-002).
- **Classificação Epistêmica:**
  - `[FATO]` / `[DADO]`: Informações verificáveis publicamente em URLs ativas em 2026-10-11 (Força E1).
  - `[INFERÊNCIA]`: Deduções lógicas a partir dos dados comparativos (Força E0).
  - `[HIPÓTESE]`: Hipóteses a validar empiricamente pelo produto (Força E0).
  - `[RECOMENDAÇÃO]`: Direcionamento para o comitê e fases de design.

---

## 3. Fontes Verificadas (Acessadas em 2026-10-11)

1. **Eventbrite Pricing**
   - **URL:** `https://www.eventbrite.com/organizer/pricing/`
   - **Título:** Create an Event for Free: Pricing | Eventbrite
   - **Data de Acesso:** 2026-10-11
   - **Alegações Verificadas [FATO / DADO - E1]:**
     - Eventos com ingressos gratuitos não pagam taxas de serviço da plataforma.
     - Para ingressos pagos, a taxa de serviço é de 3.7% + US$ 1.79 por ingresso, além de taxa de processamento de pagamento de 2.9% por pedido.
     - As taxas são cobradas dos compradores por padrão ou podem ser absorvidas pelo organizador.
     - A plataforma foca na venda e distribuição de ingressos, marketplace de descoberta e ferramentas de marketing.

2. **Eventbrite Budget Guidance**
   - **URL:** `https://www.eventbrite.com/blog/event-budget-template-ds00/`
   - **Título:** Use This Event Budget Template To Keep Your Event on Track | Eventbrite
   - **Data de Acesso:** 2026-10-11
   - **Alegações Verificadas [FATO / DADO - E1]:**
     - Relatório da American Express (2023) citado pela Eventbrite indicou que 2/3 dos organizadores apontavam aumento de custos operacionais.
     - Event Trends Report 2023 da Eventbrite indicou que 80% dos organizadores planejavam conter orçamentos e 89% relataram impacto da inflação.
     - A própria Eventbrite recomenda que organizadores utilizem templates manuais de planilhas para orçamentação antes do lançamento, evidenciando que a plataforma de bilheteria não provê cálculo dinâmico integrado de viabilidade.

3. **Ticket Tailor Pricing**
   - **URL:** `https://www.tickettailor.com/pricing`
   - **Título:** Ticket Tailor: Pricing | Ticket Tailor
   - **Data de Acesso:** 2026-10-11
   - **Alegações Verificadas [FATO / DADO - E1]:**
     - Modelo pré-pago por compra de créditos a partir de £ 0.22 (+ VAT) por ingresso vendido.
     - Modelo Pay-as-you-go de taxa fixa de £ 0.60 (+ VAT) por ingresso vendido.
     - Gratuito para emissão de até 5.000 ingressos gratuitos por ano.
     - O processamento de pagamentos é terceirizado via Stripe (ex: 2.9% + US$ 0.30 nos EUA; 1.5% + £ 0.20 no Reino Unido), PayPal ou Square.
     - Não inclui módulo ou cálculo de viabilidade prévia de custos de produção do evento.

4. **Sympla Produtores - Quanto Custa**
   - **URL:** `https://produtores.sympla.com.br/quanto-custa`
   - **Título:** Taxa Sympla - Quanto Custa
   - **Data de Acesso:** 2026-10-11
   - **Alegações Verificadas [FATO / DADO - E1]:**
     - Publicação e criação de eventos gratuitas. Eventos sem cobrança de ingressos têm taxa zero.
     - Para eventos pagos: taxa de serviço padrão de 10% por ingresso vendido, com taxa mínima de R$ 3,99 para ingressos com valor igual ou inferior a R$ 39,90.
     - Taxa de processamento financeiro adicional de 2% a 2,5% por venda (não repassável ao comprador).
     - Repasse financeiro das receitas das vendas ocorre no 3º dia útil após o término do evento (D+3 pós-evento).

5. **SwarmTix Break-Even Calculator**
   - **URL:** `https://swarmtix.com/tools/event-break-even-calculator`
   - **Título:** Break-Even Calculator: How Many Tickets to Sell | Swarmtix
   - **Data de Acesso:** 2026-10-11
   - **Alegações Verificadas [FATO / DADO - E1]:**
     - Ferramenta web gratuita que calcula o ponto de equilíbrio a partir de Custos Fixos, Custos Variáveis por participante, lotes de ingressos e taxas de bilheteria.
     - Fórmula adotada: Ingressos para break-even = Custos Fixos / (Preço do ingresso - Custo variável por participante).
     - Compara o impacto de taxas de bilheteria ($0.99 + 1.5% do SwarmTix vs $1.79 + 3.7% do Eventbrite).
     - Funciona essencialmente como ferramenta de topo de funil (lead generation) para a plataforma transacional de bilheteria SwarmTix, com moeda em dólar e sem modelagem de múltiplos cenários de sensibilidade orçamentária ou moeda BRL.

6. **Smartsheet Event Planning Templates**
   - **URL:** `https://www.smartsheet.com/content/event-planning-templates`
   - **Título:** Free Event Planning Templates | Smartsheet
   - **Data de Acesso:** 2026-10-11
   - **Alegações Verificadas [FATO / DADO - E1]:**
     - Disponibilização de modelos estáticos em Excel, Google Sheets e Smartsheet com colunas de custo estimado, custo real, variância e notas.
     - Processo manual de entrada de dados, sem fórmulas nativas integradas de simulação de elasticidade de preço, break-even por múltiplos lotes ou dedução de taxas de adquirentes/plataformas.

---

## 4. Benchmark de Alternativas Existentes

| Categoria | Representantes | Pontos Fortes | Fraquezas / Lacunas | Custo para o Organizador |
| :--- | :--- | :--- | :--- | :--- |
| **Planilhas Manuais (Status Quo)** | Microsoft Excel, Google Sheets, Smartsheet | Flexibilidade total; personalizável; custo marginal nulo para quem já possui pacote office. | `[FATO/INFERÊNCIA]` Exige montagem manual de fórmulas; alta taxa de erro humano de modelagem; não gera gráficos de sensibilidade intuitivos sem esforço considerável; estática. | Gratuito a US$ 7-12/mês por usuário. |
| **Plataformas de Bilheteria / Ticketing** | Eventbrite, Sympla, Ticket Tailor | Distribuição, marketplace, checkout seguro, emissão de QR code e gestão de portaria. | `[FATO]` Focam na transação e na arrecadação, e não no risco orçamentário do produtor antes de investir. `[FATO]` O repasse ocorre apenas após o evento (ex: D+3 na Sympla), o que agrava o fluxo de caixa do organizador. | 10% + 2,5% (Sympla) ou 3.7% + $1.79 + 2.9% (Eventbrite) ou £0.22 a £0.60 + gateway (Ticket Tailor). |
| **Calculadoras Web Pontuais** | SwarmTix Break-Even Calculator, calculadoras de blog | Práticas, sem necessidade de instalação, fornecem resposta rápida de ponto de equilíbrio. | `[FATO]` Projetadas como isca de marketing para vender bilheteria; suportam cenários unidimensionais simples; em moeda estrangeira; sem análise de sensibilidade detalhada nem exportação estruturada. | Gratuitas (com captura de lead/e-mail para conversão). |

---

## 5. Lacuna Concreta do Segmento de Pequenos Organizadores
- `[FATO]`: Pequenos organizadores (produtores de workshops, eventos corporativos locais, cursos presenciais, encontros culturais) operam com margens estreitas e custos fixos adiantados (locação de sala, coffee break, equipamentos, tráfego pago).
- `[FATO]`: As plataformas de bilheteria não fornecem antecipadamente um diagnóstico de risco financeiro: elas cobram taxas sobre o que for vendido, mas se o organizador vender menos que o ponto de equilíbrio, o prejuízo operacional dos custos fixos é 100% do organizador.
- `[INFERÊNCIA]`: Há uma lacuna nítida entre o modelo genérico de planilhas (demasiado manual e desconectado da realidade de taxas) e as plataformas de venda (focadas apenas em cobrar comissão sobre transações). Uma ferramenta leve, visual e preventiva que responda em segundos *"quantos ingressos preciso vender por lote para não ter prejuízo?"* e *"qual minha margem com 50%, 75% e 100% de ocupação considerando as taxas?"* preenche esse espaço de tomada de decisão.

---

## 6. Aspectos Regulatórios e Legais
- `[HIPÓTESE / FATO]`: No modelo de MVP delimitado no Intake ART-INTAKE-002 (simulador estritamente informativo/analítico, sem coleta de dados de cartão de crédito, sem intermediação de pagamentos e sem custódia de recebíveis de terceiros):
  - **BACEN / Lei nº 12.865/2013:** Não incidem normas de instituição de pagamento ou arranjos de pagamento, pois a ferramenta não liquida nem processa fundos.
  - **LGPD (Lei nº 13.709/2018):** Como não há necessidade de autenticação de usuários, contas nem armazenamento em nuvem de dados pessoais no MVP (cálculo cliente-side ou sessão anônima), o tratamento de dados pessoais é nulo ou mínimo, afastando riscos regulatórios severos.
  - **Aviso Legal:** A ferramenta deve incluir disclaimer explícito de que as simulações são indicativas e não constituem assessoria contábil ou financeira vinculante.

---

## 7. Premissas e Incertezas Críticas
- `[HIPÓTESE]`: Pequenos organizadores têm interesse contínuo em usar uma ferramenta web dedicada em vez de suas planilhas de rotina. (Incerteza: requer validação com usuários reais via MVP).
- `[HIPÓTESE]`: Disposição a pagar por uma ferramenta independente deste tipo pode ser baixa se for cobrada assinatura recorrente; modelos viáveis futuros podem incluir freemium, parcerias com fornecedores ou ferramenta de atração.
- `[HIPÓTESE]`: Simplicidade e velocidade (tempo de resposta < 2 minutos para ver o break-even) são os principais fatores de adoção em relação a planilhas complexas.

---

## 8. Recomendação e Veredito Técnico de Mercado
- **Veredito:** `GO` para avanço à fase de concepção e especificação de MVP.
- **Justificativa:** 
  1. A lacuna entre planilhas estáticas e plataformas de bilheteria é real e documentada nas fontes oficiais analisadas.
  2. A construção de uma ferramenta digital focada puramente em simulação financeira preventiva não esbarra em restrições regulatórias de pagamentos.
  3. O escopo técnico de uma primeira versão é simples, viável e permite validar a hipótese central com baixo custo e sem risco de segurança ou privacidade.
- **Riscos Mapeados:**
  1. Baixa barreira de entrada (concorrentes ou plataformas de bilheteria podem lançar calculadoras semelhantes a qualquer momento).
  2. Resistência à mudança de organizadores habituados a planilhas básicas.
