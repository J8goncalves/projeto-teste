import os
import sys
import json
import re

fails = []

def fail(msg):
    fails.append(msg)
    print(f"FALHA: {msg}")

def ok(msg):
    print(f"OK: {msg}")

# 1. Regras
rule_files = [f for f in os.listdir('.agents/rules') if f.endswith('.md')]
always_on_size = 0
if os.path.exists('AGENTS.md'):
    always_on_size += os.path.getsize('AGENTS.md')

for f in rule_files:
    path = f".agents/rules/{f}"
    size = os.path.getsize(path)
    if size > 24 * 1024:
        fail(f"Arquivo {f} maior que 24KB")
    with open(path, 'r', encoding='utf-8') as file:
        content = file.read()
        if not content.startswith('---'):
            fail(f"{f} nao comeca com frontmatter")
        else:
            fm = content.split('---')[1]
            if 'trigger: always_on' in fm:
                always_on_size += size
            if 'trigger:' not in fm:
                fail(f"{f} sem trigger")
            if 'trigger: model_decision' in fm and 'description:' not in fm:
                fail(f"{f} model_decision sem description")

if always_on_size > 12 * 1024:
    fail(f"always_on_size > 12KB ({always_on_size} bytes)")
else:
    ok("Regras validadas")

# 2. Cards
cards = ["orchestrator", "ceo", "market-researcher", "customer-researcher", "product-strategist", "marketing-strategist", "critical-reviewer", "legal-compliance", "experiment-designer", "data-analytics", "product-manager", "architect", "developer", "security-reviewer", "qa", "devops-finops"]
allowed_tools = ['view_file', 'list_dir', 'find_by_name', 'grep_search', 'search_web', 'read_url_content', 'write_to_file', 'replace_file_content', 'multi_replace_file_content', 'run_command']

for c in cards:
    p = f".agents/agents/{c}.md"
    if not os.path.exists(p):
        fail(f"Card {c} nao existe")
        continue
    with open(p, 'r', encoding='utf-8') as file:
        content = file.read()
        fm = content.split('---')[1]
        if f'name: {c}' not in fm: fail(f"Name incorreto em {c}")
        if 'skills:' in fm: fail(f"skills: presente em {c}")
        if 'commandExecutionPolicy' not in fm: fail(f"commandExecutionPolicy ausente em {c}")
        
        main = re.search(r'mainAgent:\s*(true|false)', fm)
        if main and main.group(1) == 'true' and c != 'orchestrator': fail(f"{c} tem mainAgent true")
        if main and main.group(1) == 'false' and c == 'orchestrator': fail(f"orchestrator tem mainAgent false")

        mod = re.search(r'model:\s*(\w+)', fm)
        if not mod or mod.group(1) not in ['inherit', 'flash', 'pro']: fail(f"Model incorreto em {c}")
        
        if '## Definition of Done' not in content: fail(f"DoD ausente em {c}")
        if '## Memória' not in content: fail(f"Memoria ausente em {c}")
        if '## Regras' not in content: fail(f"Regras Globais ausente em {c}")

        tools_match = re.search(r'tools:\s*\n((?:\s*-\s*\w+\n)+)', fm)
        if tools_match:
            tools = re.findall(r'-\s*(\w+)', tools_match.group(1))
            for t in tools:
                if t not in allowed_tools:
                    fail(f"Tool não permitida em {c}: {t}")

ok("Cards validados")

# 3. Skills
skills_aprovadas = ["org-intake", "org-run", "org-gate", "org-memory-ops", "org-decision-docs", "org-agent-eval", "legal-reference", "market-research-playbook", "product-strategy-playbook", "gtm-playbook"]
for s in skills_aprovadas:
    p = f".agents/skills/{s}/SKILL.md"
    if not os.path.exists(p):
        fail(f"Skill {s} não existe")
    else:
        with open(p, 'r', encoding='utf-8') as file:
            fm = file.read().split('---')[1]
            if 'description:' not in fm: fail(f"Description ausente na skill {s}")
            if f'name: {s}' not in fm: fail(f"Name incorreto na skill {s}")
ok("Skills validadas")

# 4. Políticas
with open('.agents/policies/transitions.json', 'r', encoding='utf-8') as f:
    try:
        j = json.load(f)
    except:
        fail("transitions.json invalido")
        
with open('.agents/policies/levels.json', 'r', encoding='utf-8') as f:
    try:
        j = json.load(f)
    except:
        fail("levels.json invalido")
ok("Politicas parseadas")

# 5. Texto
terms = ['ceo-orchestrator', 'CONDITIONAL GO', 'princpios']
for root, dirs, files in os.walk('.agents'):
    for f in files:
        if f.endswith('.md'):
            with open(os.path.join(root, f), 'r', encoding='utf-8') as file:
                content = file.read()
                for t in terms:
                    if t in content:
                        fail(f"Termo {t} encontrado em {f}")
ok("Texto validado")

# 6. Hooks
if os.path.exists('.agents/hooks.json'):
    with open('.agents/hooks.json', 'r', encoding='utf-8') as f:
        try:
            h = json.load(f)
            for k, v in h.items():
                if v.get('enabled'): fail(f"Hook {k} esta ativado!")
        except Exception as e:
            fail("hooks.json invalido")
ok("Hooks validados")

if fails:
    sys.exit(1)
print("Todas as verificacoes de org_check.py passaram.")
