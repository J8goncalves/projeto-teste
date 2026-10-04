import os
import json

guards = [
    {'id': 'kill-switch', 'ferramentas': ['*'], 'padrao': 'existe .agents/state/STOP', 'decisao': 'deny', 'motivo': 'Kill switch acionado.'},
    {'id': 'run-parada', 'ferramentas': ['write_to_file', 'replace_file_content', 'multi_replace_file_content', 'run_command', 'invoke_subagent'], 'padrao': 'estado da run em ESCALATED ou PAUSED, exceto comandos de state.py status, events.py e kill.py status', 'decisao': 'deny', 'motivo': 'Run parada ou escalonada. Aguardando intervenção humana.'},
    {'id': 'ferramentas-proibidas', 'ferramentas': ['schedule', 'define_subagent'], 'padrao': '.*', 'decisao': 'deny', 'motivo': 'Ferramenta proibida nesta organização.'},
    {'id': 'segredos-arquivos', 'ferramentas': ['read_file', 'write_to_file', 'replace_file_content', 'multi_replace_file_content'], 'padrao': r'\.env(?!(\.example|\.sample|\.template))|\.pem$|\.key$|\.p12$|\.pfx$|id_rsa|id_ed25519|credentials.*\.json$|\.npmrc$|\.pypirc$|\.tfstate$', 'decisao': 'deny', 'motivo': 'Acesso a arquivos de segredos bloqueado.'},
    {'id': 'segredos-comandos', 'ferramentas': ['run_command'], 'padrao': r'(cat|type|more|less|head|tail|Get-Content)\s+.*\.env|printenv|^env$|Env:', 'decisao': 'deny', 'motivo': 'Acesso a segredos no terminal bloqueado.'},
    {'id': 'destrutivo-catastrofico', 'ferramentas': ['run_command'], 'padrao': r'rm\s+-r[f]?\s+(/|~|\$HOME|\*|C:\\)|rd\s+/s\s+/q\s+.*|del\s+/s\s+/q\s+.*', 'decisao': 'deny', 'motivo': 'Comando destrutivo catastrófico bloqueado.'},
    {'id': 'destrutivo', 'ferramentas': ['run_command'], 'padrao': r'rm\s+-r|Remove-Item\s+-Recurse|rd\s+/s|git\s+clean\s+-f|git\s+reset\s+--hard', 'decisao': 'force_ask', 'motivo': 'Confirmação exigida para comando destrutivo.'},
    {'id': 'git-push-forcado', 'ferramentas': ['run_command'], 'padrao': r'git\s+push\s+.*(--force|-f|--force-with-lease)|git\s+push\s+.*(main|master)', 'decisao': 'deny', 'motivo': 'Push forçado ou para branch principal bloqueado.'},
    {'id': 'git-branch-principal', 'ferramentas': ['run_command'], 'padrao': r'(git\s+commit|git\s+merge)\s+.*', 'decisao': 'deny', 'motivo': 'Operação bloqueada: a branch atual é a principal.'},
    {'id': 'git-publicacao', 'ferramentas': ['run_command'], 'padrao': r'git\s+(push|merge|rebase)|gh\s+(pr\s+merge|release|workflow\s+run)', 'decisao': 'force_ask', 'motivo': 'Confirmação exigida para publicar código.'},
    {'id': 'deploy-nuvem', 'ferramentas': ['run_command'], 'padrao': r'^(gcloud|aws|az|kubectl|helm|terraform|pulumi|firebase|vercel|netlify|heroku|fly|flyctl|wrangler|docker\s+push|docker\s+login|npm\s+publish|yarn\s+publish|pnpm\s+publish|twine\s+upload)', 'decisao': 'force_ask', 'motivo': 'Confirmação exigida para deploy ou cloud.'},
    {'id': 'suprimentos', 'ferramentas': ['run_command'], 'padrao': r'npx\s+|pnpm\s+dlx|yarn\s+dlx|pipx\s+run|uvx|npm\s+(install|i|add).*(-g|.*)|yarn\s+add|pnpm\s+add|pip\s+install(?!\s+-r)|cargo\s+(add|install)|go\s+install|agy\s+plugin|npx\s+skills\s+add|memanto\s+connect', 'decisao': 'force_ask', 'motivo': 'Confirmação exigida para instalar pacotes de terceiros.'},
    {'id': 'memanto-direto', 'ferramentas': ['run_command'], 'padrao': r'memanto\s+(remember|edit|forget|upload|migrate|connect|serve|ui|schedule|policy|memory|agent|answer|recall|daily-summary|detect-conflicts|conflicts)', 'decisao': 'deny', 'motivo': 'Use o wrapper memory_ops.py em vez do CLI do Memanto.'}
]

with open('.agents/policies/guards.json', 'w', encoding='utf-8') as f:
    json.dump(guards, f, ensure_ascii=False, indent=2)
print('Fixed guards.json')
