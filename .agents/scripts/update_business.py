import os

filepath = '.agents/rules/business-governance.md'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Make sure frontmatter is exactly as instructed
lines = content.split('\n')
new_lines = []
in_frontmatter = False
frontmatter_done = False

for line in lines:
    if not frontmatter_done and line == '---':
        if not in_frontmatter:
            in_frontmatter = True
        else:
            in_frontmatter = False
            frontmatter_done = True
            new_lines.append("trigger: model_decision")
            new_lines.append('description: "Regras de governança e dinâmica de comunicação para o Business Pod (Comitê Executivo). Aplique no Discovery, no debate do comitê, na arbitragem e no formato das decisões."')
            new_lines.append("---")
        continue
    if in_frontmatter:
        continue # drop old frontmatter
    new_lines.append(line)

if not frontmatter_done:
    new_lines = ["---", "trigger: model_decision", 'description: "Regras de governança e dinâmica de comunicação para o Business Pod (Comitê Executivo). Aplique no Discovery, no debate do comitê, na arbitragem e no formato das decisões."', "---"] + new_lines

content = '\n'.join(new_lines)

# Apply text modifications manually. Since the prompt tells us to "Substitua o primeiro item por...", it's easier to do string replacements if we find the text.
# For section 1:
s1_old1 = "- Os agentes especializados devem fazer suas análises de forma independente ao receberem um brief do orchestrator."
s1_new1 = "- Ao receberem um brief do `orchestrator`, os agentes especializados (`market-researcher`, `customer-researcher`, `product-strategist`, `marketing-strategist`, `critical-reviewer`, `legal-compliance`) devem fazer suas análises iniciais de forma **independente**."
content = content.replace(s1_old1, s1_new1)

if "Ordem: (1)" not in content:
    content = content.replace('evidência (`evidence.md`).', 'evidência (`evidence.md`).\n- Ordem: (1) `market-researcher` e `customer-researcher` com briefings separados; (2) `product-strategist` e depois `marketing-strategist`, que consomem os relatórios da etapa 1; (3) `critical-reviewer` e `legal-compliance`, em paralelo, revisam o material original e o consolidado. Antes de entregar seu parecer, os agentes independentes recebem da memória apenas fatos, instruções e aprendizados metodológicos (`memory.md`).')

# For section 2:
s2_old1 = "- Se houver divergência material entre os agentes (conclusões contraditórias baseadas em evidências diferentes), o orchestrator convoca um debate."
s2_new1 = "- Se houver divergência material entre agentes (conclusões que se contradizem, com evidência dos dois lados), o `orchestrator` convoca o debate. Sem divergência material, não há debate."
content = content.replace(s2_old1, s2_new1)

if "Limite: no máximo 2 rodadas" not in content:
    content = content.replace('fatos para embasar a posição.', 'fatos para embasar a posição.\n- Limite: no máximo 2 rodadas de réplica, cada agente respondendo uma vez por rodada. Sem consenso, o `orchestrator` documenta as posições no Decision Package e segue.')

# For section 3:
s3_old1 = "- O orchestrator é responsável por consolidar o Decision Package de forma objetiva, apontando prós, contras e riscos sem tomar partido."
s3_new1 = "- O `orchestrator` monta o Decision Package de forma mecânica (links, divergências, vetos, força da evidência, custo, riscos), sem síntese avaliativa. No Nível 3, o `ceo` lê o pacote e RECOMENDA; o humano decide (A1). Nos Níveis 1 e 2 não há CEO e o humano decide pelo pacote."
content = content.replace(s3_old1, s3_new1)

s3_old2 = "o CEO deve documentar as posições e **escalar para o usuário** no Decision Memo"
s3_new2 = "as posições são documentadas no Decision Package e o `ceo` (Nível 3) as expõe no memo para decisão do usuário"
content = content.replace(s3_old2, s3_new2)

# For section 4:
if "O parecer jurídico pertence" not in content:
    content = content.replace('não é ignorado ou diluído em médias.', 'não é ignorado ou diluído em médias.\n- O parecer jurídico pertence ao `legal-compliance`, obrigatório quando houver gatilho jurídico (dado pessoal, setor regulado, contrato, propriedade intelectual, menores, crédito, saúde ou investimentos). O `critical-reviewer` incorpora os riscos jurídicos na sua matriz e não repete a pesquisa. Vetos seguem `vetoes.md`.')

# For section 5:
if "GO CONDICIONADO exige condições" not in content:
    content = content.replace('NO-GO', 'NO-GO\n- GO CONDICIONADO exige condições com dono, prazo e verificação; VALIDAR ANTES exige o que validar e o critério de sucesso; PIVOT exige a nova hipótese. O Executive Decision Memo (curto) fica em `intelligence/decisions/` com ID `DEC-###`; o Decision Package e o Handoff Package ficam em `docs/initiatives/<slug>/`.')

if "## 6. Níveis" not in content:
    content += "\n## 6. Níveis\nNível 1, 2 e 3 são definidos em `governance.md`.\n"

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print('business-governance.md updated')
